(ai-agent-standards)=
# Standards for AI Agents

An AI agent is a software system that can use a large language model (LLM) to interpret a task, decide what steps to take, and act through available tools or services.
In a research context, an agent might help draft documentation, inspect and write code, run tests, query project files, or coordinate steps in a workflow.
Because agents can act on behalf of a user, their instructions, permissions, and connections to other systems should be carefully considered.

AI agents can be configured in different ways.
Two emerging standards are especially relevant: [Agent Skills](https://agentskills.io/home) and the [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro) (MCP).
They solve related but different problems.

## Agent Skills

Agent Skills are lightweight, portable bundles of instructions that teach an agent how to perform a particular task.
An Agent Skill is usually a directory containing a required `SKILL.md` file, with optional subdirectories for scripts, references, or other resources.
At minimum, `SKILL.md` contains a `name`, a `description` and instructions that explain when and how the Skill should be used.

A basic `SKILL.md` might look like this:

```markdown
---
name: metadata-check
description: Check whether a dataset has the core metadata needed before sharing.
---

Use this Skill when reviewing a dataset for sharing or archiving.

Check that the dataset includes:

- a clear title;
- creator names and affiliations;
- a short description of the data;
- license information;
- information about how the data were collected;
- any access restrictions or sensitivity concerns.

Report missing items as a checklist.
Do not invent metadata values.
```

A common project-level layout is:

```text
.agents/
+-- skills/
    +-- data-cleaning/
        +-- SKILL.md
        +-- scripts/
        +-- references/
        +-- assets/
```

Skills are useful when an agent needs procedural knowledge: how to follow a lab's data-cleaning checklist, how to prepare a manuscript according to a journal style, or how to run a recurring quality-control workflow.
They are designed around progressive disclosure: agents first see only a Skill's name and description, and load the full instructions only when the task requires it.
This helps reduce context use and makes Skills relatively token-efficient.

Skills are best suited for reusable guidance and lightweight automation.
While they can include executable scripts, they do not provide an access-management system, instead relying on tokens saved locally.
If a Skill needs to interact with services, the surrounding agent environment still needs appropriate authentication, permissions, etc.

## Model Context Protocol

The Model Context Protocol is an open protocol for connecting AI applications to external systems.
MCP servers can expose tools, resources, prompts and workflows to an AI client.
For example, an MCP server might let an agent query a database, read documents from a project repository, search an institutional knowledge base or call a service API.

MCP is useful when the agent needs a structured connection to an external provider or system.
Unlike a Skill, which primarily tells an agent how to do something, an MCP server gives the agent a defined interface for accessing something.
MCP also includes an [authorization framework](https://modelcontextprotocol.io/docs/tutorials/security/authorization) for HTTP-based transports, supporting patterns such as OAuth-based access to protected resources.
This can make MCP more suitable for shared services, enterprise environments and cases where identity, permissions and audit trails matter.

However, MCP authorization is not automatic.
Implementers still need to configure servers and clients securely, minimise scopes, validate tokens and avoid unsafe patterns such as token passthrough.

## Choosing Between Skills and MCP

Skills and MCPs are complementary.

Use a Skill when you want to package reusable expertise, instructions, examples or small scripts for an agent.
A Skill might describe how to run a reproducibility checklist, prepare metadata or follow a project's contribution workflow.

Use an MCP server when the agent needs controlled access to an external system: a database, cloud storage provider, calendar, issue tracker or another service where authentication and permissions matter.

In practice, the two can work together.

## Security and Trust

Both Skills and MCP servers should be treated as part of the software supply chain.
They may contain instructions, code, links, dependencies or service connections that affect what an agent can do.
Guidance from the MCP security documentation highlights risks such as prompt injection, tool poisoning, excessive permissions and token misuse.
Similar caution is appropriate for Skills, especially when they include scripts or instructions from untrusted sources.

Good practice includes:

- install Skills and MCP servers only from trusted sources;
- review `SKILL.md`, scripts, dependencies and external URLs before use;
- run code with the least privileges needed;
- use scoped credentials rather than broad tokens;
- require human confirmation for sensitive actions;
- be especially careful with content from untrusted sources, as these may contain prompt-injection attempts.

For research projects, these standards are most valuable when they are version-controlled, documented, reviewed and maintained like other research software infrastructure.

## Further Resources

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills client implementation guidance](https://agentskills.io/client-implementation/adding-skills-support)
- [Model Context Protocol documentation](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- [MCP authorization guide](https://modelcontextprotocol.io/docs/tutorials/security/authorization)
