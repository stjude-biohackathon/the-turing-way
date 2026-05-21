(ai-agent-standards)=
# Standards for Extending AI Agents

AI agents can be extended in different ways.
Two emerging standards are especially relevant for research software, data stewardship and reproducible workflows: [Agent Skills](https://agentskills.io/home) and the [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro) (MCP).
They solve related but different problems.

## Agent Skills

Agent Skills are lightweight, portable bundles of instructions that teach an agent how to perform a particular task.
An Agent Skill is usually a directory containing a required `SKILL.md` file, with optional scripts, references, templates or other resources.
At minimum, `SKILL.md` contains a `name`, a `description` and instructions that explain when and how the skill should be used.

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
They are designed around progressive disclosure: agents first see only a skill's name and description, and load the full instructions only when the task requires it.
This helps reduce context use and makes skills relatively token-efficient.

Skills are best suited for reusable guidance, local workflows and lightweight automation.
They can include executable scripts, but they are not, by themselves, an enterprise identity or access-management system.
If a skill needs to interact with sensitive services, the surrounding agent environment still needs appropriate authentication, permissions, logging and review.

## Model Context Protocol

The Model Context Protocol is an open protocol for connecting AI applications to external systems.
MCP servers can expose tools, resources, prompts and workflows to an AI client.
For example, an MCP server might let an agent query a database, read documents from a project repository, search an institutional knowledge base or call a service API.

MCP is useful when the agent needs a structured connection to an external provider or system.
Unlike a skill, which primarily tells an agent how to do something, an MCP server gives the agent a defined interface for accessing something.
MCP also includes an [authorisation framework](https://modelcontextprotocol.io/docs/tutorials/security/authorization) for HTTP-based transports, supporting patterns such as OAuth-based access to protected resources.
This can make MCP more suitable for shared services, enterprise environments and cases where identity, permissions and audit trails matter.

However, MCP authorisation is not automatic.
Implementers still need to configure servers and clients securely, minimise scopes, validate tokens and avoid unsafe patterns such as token passthrough.

## Choosing Between Skills and MCP

Skills and MCPs are complementary.

Use a Skill when you want to package reusable expertise, instructions, examples or small scripts for an agent.
A skill might describe how to run a reproducibility checklist, prepare FAIR metadata, format a data dictionary or follow a project's contribution workflow.

Use an MCP server when the agent needs controlled access to an external system: a database, cloud storage provider, calendar, issue tracker, institutional repository or another service where authentication and permissions matter.

In practice, the two can work together.
A skill might teach the agent the correct workflow for depositing a dataset, while an MCP server provides authenticated access to the repository where the dataset will be deposited.

## Security and Trust

Both Skills and MCP servers should be treated as part of the software supply chain.
They may contain instructions, code, links, dependencies or service connections that affect what an agent can do.
Guidance from the MCP security documentation highlights risks such as prompt injection, tool poisoning, excessive permissions and token misuse.
Similar caution is appropriate for skills, especially when they include scripts or instructions from untrusted sources.

Good practice includes:

- install Skills and MCP servers only from trusted sources;
- review `SKILL.md`, scripts, dependencies and external URLs before use;
- run code with the least privileges needed;
- use scoped credentials rather than broad tokens;
- require human confirmation for sensitive actions;
- monitor logs and audit trails where services or personal data are involved;
- be especially careful with content from untrusted repositories, websites or tool outputs, as these may contain prompt-injection attempts.

For research projects, these standards are most valuable when they are version-controlled, documented, reviewed and maintained like other research software infrastructure.

## Further Resources

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills client implementation guidance](https://agentskills.io/client-implementation/adding-skills-support)
- [Model Context Protocol documentation](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- [MCP authorisation guide](https://modelcontextprotocol.io/docs/tutorials/security/authorization)
