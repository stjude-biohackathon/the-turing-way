"""Fetch and cache Turing Way chapters from GitHub for tool-callable search."""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Optional

import httpx
import yaml
from rank_bm25 import BM25Okapi

# Raw content is served without authentication, but a token raises the hourly
# rate limit from 60 to 5 000 requests, which matters when preloading all chapters.
_RAW_BASE = (
    "https://raw.githubusercontent.com"
    "/the-turing-way/the-turing-way/main/book/website"
)
_MYST_YML_URL = f"{_RAW_BASE}/myst.yml"

# GitHub REST API base for the upstream repository.
_API_BASE = "https://api.github.com/repos/the-turing-way/the-turing-way"

# One refresh per day keeps the chapter list current without hammering GitHub.
_TOC_TTL_SECONDS: float = 86_400.0

# Commit metadata is refreshed hourly — frequent enough to catch recent edits,
# infrequent enough to stay well within the authenticated rate limit.
_COMMIT_TTL_SECONDS: float = 3_600.0

# Spacing between background fetches avoids saturating GitHub's rate limiter.
_PRELOAD_INTERVAL_SECONDS: float = 0.2


@dataclass(frozen=True)
class Chapter:
    title: str
    file: str   # Path relative to book/website/, e.g. "reproducible-research/overview.md"
    slug: str   # File path without the .md suffix, used as a stable public identifier
    guide: str  # Top-level section name derived from the first path component
    depth: int  # Nesting level in the TOC; 0 = guide root, 1 = chapter, 2 = subchapter


@dataclass(frozen=True)
class CommitInfo:
    sha: str      # Short (7-char) commit hash
    message: str  # First line of the commit message
    author: str   # Display name of the commit author
    date: str     # ISO-8601 date, e.g. "2024-03-15"
    url: str      # Link to the commit on GitHub


@dataclass(frozen=True)
class SearchResult:
    chapter: Chapter
    score: float
    excerpt: Optional[str]  # None when the chapter has not been fetched yet


class ContentStore:
    def __init__(self, github_token: Optional[str] = None) -> None:
        headers: dict[str, str] = {}
        if github_token:
            # Bearer auth is required by GitHub's API; Basic auth no longer works.
            headers["Authorization"] = f"Bearer {github_token}"
        self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        self._chapters: list[Chapter] = []
        self._content: dict[str, str] = {}       # slug → raw Markdown text
        self._refreshed_at: float = float("-inf")  # force a fetch on the first call
        self._bm25: Optional[BM25Okapi] = None   # rebuilt lazily whenever content changes
        self._bm25_slugs: list[str] = []         # parallel to the BM25 corpus rows
        self._index_dirty: bool = True
        # Commit metadata caches — keyed by slug (chapter) or a path string (recent changes).
        self._chapter_commit_cache: dict[str, CommitInfo] = {}
        self._chapter_commit_fetched_at: dict[str, float] = {}
        self._recent_commit_cache: dict[str, list[CommitInfo]] = {}
        self._recent_commit_fetched_at: dict[str, float] = {}

    async def close(self) -> None:
        await self._client.aclose()

    # ── Public interface ────────────────────────────────────────────────────────

    async def list_chapters(self) -> list[Chapter]:
        await self._ensure_toc()
        return list(self._chapters)

    async def get_chapter(self, slug: str) -> Optional[str]:
        await self._ensure_toc()
        chapter = self._find_chapter(slug)
        if chapter is None:
            return None
        if slug not in self._content:
            text = await self._fetch_file(chapter.file)
            if text is not None:
                self._content[slug] = text
                # Adding full text changes this chapter's BM25 document from
                # title-only to the complete body, so the index must be rebuilt.
                self._index_dirty = True
        return self._content.get(slug)

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        await self._ensure_toc()
        if self._index_dirty:
            self._rebuild_index()
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        # Sort indices by descending score and stop once scores reach zero.
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results: list[SearchResult] = []
        for i in ranked:
            if scores[i] <= 0.0 or len(results) >= max_results:
                break
            chapter = self._find_chapter(self._bm25_slugs[i])
            if chapter is None:
                continue
            excerpt = _best_excerpt(self._content.get(chapter.slug, ""), query.lower().split())
            results.append(SearchResult(chapter=chapter, score=float(scores[i]), excerpt=excerpt))
        return results

    async def preload_content(self) -> None:
        """Gradually fetch every chapter so full-text search is available for all results."""
        await self._ensure_toc()
        for chapter in self._chapters:
            if chapter.slug not in self._content:
                await self.get_chapter(chapter.slug)
                # Spacing requests avoids saturating GitHub's rate limiter.
                await asyncio.sleep(_PRELOAD_INTERVAL_SECONDS)

    async def get_chapter_commit(self, slug: str) -> Optional[CommitInfo]:
        """Return the most recent commit that touched this chapter (1-hour cache)."""
        await self._ensure_toc()
        chapter = self._find_chapter(slug)
        if chapter is None:
            return None
        fetched_at = self._chapter_commit_fetched_at.get(slug, float("-inf"))
        if time.monotonic() - fetched_at < _COMMIT_TTL_SECONDS and slug in self._chapter_commit_cache:
            return self._chapter_commit_cache[slug]
        commits = await self._fetch_commits(f"book/website/{chapter.file}", limit=1)
        if not commits:
            return None
        info = _parse_commit(commits[0])
        self._chapter_commit_cache[slug] = info
        self._chapter_commit_fetched_at[slug] = time.monotonic()
        return info

    async def get_recent_changes(
        self, limit: int = 10, slug: Optional[str] = None
    ) -> list[CommitInfo]:
        """Return recent commits to book content, optionally scoped to one chapter.

        When slug is None the query covers the entire book/website tree.
        Results are cached for one hour per (slug, limit) combination.
        """
        if slug is not None:
            await self._ensure_toc()
            chapter = self._find_chapter(slug)
            if chapter is None:
                return []
            api_path = f"book/website/{chapter.file}"
        else:
            api_path = "book/website"
        cache_key = f"{api_path}:{limit}"
        fetched_at = self._recent_commit_fetched_at.get(cache_key, float("-inf"))
        if (
            time.monotonic() - fetched_at < _COMMIT_TTL_SECONDS
            and cache_key in self._recent_commit_cache
        ):
            return self._recent_commit_cache[cache_key]
        commits = await self._fetch_commits(api_path, limit=limit)
        result = [_parse_commit(c) for c in commits]
        self._recent_commit_cache[cache_key] = result
        self._recent_commit_fetched_at[cache_key] = time.monotonic()
        return result

    # ── Internal helpers ────────────────────────────────────────────────────────

    async def _ensure_toc(self) -> None:
        elapsed = time.monotonic() - self._refreshed_at
        if elapsed >= _TOC_TTL_SECONDS:
            await self._refresh_toc()

    async def _refresh_toc(self) -> None:
        try:
            response = await self._client.get(_MYST_YML_URL)
            response.raise_for_status()
            parsed = yaml.safe_load(response.text)
            toc_entries = parsed.get("project", {}).get("toc", [])
            chapters: list[Chapter] = []
            for entry in toc_entries:
                _walk_toc(entry, chapters, depth=0)
            self._chapters = chapters
            self._refreshed_at = time.monotonic()
            # Chapter list changed, so every document in the index is potentially stale.
            self._index_dirty = True
        except Exception:
            # Retain stale chapters rather than crashing; a first-time failure still raises.
            if not self._chapters:
                raise

    async def _fetch_file(self, file_path: str) -> Optional[str]:
        url = f"{_RAW_BASE}/{file_path}"
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError:
            return None

    async def _fetch_commits(self, path: str, limit: int) -> list[dict]:
        """Call the GitHub Commits API and return raw commit dicts.

        path is relative to the repository root, e.g. "book/website/reproducible-research/vcs.md".
        limit is capped at 100 (GitHub's per_page maximum).
        Returns an empty list on any error so callers can degrade gracefully.
        """
        url = f"{_API_BASE}/commits"
        params: dict = {"path": path, "per_page": min(limit, 100)}
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    def _find_chapter(self, slug: str) -> Optional[Chapter]:
        # Linear scan is acceptable; the chapter list is at most a few hundred entries.
        for chapter in self._chapters:
            if chapter.slug == slug:
                return chapter
        return None

    def _rebuild_index(self) -> None:
        corpus = [_build_document(c, self._content.get(c.slug)) for c in self._chapters]
        # BM25Okapi requires at least one document; guard against an empty chapter list.
        self._bm25 = BM25Okapi(corpus) if corpus else None
        self._bm25_slugs = [c.slug for c in self._chapters]
        self._index_dirty = False


# ── TOC parser ──────────────────────────────────────────────────────────────────

def _walk_toc(entry: dict, out: list[Chapter], depth: int) -> None:
    file_path: Optional[str] = entry.get("file")
    title: Optional[str] = entry.get("title")

    if file_path:
        slug = file_path.removesuffix(".md")
        # The guide name is the first path component, matching TTW's section prefixes.
        guide = slug.split("/")[0]
        out.append(Chapter(
            title=title or _title_from_slug(slug),
            file=file_path,
            slug=slug,
            guide=guide,
            depth=depth,
        ))

    for child in entry.get("children") or []:
        _walk_toc(child, out, depth=depth + 1)


def _title_from_slug(slug: str) -> str:
    # Fallback when the TOC entry has no explicit title field.
    leaf = slug.split("/")[-1]
    return leaf.replace("-", " ").title()


# ── BM25 helpers ────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _build_document(chapter: Chapter, content: Optional[str]) -> list[str]:
    # Title tokens are repeated so that title matches outweigh sparse mentions in
    # long body text — BM25 normalises for document length, so without this boost
    # a query like "version control" would rank a subchapter that mentions it once
    # above the version control guide landing page.
    title_tokens = _tokenize(chapter.title) * 3
    body = content if content else chapter.slug
    return title_tokens + _tokenize(body)


def _parse_commit(data: dict) -> CommitInfo:
    """Extract the fields we care about from a raw GitHub Commits API response dict."""
    commit = data.get("commit", {})
    author = commit.get("author", {})
    return CommitInfo(
        sha=data.get("sha", "")[:7],
        message=commit.get("message", "").split("\n")[0],
        author=author.get("name", "unknown"),
        date=author.get("date", "")[:10],  # keep only the YYYY-MM-DD part
        url=data.get("html_url", ""),
    )


def _best_excerpt(text: str, words: list[str]) -> Optional[str]:
    """Return the paragraph that contains the most query words, truncated to 300 characters."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    best: Optional[str] = None
    best_count = 0
    for para in paragraphs:
        para_lower = para.lower()
        count = sum(1 for w in words if w in para_lower)
        if count > best_count:
            best_count = count
            best = para
    if best is None:
        return None
    # Truncating keeps responses within typical LLM context limits.
    return best[:300] + ("…" if len(best) > 300 else "")
