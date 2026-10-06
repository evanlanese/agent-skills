#!/usr/bin/env bash
# Locate and validate a local docs-repo clone.
# Usage: find-repo.sh [CANDIDATE_PATH]
#   - If CANDIDATE_PATH is given, validate just that path (expands ~).
#   - Otherwise search the common clone locations + a home-tree fallback.
# On success prints the validated absolute path and exits 0.
# On failure prints nothing to stdout and exits 1.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
. "$HERE/lib.sh"

if [ "$#" -ge 1 ] && [ -n "${1:-}" ]; then
  cand="${1/#\~/$HOME}"
  if validate_repo "$cand"; then
    ( cd "$cand" && pwd )
    exit 0
  fi
  echo "ERROR: '$cand' is not a valid docs-repo clone (needs docs.json + docs-repo remote)" >&2
  exit 1
fi

if repo="$(find_repo)"; then
  echo "$repo"
  exit 0
fi
exit 1
