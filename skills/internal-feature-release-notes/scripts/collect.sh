#!/usr/bin/env bash
# Gather everything the skill needs to write a release-notes report, in one
# call, so the model never has to re-derive the git/date/URL plumbing.
#
# Usage: collect.sh [--days N] [--repo PATH] [--diffs]
#   --days N     look-back window in days (default 7)
#   --repo PATH  use this docs clone instead of auto-discovering it
#   --diffs      also emit the full diff of each published (.mdx) file touched
#
# Output is a single structured text blob with clearly delimited sections:
#   META        key=value lines (repo, git, window, since/today, commit count)
#   COMMITS     one "hash|date|author|subject" line per commit in window
#   PERCOMMIT   per-commit file lists, each file tagged with its live URL or a
#               NONPUBLISHED:<reason> marker
#   DIFFS       (only with --diffs) the actual diff content of published files
#
# Exit codes: 0 ok (incl. "no commits"), 1 no valid repo found, 2 bad args.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
. "$HERE/lib.sh"

DAYS=7
REPO=""
WANT_DIFFS=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --days) DAYS="${2:-}"; shift 2 ;;
    --repo) REPO="${2:-}"; shift 2 ;;
    --diffs) WANT_DIFFS=1; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "ERROR: unknown arg '$1'" >&2; exit 2 ;;
  esac
done
case "$DAYS" in ''|*[!0-9]*) echo "ERROR: --days must be an integer" >&2; exit 2 ;; esac

GIT="$(resolve_git)" || exit 1

# Resolve repo (validate a supplied path, else auto-discover).
if [ -n "$REPO" ]; then
  REPO="${REPO/#\~/$HOME}"
  validate_repo "$REPO" || { echo "ERROR: '$REPO' is not a valid docs-repo clone" >&2; exit 1; }
  REPO="$( cd "$REPO" && pwd )"
else
  REPO="$(find_repo)" || {
    echo "ERROR: no valid docs-repo clone found (searched common locations + home tree)" >&2
    exit 1
  }
fi

SINCE="$(since_date "$DAYS")"
TODAY="$(today_date)"

# Commits in window, across all branches.
COMMITS="$("$GIT" -C "$REPO" log --since="$SINCE 00:00:00" \
  --pretty=format:"%h|%ad|%an|%s" --date=format:"%Y-%m-%d %H:%M" --all)"
COUNT=0
[ -n "$COMMITS" ] && COUNT="$(printf '%s\n' "$COMMITS" | grep -c '|')"

echo "=== META ==="
echo "REPO=$REPO"
echo "GIT=$GIT"
echo "WINDOW_DAYS=$DAYS"
echo "SINCE=$SINCE"
echo "TODAY=$TODAY"
echo "COMMIT_COUNT=$COUNT"

echo "=== COMMITS ==="
[ -n "$COMMITS" ] && printf '%s\n' "$COMMITS"

if [ "$COUNT" -eq 0 ]; then
  # Helpful context: show the most recent commit so the report can mention it.
  echo "=== MOST_RECENT (outside window) ==="
  "$GIT" -C "$REPO" log -3 --pretty=format:"%h|%ad|%an|%s" \
    --date=format:"%Y-%m-%d %H:%M" --all
  echo
  exit 0
fi

HASHES="$(printf '%s\n' "$COMMITS" | cut -d'|' -f1)"

echo "=== PERCOMMIT ==="
for h in $HASHES; do
  subj="$("$GIT" -C "$REPO" show -s --pretty=format:"%s" "$h")"
  echo "## $h $subj"
  # name-status: status<TAB>path  (handle renames: R### old new)
  "$GIT" -C "$REPO" show --name-status --pretty=format: "$h" | sed '/^$/d' | \
  while IFS=$'\t' read -r status f1 f2; do
    path="$f1"; [ -n "${f2:-}" ] && path="$f2"   # for renames, use the new path
    url="$(map_url "$path")"
    printf '%s\t%s\t%s\n' "$status" "$path" "$url"
  done
  echo "---"
done

if [ "$WANT_DIFFS" -eq 1 ]; then
  echo "=== DIFFS ==="
  for h in $HASHES; do
    # Only diff published .mdx pages — internal/config/images are noise here.
    files="$("$GIT" -C "$REPO" show --name-only --pretty=format: "$h" | sed '/^$/d' | grep -E '\.mdx$' || true)"
    [ -z "$files" ] && continue
    echo "## $h"
    # shellcheck disable=SC2086
    "$GIT" -C "$REPO" show "$h" -- $files
    echo "=== END $h ==="
  done
fi
