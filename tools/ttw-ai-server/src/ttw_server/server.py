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
        "and get_chapter to read a specific chapter in full."
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

    Args:
        slug: Chapter identifier from list_chapters, such as "reproducible-research/overview".
    """
    content = await _store.get_chapter(slug)
    if content is None:
        return f"Chapter '{slug}' was not found. Use list_chapters to browse available slugs."
    return content


def run() -> None:
    # stdio transport is required for Claude Desktop and Claude Code MCP integration.
    mcp.run(transport="stdio")
