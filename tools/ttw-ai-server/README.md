# The Turing Way AI Server

This server makes _The Turing Way_ available as a set of callable tools for AI assistants.
Once running, any language model that supports tool use — including Claude, ChatGPT, and
open-source models — can search the book, retrieve chapter content, and browse the table
of contents on behalf of a user.

The server exposes two interfaces from one codebase:

- An **MCP server** (Model Context Protocol, stdio transport) for Claude Desktop and Claude Code.
- An **OpenAI-compatible HTTP API** for any tool-calling framework that speaks the OpenAI
  function-calling format.

Both interfaces expose the same three tools and draw from the same live content, so you only
need to run one depending on your AI platform.

## Why This Exists

_The Turing Way_ is a large, continuously updated handbook.
Finding the right chapter for a specific question can take time, and the answer is often
spread across several subchapters.
This server lets an AI assistant do that navigation work for you: ask it a question in plain
English, and it will locate, retrieve, and summarise the relevant content from the book.

Because the server fetches content directly from the GitHub repository at query time, the
knowledge base is always as current as the latest commit on the main branch.

## Project Layout

```
ttw-ai-server/
├── src/ttw_server/
│   ├── content.py       The content store: TOC parsing, caching, and search
│   ├── server.py        MCP server definition (FastMCP)
│   ├── openai_api.py    OpenAI-compatible HTTP server (FastAPI)
│   └── cli.py           Command-line entry point
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## How the Server Works

### Fetching and Caching Content

All content comes from the GitHub raw content API at query time rather than from a bundled
static copy.
This means the server always reflects the current state of the book without requiring
a redeploy.

When the server starts, it fetches the book's table of contents from `myst.yml` — the
file that drives the Jupyter Book build — and parses it into a flat list of chapters.
Each chapter record stores its title, its file path relative to `book/website/`, and the
slug (the path without the `.md` extension) that users pass to `get_chapter`.

Chapter content is fetched lazily: a chapter's Markdown is only downloaded the first time
it is requested, then stored in memory.
In the background, the server gradually fetches every chapter at a rate of one every 0.2
seconds so that full-text search improves over time without hammering GitHub's API.
The chapter list refreshes automatically every 24 hours so new and renamed chapters
appear without a restart.

A `GITHUB_TOKEN` environment variable is optional but recommended.
Without one, GitHub limits unauthenticated requests to 60 per hour, which the background
preloader can exhaust in a few minutes.
A token raises this limit to 5 000 requests per hour.

### Searching

The `search_turing_way` tool scores each chapter against the query using two signals:

1. **Title matching** — exact matches score highest, followed by substring matches, then
   individual word matches.
   Guide landing pages receive a small bonus so navigational queries surface them first.
2. **Content matching** — for chapters that have already been fetched and cached, the tool
   counts how many times the query words appear in the text and selects the most relevant
   paragraph as an excerpt.

Chapters that have not yet been cached are still searchable by title, so search is useful
from the first request even before the background preloader has finished.

### The MCP Server

`server.py` defines a `FastMCP` application with three tools.
FastMCP is the high-level interface provided by the MCP Python SDK; it handles the
protocol handshake, type conversion, and stdio transport automatically.

The server runs on stdio, which is the transport expected by Claude Desktop and Claude Code.
When an AI assistant calls one of the tools, FastMCP routes the call to the corresponding
async function, awaits the result from the content store, and returns the text to the model.

### The HTTP Server

`openai_api.py` defines a FastAPI application with the same three tools exposed as HTTP
endpoints.

`GET /tools` returns the tool definitions in OpenAI's function-calling JSON schema so that
any client can discover and describe the tools without hardcoding them.
`POST /tools/{tool_name}` accepts a JSON body with an `arguments` field and returns the
tool result.

This design means you can wire the server into any LLM framework that supports custom HTTP
tool endpoints by pointing it at the running server's address.

On startup, the FastAPI lifespan handler warms the TOC index and launches the background
content preloader as an asyncio task.

### The Command-Line Interface

`cli.py` provides a single entry point, `ttw-server`, with two subcommands:

```
ttw-server mcp          Run the MCP server on stdio
ttw-server http         Run the HTTP server (default port 8000)
ttw-server http --port 9000 --host 127.0.0.1
```

The CLI reads `GITHUB_TOKEN` from the environment and passes it to whichever server is
being started.
Importing the server modules is deferred until the relevant subcommand is chosen, so
starting in MCP mode does not load FastAPI or uvicorn, and vice versa.

## Prerequisites

- Python 3.11 or later
- Or Docker (no Python installation required)

## Running Locally

Install the package and its dependencies:

```bash
pip install -e .
```

Copy the environment file and optionally add your GitHub token:

```bash
cp .env.example .env
# Edit .env and set GITHUB_TOKEN=ghp_...
```

Start the HTTP server:

```bash
ttw-server http
```

Or start the MCP server (used when Claude Desktop or Claude Code calls the binary
directly):

```bash
ttw-server mcp
```

## Running with Docker

Build the image and start the HTTP server:

```bash
docker compose up --build
```

The server will be available at `http://localhost:8000`.
Pass a token by setting `GITHUB_TOKEN` in your shell before running `docker compose up`,
or by adding it to a `.env` file in this directory.

To use the image as an MCP server (for example in Claude Desktop), override the command:

```bash
docker run -i ttw-ai-server ttw-server mcp
```

The `-i` flag keeps stdin open, which is required for stdio-based MCP communication.

## Connecting to Claude Desktop

Add the following to your Claude Desktop configuration file
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS,
`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "the-turing-way": {
      "command": "ttw-server",
      "args": ["mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_..."
      }
    }
  }
}
```

If you installed the package in a virtual environment, replace `"ttw-server"` with the
full path to the binary, such as `"/path/to/venv/bin/ttw-server"`.

After saving the configuration, restart Claude Desktop.
The three tools will appear in the tool list and Claude will use them automatically when
you ask questions about research practices, reproducibility, or data science.

## Connecting to Claude Code

Add the server as a local MCP server from the command line:

```bash
claude mcp add the-turing-way ttw-server mcp
```

## Connecting to OpenAI-Compatible Clients

With the HTTP server running, fetch the tool definitions:

```bash
curl http://localhost:8000/tools
```

Pass the returned definitions as the `tools` parameter in your OpenAI API calls.
When the model returns a `tool_call`, forward the arguments to the matching endpoint:

```bash
curl -X POST http://localhost:8000/tools/search_turing_way \
     -H "Content-Type: application/json" \
     -d '{"arguments": {"query": "version control best practices"}}'
```

## Available Tools

| Tool | Description |
| ---- | ----------- |
| `list_chapters` | Returns the full Turing Way table of contents as a slug-and-title list |
| `search_turing_way` | Searches for chapters matching a keyword query; returns up to five results with excerpts |
| `get_chapter` | Returns the full Markdown source of the chapter identified by a slug from `list_chapters` |

## Configuration

| Environment variable | Required | Description |
| -------------------- | -------- | ----------- |
| `GITHUB_TOKEN` | No | GitHub personal access token; raises the API rate limit from 60 to 5 000 requests per hour |

## Licence

This server is part of _The Turing Way_ project and is released under the
[MIT licence](../../LICENSE.md) for code and
[CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/) for any written content.
