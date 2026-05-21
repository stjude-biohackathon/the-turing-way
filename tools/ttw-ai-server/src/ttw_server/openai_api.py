"""FastAPI server exposing the same three tools in OpenAI's function-calling format."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ttw_server.content import ContentStore

# Tool definitions are kept in the OpenAI schema format so any LLM framework can
# consume them directly from GET /tools without additional transformation.
_TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_chapters",
            "description": "Return The Turing Way table of contents as a slug-title list.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_turing_way",
            "description": (
                "Search The Turing Way for chapters relevant to a query. "
                "Returns up to five matching chapters with excerpts where available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Keywords or a plain-English question about "
                            "data science, research practice, or reproducibility."
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_chapter",
            "description": "Retrieve the full Markdown source of a Turing Way chapter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": (
                            "Chapter identifier from list_chapters, "
                            "such as 'reproducible-research/overview'."
                        ),
                    }
                },
                "required": ["slug"],
            },
        },
    },
]


class ToolCallRequest(BaseModel):
    arguments: dict[str, Any] = {}


def create_app(github_token: Optional[str] = None) -> FastAPI:
    store = ContentStore(github_token=github_token)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Warm the TOC before accepting requests so the first search is not the one
        # that triggers the blocking myst.yml fetch.
        await store._ensure_toc()
        # Preloading runs in the background so startup remains fast.
        preload_task = asyncio.create_task(store.preload_content())
        yield
        preload_task.cancel()
        await store.close()

    app = FastAPI(
        title="The Turing Way Tool Server",
        description=(
            "Exposes The Turing Way as OpenAI-compatible function-calling endpoints. "
            "Fetch tool definitions from GET /tools, then POST to /tools/{name} to invoke them."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/tools")
    async def list_tools() -> list:
        return _TOOL_DEFINITIONS

    @app.post("/tools/list_chapters")
    async def call_list_chapters() -> dict:
        chapters = await store.list_chapters()
        return {"result": "\n".join(f"{c.slug}  —  {c.title}" for c in chapters)}

    @app.post("/tools/search_turing_way")
    async def call_search(body: ToolCallRequest) -> dict:
        query: str = body.arguments.get("query", "")
        if not query:
            raise HTTPException(status_code=422, detail="'query' is required.")
        results = await store.search(query)
        if not results:
            return {"result": "No chapters matched your query."}
        parts: list[str] = []
        for r in results:
            entry = f"{r.chapter.title} ({r.chapter.slug})"
            if r.excerpt:
                entry += f"\n{r.excerpt}"
            parts.append(entry)
        return {"result": "\n\n".join(parts)}

    @app.post("/tools/get_chapter")
    async def call_get_chapter(body: ToolCallRequest) -> dict:
        slug: str = body.arguments.get("slug", "")
        if not slug:
            raise HTTPException(status_code=422, detail="'slug' is required.")
        content = await store.get_chapter(slug)
        if content is None:
            raise HTTPException(status_code=404, detail=f"Chapter '{slug}' was not found.")
        return {"result": content}

    return app


def run(host: str = "0.0.0.0", port: int = 8000, github_token: Optional[str] = None) -> None:
    app = create_app(github_token=github_token)
    uvicorn.run(app, host=host, port=port)
