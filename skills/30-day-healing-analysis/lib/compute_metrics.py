#!/usr/bin/env python3
"""
compute_metrics.py — Phase 1.5 metric computation for the
30-day-healing-analysis skill.

Reads <workspace>/classifications.jsonl plus the per-(commit, file) diff
files written by collect.py, then writes <workspace>/metrics.json with
every number the Phase 2 synthesizer needs to render the customer-facing
report. The synthesizer MUST use these numbers verbatim — the AI does no
arithmetic.

────────────────────────────────────────────────────────────────────────
HOW THE MATH WORKS (this is the contract — read it before editing)
────────────────────────────────────────────────────────────────────────

Two cost rates, two flavors of "change event":

  • Routine fix (locator, stability, flow, data, framework):
      Each unique commit in a category counts as ONE fix.
      Each fix = `--per-fix-minutes` (default 30) of saved human review.
      NOTE: `assertion-update` is intentionally NOT a counted category.
      Adjusting an expected value/text/count is trivial work already
      baked into the per-fix estimate of whatever fix it accompanies; it
      is not its own time-consuming exercise. The classifier still emits
      the label (so the evidence is preserved), but it never produces a
      Maintenance Impact row and an assertion-only commit contributes
      nothing to the totals.

  • Bug annotation:
      Each unique bug `description: "..."` added during the window counts
      as ONE bug. "Unique" means verbatim normalized text (whitespace
      collapsed, quote-style ignored). If five different tests get the
      same word-for-word description, that's ONE bug; if they get five
      different descriptions, that's FIVE bugs.
      Each bug = `--per-bug-minutes` (default 60) of saved human review.
      Bug review is longer than a routine fix because product
      investigation is required to confirm the underlying defect.

Per-category counts can OVERLAP (a single commit classified into both
`locator-change` and `stability-fix` shows up in BOTH categories).
That overlap is intentional: each category represents a distinct unit
of human-review attention that would have been required if the AI
weren't doing the work. The grand total is therefore the SUM of all
category counts + the bug count — it does NOT deduplicate commits
across categories. This guarantees the Maintenance Impact table's
math adds up exactly: per-category Time Saved cells sum to the Total
Time Saved cell, every time.

────────────────────────────────────────────────────────────────────────
USAGE
────────────────────────────────────────────────────────────────────────

  python3 compute_metrics.py \\
      --workspace /tmp/checksum-heals-audit-acme-corp \\
      [--per-fix-minutes 30] \\
      [--per-bug-minutes 60]

Exit codes:
  0  metrics.json written, JSON also printed to stdout
  1  workspace missing or classifications.jsonl missing

The pure `calculate_time_saved()` function is importable and takes
counts + rates as plain arguments — useful for ad-hoc what-if analysis
without a workspace.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────
# Tunable defaults — the customer-facing assumptions
# ────────────────────────────────────────────────────────────────────────
DEFAULT_PER_FIX_MINUTES = 30
DEFAULT_PER_BUG_MINUTES = 60

# ────────────────────────────────────────────────────────────────────────
# Display categories — the rows shown in the Maintenance Impact table.
# Categories deliberately NOT mapped (and therefore NOT shown as a row):
#   • bug-annotation-added / bug-annotation-removed — bugs get their own
#     row computed from text-deduped descriptions, not from classification
#     row counts.
#   • assertion-update — adjusting an expected text/count/role assertion is
#     trivial work already baked into the per-fix estimate of the fix it
#     rides along with; it is not a separate time-consuming exercise. Like
#     uncategorized, it never produces a row and assertion-only commits do
#     NOT contribute to the totals. The classifier still emits the label so
#     the underlying evidence is preserved.
#   • uncategorized — does not represent a customer-facing value-prop
#     line. These commits also do NOT contribute to the totals; they are
#     orphan classifications that the AI failed to bucket.
# ────────────────────────────────────────────────────────────────────────
DISPLAY_CATEGORIES = [
    {
        "key": "locator-change",
        "label": "Locator / Selector Updates",
        "description": "Element selectors hardened against UI churn",
    },
    {
        "key": "stability",  # combined: wait-timing + stability-fix
        "label": "Test Stability & Reliability",
        "description": "Wait times, race conditions, retry loops, dialog handlers",
    },
    {
        "key": "flow-change",
        "label": "Flow & Step Restructuring",
        "description": "Reordered or restructured test actions to match application flow",
    },
    {
        "key": "data-fixture",
        "label": "Data & Fixture Updates",
        "description": "Test data, role assignments, or environment-specific values refreshed",
    },
    {
        "key": "framework-upgrade",
        "label": "Framework / Config",
        "description": "Playwright config, login helpers, framework-level changes",
    },
]

# Label of the bug-annotation row in the impact table.
BUG_CATEGORY_LABEL = "Bug Annotations"
BUG_CATEGORY_DESCRIPTION = (
    "Unique product bugs Checksum identified and tracked via `@bug` annotations"
)

CLASSIFIER_TO_DISPLAY = {
    "locator-change": "locator-change",
    "wait-timing": "stability",
    "stability-fix": "stability",
    "flow-change": "flow-change",
    "data-fixture": "data-fixture",
    "framework-upgrade": "framework-upgrade",
    # assertion-update: intentionally absent — trivial work baked into the per-fix
    #   estimate; never its own counted row (see DISPLAY_CATEGORIES comment above).
    # bug-annotation-added / bug-annotation-removed / uncategorized: intentionally absent
}

# Regex set for extracting bug `description: "..."` strings from added
# diff lines. Supports double-quoted, single-quoted, and template-literal
# (backtick) string forms. DOTALL so the multi-line backtick form works.
DESCRIPTION_PATTERNS = [
    re.compile(r'description\s*:\s*"((?:[^"\\]|\\.)*?)"', re.DOTALL),
    re.compile(r"description\s*:\s*'((?:[^'\\]|\\.)*?)'", re.DOTALL),
    re.compile(r"description\s*:\s*`((?:[^`\\]|\\.)*?)`", re.DOTALL),
]

# Quick check: does the added-line text contain `type: "bug"` (any quote
# style)? We only collect descriptions from diffs that also add a bug
# type marker, so we don't accidentally pick up unrelated `description:`
# fields elsewhere in the code.
BUG_TYPE_RE = re.compile(r"""type\s*:\s*['"`]bug['"`]""")

# Spec-file name suffixes we strip when deriving a human-readable test
# name from a file path. Order matters — the longest must come first.
TEST_NAME_SUFFIXES = (
    ".checksum.spec.ts",
    ".checksum.spec.js",
    ".spec.ts",
    ".spec.js",
    ".ts",
    ".js",
)


# ────────────────────────────────────────────────────────────────────────
# Pure utility functions (no I/O)
# ────────────────────────────────────────────────────────────────────────

def safe_filename(s: str) -> str:
    """Mirrors collect.py's safe_filename so we can reconstruct diff paths."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def round_half(x: float) -> float:
    """Round a float to the nearest 0.5."""
    return round(x * 2) / 2


def format_hours(hours: float) -> str:
    """Pretty-print hours for table cells: '~15 hrs', '~7.5 hrs', '~1 hr'.

    Trailing `.0` is dropped (15.0 -> '~15 hrs'), and the singular '1 hr'
    is special-cased for grammar.
    """
    if hours == 1:
        return "~1 hr"
    if hours == int(hours):
        return f"~{int(hours)} hrs"
    return f"~{hours:.1f} hrs"


def format_hours_bare(hours: float) -> str:
    """Pretty-print hours as a bare number for prose headlines: '15', '7.5'.

    The headline blockquote reads 'approximately <HOURS> hours of engineering
    time' — we want just the number, no leading ~ or trailing ' hrs'.
    """
    if hours == int(hours):
        return f"{int(hours)}"
    return f"{hours:.1f}"


def normalize_description(text: str) -> str:
    """Normalize a bug description for verbatim de-duplication.

    Strips leading/trailing whitespace and collapses internal whitespace
    runs to a single space. Two descriptions that differ only in
    indentation or line wrapping hash to the same key.
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_added_lines(diff_text: str) -> str:
    """Return the concatenation of all `+` (added) lines from a unified diff,
    excluding the `+++` file-header marker. Each line keeps its content but
    drops the leading `+`."""
    out: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            out.append(line[1:])
    return "\n".join(out)


def extract_added_bug_descriptions(diff_text: str) -> list[str]:
    """Find every `description: "..."` in added lines, but only if the same
    diff also adds a `type: "bug"` marker. Returns descriptions in the order
    encountered, with whitespace normalized."""
    added = extract_added_lines(diff_text)
    if not BUG_TYPE_RE.search(added):
        return []
    descriptions: list[str] = []
    for pat in DESCRIPTION_PATTERNS:
        for m in pat.finditer(added):
            d = normalize_description(m.group(1))
            if d:
                descriptions.append(d)
    return descriptions


def extract_test_name(file_path: str) -> str:
    """Derive a human-readable test name from a Checksum spec file path.

    e.g. 'checksum/tests/.../Create Order - Required Fields - Ab12C.checksum.spec.ts'
      -> 'Create Order - Required Fields - Ab12C'
    """
    name = Path(file_path).name
    for suf in TEST_NAME_SUFFIXES:
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


# ────────────────────────────────────────────────────────────────────────
# THE pure calculator — counts in, metrics out. No file I/O.
# Importable and reusable for ad-hoc what-if analysis without a workspace.
# ────────────────────────────────────────────────────────────────────────

def calculate_time_saved(
    per_category_commits: dict[str, int],
    bug_count: int,
    per_fix_minutes: int = DEFAULT_PER_FIX_MINUTES,
    per_bug_minutes: int = DEFAULT_PER_BUG_MINUTES,
) -> dict:
    """Compute the Maintenance Impact metrics from raw counts.

    Args:
        per_category_commits: map of display label → commit count for that
            category. Categories with a zero count are filtered out.
            A commit appearing in two categories should be counted once
            in each — the totals are additive on purpose.
        bug_count: number of unique bug annotations (verbatim-deduped).
        per_fix_minutes: saved human-review minutes per routine fix.
        per_bug_minutes: saved human-review minutes per bug annotation.

    Returns:
        A dict ready to be merged into metrics.json. The Total Time Saved
        is guaranteed to equal the SUM of every category's Time Saved
        plus the Bug Annotations row — so the customer-facing impact
        table always adds up exactly.
    """
    # Per-category breakdown (drop zero-count rows, then sort by count desc).
    categories: list[dict] = []
    for label, count in per_category_commits.items():
        if count <= 0:
            continue
        minutes = count * per_fix_minutes
        hours = round_half(minutes / 60.0)
        categories.append({
            "label": label,
            "commits": count,
            "minutes_saved": minutes,
            "hours_saved": hours,
            "time_saved_display": format_hours(hours),
        })
    categories.sort(key=lambda c: c["commits"], reverse=True)

    # Bug row (only included if at least one bug was found).
    bug_minutes = bug_count * per_bug_minutes
    bug_hours = round_half(bug_minutes / 60.0)
    bugs_row: dict | None
    if bug_count > 0:
        bugs_row = {
            "label": BUG_CATEGORY_LABEL,
            "description": BUG_CATEGORY_DESCRIPTION,
            "commits": bug_count,
            "minutes_saved": bug_minutes,
            "hours_saved": bug_hours,
            "time_saved_display": format_hours(bug_hours),
        }
    else:
        bugs_row = None

    # Totals — strictly additive: every cell in the table sums to the bottom.
    cat_minutes = sum(c["minutes_saved"] for c in categories)
    cat_commits = sum(c["commits"] for c in categories)
    total_minutes = cat_minutes + bug_minutes
    total_change_events = cat_commits + bug_count
    total_hours = round_half(total_minutes / 60.0)

    # Pre-formatted calculation string for the metadata table.
    if bug_count > 0:
        calc_display = (
            f"{cat_commits} fixes × {per_fix_minutes} min "
            f"+ {bug_count} bugs × {per_bug_minutes} min"
        )
    else:
        calc_display = f"{cat_commits} fixes × {per_fix_minutes} min"

    return {
        "per_fix_minutes": per_fix_minutes,
        "per_bug_minutes": per_bug_minutes,
        "categories": categories,
        "bugs_row": bugs_row,
        "category_commits_subtotal": cat_commits,
        "category_minutes_subtotal": cat_minutes,
        "total_change_events": total_change_events,
        "total_minutes_saved": total_minutes,
        "total_hours_saved": total_hours,
        "total_hours_saved_display": format_hours(total_hours),
        "total_hours_saved_headline": format_hours_bare(total_hours),
        "total_calculation_display": calc_display,
    }


# ────────────────────────────────────────────────────────────────────────
# Workspace-reading layer (I/O wrappers around the pure calculator)
# ────────────────────────────────────────────────────────────────────────

def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def build_diff_path_index(workspace: Path) -> dict[tuple[str, str], str]:
    """Map (commit_sha, file) → diff_path, sourced from commits.jsonl."""
    commits_path = workspace / "commits.jsonl"
    if not commits_path.exists():
        return {}
    idx: dict[tuple[str, str], str] = {}
    for row in load_jsonl(commits_path):
        if "commit" in row and "file" in row and "diff_path" in row:
            idx[(row["commit"], row["file"])] = row["diff_path"]
    return idx


def resolve_diff_path(
    workspace: Path,
    row: dict,
    diff_index: dict[tuple[str, str], str],
) -> Path | None:
    """Best-effort resolution of the diff file for a classification row.

    1. If commits.jsonl indexed it, use that path.
    2. Otherwise reconstruct from short_sha + safe_filename(file).
    3. Return None if neither exists on disk.
    """
    indexed = diff_index.get((row.get("commit"), row.get("file")))
    if indexed:
        p = Path(indexed)
        if p.exists():
            return p
    short_sha = row.get("short_sha") or (row.get("commit", "")[:7])
    file_path = row.get("file", "")
    if not short_sha or not file_path:
        return None
    safe = safe_filename(file_path.replace("/", "__"))
    p = workspace / "diffs" / f"{short_sha}__{safe}.diff"
    return p if p.exists() else None


def compute_per_category_commits(rows: list[dict]) -> dict[str, int]:
    """For each display category, count UNIQUE commit SHAs that include it.

    A commit classified into multiple categories contributes once to each
    of those categories — the totals are additive by design.
    """
    commit_to_keys: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.get("isNoise"):
            continue
        for cat in row.get("categories", []):
            display_key = CLASSIFIER_TO_DISPLAY.get(cat)
            if display_key is None:
                continue
            commit_to_keys[row["commit"]].add(display_key)

    counts: dict[str, int] = {}
    for spec in DISPLAY_CATEGORIES:
        n = sum(1 for keys in commit_to_keys.values() if spec["key"] in keys)
        if n > 0:
            counts[spec["label"]] = n
    return counts


def extract_bug_records(
    rows: list[dict],
    workspace: Path,
    diff_index: dict[tuple[str, str], str],
) -> tuple[int, list[str], list[dict]]:
    """Walk every non-noise bug-annotation-added row, open the diff, and
    extract added bug descriptions. De-duplicates verbatim across the entire
    window.

    Returns (bug_count, ordered_unique_descriptions, ordered_unique_records).
    `records` is the customer-facing payload for the Bugs Found section —
    one entry per unique description, with the first test the bug was
    observed in attached for context.
    """
    seen: set[str] = set()
    descriptions: list[str] = []
    records: list[dict] = []

    bug_rows = [
        r for r in rows
        if not r.get("isNoise") and "bug-annotation-added" in r.get("categories", [])
    ]
    for row in bug_rows:
        diff_path = resolve_diff_path(workspace, row, diff_index)
        if diff_path is None:
            print(
                f"WARN: diff not found for {row.get('short_sha')} {row.get('file')}",
                file=sys.stderr,
            )
            continue
        try:
            diff_text = diff_path.read_text(errors="replace")
        except OSError as exc:
            print(f"WARN: could not read {diff_path}: {exc}", file=sys.stderr)
            continue
        for desc in extract_added_bug_descriptions(diff_text):
            if desc in seen:
                continue
            seen.add(desc)
            descriptions.append(desc)
            records.append({
                "description": desc,
                "first_short_sha": row.get("short_sha", ""),
                "first_date": (row.get("date") or "")[:10],
                "first_file": row.get("file", ""),
                "first_test_name": extract_test_name(row.get("file", "")),
            })
    return len(descriptions), descriptions, records


# ────────────────────────────────────────────────────────────────────────
# CLI entrypoint
# ────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Compute the Maintenance Impact metrics for the "
            "30-day-healing-analysis skill. Writes <workspace>/metrics.json "
            "and prints the same JSON to stdout."
        )
    )
    ap.add_argument("--workspace", required=True, type=Path)
    ap.add_argument(
        "--per-fix-minutes", type=int, default=DEFAULT_PER_FIX_MINUTES,
        help="Saved review minutes per routine fix (default: 30).",
    )
    ap.add_argument(
        "--per-bug-minutes", type=int, default=DEFAULT_PER_BUG_MINUTES,
        help="Saved review minutes per unique bug annotation (default: 60).",
    )
    args = ap.parse_args()

    ws = args.workspace.resolve()
    if not ws.exists():
        sys.exit(f"FATAL: workspace not found: {ws}")
    classifications_path = ws / "classifications.jsonl"
    if not classifications_path.exists():
        sys.exit(
            f"FATAL: {classifications_path} not found — run Phase 1 "
            "(diff classification) before computing metrics."
        )

    rows = load_jsonl(classifications_path)
    diff_index = build_diff_path_index(ws)

    bugs_found, bug_descriptions, bug_records = extract_bug_records(
        rows, ws, diff_index
    )
    per_category = compute_per_category_commits(rows)

    math = calculate_time_saved(
        per_category_commits=per_category,
        bug_count=bugs_found,
        per_fix_minutes=args.per_fix_minutes,
        per_bug_minutes=args.per_bug_minutes,
    )

    metrics = {
        "bugs_found": bugs_found,
        "bug_descriptions": bug_descriptions,
        "bug_records": bug_records,
        **math,
    }

    out_path = ws / "metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    # The skill is decommissioned; the code above is kept for reference only.
    sys.exit("DECOMMISSIONED: 30-day-healing-analysis was previously for internal use at Checksum "
             "and is now a non-functional skeleton kept on GitHub for "
             "demonstration purposes only. It no longer runs.")
