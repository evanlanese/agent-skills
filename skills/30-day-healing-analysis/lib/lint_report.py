#!/usr/bin/env python3
"""
lint_report.py — Phase 2.5 deterministic lint pass for the customer-facing report.

Runs AFTER the Phase 2 synthesizer writes the report and BEFORE the Phase 2
reviewer is dispatched. Catches the cheapest, highest-confidence violations
via regex matching so the reviewer round-trip doesn't burn a subagent call on
issues a `grep -E` could find in milliseconds.

Two categories of checks:

1. **Structural lint** (whole-report):
   - Forbidden section headings (Executive Summary, Observations, Smell signals,
     Detailed Commit Breakdown [retired name], Methodology, Appendix, ...)
   - Numbered section headings (`## 1.`, `## 2.`, `## 3.`, ...) — the report
     uses plain H2 titles
   - `**Files Changed:**` lines — retired forensics format
   - Footer presence (`_Report dated`, `_Questions? Contact your Checksum CSM._`)
   - `/tmp/` paths leaking from the workspace into the deliverable

2. **Bug-annotation context lint** (within the "## Bugs Found in Your Application"
   section only, with verbatim bug descriptions in `> blockquotes` stripped before
   matching so the lint doesn't false-positive on customer content):
   - Bug-annotation REMOVAL language: "closed", "removed", "reopened",
     "re-enabled", "net delta". Removals are internal cleanup work and must
     never surface in the customer report.

3. **Audit-window cross-check** (skipped when `--workspace` is not passed):
   - Reads `<workspace>/metadata.json` and verifies the report's "Dated:" line
     and "Audit window" cell match `metadata.report_date_pretty`,
     `metadata.audit_window_start_date`, `metadata.audit_window_end_date`,
     and `metadata.audit_window_days` exactly. This catches the historical
     bug where the synthesizer pasted `observed_first_commit_date →
     observed_last_commit_date` into the window cell, under-reporting the
     window whenever Checksum was quiet at the start or end of the period.

Exit code:
  0 — clean, report is ready for the reviewer (or to ship as-is)
  1 — violations found, parent agent must re-dispatch the synthesizer with
      lint.json as feedback

Output:
  <workspace>/lint.json — structured list of violations, even when empty.
  Also pretty-prints the violations to stdout for human-readable inspection.

Usage:
  python3 lint_report.py --report ~/Desktop/checksum-heals-audit-acme-2026-05-28.md \\
                         --workspace /tmp/checksum-heals-audit-acme
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ----- Forbidden section headings -----
# Matches against `^## <Name>` (also `### <Name>` etc.) with optional leading
# `1.` / `2.` numbering. Case-insensitive.
FORBIDDEN_HEADINGS = [
    "Executive Summary",
    "Overview",
    "Summary",
    "Summary by Category",
    "Maintenance Hotspots",
    "Most-Touched Utility Files",
    "Most Touched Utility Files",
    "Commit Timeline",
    "Bug Annotation Ledger",
    "Smell Signals",
    "Observations",
    "Concerns",
    "Findings",
    "Methodology",
    "Appendix",
    "Appendix A",
    "Appendix B",
    "Detailed Commit Breakdown",  # retired name; must be "Healing Examples"
    "Bug Annotations & Tagging",  # bugs roll up to dedicated section + scorecard
    "Bug Annotations and Tagging",
]

# ----- Forbidden whole-report line patterns -----
# Anchored regexes so they don't false-positive on diff content inside fenced
# code blocks (code blocks contain real customer code that may include phrases
# like "the workspace" or "phase 2" in unrelated contexts).
FORBIDDEN_LINE_PATTERNS: list[tuple[str, str, str]] = [
    # (regex, rule_id, human-readable description)
    (
        r"^##\s+\d+\.\s",
        "numbered_section_heading",
        "Numbered section heading (## 1. / ## 2. / ...) — sections use plain titles",
    ),
    (
        r"^\*\*Files Changed:?\*\*",
        "files_changed_line",
        "`**Files Changed:**` line — retired; the before/after code IS the evidence",
    ),
    (
        r"^_Report dated\b",
        "footer_report_dated",
        "Footer `_Report dated…_` line — report has no footer",
    ),
    (
        r"^_Questions\?\s+Contact your Checksum CSM\._",
        "footer_csm_contact",
        "Footer `_Questions? Contact your Checksum CSM._` line — report has no footer",
    ),
    (
        r"/tmp/checksum-heals-audit-",
        "workspace_path_leak",
        "`/tmp/checksum-heals-audit-…` workspace path leaked into the customer deliverable",
    ),
]

# ----- Bug-annotation REMOVAL language -----
# Only checked within the "## Bugs Found in Your Application" section, AFTER
# verbatim blockquote lines (which carry customer-content bug descriptions) are
# stripped, so the lint never trips on legitimate customer text like
# "the modal closed after 5 seconds".
BUG_REMOVAL_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"\bclos(?:ed|ing|ure)\b",
        "bug_annotation_closed",
        "'closed' / 'closing' / 'closure' near a bug annotation — never narrate bug-removal events",
    ),
    (
        r"\bremov(?:ed|ing|al)\b",
        "bug_annotation_removed",
        "'removed' / 'removing' / 'removal' near a bug annotation — never narrate bug-removal events",
    ),
    (
        r"\breopen(?:ed|ing)?\b",
        "bug_annotation_reopened",
        "'reopened' / 'reopening' near a bug annotation — never narrate bug-removal events",
    ),
    (
        r"\bre-?enabled?\b",
        "bug_annotation_re_enabled",
        "'re-enabled' / 'reenabled' near a bug annotation — never narrate bug-removal events",
    ),
    (
        r"\bnet delta\b",
        "bug_annotation_net_delta",
        "'net delta' near a bug annotation — never narrate added-vs-removed deltas",
    ),
    (
        r"\bresolved\b",
        "bug_annotation_resolved",
        "'resolved' near a bug annotation — never imply Checksum closed out a bug",
    ),
]

BUG_SECTION_HEADING_RE = re.compile(
    r"^##\s+Bugs Found in Your Application\s*$", re.MULTILINE
)
NEXT_SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)


def line_of_offset(text: str, offset: int) -> int:
    """1-indexed line number for a character offset."""
    return text.count("\n", 0, offset) + 1


def heading_pattern(name: str) -> re.Pattern[str]:
    """Match `## Name`, `### Name`, `## 1. Name`, etc. (case-insensitive)."""
    return re.compile(
        rf"^#{{2,6}}\s+(?:\d+\.\s*)?{re.escape(name)}\s*$",
        re.MULTILINE | re.IGNORECASE,
    )


def find_structural_violations(report_text: str) -> list[dict]:
    """Lint the whole report for forbidden headings + line patterns."""
    violations: list[dict] = []

    for heading in FORBIDDEN_HEADINGS:
        for m in heading_pattern(heading).finditer(report_text):
            violations.append({
                "rule": "forbidden_heading",
                "heading": heading,
                "line": line_of_offset(report_text, m.start()),
                "matched_text": m.group(0).strip(),
                "fix": (
                    f"Remove the `{heading}` section entirely. The report has no "
                    f"such section by design."
                ),
            })

    for pat, rule_id, description in FORBIDDEN_LINE_PATTERNS:
        cre = re.compile(pat, re.MULTILINE)
        for m in cre.finditer(report_text):
            violations.append({
                "rule": rule_id,
                "line": line_of_offset(report_text, m.start()),
                "matched_text": m.group(0).strip(),
                "fix": description,
            })

    return violations


def extract_bug_section_lintable(report_text: str) -> tuple[str, int] | None:
    """Return (section body with `>` blockquote lines neutralized, body start line)
    for the Bugs Found section, or None if the section is absent.

    Blockquote lines are replaced with empty strings (NOT removed) so that line
    numbers reported to the user still align with the source file.
    """
    m = BUG_SECTION_HEADING_RE.search(report_text)
    if not m:
        return None
    body_start_offset = m.end()
    next_match = NEXT_SECTION_RE.search(report_text, body_start_offset)
    body_end_offset = next_match.start() if next_match else len(report_text)
    body_text = report_text[body_start_offset:body_end_offset]
    body_start_line = line_of_offset(report_text, body_start_offset)

    lintable_lines: list[str] = []
    for line in body_text.split("\n"):
        # Strip leading whitespace before checking for blockquote prefix
        if line.lstrip().startswith(">"):
            lintable_lines.append("")
        else:
            lintable_lines.append(line)
    return ("\n".join(lintable_lines), body_start_line)


def find_bug_context_violations(report_text: str) -> list[dict]:
    section = extract_bug_section_lintable(report_text)
    if section is None:
        return []
    body_text, body_start_line = section

    violations: list[dict] = []
    for pat, rule_id, description in BUG_REMOVAL_PATTERNS:
        cre = re.compile(pat, re.IGNORECASE)
        for m in cre.finditer(body_text):
            relative_line = body_text.count("\n", 0, m.start())
            violations.append({
                "rule": rule_id,
                "line": body_start_line + relative_line,
                "matched_text": m.group(0),
                "context": "Bugs Found in Your Application",
                "fix": description,
            })
    return violations


# ----- Audit-window cross-check (Dated: line + Audit window cell) -----
# These regexes match the two places the audit window surfaces in the report
# template. Both must reflect metadata.json's canonical audit_window_* fields
# verbatim — never observed_first_commit_date / observed_last_commit_date.

DATED_LINE_RE = re.compile(
    r"^\*\*Dated:\s*(?P<dated>[^*]+?)\s*\*\*\s*"
    r"·\s*Window:\s*last\s+(?P<days>\d+)\s+days\s+of\s+`main`\s*"
    r"\((?P<start>\d{4}-\d{2}-\d{2})\s*(?:→|->|—)\s*(?P<end>\d{4}-\d{2}-\d{2})\)",
    re.MULTILINE,
)

AUDIT_WINDOW_CELL_RE = re.compile(
    r"^\|\s*Audit window\s*\|\s*"
    r"(?P<start>\d{4}-\d{2}-\d{2})\s*(?:→|->|—)\s*"
    r"(?P<end>\d{4}-\d{2}-\d{2})\s*"
    r"\((?P<days>\d+)\s*days\)\s*\|",
    re.MULTILINE,
)


def find_audit_window_violations(
    report_text: str, workspace: Path | None
) -> list[dict]:
    """Cross-check the report's window references against metadata.json.

    Only runs when --workspace was provided AND <workspace>/metadata.json
    exists with the canonical audit_window_* fields populated. Older runs
    that predate audit_window.py will lack the fields and are skipped (the
    lint surfaces a single non-fatal info entry so the operator knows the
    cross-check was bypassed).
    """
    if workspace is None:
        return []
    metadata_path = workspace / "metadata.json"
    if not metadata_path.exists():
        return []

    try:
        metadata = json.loads(metadata_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return [{
            "rule": "audit_window_metadata_unreadable",
            "line": 0,
            "matched_text": str(metadata_path),
            "fix": (
                f"metadata.json could not be read ({e}); the audit-window "
                "cross-check was skipped. Investigate the workspace before "
                "shipping the report."
            ),
        }]

    canonical_start = metadata.get("audit_window_start_date")
    canonical_end = metadata.get("audit_window_end_date")
    canonical_days = metadata.get("audit_window_days")
    canonical_dated = metadata.get("report_date_pretty")

    missing = [
        name for name, val in [
            ("audit_window_start_date", canonical_start),
            ("audit_window_end_date", canonical_end),
            ("audit_window_days", canonical_days),
            ("report_date_pretty", canonical_dated),
        ] if val is None
    ]
    if missing:
        return [{
            "rule": "audit_window_metadata_missing_fields",
            "line": 0,
            "matched_text": ", ".join(missing),
            "fix": (
                "metadata.json is missing canonical audit-window fields "
                f"({', '.join(missing)}). The collect.py run that produced "
                "this workspace predates lib/audit_window.py — re-run collect "
                "with the current version of the skill."
            ),
        }]

    violations: list[dict] = []

    dated_match = DATED_LINE_RE.search(report_text)
    if not dated_match:
        violations.append({
            "rule": "audit_window_dated_line_missing",
            "line": 0,
            "matched_text": "",
            "fix": (
                "Could not locate the `**Dated: <Month D, YYYY>** · Window: "
                "last N days of `main` (YYYY-MM-DD → YYYY-MM-DD)` header under "
                "the H2. The synthesizer must emit this line verbatim using "
                "metadata.report_date_pretty + audit_window_* fields."
            ),
        })
    else:
        dated_line_no = line_of_offset(report_text, dated_match.start())
        if dated_match.group("dated").strip() != canonical_dated:
            violations.append({
                "rule": "audit_window_dated_mismatch",
                "line": dated_line_no,
                "matched_text": dated_match.group("dated").strip(),
                "fix": (
                    f"`Dated:` line shows `{dated_match.group('dated').strip()}` "
                    f"but `metadata.report_date_pretty` is `{canonical_dated}`. "
                    "Paste the metadata field verbatim — do not type the date by hand."
                ),
            })
        if dated_match.group("start") != canonical_start:
            violations.append({
                "rule": "audit_window_start_mismatch_dated",
                "line": dated_line_no,
                "matched_text": dated_match.group("start"),
                "fix": (
                    f"`Dated:` line window-start is `{dated_match.group('start')}` "
                    f"but `metadata.audit_window_start_date` is `{canonical_start}`. "
                    "If you used `observed_first_commit_date` instead, that under-reports "
                    "the window — use the canonical field."
                ),
            })
        if dated_match.group("end") != canonical_end:
            violations.append({
                "rule": "audit_window_end_mismatch_dated",
                "line": dated_line_no,
                "matched_text": dated_match.group("end"),
                "fix": (
                    f"`Dated:` line window-end is `{dated_match.group('end')}` "
                    f"but `metadata.audit_window_end_date` is `{canonical_end}`. "
                    "If you used `observed_last_commit_date` instead, that under-reports "
                    "the window — use the canonical field."
                ),
            })
        if int(dated_match.group("days")) != int(canonical_days):
            violations.append({
                "rule": "audit_window_days_mismatch_dated",
                "line": dated_line_no,
                "matched_text": dated_match.group("days"),
                "fix": (
                    f"`Dated:` line day-count is `{dated_match.group('days')}` "
                    f"but `metadata.audit_window_days` is `{canonical_days}`."
                ),
            })

    cell_match = AUDIT_WINDOW_CELL_RE.search(report_text)
    if not cell_match:
        violations.append({
            "rule": "audit_window_cell_missing",
            "line": 0,
            "matched_text": "",
            "fix": (
                "Could not locate the `| Audit window | YYYY-MM-DD → YYYY-MM-DD "
                "(N days) |` row in the metadata table. The synthesizer must "
                "emit this row verbatim using metadata.audit_window_* fields."
            ),
        })
    else:
        cell_line_no = line_of_offset(report_text, cell_match.start())
        if cell_match.group("start") != canonical_start:
            violations.append({
                "rule": "audit_window_start_mismatch_cell",
                "line": cell_line_no,
                "matched_text": cell_match.group("start"),
                "fix": (
                    f"`Audit window` cell start is `{cell_match.group('start')}` "
                    f"but `metadata.audit_window_start_date` is `{canonical_start}`. "
                    "If you used `observed_first_commit_date` instead, that under-reports "
                    "the window — use the canonical field."
                ),
            })
        if cell_match.group("end") != canonical_end:
            violations.append({
                "rule": "audit_window_end_mismatch_cell",
                "line": cell_line_no,
                "matched_text": cell_match.group("end"),
                "fix": (
                    f"`Audit window` cell end is `{cell_match.group('end')}` "
                    f"but `metadata.audit_window_end_date` is `{canonical_end}`. "
                    "If you used `observed_last_commit_date` instead, that under-reports "
                    "the window — use the canonical field."
                ),
            })
        if int(cell_match.group("days")) != int(canonical_days):
            violations.append({
                "rule": "audit_window_days_mismatch_cell",
                "line": cell_line_no,
                "matched_text": cell_match.group("days"),
                "fix": (
                    f"`Audit window` cell day-count is `{cell_match.group('days')}` "
                    f"but `metadata.audit_window_days` is `{canonical_days}`."
                ),
            })

    return violations


def find_violations(report_text: str, workspace: Path | None = None) -> list[dict]:
    return (
        find_structural_violations(report_text)
        + find_bug_context_violations(report_text)
        + find_audit_window_violations(report_text, workspace)
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Phase 2.5 lint pass. Scans the synthesized report for forbidden "
            "headings, retired formatting, footer leakage, and bug-annotation "
            "removal language. Exits 1 on any violation so the parent agent "
            "can re-dispatch the synthesizer with structured feedback."
        )
    )
    ap.add_argument("--report", required=True, type=Path, help="Path to the report markdown")
    ap.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Workspace dir to write lint.json into (optional but recommended)",
    )
    args = ap.parse_args()

    if not args.report.exists():
        sys.exit(f"FATAL: report not found: {args.report}")

    report_text = args.report.read_text(errors="replace")
    violations = find_violations(report_text, workspace=args.workspace)

    output = {
        "report": str(args.report),
        "violations_count": len(violations),
        "violations": violations,
        "status": "clean" if not violations else "dirty",
    }

    if args.workspace:
        args.workspace.mkdir(parents=True, exist_ok=True)
        lint_path = args.workspace / "lint.json"
        lint_path.write_text(json.dumps(output, indent=2))

    print(json.dumps(output, indent=2))
    sys.exit(0 if not violations else 1)


if __name__ == "__main__":
    # The skill is decommissioned; the code above is kept for reference only.
    sys.exit("DECOMMISSIONED: 30-day-healing-analysis was previously for internal use at Checksum "
             "and is now a non-functional skeleton kept on GitHub for "
             "demonstration purposes only. It no longer runs.")
