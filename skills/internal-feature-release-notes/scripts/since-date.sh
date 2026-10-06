#!/usr/bin/env bash
# Print the "since" date for the release-notes window.
# Usage: since-date.sh [DAYS]   (DAYS defaults to 7)
#
# Prints two lines so the caller never has to do date math by hand:
#   SINCE=<YYYY-MM-DD>   (today - DAYS)
#   TODAY=<YYYY-MM-DD>
#
# Cross-platform (macOS BSD date and GNU date). This exists so the window is
# always computed from the real system clock, not guessed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
. "$HERE/lib.sh"

DAYS="${1:-7}"
case "$DAYS" in
  ''|*[!0-9]*) echo "ERROR: DAYS must be a non-negative integer, got '$DAYS'" >&2; exit 2 ;;
esac

echo "SINCE=$(since_date "$DAYS")"
echo "TODAY=$(today_date)"
