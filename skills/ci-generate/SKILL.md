---
name: ci-generate
description: Generate a production-ready CI/CD pipeline config (GitHub Actions,
  GitLab CI, CircleCI, or Jenkins) by discovering the project's actual stack,
  test/build commands, and dependencies. Use when setting up CI for a new
  project, adding a missing workflow file, or asked to create/generate a
  pipeline, workflow, or `.gitlab-ci.yml`/`Jenkinsfile`. Not for writing a
  Dockerfile itself (see docker-init), this only wires CI stages around one.
  Not for running existing CI checks locally (use ci-local), this skill only
  authors the pipeline file itself.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
---

# CI/CD Pipeline Generator

Generate a CI/CD pipeline config for the detected project stack, with stages for lint, test, build, security scan, and deploy.

## Pipeline to Generate

Parse the arguments passed to this skill invocation (platform, `--deploy`, `--monorepo`): see Phase 0 below.

## Anti-Hallucination Guidelines

**CRITICAL**: Pipeline configurations must match ACTUAL project tooling:
1. **Discover before generating** - Never assume package managers, test runners, or build tools
2. **Verify commands exist** - Check `package.json` scripts, `Makefile` targets, `pyproject.toml` scripts before referencing them
3. **Match real versions** - Use actual language/runtime versions from project config files (`.node-version`, `.python-version`, `pyproject.toml`, etc.)
4. **No phantom dependencies** - Only include services (Redis, PostgreSQL, etc.) confirmed in project dependencies
5. **Platform-specific syntax** - Each CI platform has distinct YAML structure; never mix syntax between platforms

## Workflow

### Phase 0: Parse Arguments

Extract configuration from the arguments passed to this skill:

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
```

### Phase 1: Project Stack Detection

Explore the codebase to discover the complete project technology stack.

### Phase 2: Research Best Practices (only if needed)

`references/platform-patterns.md` already ships current, comprehensive patterns for Node/Python/matrix/Docker/deploy across all four platforms: check it first. Only reach for WebSearch when the detected stack/platform combo isn't covered there (e.g. an unusual language or a deploy target not in the reference):

```
Use WebSearch:
- query: "[detected platform] CI/CD best practices [detected language] [current year]"

Use WebSearch:
- query: "[detected platform] security scanning pipeline [detected language] [current year]"
```

Focus on:
- Caching strategies for the detected package manager
- Recommended runner images and versions
- Security scanning tools appropriate for the language
- Deployment best practices for the target platform
- Matrix testing strategies if multiple versions needed

### Phase 3: Design Pipeline Architecture

Based on discovery and research, design the pipeline with these stages. For platform-specific triggers, caching, and syntax conventions, see [references/platform-patterns.md](references/platform-patterns.md).

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
 - **Thread the built artifact reference into the deploy step.** The Build stage must expose the image tag/digest it just produced (job `outputs`, `GITHUB_OUTPUT`, an artifact file, etc.), and the deploy step must consume that same reference: rendering it into a task definition, `helm upgrade --set image.tag=<ref>`, `kubectl set image deployment/<name> <container>=<ref>`, or equivalent. Never emit a blind restart (`aws ecs update-service --force-new-deployment`, `kubectl rollout restart` with no image change) as the whole deploy step: if the target pins an image tag/digest, a blind restart just re-pulls the OLD image and ships nothing new.

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
# Any YAML-based platform (GitHub Actions, GitLab CI, CircleCI) — parse the generated file
python3 -c "import yaml; yaml.safe_load(open('<config_file>'))"

# GitLab CI — prefer the project's own linter if available
gitlab-ci-lint .gitlab-ci.yml 2>/dev/null || python3 -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml'))"

# CircleCI — prefer the project's own CLI if available
circleci config validate 2>/dev/null || python3 -c "import yaml; yaml.safe_load(open('.circleci/config.yml'))"

# Jenkins — Jenkinsfile is Groovy, not YAML; no local parser available, so
# just re-read the generated file for obvious syntax errors (unbalanced
# braces/quotes) instead of skipping validation
```

**Step 5.2: Cross-Reference Check**

Verify all referenced commands and paths exist:
1. Every script/command in the pipeline exists in the project
2. Every referenced file path is valid
3. Service versions match project requirements
4. Environment variable names are consistent
5. If a deploy stage exists, its deploy step references the image tag/digest (or equivalent build artifact) produced by the Build stage, not a blind restart with no reference to what was just built

**Step 5.3: Present Summary**

Output a summary including:
- Pipeline architecture overview
- Stages and their purposes
- Trigger conditions (which branches, PR events)
- Required secrets/environment variables to configure
- Cache strategy explanation
- Any manual steps needed (e.g., setting up deployment secrets)

Do not estimate run time per stage: it hasn't run yet and any number would be a guess.

## Handling Ambiguity

If encountering unclear requirements:
1. Ask the user to clarify platform choice, deployment target, or branching strategy.
2. Present options with trade-offs when multiple valid approaches exist.
3. Default to the most common configuration for the detected stack.

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
```

## Important Notes

- **Discover first**: Never assume project tooling; always run Phase 1
- **Pin versions**: Use specific versions for actions, orbs, images, and tools
- **Secrets documentation**: List all required secrets so users know what to configure
- **Existing config**: Always check for and respect existing CI configuration
- **Security by default**: Include dependency scanning and secret detection in every pipeline
- **Cache effectively**: Proper caching can reduce CI times by 50-80%
