#!/usr/bin/env python3
"""
snapshot.py — DECOMMISSIONED skeleton of the "quick suite snapshot" script.

This script was previously for internal use at Checksum. It is now kept on
GitHub as a non-functional skeleton for demonstration purposes only. All
platform API access, endpoints, and credential handling have been removed;
running it only prints a decommission notice.

What it used to do (for reference):
  1. Resolve each customer name to an application, by EXACT name only.
  2. Pull LIFETIME totals: tests generated, test runs, distinct bugs found.
  3. Pull the most recent runs (~30) and compute two pass rates:
       * run-level  pass rate = runs with status == "passed" / runs analyzed
       * test-level pass rate = Σpassed / Σ(passed + failed) across runs that
                                carry per-test counts (infra-failed runs with
                                null counts are excluded from this ratio)
  4. Render a plain-text or markdown block per customer, concatenated in input
     order; an unmatched customer is marked SKIPPED without aborting the rest.

The pure calculation helpers below are retained to show the metric logic.
"""

from __future__ import annotations

import sys

DECOMMISSIONED = (
    "DECOMMISSIONED: quick-suite-snapshot was previously for internal use at "
    "Checksum and is now a non-functional skeleton kept on GitHub for "
    "demonstration purposes only. It no longer runs or calls any API."
)


def compute_pass_rates(runs: list[dict]) -> dict:
    """Run-level and test-level pass rates for a list of run records.

    Each run is a dict shaped like
    {"status": "passed" | "failed", "passed": int | None, "failed": int | None,
     "healed": int | None, "bug": int | None}.
    """
    analyzed = len(runs)
    run_passed = sum(1 for r in runs if r.get("status") == "passed")

    counted, p_sum, f_sum, healed_sum, bug_sum = 0, 0, 0, 0, 0
    for r in runs:
        p, f = r.get("passed"), r.get("failed")
        if p is None and f is None:
            continue  # infra-failed / not-yet-reported run — no per-test counts
        counted += 1
        p_sum += p or 0
        f_sum += f or 0
        healed_sum += r.get("healed") or 0
        bug_sum += r.get("bug") or 0

    test_denom = p_sum + f_sum
    return {
        "analyzed": analyzed,
        "run_passed": run_passed,
        "run_failed": analyzed - run_passed,
        "run_rate": (run_passed / analyzed) if analyzed else None,
        "counted_runs": counted,
        "passed": p_sum,
        "failed": f_sum,
        "healed": healed_sum,
        "bug": bug_sum,
        "test_rate": (p_sum / test_denom) if test_denom else None,
    }


def group_by_description(bugs: list[tuple[str, str]]) -> list[tuple[str, list[str]]]:
    """Group distinct (test, description) pairs by WORD-FOR-WORD description,
    preserving first-occurrence order of both descriptions and their tests."""
    order, groups = [], {}
    for test, desc in bugs:
        if desc not in groups:
            groups[desc] = []
            order.append(desc)
        groups[desc].append(test)
    return [(desc, groups[desc]) for desc in order]


if __name__ == "__main__":
    sys.exit(DECOMMISSIONED)
