#!/usr/bin/env python3
"""
customer_report.py — DECOMMISSIONED skeleton of the Part 2 "lifetime metrics"
digest for the 30-day-healing-analysis skill.

This script was previously for internal use at Checksum. It is now kept on
GitHub as a non-functional skeleton for demonstration purposes only. All
platform API access, endpoints, and credential handling have been removed;
running it only prints a decommission notice.

What it used to do (for reference):
  1. Resolve the customer to an application, by EXACT name only.
  2. Pull LIFETIME totals: tests generated, test runs, and every test marked
     as a bug.
  3. Render a `## Lifetime Testing Metrics` markdown section — a 3-cell table
     (Total Tests Generated · Total Test Runs · Total Bugs Found) plus the bug
     list grouped by word-for-word description — and append it to the Part 1
     report. The append was idempotent: re-running replaced the section.
"""

from __future__ import annotations

import sys

DECOMMISSIONED = (
    "DECOMMISSIONED: 30-day-healing-analysis was previously for internal use at "
    "Checksum and is now a non-functional skeleton kept on GitHub for "
    "demonstration purposes only. It no longer runs or calls any API."
)


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


def render_markdown(total_tests: int, total_runs: int,
                    bugs: list[tuple[str, str]]) -> str:
    """The shape of the appended Part 2 section."""
    groups = group_by_description(bugs)
    L = [
        "## Lifetime Testing Metrics — Checksum AI",
        "",
        "| Total Tests Generated | Total Test Runs | Total Bugs Found |",
        "| --------------------: | --------------: | ---------------: |",
        f"| {total_tests:,} | {total_runs:,} | {len(bugs):,} |",
        "",
    ]
    for i, (desc, tests) in enumerate(groups, 1):
        L.append(f"{i}. {desc}")
        L += [f"   - `{t}`" for t in tests]
        L.append("")
    return "\n".join(L).rstrip() + "\n"


if __name__ == "__main__":
    sys.exit(DECOMMISSIONED)
