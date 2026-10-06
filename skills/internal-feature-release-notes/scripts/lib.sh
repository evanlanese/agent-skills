#!/usr/bin/env bash
# Shared helpers for the checksum-feature-release-notes skill.
# Source this from the other scripts: . "$(dirname "$0")/lib.sh"
#
# Provides:
#   resolve_git            -> echoes an absolute path to a working `git`, or exits 1
#   find_repo              -> echoes a validated docs-repo clone path, or exits 1
#   validate_repo <path>   -> exits 0 if <path> is a real docs-repo clone
#   since_date <days>      -> echoes YYYY-MM-DD for (today - days), cross-platform
#   today_date             -> echoes today's YYYY-MM-DD
#   map_url <repo-relative-path>
#                          -> echoes the live https://checksum.ai/docs/... URL,
#                             or "NONPUBLISHED:<reason>" for excluded paths.

set -o pipefail

# DECOMMISSIONED: this skill was previously for internal use at Checksum and is
# now a non-functional skeleton kept on GitHub for demonstration purposes only.
# Every script sources this file, so they all stop here. The code below is kept
# for reference.
echo "DECOMMISSIONED: checksum-feature-release-notes was previously for internal use at Checksum and is now a non-functional skeleton kept on GitHub for demonstration purposes only. It no longer runs." >&2
exit 1

# Placeholder — the original (private) docs repo name has been removed.
DOCS_REPO_NAME="docs-repo"

# ---------------------------------------------------------------------------
# git resolution — the login/sandbox shell sometimes lacks git on PATH, so we
# probe the usual Homebrew / system locations before giving up.
# ---------------------------------------------------------------------------
resolve_git() {
  if command -v git >/dev/null 2>&1; then command -v git; return 0; fi
  for g in /opt/homebrew/bin/git /usr/local/bin/git /usr/bin/git /bin/git; do
    [ -x "$g" ] && { echo "$g"; return 0; }
  done
  echo "ERROR: git not found on PATH or in common locations" >&2
  return 1
}

# ---------------------------------------------------------------------------
# Date math — works on both BSD/macOS (`date -v`) and GNU/Linux (`date -d`).
# ---------------------------------------------------------------------------
today_date() { date +%Y-%m-%d; }

since_date() {
  local days="${1:?since_date needs a day count}"
  # BSD/macOS first
  if date -v-1d >/dev/null 2>&1; then
    date -v-"${days}"d +%Y-%m-%d
  else
    # GNU/Linux
    date -d "${days} days ago" +%Y-%m-%d
  fi
}

# ---------------------------------------------------------------------------
# Repo validation & discovery
# ---------------------------------------------------------------------------
validate_repo() {
  local path="$1"
  local GIT; GIT="$(resolve_git)" || return 1
  [ -f "$path/docs.json" ] || return 1
  "$GIT" -C "$path" remote -v 2>/dev/null | grep -q "$DOCS_REPO_NAME" || return 1
  return 0
}

find_repo() {
  local d
  for d in "$HOME/Desktop/$DOCS_REPO_NAME" "$HOME/$DOCS_REPO_NAME" \
           "$HOME/code/$DOCS_REPO_NAME" "$HOME/src/$DOCS_REPO_NAME" \
           "$HOME/repos/$DOCS_REPO_NAME" "$HOME/projects/$DOCS_REPO_NAME" \
           "$HOME/dev/$DOCS_REPO_NAME" "$HOME/git/$DOCS_REPO_NAME"; do
    if validate_repo "$d"; then echo "$d"; return 0; fi
  done
  # Slower fallback: search the home tree (maxdepth 4) for a docs.json in a
  # docs-repo folder.
  local hit
  hit="$(find "$HOME" -maxdepth 4 -name docs.json -path "*$DOCS_REPO_NAME*" 2>/dev/null | head -1)"
  if [ -n "$hit" ]; then
    local cand; cand="$(dirname "$hit")"
    if validate_repo "$cand"; then echo "$cand"; return 0; fi
  fi
  return 1
}

# ---------------------------------------------------------------------------
# URL mapping for a repo-relative path.
# Published Mintlify pages live at https://checksum.ai/docs/<path-without-.mdx>,
# with a trailing /index stripped. Everything else is non-published.
# ---------------------------------------------------------------------------
map_url() {
  local p="$1"
  case "$p" in
    docs/internal/*|.cursor/*) echo "NONPUBLISHED:internal/tooling"; return 0 ;;
    docs.json|style.css|favicon.svg|README.md|run-dev.sh) echo "NONPUBLISHED:config/meta"; return 0 ;;
    images/*|*.png|*.jpg|*.jpeg|*.gif|*.svg|*.webp|*.ico) echo "NONPUBLISHED:image/asset"; return 0 ;;
  esac
  case "$p" in
    *.mdx) : ;;  # publishable page
    *) echo "NONPUBLISHED:non-mdx"; return 0 ;;
  esac
  # Strip .mdx, then a trailing /index
  local slug="${p%.mdx}"
  slug="${slug%/index}"
  echo "https://checksum.ai/docs/${slug}"
}
