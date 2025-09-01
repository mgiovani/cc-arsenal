# Agents

AI-powered development assistants for automated workflows and quality assurance.

## Structure

```
agents/
├── architecture/    # System design and technical architecture
├── development/     # Code implementation and debugging
├── orchestration/   # Workflow coordination and automation
├── product/         # Product management and requirements
├── productivity/    # Development efficiency and optimization
└── ux/             # User experience and design
```

## Installation

Agents are automatically symlinked to `~/.claude/agents/` when running:
```bash
uv run scripts/setup/install.py
```

## Usage

Use specialized agents via the Task tool in Claude Code:
```
Use the bmad-dev agent to implement user authentication with JWT tokens
```

## Development

Each agent should be a `.md` file with YAML frontmatter describing capabilities and allowed tools:

```yaml
---
name: "agent-name"
description: "Agent description"
capabilities: ["capability1", "capability2"]
tools: ["Tool1", "Tool2"]
---

# Agent implementation...
```

## Generation

Create new agents using the generator:
```bash
uv run scripts/generators/agent_generator.py --name "my-agent" --category "development"
```
