#!/bin/sh
# Rewrite git history to drop paths and/or redact strings, on a private repo only.
# Usage: history_rewrite.sh [--paths FILE] [--replace FILE]
#   --paths FILE    one path per line (file or directory), removed from all history
#   --replace FILE  git-filter-repo --replace-text file: `old==>new`, `literal:old`, or `regex:pattern==>new`
# Run from the repo root. It never pushes: it prints the force-push commands.
# Test-only env: HISTORY_REWRITE_SKIP_VISIBILITY=1 skips the `gh repo view` check.
set -eu

die() { printf 'history_rewrite: %s\n' "$*" >&2; exit 1; }

paths_file= replace_file=
while [ $# -gt 0 ]; do
  case $1 in
    --paths) [ $# -ge 2 ] || die "--paths needs a file"; paths_file=$2; shift 2 ;;
    --replace) [ $# -ge 2 ] || die "--replace needs a file"; replace_file=$2; shift 2 ;;
    *) die "unknown argument: $1" ;;
  esac
done
[ -n "$paths_file$replace_file" ] || die "give --paths and/or --replace"
[ -z "$paths_file" ] || [ -f "$paths_file" ] || die "not a file: $paths_file"
[ -z "$replace_file" ] || [ -f "$replace_file" ] || die "not a file: $replace_file"

git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repo"
cd "$(git rev-parse --show-toplevel)"

if [ "${HISTORY_REWRITE_SKIP_VISIBILITY:-}" != 1 ]; then
  vis=$(gh repo view --json visibility -q .visibility 2>/dev/null) || die "could not read repo visibility via gh"
  [ "$vis" = PRIVATE ] || die "repo visibility is '$vis', refusing: only a private repo may be rewritten"
fi

[ -z "$(git status --porcelain)" ] || die "working tree is not clean"
git filter-repo --version >/dev/null 2>&1 || die "git-filter-repo missing (install: brew install git-filter-repo, or uv tool install git-filter-repo)"

origin_url=$(git remote get-url origin 2>/dev/null || true)
backup="$(cd .. && pwd)/$(basename "$PWD")-pre-rewrite-backup-$(date +%Y%m%d%H%M%S).git"
git clone --quiet --mirror "$PWD" "$backup"
printf 'Backup (full mirror): %s\n' "$backup"

set -- --force
[ -z "$paths_file" ] || set -- "$@" --invert-paths --paths-from-file "$paths_file"
[ -z "$replace_file" ] || set -- "$@" --replace-text "$replace_file"
git filter-repo "$@" >/dev/null 2>&1 || die "git filter-repo failed; restore from $backup"

fail=0
if [ -n "$paths_file" ]; then
  n=$(git log --all --name-only --format= | awk -v pf="$paths_file" '
    BEGIN { while ((getline p < pf) > 0) if (p != "") { sub(/\/$/, "", p); want[p] = 1 } }
    { f = $0; while (1) { if (f in want) { n++; break } if (f !~ /\//) break; sub(/\/[^\/]*$/, "", f) } }
    END { print n + 0 }')
  printf 'Removed paths still present in history: %s\n' "$n"
  [ "$n" -eq 0 ] || fail=1
fi
if [ -n "$replace_file" ]; then
  lit=$(mktemp) rx=$(mktemp)
  trap 'rm -f "$lit" "$rx"' EXIT
  awk -v lit="$lit" -v rx="$rx" '
    /^[[:space:]]*(#|$)/ { next }
    { s = $0; sub(/==>.*/, "", s) }
    s ~ /^regex:/ { sub(/^regex:/, "", s); print s > rx; next }
    s ~ /^glob:/ { next }
    { sub(/^literal:/, "", s); if (s != "") print s > lit }' "$replace_file"
  : >>"$lit"; : >>"$rx"
  n=0
  if [ -s "$lit" ]; then n=$((n + $(git log --all -p | grep -cF -f "$lit" || true))); fi
  if [ -s "$rx" ]; then n=$((n + $(git log --all -p | grep -cE -f "$rx" || true))); fi
  printf 'Lines still matching the replace patterns in history: %s\n' "$n"
  [ "$n" -eq 0 ] || fail=1
fi
[ "$fail" -eq 0 ] || die "verification failed: do not push; restore from $backup if needed"

cat <<MSG
Verification clean. Nothing was pushed. After explicit human confirmation, run:
  git remote add origin ${origin_url:-<remote-url>}
  git fetch origin
  git push --force-with-lease origin --all
  git push --force-with-lease origin --tags
MSG
