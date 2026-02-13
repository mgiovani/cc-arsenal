---
name: inject-nextjs-docs
description: Run the Next.js agents-md codemod to inject compressed framework documentation
  into the current project's CLAUDE.md or AGENTS.md. This skill should be used when
  a user wants to add Next.js framework docs to their project for AI coding agents,
  run the Vercel agents-md codemod, or improve AI agent performance on Next.js projects.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: ''
allowed-tools: Bash(npx *), Bash(node *), Bash(cat *), Read, Grep, Glob, Task, AskUserQuestion
---

# Inject Nextjs Docs

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Next.js Agents-MD Codemod

Run the `@next/codemod` agents-md codemod to inject compressed Next.js framework documentation into the current project. This gives AI coding agents passive access to framework knowledge without requiring tool calls or skills.

**Context**: Vercel's agent evals showed this approach achieves 100% pass rate vs 53% baseline by compressing ~40KB of docs into ~8KB using a pipe-delimited index.

## Anti-Hallucination Guidelines

**CRITICAL**:
1. **Verify this is a Next.js project** before running anything - check for `next` in `package.json` dependencies
2. **Do NOT assume npx is available** - verify Node.js tooling exists
3. **Do NOT claim success** until verifying the target file exists and contains actual content after the codemod runs
4. **Read actual output** from the codemod - report what it says, not what is expected

## Implementation Workflow

### Phase 0: Project Validation (REQUIRED)

Before running anything, verify prerequisites:

1. **Check this is a Next.js project**:
 - Read `package.json` and confirm `next` is in `dependencies` or `devDependencies`
 - If `next` is not found, **STOP** and inform the user: "This does not appear to be a Next.js project. The agents-md codemod requires Next.js."

2. **Detect Next.js version**:
 - Check `package.json` for the installed Next.js version
 - Report the detected version to the user

3. **Detect target file**:
 - Check if `CLAUDE.md` exists in the project root - use `CLAUDE.md`
 - Else check if `AGENTS.md` exists - use `AGENTS.md`
 - If neither exists, default to `CLAUDE.md` (Claude Code's native format)
 - Inform the user which file will be updated

### Phase 1: Run the Codemod

Execute the codemod with the `--output` flag to target the correct file and skip interactive prompts:

```bash
npx @next/codemod@canary agents-md --output <TARGET_FILE>
Where `<TARGET_FILE>` is the file detected in Phase 0 (e.g., `CLAUDE.md` or `AGENTS.md`).

**Important**:
- Run this in the project root directory
- The `--output` flag makes the command non-interactive - no prompts will appear
- The codemod auto-detects the Next.js version and downloads matching documentation
- It injects a compressed pipe-delimited index into the target file
- It also downloads full docs to `.next-docs/` and adds it to `.gitignore`
- Capture and report the full output to the user

### Phase 2: Verify Results

After the codemod completes:

1. **Confirm the target file was updated** - Read the file to verify it contains Next.js documentation content
2. **Check content** - Look for the injected Next.js framework index (pipe-delimited entries)
3. **Report to user**:
 - Whether the file was created or updated
 - Approximate size of the injected documentation
 - Summary of what was added

### Phase 3: Report

Provide a summary to the user:
- Next.js version detected
- Which file was updated (CLAUDE.md or AGENTS.md)
- Confirmation that framework docs were injected
- Suggest reviewing the file and committing the change

## Usage

```bash
inject-nextjs-docs
## Examples

### Example: Project with existing CLAUDE.md

```
> inject-nextjs-docs

Detected Next.js 15.2.3 in package.json
Found existing CLAUDE.md - will inject documentation there
Running: npx @next/codemod@canary agents-md --output CLAUDE.md
Updated CLAUDE.md (2.1 KB -> 10.3 KB)
Added .next-docs to .gitignore

Review the changes and commit when ready:
 git add CLAUDE.md .gitignore && git commit -m "docs: add Next.js agents-md framework reference"
### Example: Project with AGENTS.md

```
> inject-nextjs-docs

Detected Next.js 14.1.0 in package.json
Found existing AGENTS.md - will inject documentation there
Running: npx @next/codemod@canary agents-md --output AGENTS.md
Updated AGENTS.md (1.5 KB -> 9.8 KB)
Added .next-docs to .gitignore
## Important Notes

- **Next.js only**: This codemod is specifically for Next.js projects
- **Version-aware**: The codemod downloads documentation matching the installed Next.js version
- **Non-destructive**: If the target file already exists, the codemod injects/updates the index section without overwriting existing content
- **Requires network**: The codemod downloads documentation from Vercel's servers
- **Target file priority**: CLAUDE.md (if exists) -> AGENTS.md (if exists) -> CLAUDE.md (default)
- **Full docs downloaded**: The codemod also saves full documentation to `.next-docs/` and auto-adds it to `.gitignore`

## Claude Code Enhanced Features

This skill integrates with Claude Code's tool ecosystem for enhanced automation.

**Allowed Tools**: B, a, s, h, (, n, p, x,  , *, ), ,,  , B, a, s, h, (, n, o, d, e,  , *, ), ,,  , B, a, s, h, (, c, a, t,  , *, ), ,,  , R, e, a, d, ,,  , G, r, e, p, ,,  , G, l, o, b, ,,  , T, a, s, k, ,,  , A, s, k, U, s, e, r, Q, u, e, s, t, i, o, n
