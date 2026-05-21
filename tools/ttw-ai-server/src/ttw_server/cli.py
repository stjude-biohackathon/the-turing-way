"""Command-line entry point for the TTW AI server."""

from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ttw-server",
        description="Serve The Turing Way as a tool-callable knowledge base.",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser(
        "mcp",
        help="Run the MCP server on stdio (for Claude Desktop and Claude Code).",
    )

    http_parser = subparsers.add_parser(
        "http",
        help="Run the OpenAI-compatible HTTP server.",
    )
    http_parser.add_argument("--host", default="0.0.0.0", help="Bind address.")
    http_parser.add_argument("--port", type=int, default=8000, help="Listen port.")

    args = parser.parse_args()

    # Read the token here so neither server module needs to know about the environment.
    github_token: str | None = os.environ.get("GITHUB_TOKEN")

    if args.mode == "mcp":
        # The MCP server owns its own store and token; import is deferred to avoid
        # loading FastAPI and uvicorn when only the MCP runtime is needed.
        from ttw_server import server as mcp_server
        if github_token:
            mcp_server._store._client.headers["Authorization"] = f"Bearer {github_token}"
        mcp_server.run()

    elif args.mode == "http":
        from ttw_server.openai_api import run as http_run
        http_run(host=args.host, port=args.port, github_token=github_token)

    else:
        # argparse enforces valid modes, so this branch is unreachable in normal use.
        parser.print_help()
        sys.exit(1)
