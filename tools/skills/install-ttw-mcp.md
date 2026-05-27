---
description: >
  One-command installer for The Turing Way MCP server. Detects Docker, builds
  the image, registers the server in Claude Code settings, and installs
  companion skills. Run this once and Claude gains live access to all TTW
  chapters with no further configuration needed.
---

# The Turing Way MCP Server — Installer

You are an automated installer. When invoked, execute every step below using
your tools (Bash, Read, Write, Edit). Do not ask the user to run commands
manually unless Docker is missing from their system. Complete all steps in
order, show brief progress after each step, and report any error in plain
language with a clear next action.

---

## Step 1 — Find the repository root

Search for a `tools/ttw-ai-server/Dockerfile` relative to:
1. The current working directory
2. Parent directories (up to 4 levels up)

Set a variable `REPO_ROOT` to the first directory that contains
`tools/ttw-ai-server/Dockerfile`.

If no match is found in any of those locations, tell the user:

> The TTW repository was not found. Please either:
> - Open Claude Code from inside a cloned copy of the repository, or
> - Clone it first: `git clone https://github.com/the-turing-way/the-turing-way.git`
>   then re-run `/install-ttw-mcp` from inside that directory.

Stop here if the repository cannot be located.

---

## Step 2 — Check Docker

Run:
```
docker info
```

**If Docker is not installed** (command not found):
Tell the user:
> Docker is required. Install Docker Desktop from
> https://www.docker.com/products/docker-desktop/ (free for personal use),
> then restart this terminal and re-run `/install-ttw-mcp`.

Stop here.

**If Docker is installed but the daemon is not running** (connection refused /
"Is the docker daemon running?"):
Tell the user:
> Docker is installed but not running. Please start Docker Desktop, wait for
> the whale icon to appear in your menu bar, then re-run `/install-ttw-mcp`.

Stop here.

---

## Step 3 — Build the Docker image

Run:
```
docker build -t ttw-ai-server:latest <REPO_ROOT>/tools/ttw-ai-server/
```

Inform the user: "Building the Docker image — this takes 2–3 minutes on first
run and is much faster afterwards."

If the build fails, show the last 20 lines of output and stop with:
> The Docker build failed. The error above usually means a network issue or a
> changed upstream package. Try again in a few minutes; if it keeps failing,
> open an issue at https://github.com/the-turing-way/the-turing-way/issues

---

## Step 4 — Verify the server starts

Run this smoke test (30-second timeout):
```
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}\n' \
  | timeout 30 docker run --rm -i ttw-ai-server:latest ttw-server mcp 2>/dev/null \
  | head -c 800
```

The output should contain `"protocolVersion"`. If it does not, or if the
command times out, tell the user the build completed but the server returned
an unexpected response, then show the raw output and stop.

---

## Step 5 — Register the MCP server in Claude Code

**Read** `~/.claude/settings.json`.

- If the file does not exist, treat its content as `{}`.
- Parse the JSON.
- Add or overwrite the key `mcpServers.the-turing-way` with:

```json
{
  "command": "docker",
  "args": ["run", "--rm", "-i", "ttw-ai-server:latest", "ttw-server", "mcp"]
}
```

- Leave all other keys in `settings.json` untouched.
- Write the merged result back to `~/.claude/settings.json` with 2-space
  indentation.

**Example** — if the file currently contains:
```json
{ "permissions": { "allow": ["Bash(git add:*)"] } }
```

The result should be:
```json
{
  "permissions": {
    "allow": ["Bash(git add:*)"]
  },
  "mcpServers": {
    "the-turing-way": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ttw-ai-server:latest", "ttw-server", "mcp"]
    }
  }
}
```

---

## Step 6 — Also configure Claude Desktop (if present)

Check whether the standalone Claude Desktop config exists at any of these paths:
- `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- `~/.config/Claude/claude_desktop_config.json` (Linux)

If any of those files exist, apply the same JSON merge from Step 5 to that file
(preserve all existing keys, add/update only `mcpServers.the-turing-way`).

Note to user that Claude Desktop requires a restart to pick up the change.

Skip silently if none of those files exist.

---

## Step 7 — Install companion skills globally

Run:
```
mkdir -p ~/.claude/commands
```

Copy (overwriting if they already exist):
- `<REPO_ROOT>/tools/skills/style.md` → `~/.claude/commands/style.md`
- `<REPO_ROOT>/tools/skills/the-turing-way--combined.md` → `~/.claude/commands/the-turing-way--combined.md`
- `<REPO_ROOT>/tools/skills/install-ttw-mcp.md` → `~/.claude/commands/install-ttw-mcp.md`

Installing the installer itself globally means the user can re-run
`/install-ttw-mcp` from any future project directory to upgrade.

---

## Step 8 — Report success

Print the following (adjust the Claude Desktop line based on whether
Step 6 applied):

---

**The Turing Way is ready.**

**New slash commands:**

| Command | What it does |
|---|---|
| `/style` | Review or write content in The Turing Way's voice |
| `/the-turing-way` | Ask anything about TTW principles and practices |
| `/install-ttw-mcp` | Re-run this installer to upgrade (now available everywhere) |

**MCP server:** Claude now has live access to all Turing Way chapters via four
tools — `list_chapters`, `search_turing_way`, `get_chapter`, and
`get_recent_changes`. The server starts automatically when needed; no manual
setup required.

**Try it now** — start a new conversation and ask:
> "What does The Turing Way say about writing a data management plan?"

**Optional — add a GitHub token** to raise the API rate limit from 60 to
5 000 requests/hour. Edit `~/.claude/settings.json` and add your token:
```json
"mcpServers": {
  "the-turing-way": {
    "command": "docker",
    "args": ["run", "--rm", "-i", "ttw-ai-server:latest", "ttw-server", "mcp"],
    "env": { "GITHUB_TOKEN": "ghp_your_token_here" }
  }
}
```

**Keeping up to date:** Pull the latest TTW repo changes, then re-run
`/install-ttw-mcp` to rebuild the image and refresh the skills.

---

## Error handling rules

- After any failed step, explain what went wrong in plain, jargon-free language
  and give a single concrete next action.
- Never silently skip a step that fails.
- If Steps 5–7 succeed but a later step fails, do not undo the earlier steps —
  the user has a working installation; only the failed step needs attention.
