# Workflows and Best Practices

Patterns for finding, evaluating, installing, and managing skills from outside this repo.

---

## Discovery Patterns

### By Domain

```bash
# Frontend development
npx skills find react
npx skills find nextjs
npx skills find tailwind
npx skills find frontend

# Backend development
npx skills find api
npx skills find database
npx skills find authentication

# DevOps and infrastructure
npx skills find docker
npx skills find kubernetes
npx skills find ci-cd

# Testing
npx skills find testing
npx skills find playwright
npx skills find unit-test
```

### By Task Type

```bash
# Code quality
npx skills find "code review"
npx skills find linting
npx skills find refactoring

# Documentation
npx skills find documentation
npx skills find api-docs

# Security
npx skills find security
npx skills find vulnerability
```

### Browse Known Repositories

```bash
# Vercel's official collection (React, Next.js, design patterns)
npx skills add vercel-labs/agent-skills --list

# Anthropic's example skills
npx skills add anthropics/skills --list

# Any GitHub user's skills
npx skills add <username>/<repo> --list
```

---

## Installation Strategies

### Global vs Project Scope

**Install globally** (`-g`) when the skill is:
- General-purpose (code review, testing patterns, git workflows)
- Applicable across all projects
- Personal productivity (not team-shared)

```bash
npx skills add owner/repo --skill code-review -a claude-code -g
```

**Install at project scope** (default) when the skill is:
- Framework-specific (React, Django, Rails patterns)
- Project-specific (custom API, internal tooling)
- Shared with team via version control

```bash
npx skills add owner/repo --skill nextjs-patterns -a claude-code
```

### Single Agent vs Multi-Agent

Install to a single agent when only using one AI coding tool:

```bash
npx skills add owner/repo --skill my-skill -a claude-code
```

Install to multiple agents when using several tools:

```bash
npx skills add owner/repo --skill my-skill -a claude-code -a cursor -a codex
```

Install to all detected agents:

```bash
npx skills add owner/repo --skill my-skill
# The CLI auto-detects installed agents and prompts for selection
```

### Non-Interactive Installation (CI/CD)

For automated setups or scripts:

```bash
# Fully non-interactive
npx skills add owner/repo --skill my-skill -a claude-code -g -y

# Install everything
npx skills add owner/repo --all
```

---

## Security Review

### Before Installing an External Skill

**Always review skill contents before installation.** Skills contain instructions that AI agents follow, which could include:
- Running arbitrary commands
- Modifying files
- Making network requests
- Installing dependencies

### Review Checklist

1. **Check the source repository**: Verify the repository is from a trusted author or organization
2. **List skills first**: Use `--list` to see what will be installed
3. **Read the SKILL.md**: Review the actual instructions before installing
4. **Check for scripts**: Look for `scripts/` directories that contain executable code
5. **Review references**: Check `references/` for any suspicious content

```bash
# Step 1: List available skills
npx skills add owner/repo --list

# Step 2: Browse the repository on GitHub before installing
# https://github.com/owner/repo/tree/main/skills/

# Step 3: Install after review
npx skills add owner/repo --skill verified-skill -a claude-code
```

### Trust Indicators

- Repository from a recognized organization (Vercel, Anthropic, etc.)
- High install count on skills.sh
- Active maintenance and recent commits
- Clear documentation and SKILL.md content
- Open source with visible code

---

## Combining External Skills with cc-arsenal

### Avoiding Redundancy

Run `ls skills/` in this repo before installing an external equivalent. cc-arsenal already has 20+ skills (browser automation, Jira, docs, git, review, testing, and more) and a hardcoded list here would only go stale as skills are added.

### Complementary Skills

Good candidates to install alongside cc-arsenal:
- Framework-specific skills (React, Next.js, Django, Rails patterns)
- Language-specific skills (Rust, Go, Python best practices)
- Design system skills (Tailwind, Material UI)
- Cloud provider skills (AWS, GCP, Azure)
- Database skills (PostgreSQL, MongoDB, Redis)

### Conflict Resolution

If an installed skill overlaps with cc-arsenal:
1. Prefer cc-arsenal's built-in skill (better integration, maintained by the same team)
2. Remove the duplicate: `npx skills remove <name>`
3. If the third-party skill is superior, consider contributing improvements to cc-arsenal instead

---

## Managing Updates and Versions

### Regular Maintenance

```bash
# Check for available updates
npx skills check

# Update all installed skills
npx skills update

# List current installations to audit
npx skills list
```

### Cleaning Up Unused Skills

```bash
# Interactive removal (shows installed skills)
npx skills remove

# Remove a specific skill
npx skills remove old-skill

# Remove all skills from a specific agent
npx skills rm --skill '*' -a cursor

# Nuclear option: remove everything
npx skills remove --all
```

### Version Pinning

The skills CLI does not support version pinning. Skills always install from the latest commit on the default branch. To pin a version:

1. Fork the skill repository
2. Install from the fork: `npx skills add your-fork/repo`
3. Control updates by merging upstream changes manually

---

## Publishing Skills to skills.sh

To make skills discoverable on skills.sh:

1. **Host skills in a public GitHub repository** with `SKILL.md` files in a `skills/` directory
2. **Follow the Agent Skills format**: YAML frontmatter with `name` and `description` fields
3. **Skills appear on skills.sh** when users install them via `npx skills add`
4. **Install counts** are tracked automatically on the skills.sh leaderboard

The skills.sh directory indexes skills from Git repositories. There is no separate publishing step: any public repository with properly structured skills is installable.

```bash
# Verify your repo's skills are discoverable
npx skills add your-username/your-repo --list
```
