---
name: ci-generate
description: Generate CI/CD pipeline configurations for GitHub Actions, GitLab CI,
  CircleCI, or Jenkins.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
---

# Ci Generate

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# CI/CD Pipeline Generator

Generate production-ready CI/CD pipeline configurations with auto-detected project stack, current best practices, and comprehensive stages (lint, test, build, security scan, deploy).

## Pipeline to Generate

command arguments

## Anti-Hallucination Guidelines

**CRITICAL**: Pipeline configurations must match ACTUAL project tooling:
1. **Discover before generating** - Never assume package managers, test runners, or build tools
2. **Verify commands exist** - Check `package.json` scripts, `Makefile` targets, `pyproject.toml` scripts before referencing them
3. **Match real versions** - Use actual language/runtime versions from project config files (`.node-version`, `.python-version`, `pyproject.toml`, etc.)
4. **No phantom dependencies** - Only include services (Redis, PostgreSQL, etc.) confirmed in project dependencies
5. **Platform-specific syntax** - Each CI platform has distinct YAML structure; never mix syntax between platforms

## Workflow

### Phase 0: Parse Arguments

Extract configuration from `command arguments`:

```
Arguments:
- <platform>: Target CI platform (default: auto-detect from existing config)
 - "github" or "gh": GitHub Actions
 - "gitlab" or "gl": GitLab CI
 - "circle" or "circleci": CircleCI
 - "jenkins": Jenkins (Jenkinsfile)
- "--deploy <target>": Deployment target (optional)
 - "vercel", "netlify", "aws", "gcp", "azure", "docker", "k8s", "fly", "railway"
- "--monorepo": Generate matrix/path-filtered workflows
- No args: Auto-detect platform from existing CI config files, default to GitHub Actions
If no platform specified, detect from existing files:
- `.github/workflows/*.yml` → GitHub Actions
- `.gitlab-ci.yml` → GitLab CI
- `.circleci/config.yml` → CircleCI
- `Jenkinsfile` → Jenkins
- No CI config found → Default to GitHub Actions

### Phase 1: Project Stack Detection

Explore the codebase to discover the complete project technology stack:

### Phase 2: Research Best Practices

Search for current CI/CD best practices for the detected stack:

```
Use WebSearch:
- query: "[detected platform] CI/CD best practices [detected language] [current year]"

Use WebSearch:
- query: "[detected platform] security scanning pipeline [detected language] [current year]"
Focus on:
- Caching strategies for the detected package manager
- Recommended runner images and versions
- Security scanning tools appropriate for the language
- Deployment best practices for the target platform
- Matrix testing strategies if multiple versions needed

### Phase 3: Design Pipeline Architecture

Based on discovery and research, design the pipeline with these stages:

**Standard Stages (always include):**

1. **Lint & Format Check**
 - Run linter discovered in Phase 1 (e.g., `ruff check`, `eslint`, `golangci-lint`)
 - Run formatter check if available (e.g., `ruff format --check`, `prettier --check`)
 - Run type checker if applicable (e.g., `pyright`, `tsc --noEmit`, `mypy`)

2. **Test**
 - Run test suite with discovered test command
 - Include coverage reporting if configured
 - Set up service containers if tests require databases/caches
 - Consider matrix testing for multiple runtime versions

3. **Build**
 - Run build command if applicable (e.g., `npm run build`, `cargo build --release`)
 - Build Docker image if Dockerfile exists
 - Generate artifacts for deployment

4. **Security Scan**
 - Dependency vulnerability scanning (language-appropriate tool)
 - Static analysis if available for the language
 - Container scanning if Docker is used
 - Secret detection

5. **Deploy** (if `--deploy` specified or deployment config detected)
 - Environment-specific deployment steps
 - Staging/production separation
 - Post-deployment health checks

**Design Decisions:**

- **Parallelism**: Lint, test, and security scan run in parallel when possible
- **Fail fast**: Lint stage runs first (fastest feedback)
- **Caching**: Cache dependency installation for faster runs
- **Branch strategy**: Main/master triggers deploy; PRs trigger lint+test+build
- **Artifacts**: Build outputs passed between stages where needed

### Phase 4: Generate Pipeline Configuration

Generate the complete CI/CD configuration file based on the designed architecture.

For platform-specific syntax and patterns, consult:
- [references/platform-patterns.md](references/platform-patterns.md) - Detailed YAML patterns for each platform

**File Locations by Platform:**

| Platform | File Path |
|----------|-----------|
| GitHub Actions | `.github/workflows/ci.yml` |
| GitLab CI | `.gitlab-ci.yml` |
| CircleCI | `.circleci/config.yml` |
| Jenkins | `Jenkinsfile` |

**Generation Guidelines:**

1. Use discovered commands exactly (do not invent scripts)
2. Pin action/orb/image versions to specific tags (not `latest`)
3. Include inline comments explaining non-obvious configuration
4. Set appropriate timeouts for each job
5. Use environment variables for configurable values
6. Follow the platform's recommended project structure

**If an existing CI config exists:**
- Read the existing file first
- Ask the user whether to replace or augment
- Preserve any custom configuration the user has added
- Merge new stages with existing ones where appropriate

### Phase 5: Validate & Present

**Step 5.1: Syntax Validation**

Validate the generated configuration:

```bash
# GitHub Actions - validate YAML structure
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# GitLab CI - validate if gitlab-ci-lint available
# gitlab-ci-lint .gitlab-ci.yml

# CircleCI - validate if circleci CLI available
# circleci config validate

# General YAML validation
python3 -c "import yaml; yaml.safe_load(open('<config_file>'))"
**Step 5.2: Cross-Reference Check**

Verify all referenced commands and paths exist:
1. Every script/command in the pipeline exists in the project
2. Every referenced file path is valid
3. Service versions match project requirements
4. Environment variable names are consistent

**Step 5.3: Present Summary**

Output a summary including:
- Pipeline architecture overview
- Stages and their purposes
- Trigger conditions (which branches, PR events)
- Estimated run time per stage
- Required secrets/environment variables to configure
- Cache strategy explanation
- Any manual steps needed (e.g., setting up deployment secrets)

## Platform Quick Reference

### GitHub Actions
- **Triggers**: `push`, `pull_request`, `workflow_dispatch`, `schedule`
- **Runners**: `ubuntu-latest`, `ubuntu-24.04`, `macos-latest`, `windows-latest`
- **Caching**: `actions/cache@v4` or built-in package manager caching
- **Artifacts**: `actions/upload-artifact@v4`, `actions/download-artifact@v4`
- **Secrets**: `${{ secrets.SECRET_NAME }}`
- **Matrix**: `strategy.matrix` for multi-version testing

### GitLab CI
- **Stages**: Defined globally, jobs assigned to stages
- **Caching**: Per-job or global cache with keys
- **Artifacts**: Job artifacts with expiry
- **Variables**: `variables:` block or CI/CD settings
- **Rules**: `rules:` for conditional execution
- **Services**: `services:` for database containers

### CircleCI
- **Executors**: Docker, machine, macOS
- **Orbs**: Reusable config packages (e.g., `node`, `python`, `docker`)
- **Workflows**: Named workflow with job dependencies
- **Caching**: `save_cache`/`restore_cache` with keys
- **Contexts**: Shared environment variables

### Jenkins
- **Pipeline**: Declarative or scripted
- **Stages**: Named stages with steps
- **Agent**: Docker, node labels
- **Post**: Always/success/failure actions
- **Credentials**: `credentials` for secrets
- **Parallel**: `parallel` block for concurrent stages

## Handling Ambiguity

If encountering unclear requirements:
1. Use `interactive clarification` to clarify platform choice, deployment target, or branching strategy
2. Present options with trade-offs when multiple valid approaches exist
3. Default to the most common configuration for the detected stack

## Usage Examples

```bash
# Auto-detect everything
ci-generate

# Specify platform
ci-generate github
ci-generate gitlab
ci-generate circleci
ci-generate jenkins

# With deployment target
ci-generate github --deploy vercel
ci-generate gitlab --deploy docker
ci-generate github --deploy aws

# Monorepo support
ci-generate github --monorepo

# Combined options
ci-generate github --deploy k8s --monorepo
## Important Notes

- **Discover first**: Never assume project tooling; always run Phase 1
- **Pin versions**: Use specific versions for actions, orbs, images, and tools
- **Secrets documentation**: List all required secrets so users know what to configure
- **Existing config**: Always check for and respect existing CI configuration
- **Security by default**: Include dependency scanning and secret detection in every pipeline
- **Cache effectively**: Proper caching can reduce CI times by 50-80%
