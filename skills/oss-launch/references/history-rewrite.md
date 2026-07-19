# History rewrite — procedure

Load this only after all three gate conditions in Stage 6 of `SKILL.md` are satisfied (still private, no fork/star evidence of prior public exposure or explicit override, explicit confirmation this turn). Every command below runs against a repo that is confirmed private — this is not a general-purpose history-rewrite recipe for any repo.

## 1. Back up first, unconditionally

Before touching anything:

```bash
git bundle create ../<repo-name>-pre-rewrite-backup-$(date +%Y%m%d%H%M%S).bundle --all
git tag pre-history-rewrite-backup-$(date +%Y%m%d%H%M%S)
```

The bundle is a full, restorable copy independent of the tag (a tag alone doesn't survive a bad `filter-repo` run against the same repo). Tell the user where the bundle landed.

## 2. Rewrite with git filter-repo

Prefer [`git filter-repo`](https://github.com/newren/git-filter-repo) over `git filter-branch` (deprecated, slower, easy to misuse) or BFG unless the user's environment already standardizes on BFG.

```bash
# Remove a file (and its history) entirely
git filter-repo --path secrets/creds.json --invert-paths

# Replace matched text across all history (e.g. a leaked key, an internal hostname)
printf 'sk_live_XXXXXXXXXXXXXXXX==>REDACTED\n' > /tmp/replacements.txt
git filter-repo --replace-text /tmp/replacements.txt
```

If `git filter-repo` isn't installed, say so and ask before falling back to `filter-branch` — don't silently downgrade to the slower, riskier tool.

## 3. Verify before pushing

```bash
git log --all --oneline | head -20         # history looks sane, no missing commits
git log --all -p | grep -iE "secret|password|api_key" # re-run the Stage 1 secrets scan against full history
```

If the re-scan still finds something, stop and report it — don't push a rewrite that didn't actually fix the problem.

## 4. The one narrow force-push exception

Every other skill in this arsenal says never force-push. This is the sole exception, and only for this stage, because `filter-repo` rewrites every commit SHA and a normal push will be rejected.

```bash
git push --force-with-lease origin --all
git push --force-with-lease origin --tags
```

`--force-with-lease`, never bare `--force` — it still refuses if the remote has commits you haven't seen (e.g. a collaborator pushed since your last fetch).

## 5. After pushing

Tell every collaborator (if any exist even on a private repo) to re-clone rather than pull — their local history now diverges permanently from origin.
