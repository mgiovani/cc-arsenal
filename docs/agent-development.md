# Agent Development Guide

Complete guide to creating, customizing, and deploying AI agents for Claude Code Arsenal.

## Overview

Agents in Claude Code Arsenal are specialized AI assistants designed for specific development tasks. They are defined as Markdown files with YAML frontmatter that specify their capabilities, tools, and behavior patterns.

## Agent Architecture

### Structure

```
agents/
├── category/
│   ├── README.md           # Category overview
│   └── agent-name.md       # Individual agent
└── README.md               # Agents overview
```

### Agent File Format

Each agent is a `.md` file with this structure:

```yaml
---
name: "agent-name"
description: "Brief description of agent capabilities"
capabilities: ["capability1", "capability2", "capability3"]
tools: ["Tool1", "Tool2", "Tool3"]
category: "development"
version: "1.0.0"
author: "Your Name"
---

# Agent Name

## Purpose

Detailed description of what this agent does and when to use it.

## Capabilities

- **Capability 1**: Detailed explanation
- **Capability 2**: Detailed explanation
- **Capability 3**: Detailed explanation

## Usage Examples

### Basic Usage
```
Use the agent-name to perform specific task
```

### Advanced Usage
```
Use the agent-name with specific parameters to achieve complex goal
```

## Best Practices

Guidelines for optimal usage of this agent.

## Limitations

What this agent cannot or should not do.
```

## Creating New Agents

### Method 1: Using the Generator (Recommended)

```bash
# Generate a new agent with the built-in generator
make generate-agent NAME=my-agent CATEGORY=development

# Or use the Python module directly
uv run python -m scripts.generators.agent_generator --name "crypto-validator" --category "security"
```

The generator will:
1. Create the agent file in the correct category directory
2. Generate appropriate YAML frontmatter
3. Provide a basic template to customize
4. Update category README if needed

### Method 2: Manual Creation

1. **Choose Category**: Select from existing categories or create a new one
2. **Create File**: Create `category/agent-name.md`
3. **Add Frontmatter**: Include required YAML metadata
4. **Write Content**: Add agent description and guidelines
5. **Test**: Install and test the agent

## Agent Categories

### Architecture
**Purpose**: System design and technical architecture
**Examples**: system-designer, architecture-reviewer, scalability-analyst

```yaml
capabilities: ["system_design", "architecture_review", "scalability_analysis"]
tools: ["Read", "Write", "Glob", "Grep", "TodoWrite"]
```

### Development
**Purpose**: Code implementation and debugging
**Examples**: code-reviewer, debug-specialist, feature-builder

```yaml
capabilities: ["code_implementation", "debugging", "testing", "refactoring"]
tools: ["Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep"]
```

### Security
**Purpose**: Security analysis and validation
**Examples**: security-validator, vulnerability-scanner, auth-specialist

```yaml
capabilities: ["security_analysis", "vulnerability_detection", "compliance_check"]
tools: ["Read", "Grep", "Bash", "TodoWrite"]
```

### Orchestration
**Purpose**: Workflow coordination and automation
**Examples**: workflow-coordinator, deployment-manager, ci-cd-specialist

```yaml
capabilities: ["workflow_coordination", "automation", "deployment"]
tools: ["Task", "Bash", "TodoWrite", "Read", "Write"]
```

### Product
**Purpose**: Product management and requirements
**Examples**: requirements-analyst, feature-planner, user-story-writer

```yaml
capabilities: ["requirements_analysis", "feature_planning", "user_research"]
tools: ["Read", "Write", "TodoWrite", "WebSearch"]
```

### UX
**Purpose**: User experience and design
**Examples**: ux-designer, accessibility-auditor, design-reviewer

```yaml
capabilities: ["ux_design", "accessibility_audit", "design_review"]
tools: ["Read", "Write", "WebSearch", "TodoWrite"]
```

## YAML Frontmatter Reference

### Required Fields

```yaml
name: "agent-name"                    # Unique identifier (kebab-case)
description: "Brief description"      # One-line summary
capabilities: ["cap1", "cap2"]        # Array of capabilities
tools: ["Tool1", "Tool2"]            # Claude Code tools the agent can use
```

### Optional Fields

```yaml
category: "development"               # Agent category
version: "1.0.0"                     # Semantic version
author: "Your Name"                  # Agent creator
tags: ["tag1", "tag2"]              # Searchable tags
priority: "high"                     # Usage priority (high/medium/low)
experimental: false                  # Whether agent is experimental
deprecated: false                    # Whether agent is deprecated
```

### Advanced Configuration

```yaml
# Tool restrictions
tool_restrictions:
  Bash:
    allowed_commands: ["git", "npm", "pytest"]
    forbidden_commands: ["rm", "sudo"]

# Context requirements
context_requirements:
  min_files: 1                       # Minimum files to analyze
  preferred_patterns: ["*.py", "*.ts"] # File patterns to focus on

# Collaboration settings
collaboration:
  works_well_with: ["code-reviewer", "test-orchestrator"]
  conflicts_with: ["legacy-agent"]

# Performance settings
performance:
  max_context_size: 50000           # Maximum context tokens
  timeout_seconds: 300              # Operation timeout
```

## Tool Access Patterns

### Read-Only Agents
For analysis and reporting:
```yaml
tools: ["Read", "Glob", "Grep", "WebSearch", "TodoWrite"]
```

### Development Agents
For code modification:
```yaml
tools: ["Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep", "TodoWrite"]
```

### Orchestration Agents
For workflow coordination:
```yaml
tools: ["Task", "Read", "Write", "Bash", "TodoWrite", "SlashCommand"]
```

### Specialized Agents
For specific domains:
```yaml
# Security agent
tools: ["Read", "Grep", "Bash", "TodoWrite"]

# Documentation agent
tools: ["Read", "Write", "WebSearch", "TodoWrite"]

# Testing agent
tools: ["Read", "Write", "Bash", "TodoWrite", "NotebookEdit"]
```

## Agent Design Patterns

### Single Responsibility
Each agent should have a clear, focused purpose:

```yaml
# Good: Focused responsibility
name: "jwt-validator"
description: "Validates JWT token implementation and security"
capabilities: ["jwt_validation", "token_security_check"]

# Avoid: Too broad
name: "auth-everything"
description: "Handles all authentication tasks"
capabilities: ["jwt", "oauth", "saml", "ldap", "passwords"]
```

### Composable Agents
Design agents to work together:

```yaml
# Agent A: Analysis
name: "security-analyzer"
capabilities: ["vulnerability_detection", "security_analysis"]

# Agent B: Implementation
name: "security-implementer"
capabilities: ["security_fix_implementation", "secure_coding"]

# Agent C: Validation
name: "security-validator"
capabilities: ["security_testing", "compliance_check"]
```

### Progressive Complexity
Offer different levels of assistance:

```yaml
# Basic agent
name: "code-formatter"
capabilities: ["code_formatting", "style_checking"]

# Advanced agent
name: "code-optimizer"
capabilities: ["performance_optimization", "advanced_refactoring", "architecture_improvement"]
```

## Best Practices

### Agent Naming

```bash
# Good: Clear, descriptive names
security-validator
jwt-implementer
react-component-generator
api-documenter

# Avoid: Vague or overly generic
helper
utils
dev-agent
ai-assistant
```

### Capability Definition

```yaml
# Good: Specific, actionable capabilities
capabilities:
  - "jwt_token_validation"
  - "session_management_review"
  - "oauth_flow_implementation"

# Avoid: Vague capabilities
capabilities:
  - "authentication"
  - "security"
  - "help"
```

### Tool Selection

```yaml
# Good: Minimal necessary tools
tools: ["Read", "Grep", "TodoWrite"]  # For analysis agent

# Avoid: Kitchen sink approach
tools: ["Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep", "TodoWrite", "Task", "WebSearch", "SlashCommand"]
```

### Documentation Quality

- **Clear Purpose**: Explain when and why to use the agent
- **Concrete Examples**: Provide real usage scenarios
- **Limitations**: Be honest about what the agent cannot do
- **Integration**: Show how it works with other agents

## Testing Agents

### Manual Testing

```bash
# Install agent locally
make install

# Test in Claude Code
# "Use the my-new-agent to analyze this codebase"

# Verify behavior matches expectations
```

### Automated Testing

```python
# tests/test_agents.py
def test_agent_yaml_valid():
    """Test that all agent YAML frontmatter is valid."""
    for agent_file in glob("agents/**/*.md"):
        content = read_file(agent_file)
        frontmatter = extract_yaml_frontmatter(content)

        assert "name" in frontmatter
        assert "description" in frontmatter
        assert "capabilities" in frontmatter
        assert "tools" in frontmatter

def test_agent_tools_valid():
    """Test that all specified tools are valid Claude Code tools."""
    valid_tools = ["Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep", "TodoWrite", "Task", "WebSearch"]

    for agent_file in glob("agents/**/*.md"):
        frontmatter = extract_yaml_frontmatter(read_file(agent_file))
        for tool in frontmatter.get("tools", []):
            assert tool in valid_tools, f"Invalid tool {tool} in {agent_file}"
```

## Advanced Features

### Conditional Agents

Agents that activate based on context:

```yaml
# Only for Python projects
activation_conditions:
  file_patterns: ["*.py", "pyproject.toml", "requirements.txt"]

# Only for security-related tasks
activation_keywords: ["security", "auth", "encryption", "vulnerability"]
```

### Agent Chains

Define workflows between agents:

```yaml
# Primary agent
name: "security-audit-coordinator"
chain_agents:
  - step: 1
    agent: "vulnerability-scanner"
    condition: "always"
  - step: 2
    agent: "security-implementer"
    condition: "vulnerabilities_found"
  - step: 3
    agent: "security-validator"
    condition: "fixes_implemented"
```

### Dynamic Tool Selection

Adjust tools based on project type:

```yaml
dynamic_tools:
  python_project:
    additional_tools: ["NotebookEdit"]
  javascript_project:
    restricted_tools: ["NotebookEdit"]
  security_audit:
    required_tools: ["Grep", "Bash"]
```

## Deployment and Distribution

### Local Installation

```bash
# Install single agent
cp agents/security/my-agent.md ~/.claude/agents/security/

# Install via make
make install-agents
```

### Team Distribution

```bash
# Package agents for team
make package-agents

# Install team package
make install-team-agents
```

### Version Management

```yaml
# In agent frontmatter
version: "2.1.0"
compatibility: ">=1.0.0"
deprecated_in: "3.0.0"
```

## Troubleshooting

### Common Issues

#### Agent Not Found
```bash
# Check installation
ls ~/.claude/agents/category/

# Verify YAML syntax
uv run python -c "import yaml; print(yaml.safe_load(open('agent.md').read().split('---')[1]))"
```

#### Invalid Tools
```bash
# Check tool names against valid list
grep -r "tools:" agents/ | grep -v "Read\|Write\|Edit\|MultiEdit\|Bash\|Glob\|Grep\|TodoWrite\|Task\|WebSearch"
```

#### Poor Performance
- Reduce tool scope
- Limit context requirements
- Optimize capability descriptions
- Add performance settings

### Debugging

```bash
# Test agent YAML
make validate-agents

# Check agent loading
claude --debug "List available agents"

# Monitor agent usage
tail -f ~/.claude/agent.log
```

## Contributing Agents

### Submission Process

1. **Design**: Plan agent purpose and capabilities
2. **Implement**: Create agent file with proper structure
3. **Test**: Verify functionality and performance
4. **Document**: Add comprehensive documentation
5. **Submit**: Create pull request with description

### Review Criteria

- **Purpose**: Clear, focused responsibility
- **Quality**: Well-documented with examples
- **Security**: Safe tool usage and input handling
- **Performance**: Efficient operation and resource usage
- **Integration**: Works well with existing agents

### Community Agents

Share agents with the community:

```bash
# Submit to community repository
git clone https://github.com/mgiovani/cc-arsenal-community
cp my-agent.md cc-arsenal-community/agents/category/
```

## Future Enhancements

### Planned Features

- **Agent Marketplace**: Browse and install community agents
- **Interactive Agent Builder**: GUI for creating agents
- **Agent Analytics**: Usage statistics and optimization suggestions
- **Agent Versioning**: Semantic versioning and update management

### Experimental Features

- **Learning Agents**: Agents that improve based on usage
- **Collaborative Agents**: Multi-agent problem solving
- **Context-Aware Agents**: Automatic activation based on project context

---

For more information:
- [Getting Started](getting-started.md)
- [Troubleshooting](troubleshooting.md)
- [Contributing](../CONTRIBUTING.md)
