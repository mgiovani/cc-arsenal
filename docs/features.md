# Features

Complete reference for all cc-arsenal skills and optional features.

## Skills

### Development (12 skills)

#### `/implement-feature`
Feature implementation with parallel subagents and automated test verification.
- Parallel subagent orchestration
- Automated test verification
- SOLID, DRY, and YAGNI principles

#### `/fix-bug`
Test-driven debugging with fix verification.
- Root cause analysis
- Regression testing
- Fix verification hook

#### `/test-suite`
Test generation and coverage analysis (model-invoked).
- Comprehensive test generation
- Coverage analysis and reporting

#### `/refactor`
Safe codebase refactoring with characterization tests (model-invoked).
- Characterization test generation
- Safe refactoring patterns
- Regression prevention

#### `/review-code`
Multi-agent PR code review with 5 parallel specialists.
- 5 specialized review agents
- Comprehensive code quality analysis
- Security, performance, and best practices

#### `/review-security`
OWASP Top 10 2025 security analysis.
- Automated vulnerability scanning
- OWASP compliance checking
- Security best practices

#### `/review-deps`
Dependency audit, vulnerability scanning, and upgrade planning.
- Vulnerability detection
- Upgrade recommendations
- Dependency health scoring

#### `/review-perf`
Performance analysis with 4 parallel agents.
- Database optimization
- Algorithm analysis
- Frontend performance
- Resource optimization

#### `/ci-generate`
CI/CD workflow generator.
- GitHub Actions, GitLab CI, CircleCI, Jenkins
- Best practices templates
- Test integration

#### `/inject-docs`
Framework documentation injector.
- Next.js via agents-md
- FastAPI via best practices
- Framework-specific patterns

#### `/inject-nextjs-docs` (legacy)
Next.js agents-md codemod (use `/inject-docs` instead).

#### `/project-planner`
Break down large projects into dependency-aware tasks.
- Dependency graph generation
- Task breakdown with estimates
- Mermaid visualization

### Documentation (6 skills)

#### `/docs-init`
Initialize comprehensive documentation structure.
- Standard documentation templates
- Best practices structure

#### `/docs-adr`
Architecture Decision Records creation.
- ADR templates (full, lightweight, Nygard)
- Decision documentation
- Context and consequences

#### `/docs-rfc`
Request for Comments documentation.
- RFC templates (detailed, minimal, standard)
- Proposal structure
- Review workflow

#### `/docs-diagram`
Architecture diagrams (Mermaid).
- System architecture
- Component diagrams
- Flow diagrams

#### `/docs-check`
Documentation validation and health scoring.
- Freshness checks
- Completeness analysis
- Quality scoring

#### `/docs-update`
Documentation sync with codebase.
- Automatic update detection
- Sync recommendations
- Change tracking

### Git & GitHub (4 skills)

#### `/git-commit`
Conventional commits with automated linting.
- Conventional Commits format
- Pre-commit linting hook
- Multi-language linter support

#### `/git-create-pr`
PR creation with templates and test verification.
- PR templates
- Test verification hook
- Automated checklist

#### `/git-release`
Release management with automated changelog generation.
- Semantic versioning
- Automated changelog
- Release notes generation

#### `/gh-daily`
GitHub Issues daily planner with priority scoring.
- Priority scoring algorithm
- Daily task planning
- Issue organization

### Jira (2 skills)

#### `/jira-daily`
Standup report generator with activity analysis.
- Activity analysis
- Report generation
- Status tracking

#### `/jira-todo`
Work prioritization planner with intelligent prioritization.
- Intelligent prioritization
- Task recommendations
- Workload balancing

### Teams (2 skills - experimental)

#### `/team-implement`
Spec-driven team orchestration (3-11 agents).
- Adaptive team scaling
- Spec-driven development
- Multi-phase workflow

#### `/team-review`
Multi-agent PR review team.
- 7 specialized reviewers
- Adversary reviewer
- Comprehensive analysis

### Utilities (6 skills)

#### `/create-command` (skill)
Create new skills following best practices.
- Skill templates
- Best practices guidance

#### `/create-rule` (skill)
Create memory rules for Claude Code.
- CLAUDE.md guidelines
- Memory patterns

#### `agent-browser` (model-invoked)
AI-optimized browser automation.
- 93% less context overhead vs Playwright
- Snapshot + refs system
- Web testing and automation

#### `find-skills` (model-invoked)
Discover third-party skills from skills.sh.
- Skill discovery
- Installation automation
- Community skills

#### `jira-cli` (model-invoked)
Interactive command-line tool for Jira.
- Issue management
- Sprint planning
- Epic tracking

#### `skill-creator` (model-invoked)
Comprehensive guide for creating skills.
- Creation guidelines
- Best practices
- Template patterns

## Optional Features

### Statusline

Real-time cost and usage tracking in your Claude Code prompt.

**Shows:**
- Model name and version
- Current directory
- Git branch with uncommitted changes (●)
- Git worktree name
- Context window usage percentage
- Session costs
- Lines changed (+added/-removed)
- Session duration
- Time until 5-hour reset

**Example:**
```
🤖 Opus 4.5 │ 📁 ~/projects/cc-arsenal │ 🌿 main ● │ 📊 66% │ 💰 $3.169 │ 📝 +719/-545 │ ⏱️ 21m │ 🔄 4h 23m until reset at 13:00
```

**Installation:**
```bash
make statusline-install
```

**Documentation:** [Statusline Guide](../scripts/claude/statusline/STATUSLINE.md)

### Claude Hi Scheduler

Automatically start fresh 5-hour windows before your peak coding times.

**Features:**
- Preset schedules (9am/2pm/7pm standard)
- Custom schedule creation
- Automated window triggers
- Peak productivity optimization

**Installation:**
```bash
make claude-hi-setup      # Interactive setup
make claude-hi-standard   # Quick 9am/2pm/7pm schedule
```

**Documentation:** [Claude Hi Guide](../scripts/claude-hi/README.md)

## Platform Compatibility

### Enhanced Skills (Claude Code)
- **Full feature set**: Subagents, hooks, Task Management System
- **Installation**: `/plugin install cc-arsenal@cc-arsenal-marketplace`
- **Skills**: All 32 skills with Claude Code optimizations

### Base Skills (Cross-Platform)
- **Compatible with**: Claude Code, Cursor, Windsurf, and 30+ AI agents
- **Installation**: `npx skills add mgiovani/skills`
- **Skills**: 22 core skills in platform-agnostic format
- **Repository**: [mgiovani/skills](https://github.com/mgiovani/skills)

## Model-Invoked vs User-Invoked Skills

**User-Invoked** (slash commands):
- Triggered explicitly by user (e.g., `/git-commit`, `/docs-adr`)
- Workflow automation for specific tasks
- 26 user-invoked skills

**Model-Invoked** (automatic):
- Claude detects context and loads automatically
- No confirmation dialogs
- Examples: `agent-browser`, `jira-cli`, `skill-creator`, `find-skills`, `test-suite`, `refactor`
- 6 model-invoked skills
