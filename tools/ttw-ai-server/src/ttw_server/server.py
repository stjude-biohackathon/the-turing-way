"""MCP server exposing The Turing Way as three callable tools."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from ttw_server.content import ContentStore

# One store per process; the token is optional but avoids GitHub's unauthenticated rate limit.
_store = ContentStore(github_token=os.environ.get("GITHUB_TOKEN"))

mcp = FastMCP(
    "The Turing Way",
    instructions=(
        "You have access to The Turing Way, a community handbook for reproducible, "
        "ethical, and collaborative data science. "
        "Use list_chapters to explore available topics, "
        "search_turing_way to find chapters by keyword, "
        "get_chapter to read a specific chapter in full (commit metadata is appended automatically), "
        "and get_recent_changes to see what has been edited recently across the book or within a single chapter."
    ),
)


@mcp.tool()
async def list_chapters() -> str:
    """Return The Turing Way table of contents as a slug-title list."""
    chapters = await _store.list_chapters()
    return "\n".join(f"{c.slug}  —  {c.title}" for c in chapters)


@mcp.tool()
async def search_turing_way(query: str) -> str:
    """Search The Turing Way for chapters relevant to a query.

    Args:
        query: Keywords or a plain-English question about data science or research.
    """
    results = await _store.search(query)
    if not results:
        return "No chapters matched your query."
    parts: list[str] = []
    for r in results:
        entry = f"**{r.chapter.title}** (`{r.chapter.slug}`)"
        if r.excerpt:
            entry += f"\n{r.excerpt}"
        parts.append(entry)
    return "\n\n".join(parts)


@mcp.tool()
async def get_chapter(slug: str) -> str:
    """Retrieve the full Markdown source of a Turing Way chapter.

    A footer with the most recent commit (date, author, message, link) is
    appended automatically so the caller knows how current the content is.

    Args:
        slug: Chapter identifier from list_chapters, such as "reproducible-research/overview".
    """
    content = await _store.get_chapter(slug)
    if content is None:
        return f"Chapter '{slug}' was not found. Use list_chapters to browse available slugs."
    commit = await _store.get_chapter_commit(slug)
    if commit:
        content += (
            f"\n\n---\n"
            f"*Last updated: {commit.date} — "
            f"[{commit.sha}]({commit.url}) "
            f"by {commit.author}: {commit.message}*"
        )
    return content


@mcp.tool()
async def get_recent_changes(limit: int = 10, slug: str = "") -> str:
    """Return recent commits to The Turing Way book content.

    Args:
        limit: Number of commits to return (1–30, default 10).
        slug:  Optional chapter slug (from list_chapters) to scope results to one
               chapter. Leave empty to see recent changes across the whole book.
    """
    limit = max(1, min(limit, 30))
    commits = await _store.get_recent_changes(limit=limit, slug=slug or None)
    if not commits:
        return "No recent commits found."
    scope = f"chapter `{slug}`" if slug else "the whole book"
    header = f"**{len(commits)} recent commit(s) to {scope}:**\n"
    lines = [
        f"- [{c.sha}]({c.url}) {c.date} **{c.author}**: {c.message}"
        for c in commits
    ]
    return header + "\n".join(lines)


def run() -> None:
    # stdio transport is required for Claude Desktop and Claude Code MCP integration.
    mcp.run(transport="stdio")
