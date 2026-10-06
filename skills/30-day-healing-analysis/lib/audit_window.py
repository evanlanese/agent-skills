#!/usr/bin/env python3
"""
audit_window.py — Phase 0 helper that computes the canonical audit window.

This is the SINGLE SOURCE OF TRUTH for the audit-window dates that appear in
both the git query (`git log --since=<start>`) and the customer-facing report
("Audit window: 2026-04-28 → 2026-05-28 (30 days)"). Previously these two
were computed from different sources — the git query used the freeform
`"30 days ago"` string and the report-displayed window was reconstructed from
the FIRST and LAST observed commit dates, which under-reported the window
whenever the customer had quiet stretches at the start or end. This module
fixes that by making both consumers read from the same computed dict.

Cross-month and cross-year boundaries are handled by `datetime.timedelta`
natively — going back 30 days from January 15 correctly lands on December 16
of the prior year, etc.

The function is intentionally pure (no I/O, no globals, no side effects) so
it's trivial to unit-test by passing an explicit `end_date`.

Usage:

  # In collect.py:
  from audit_window import compute_audit_window
  window = compute_audit_window(days=30)
  # window["since_git_arg"]            -> "2026-04-28"   (pass to git --since=)
  # window["audit_window_start_date"]  -> "2026-04-28"
  # window["audit_window_end_date"]    -> "2026-05-28"
  # window["audit_window_days"]        -> 30
  # window["audit_window_display"]     -> "2026-04-28 → 2026-05-28 (30 days)"
  # window["report_date_iso"]          -> "2026-05-28"   (for filename slug)
  # window["report_date_pretty"]       -> "May 28, 2026" (for the "Dated:" line)

  # CLI smoke test:
  python3 audit_window.py --days 30
  python3 audit_window.py --days 30 --end-date 2026-01-15
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone


def compute_audit_window(
    days: int = 30,
    end_date: date | None = None,
) -> dict:
    """Compute the canonical audit window for a Checksum heals audit.

    Args:
      days: number of days the window should span. Defaults to 30. Must be > 0.
      end_date: the inclusive END of the window. Defaults to today (local
        date). Passing an explicit `end_date` makes the function deterministic
        for tests and lets a caller produce a reproducible report for an
        earlier audit.

    Returns:
      A dict with every string the rest of the pipeline needs. Keys are stable
      and consumed by `collect.py` (writes them into metadata.json) and by the
      Phase 2 synthesizer (reads them out of metadata.json into the report
      template).

    The window is inclusive on both ends: a 30-day audit ending on 2026-05-28
    starts on 2026-04-28 (which `timedelta(days=30)` produces by subtraction),
    so both endpoints are real calendar days that show up in the report.
    """
    if days <= 0:
        raise ValueError(f"days must be > 0, got {days}")

    end = end_date if end_date is not None else date.today()
    start = end - timedelta(days=days)

    return {
        # Git query input: pass to `git log --since=<this>`. Git accepts ISO
        # dates and interprets them as 00:00:00 local time on that day, so
        # commits made on `start` itself are included in the window.
        "since_git_arg": start.isoformat(),

        # Customer-facing window: pasted into the "Audit window" metadata-table
        # row and the dated line under the H2. These are the AUTHORITATIVE
        # window boundaries — derived deterministically from today's date and
        # the `days` count, NOT from observed commit dates.
        "audit_window_start_date": start.isoformat(),
        "audit_window_end_date": end.isoformat(),
        "audit_window_days": days,
        "audit_window_display": (
            f"{start.isoformat()} → {end.isoformat()} ({days} days)"
        ),

        # Report-generation date strings, used by the synthesizer for the
        # "Dated:" line and the on-disk filename slug. ISO form goes into the
        # filename, pretty form goes into the report.
        "report_date_iso": end.isoformat(),
        "report_date_pretty": _pretty_date(end),

        # When the window was computed (UTC). Useful for forensics if a report
        # is regenerated days after the audit ran.
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _pretty_date(d: date) -> str:
    """Format a date as 'Month D, YYYY' with NO leading zero on the day.

    `%-d` works on Linux/macOS but not Windows, so build the string manually
    for portability. Examples:
      2026-05-28 -> "May 28, 2026"
      2026-05-08 -> "May 8, 2026"
      2025-12-01 -> "December 1, 2025"
    """
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Compute the canonical audit window for the 30-day-healing-analysis "
            "skill. Prints a JSON dict suitable for collect.py / the report "
            "synthesizer. Run with --end-date to test cross-month boundaries."
        )
    )
    ap.add_argument(
        "--days", type=int, default=30,
        help="Window length in days (default: 30)",
    )
    ap.add_argument(
        "--end-date", type=date.fromisoformat, default=None,
        help=(
            "Inclusive end of the window as YYYY-MM-DD. Defaults to today's "
            "local date. Useful for testing or reproducing a prior audit."
        ),
    )
    args = ap.parse_args()

    try:
        window = compute_audit_window(days=args.days, end_date=args.end_date)
    except ValueError as e:
        sys.exit(f"FATAL: {e}")

    print(json.dumps(window, indent=2))


if __name__ == "__main__":
    # The skill is decommissioned; the code above is kept for reference only.
    sys.exit("DECOMMISSIONED: 30-day-healing-analysis was previously for internal use at Checksum "
             "and is now a non-functional skeleton kept on GitHub for "
             "demonstration purposes only. It no longer runs.")
