# Mention scrub — grep patterns

Load this when running Stage 5. Run every pattern group that's plausible for the repo's stack; report every hit as `file:line` (or commit SHA for the commit-message group) — never invent a hit that wasn't actually matched.

## AI-assistant / AI-tooling scaffolding

```bash
grep -rniE "generated (with|by) claude|claude code|anthropic|co-authored-by:\s*claude|chatgpt|copilot suggested|cursor(\s|-)?ai" \
  --exclude-dir={.git,node_modules,dist,build} .
```

Also check commit messages and trailers directly (these don't show up in a file grep):

```bash
git log --all --format='%H %s%n%b' | grep -niE "co-authored-by:\s*claude|generated (with|by) claude|claude code|chatgpt"
```

## Internal-only references

```bash
grep -rniE "jira\.[a-z0-9-]+\.(internal|corp)|slack\.com/archives/|\.internal\.[a-z]+|vpn\.[a-z0-9-]+\.[a-z]+" \
  --exclude-dir={.git,node_modules,dist,build} .

# Internal ticket IDs (adjust the project-key pattern to what the repo actually uses)
grep -rnE "\b[A-Z]{2,10}-[0-9]{2,6}\b" --exclude-dir={.git,node_modules,dist,build} . | grep -viE "CVE-|RFC-"
```

## Local machine / personal path leaks

```bash
grep -rnE "/Users/[a-zA-Z0-9_.-]+/|/home/[a-zA-Z0-9_.-]+/" --exclude-dir={.git,node_modules,dist,build} .
```

## Judging a match, not just finding it

A hit in these patterns is not automatically "remove this." Two matches can look identical in a grep line and mean opposite things:

- `// integrates Anthropic's Claude API for the chatbot feature` — this is the product's real, described functionality. Flag it for the user's awareness (it does mention "Anthropic"), but frame it separately from scaffolding.
- `Co-Authored-By: Claude <noreply@anthropic.com>` in a commit trailer, or a README "Generated with Claude Code" footer — this is tooling scaffolding with no product relevance. Flag it as a clear scrub candidate.

Present both in the match list, but never merge them into one undifferentiated bullet — the user needs to see which is which to decide quickly.
