# History rewrite: procedure

Load this only after all three gate conditions in Stage 6 of `SKILL.md` are satisfied (still private, no fork/star evidence of prior public exposure or explicit override, explicit confirmation this turn). The script below refuses on a non-private repo itself, but that is a backstop, not a substitute for the gates.

## 1. Prepare the inputs

Ask the user what to remove, then write the files in the scratchpad or a temp dir, never in the repo:

- Paths file, one path per line (a file or a directory), removed from every commit: `secrets/creds.json`
- Replace file for [`git filter-repo --replace-text`](https://github.com/newren/git-filter-repo), one rule per line: `old-secret==>REDACTED`, or `literal:old-secret`, or `regex:pattern==>REDACTED`

Either file or both. Never print the matched strings back to the user.

## 2. Run the script

```bash
<skill-dir>/scripts/history_rewrite.sh --paths <paths-file> --replace <replace-file>
```

From the repo root. It refuses unless the repo is private (`gh repo view --json visibility`), the working tree is clean and `git-filter-repo` is installed (`brew install git-filter-repo` or `uv tool install git-filter-repo`). If the tool is missing, say so and ask before falling back to `filter-branch` (deprecated, slower, easy to misuse).

It then:

- writes a full `git clone --mirror` backup next to the repo and prints its path (tell the user where it is)
- runs `git filter-repo` with the files you gave it
- verifies that no removed path and no replaced string remains in any commit, printing counts only
- prints the force-push commands without running them

`HISTORY_REWRITE_SKIP_VISIBILITY=1` skips the visibility check and exists for the test suite only. Never set it in a real run.

## 3. Handle failures

Any non-zero exit means stop and report; do not push. A verification count above zero means the rewrite did not fix the problem: report it, and if the rewrite files were wrong, restore from the backup mirror and retry at most 2 more times before handing back to the user.

## 4. The one narrow force-push exception

Every other skill in this arsenal says never force-push. This is the sole exception, and only for this stage, because `filter-repo` rewrites every commit SHA (and removes the `origin` remote, which the printed commands re-add). Show the user the printed commands and wait for a direct yes in this turn, then run exactly those:

```bash
git remote add origin <remote-url>
git fetch origin
git push --force-with-lease origin --all
git push --force-with-lease origin --tags
```

`--force-with-lease`, never bare `--force`: it still refuses if the remote has commits you haven't seen (e.g. a collaborator pushed since your last fetch).

## 5. After pushing

Tell every collaborator (if any exist even on a private repo) to re-clone rather than pull. Their local history now diverges permanently from origin.
