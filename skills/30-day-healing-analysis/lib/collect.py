#!/usr/bin/env python3
"""
collect.py — Phase 0 data collection for the 30-day-healing-analysis skill.

Reads the last N days of `main` branch git history in a customer test repo,
keeps only commits authored by one of the four allowed Checksum identities,
filters file modifications to `.ts` / `.js` test-suite files (specs, page
objects, helpers, utilities, fixtures), excludes newly-added files, dumps
each diff to disk, and emits structured JSON for downstream AI classification.

Lifecycle:
  - On every run, the script deletes any prior workspace at the target path
    (clean slate) before writing new outputs. Crash-resistant.
  - Workspaces live under /tmp/checksum-heals-audit-<slug>/ by default.
  - Pass --cleanup to delete a workspace WITHOUT collecting anything new.
    Used by the Phase 3 post-flight step to leave the machine clean once
    the customer-facing report has been written to ~/Desktop/.
  - Pass --cleanup-all to nuke EVERY /tmp/checksum-heals-audit-* workspace
    plus the legacy /tmp/checksum_heals_collect.py script copy. Useful when
    older runs have accumulated cruft.

Usage:
  python3 collect.py \\
      --repo /abs/path/to/customer/repo \\
      --customer "Acme Corp" \\
      --slug acme-corp \\
      [--days 30] \\
      [--end-date YYYY-MM-DD] \\
      [--workspace /tmp/checksum-heals-audit-acme-corp]

  # The audit window is computed deterministically by lib/audit_window.py
  # as `today - timedelta(days=N)` through `today`, inclusive. Cross-month
  # and cross-year boundaries are handled natively.

Freshness modes (mutually exclusive):
  --refresh    Phase-0 default. Before scraping, sync the clone to the latest
               origin/main: ensure we're on `main` (checkout if not), run the
               optional --auth-cmd (e.g. to refresh the GitHub token so a
               private-submodule pull works), then `git pull --ff-only`. Each
               step is best-effort and logged; it never edits code, commits,
               branches, or pushes. If customer repos are git submodules, the
               submodule must be checked out for the clone to exist.
  --read-only  Touch nothing: skip checkout/auth/pull and read whatever local
               `main` points at. Use offline / when no GitHub auth is present.

  # Clean up this run's workspace after the report is shipped:
  python3 collect.py --slug acme-corp --cleanup

  # Nuke all heals-audit workspaces (any customer) plus the legacy script copy:
  python3 collect.py --cleanup-all
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

# Sibling module — both files live under ~/.claude/skills/30-day-healing-analysis/lib/
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_window import compute_audit_window  # noqa: E402

ALLOWED_AUTHORS = [
    "checksum-ai",
    r"checksum-ai-test-suite-integration\[bot\]",
    "checksum-lint",
    "Checksum AI Agent",
]
ALLOWED_AUTHOR_NAMES_LOWER = {
    "checksum-ai",
    "checksum-ai-test-suite-integration[bot]",
    "checksum-lint",
    "checksum ai agent",
}

INCLUDE_EXTS = (".ts", ".js")
EXCLUDE_PATH_FRAGMENTS = (
    "node_modules/", "dist/", "build/", ".next/", ".turbo/",
    "coverage/", ".git/", ".github/",
)
EXCLUDE_FILENAMES = {
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}
EXCLUDE_SUFFIXES = (
    ".d.ts", ".config.ts", ".config.js", ".config.mjs", ".config.cjs",
)

WORKSPACE_PREFIX = "/tmp/checksum-heals-audit-"
LEGACY_SCRIPT_PATHS = (
    "/tmp/checksum_heals_collect.py",
)


def sh(cmd, cwd=None, check=True):
    return subprocess.run(
        cmd, cwd=cwd, check=check, capture_output=True, text=True
    ).stdout


# The auth-refresh command may be a SHELL ALIAS (defined in the user's ~/.zshrc),
# not a binary on PATH, so subprocess.run([...]) would raise FileNotFoundError.
# Aliases only exist in an *interactive* shell, so the command is run through the
# user's login shell with -i to load the rc file. Best-effort: returns (rc, output)
# and never raises — a missing alias / no network must not abort the audit.
# Empty by default, which skips the auth step entirely.
DEFAULT_AUTH_CMD = ""


def run_login_shell(cmd_str: str, cwd, timeout: int = 180) -> tuple[int, str]:
    shell = os.environ.get("SHELL") or "/bin/zsh"
    try:
        proc = subprocess.run(
            [shell, "-ic", cmd_str],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return 127, f"shell not found: {shell}"
    except subprocess.TimeoutExpired:
        return 124, f"`{cmd_str}` timed out after {timeout}s"


def current_branch(repo: Path) -> str:
    return sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, check=False).strip()


def refresh_repo(repo: Path, log: list, auth_cmd: str = DEFAULT_AUTH_CMD) -> str:
    """Sync the local clone to the latest origin/main BEFORE scraping history.

    Order (per skill spec): ensure we're on `main` (checkout if not) -> run the
    optional auth-refresh command (e.g. to refresh the GitHub authorization so
    a private-submodule pull can succeed) -> `git pull --ff-only` to populate
    the latest commits. Every step is best-effort and logged: if checkout fails
    (e.g. a dirty working tree), or auth/pull can't reach the network, the audit
    degrades to reading whatever local `main` already points at rather than
    aborting. This never edits code, commits, branches, or pushes.
    """
    log.append("== Refresh (sync local main to origin before scrape) ==")

    # 1. Make sure we're on main; checkout if not.
    branch = current_branch(repo)
    if branch == "main":
        log.append("  on main: OK")
    else:
        log.append(f"  current branch is '{branch}' — checking out main")
        try:
            sh(["git", "checkout", "main"], cwd=repo)
            log.append("  checked out main: OK")
        except subprocess.CalledProcessError as e:
            log.append(
                f"  WARNING: `git checkout main` failed ({(e.stderr or '').strip()}); "
                f"skipping auth refresh + pull and reading local `main` ref as-is"
            )
            sha = sh(["git", "rev-parse", "--short", "main"], cwd=repo, check=False).strip()
            if not sha:
                sys.exit("FATAL: no local `main` ref and could not check it out.")
            log.append(f"  main @ {sha} (not synced)")
            return sha

    # 2. Refresh GitHub authorization via --auth-cmd (shell alias -> login shell).
    if not auth_cmd:
        log.append("  auth refresh: skipped (no --auth-cmd set)")
    else:
        rc, out = run_login_shell(auth_cmd, cwd=repo)
        tail = "\n".join(l for l in out.splitlines() if l.strip())[-500:]
        if rc == 0:
            log.append(f"  auth refresh (`{auth_cmd}`): OK")
        else:
            log.append(
                f"  WARNING: auth refresh (`{auth_cmd}`) exited {rc} — continuing; "
                f"pull may fail if the token is stale. tail: {tail!r}"
            )

    # 3. Pull the latest main (fast-forward only — never create a merge commit).
    pull = subprocess.run(
        ["git", "pull", "--ff-only", "origin", "main"],
        cwd=repo, capture_output=True, text=True,
    )
    if pull.returncode == 0:
        log.append(f"  git pull --ff-only origin main: OK ({pull.stdout.strip().splitlines()[-1] if pull.stdout.strip() else 'up to date'})")
    else:
        log.append(
            f"  WARNING: `git pull --ff-only origin main` failed — reading local "
            f"`main` as-is. stderr: {(pull.stderr or '').strip()[-300:]!r}"
        )

    sha = sh(["git", "rev-parse", "--short", "HEAD"], cwd=repo, check=False).strip()
    log.append(f"  main @ {sha}")
    return sha


def is_in_scope(path: str) -> bool:
    p = path.lower()
    if any(frag in p for frag in EXCLUDE_PATH_FRAGMENTS):
        return False
    if os.path.basename(path) in EXCLUDE_FILENAMES:
        return False
    if any(p.endswith(suf) for suf in EXCLUDE_SUFFIXES):
        return False
    if not p.endswith(INCLUDE_EXTS):
        return False
    return True


def safe_filename(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def preflight(
    repo: Path,
    log: list,
    read_only: bool = False,
    refresh: bool = False,
    auth_cmd: str = DEFAULT_AUTH_CMD,
) -> str:
    log.append("== Pre-flight ==")
    try:
        sh(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo)
    except subprocess.CalledProcessError:
        sys.exit(f"FATAL: {repo} is not a git repo")
    log.append("  git repo: OK")

    pkg = repo / "package.json"
    if not pkg.exists():
        sys.exit("FATAL: no package.json found at repo root")
    # Accept any Playwright or Checksum-wrapper signal — customer repos often use
    # `checksumai` (the Checksum SDK that pulls Playwright transitively) instead
    # of depending on `@playwright/test` directly.
    pkg_text = pkg.read_text()
    pw_signals = [
        "@playwright/test",
        "playwright",
        "checksumai",
        "eslint-plugin-playwright",
    ]
    matched = [s for s in pw_signals if s in pkg_text]
    if not matched:
        sys.exit(
            "FATAL: no Playwright/Checksum dependency found in package.json — "
            "this skill is Playwright-only"
        )
    log.append(f"  Playwright dep: OK (matched: {matched})")

    if read_only:
        # Pure-read mode: never mutate the working tree. We do NOT fetch,
        # checkout, or pull — we read whatever `main` already points at locally.
        # Every later git call (`git log main`, `git show <sha>`, `git diff-tree
        # <sha>`) reads by ref/SHA and needs no checkout, so the audit is fully
        # non-destructive regardless of which branch is currently checked out.
        sha = sh(["git", "rev-parse", "--short", "main"], cwd=repo, check=False).strip()
        if not sha:
            sys.exit("FATAL: no local `main` ref. Pass a repo with a local main "
                     "branch, or drop --read-only to allow a fetch/checkout.")
        log.append(f"  main @ {sha} (read-only: no fetch/checkout/pull)")
        return sha

    if refresh:
        # Sync mode: ensure on main -> optional --auth-cmd (refresh GitHub auth) ->
        # git pull --ff-only, so the scrape sees the latest healing commits.
        return refresh_repo(repo, log, auth_cmd=auth_cmd)

    # Network ops are best-effort — if auth lapses or the network is unreachable,
    # fall back to the already-local main. The audit reads local git history.
    sh(["git", "fetch", "origin", "main"], cwd=repo, check=False)
    sh(["git", "checkout", "main"], cwd=repo)
    sh(["git", "pull", "--ff-only", "origin", "main"], cwd=repo, check=False)
    sha = sh(["git", "rev-parse", "--short", "HEAD"], cwd=repo).strip()
    log.append(f"  main @ {sha}")
    return sha


def author_flags() -> list[str]:
    flags = []
    for a in ALLOWED_AUTHORS:
        flags += ["--author", a]
    return flags


def collect_commits(repo: Path, since: str, until: str | None = None) -> list[dict]:
    cmd = [
        "git", "log",
        "--regexp-ignore-case",
        *author_flags(),
        f"--since={since}",
    ]
    if until is not None:
        # Git treats --until=YYYY-MM-DD as 00:00:00 on that day. Pass an end-of-day
        # boundary so commits made later on the audit-window's last day are included.
        cmd.append(f"--until={until} 23:59:59")
    cmd += [
        "--format=%H%x09%aI%x09%an%x09%s",
        "main",
    ]
    out = sh(cmd, cwd=repo)
    commits = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 3)
        if len(parts) != 4:
            continue
        sha, iso_date, author, subject = parts
        commits.append({
            "sha": sha,
            "date": iso_date,
            "author": author,
            "subject": subject,
        })
    return commits


def files_for_commit(repo: Path, sha: str) -> list[tuple[str, str]]:
    # NOTE: `git show --no-patch --name-status` errors on newer git with
    # "options '--name-only', '--name-status', '--check', and '-s' cannot be
    # used together". `git diff-tree` is the portable equivalent.
    out = sh([
        "git", "diff-tree", "-r", "--no-commit-id", "--name-status", sha
    ], cwd=repo)
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            rows.append((status, parts[2]))
        elif len(parts) >= 2:
            rows.append((status, parts[1]))
    return rows


def diff_for(repo: Path, sha: str, filepath: str) -> str:
    return sh(["git", "show", sha, "--", filepath], cwd=repo, check=False)


def is_spec_file(path: str) -> bool:
    """A Playwright spec file: basename ends in .spec.ts / .spec.js (which also
    matches .checksum.spec.ts / .checksum.spec.js), not in an excluded path."""
    p = path.lower()
    if any(frag in p for frag in EXCLUDE_PATH_FRAGMENTS):
        return False
    if not (p.endswith(".spec.ts") or p.endswith(".spec.js")):
        return False
    return True


def is_checksum_spec_file(path: str) -> bool:
    p = path.lower()
    return p.endswith(".checksum.spec.ts") or p.endswith(".checksum.spec.js")


def count_test_files_at_head(repo: Path) -> dict:
    """Count all Playwright spec files tracked at HEAD on `main`.

    Returns counts broken down by Checksum-generated (`.checksum.spec.*`) vs
    other Playwright specs (`.spec.*` that are not Checksum-generated). Used
    in the customer-facing report's "scope of the suite" headline so the
    customer sees the size of the suite Checksum is maintaining.
    """
    out = sh(["git", "ls-tree", "-r", "HEAD", "--name-only"], cwd=repo)
    all_specs: list[str] = []
    checksum_specs: list[str] = []
    other_specs: list[str] = []
    for line in out.splitlines():
        path = line.strip()
        if not path:
            continue
        if not is_spec_file(path):
            continue
        all_specs.append(path)
        if is_checksum_spec_file(path):
            checksum_specs.append(path)
        else:
            other_specs.append(path)
    return {
        "total_test_files_in_suite": len(all_specs),
        "total_checksum_spec_files": len(checksum_specs),
        "total_other_spec_files": len(other_specs),
    }


def cleanup_workspace(ws: Path) -> bool:
    if ws.exists():
        shutil.rmtree(ws, ignore_errors=True)
        return True
    return False


def cleanup_all() -> dict:
    removed_workspaces = []
    for d in glob.glob(WORKSPACE_PREFIX + "*"):
        p = Path(d)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            removed_workspaces.append(str(p))
    removed_legacy = []
    for legacy in LEGACY_SCRIPT_PATHS:
        p = Path(legacy)
        if p.exists():
            try:
                p.unlink()
                removed_legacy.append(str(p))
            except OSError:
                pass
    return {
        "removed_workspaces": removed_workspaces,
        "removed_legacy_scripts": removed_legacy,
    }


def run_collection(args) -> None:
    repo = args.repo.resolve()
    ws = args.workspace or Path(f"{WORKSPACE_PREFIX}{args.slug}")

    # Clean slate: prior workspace for this slug is always overwritten.
    cleanup_workspace(ws)
    ws.mkdir(parents=True)
    diffs_dir = ws / "diffs"
    diffs_dir.mkdir()

    log: list[str] = []
    head_sha = preflight(
        repo, log,
        read_only=getattr(args, "read_only", False),
        refresh=getattr(args, "refresh", False),
        auth_cmd=getattr(args, "auth_cmd", DEFAULT_AUTH_CMD),
    )

    # Single source of truth for the audit window: both the git --since query
    # and the customer-facing "Audit window" cell read from this dict.
    window = compute_audit_window(days=args.days, end_date=args.end_date)
    log.append("\n== Audit window ==")
    log.append(f"  {window['audit_window_display']}")
    log.append(f"  git --since={window['since_git_arg']}")
    if args.end_date is not None:
        log.append(f"  git --until={window['audit_window_end_date']} 23:59:59 (--end-date override)")

    log.append("\n== Counting test files in the suite at HEAD ==")
    suite_counts = count_test_files_at_head(repo)
    log.append(
        f"  Total spec files: {suite_counts['total_test_files_in_suite']} "
        f"(Checksum-generated: {suite_counts['total_checksum_spec_files']}, "
        f"other: {suite_counts['total_other_spec_files']})"
    )

    # Use the computed window's since string for the git query. If --end-date
    # was passed explicitly, also cap the upper bound with --until so the
    # audit is reproducible. When --end-date is omitted, leave the upper bound
    # open so commits made between window computation and git query are still
    # captured (the report still displays the canonical end date).
    git_since = window["since_git_arg"]
    git_until = window["audit_window_end_date"] if args.end_date is not None else None

    log.append(f"\n== Collecting Checksum-authored commits (--since={git_since}) ==")
    commits = collect_commits(repo, git_since, until=git_until)
    log.append(f"  {len(commits)} commits matched the author allowlist")

    seen_authors = sorted({c["author"] for c in commits})
    leaks = [a for a in seen_authors if a.strip().lower() not in ALLOWED_AUTHOR_NAMES_LOWER]
    if leaks:
        log.append(f"  WARNING: filter leak — non-Checksum authors slipped through: {leaks}")
    log.append(f"  Active Checksum identities: {seen_authors}")

    pairs: list[dict] = []
    added: set[str] = set()
    modified: set[str] = set()
    renamed: set[str] = set()
    unusual: list[dict] = []

    for c in commits:
        for status, fp in files_for_commit(repo, c["sha"]):
            if not is_in_scope(fp):
                if not any(fp.lower().endswith(ext) for ext in (".ts", ".js")):
                    unusual.append({"commit": c["sha"][:12], "file": fp, "status": status})
                continue
            if status.startswith("A"):
                added.add(fp)
            elif status.startswith("R"):
                renamed.add(fp)
            elif status.startswith("M"):
                modified.add(fp)
                pairs.append({
                    "commit": c["sha"],
                    "short_sha": c["sha"][:7],
                    "date": c["date"],
                    "author": c["author"],
                    "subject": c["subject"],
                    "file": fp,
                })

    scope = sorted(modified - added)
    pairs = [p for p in pairs if p["file"] in set(scope)]

    log.append(f"\n== Building scope ==")
    log.append(f"  Files ADDED by Checksum (excluded): {len(added)}")
    log.append(f"  Files MODIFIED by Checksum: {len(modified)}")
    log.append(f"  Files RENAMED by Checksum: {len(renamed)}")
    log.append(f"  Final scope (modified - added): {len(scope)}")
    log.append(f"  (commit, file) pairs to classify: {len(pairs)}")
    log.append(f"  Unusual non-.ts/.js files touched (logged, not classified): {len(unusual)}")

    log.append(f"\n== Dumping {len(pairs)} diffs to {diffs_dir} ==")
    for p in pairs:
        safe = safe_filename(p["file"].replace("/", "__"))
        diff_path = diffs_dir / f"{p['short_sha']}__{safe}.diff"
        diff_path.write_text(diff_for(repo, p["commit"], p["file"]))
        p["diff_path"] = str(diff_path)

    hotspot_counter: Counter[str] = Counter(p["file"] for p in pairs)
    identity_counter: Counter[str] = Counter(p["author"] for p in pairs)
    identity_files: dict[str, set[str]] = defaultdict(set)
    for p in pairs:
        identity_files[p["author"]].add(p["file"])

    weekly: dict[str, Counter[str]] = defaultdict(Counter)
    for p in pairs:
        try:
            d = datetime.fromisoformat(p["date"].replace("Z", "+00:00"))
        except ValueError:
            continue
        wk = d.strftime("%G-W%V")
        weekly[wk][p["author"]] += 1

    subjects = sorted(
        {(p["short_sha"], p["author"], p["subject"]) for p in pairs},
        key=lambda t: t[0],
    )

    noise_candidates: list[dict] = []
    for p in pairs:
        diff_text = Path(p["diff_path"]).read_text(errors="replace")
        stripped = "\n".join(
            line for line in diff_text.splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        )
        non_ws = re.sub(r"\s", "", stripped)
        if len(stripped) > 0 and len(non_ws) / max(len(stripped), 1) < 0.05:
            noise_candidates.append({
                "commit": p["short_sha"], "file": p["file"], "reason": "whitespace-only"
            })

    baseline_cmd = ["git", "log", f"--since={git_since}"]
    if git_until is not None:
        baseline_cmd.append(f"--until={git_until} 23:59:59")
    baseline_cmd += ["--oneline", "main"]
    baseline = sh(baseline_cmd, cwd=repo, check=False).strip().splitlines()

    # Observed activity range (forensic only; NOT the customer-facing window).
    # Kept in metadata so SE can see "Checksum was quiet for the first 8 days
    # of the window" — but the report itself uses the canonical audit_window_*
    # fields, which always span the full --days N regardless of quiet stretches.
    if commits:
        dates = sorted(c["date"] for c in commits)
        observed_first, observed_last = dates[0][:10], dates[-1][:10]
    else:
        observed_first = observed_last = None

    metadata = {
        "customer": args.customer,
        "slug": args.slug,
        "repo": str(repo),
        "branch": "main",
        "head_sha": head_sha,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "allowed_authors": ALLOWED_AUTHORS,
        "active_identities": seen_authors,
        "leaks_detected": leaks,
        "total_checksum_commits": len(commits),
        "total_main_commits_all_authors": len(baseline),
        "scope_files": len(scope),
        "scope_pairs": len(pairs),
        "added_excluded": len(added),
        "renamed_excluded": len(renamed),
        # Canonical audit-window fields — derived deterministically from
        # today's date and the --days input. These are what the customer
        # report's "Audit window" cell + "Dated:" line MUST use. The
        # synthesizer reads them out of metadata.json verbatim.
        "audit_window_start_date": window["audit_window_start_date"],
        "audit_window_end_date": window["audit_window_end_date"],
        "audit_window_days": window["audit_window_days"],
        "audit_window_display": window["audit_window_display"],
        "report_date_iso": window["report_date_iso"],
        "report_date_pretty": window["report_date_pretty"],
        "audit_window_computed_at_utc": window["computed_at_utc"],
        # Forensic-only "observed activity" range. NOT for the customer report.
        "observed_first_commit_date": observed_first,
        "observed_last_commit_date": observed_last,
        "noise_candidates_count": len(noise_candidates),
        "unusual_files_count": len(unusual),
        "total_test_files_in_suite": suite_counts["total_test_files_in_suite"],
        "total_checksum_spec_files": suite_counts["total_checksum_spec_files"],
        "total_other_spec_files": suite_counts["total_other_spec_files"],
    }

    aggregates = {
        "hotspots": hotspot_counter.most_common(30),
        "by_identity": dict(identity_counter),
        "files_per_identity": {k: sorted(v) for k, v in identity_files.items()},
        "weekly_activity": {k: dict(v) for k, v in sorted(weekly.items())},
        "commit_subjects": subjects,
        "added_files": sorted(added),
        "renamed_files": sorted(renamed),
        "noise_candidates": noise_candidates,
        "unusual_files": unusual,
    }

    (ws / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (ws / "scope.json").write_text(json.dumps(sorted(scope), indent=2))
    (ws / "aggregates.json").write_text(json.dumps(aggregates, indent=2))
    with (ws / "commits.jsonl").open("w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")
    (ws / "preflight.log").write_text("\n".join(log))

    print(json.dumps({
        "mode": "collect",
        "workspace": str(ws),
        "files": {
            "metadata": str(ws / "metadata.json"),
            "scope": str(ws / "scope.json"),
            "aggregates": str(ws / "aggregates.json"),
            "commits": str(ws / "commits.jsonl"),
            "preflight_log": str(ws / "preflight.log"),
            "diffs_dir": str(diffs_dir),
        },
        "summary": {
            "checksum_commits": len(commits),
            "all_authors_commits": len(baseline),
            "scope_files": len(scope),
            "scope_pairs": len(pairs),
            "added_excluded": len(added),
            "renamed_excluded": len(renamed),
            "active_identities": seen_authors,
            "noise_candidates": len(noise_candidates),
            "unusual_files": len(unusual),
            "total_test_files_in_suite": suite_counts["total_test_files_in_suite"],
            "total_checksum_spec_files": suite_counts["total_checksum_spec_files"],
            "total_other_spec_files": suite_counts["total_other_spec_files"],
            "audit_window": window["audit_window_display"],
            "audit_window_start_date": window["audit_window_start_date"],
            "audit_window_end_date": window["audit_window_end_date"],
            "observed_activity_range": [observed_first, observed_last],
        },
    }, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, help="Absolute path to the customer test repo")
    ap.add_argument("--customer", help="Customer display name, e.g. 'Acme Corp'")
    ap.add_argument("--slug", help="Customer slug for the workspace dir, e.g. 'acme-corp'")
    ap.add_argument(
        "--days", type=int, default=30,
        help=(
            "Audit-window length in days (default: 30). Window = today minus N "
            "days through today, inclusive. Cross-month/year boundaries are "
            "handled by audit_window.compute_audit_window."
        ),
    )
    ap.add_argument(
        "--end-date", type=date.fromisoformat, default=None,
        help=(
            "Optional override for the inclusive end of the audit window "
            "(YYYY-MM-DD). Defaults to today's local date. Pass this to "
            "reproduce a prior audit. When set, git --until is also capped "
            "for full determinism."
        ),
    )
    ap.add_argument("--workspace", type=Path, default=None)
    ap.add_argument(
        "--read-only", action="store_true",
        help=(
            "Never touch the working tree or network: skip checkout/auth/pull and "
            "read whatever `main` points at locally. Use offline or when no GitHub "
            "auth is available; the scrape may then miss commits landed since the "
            "last manual pull."
        ),
    )
    ap.add_argument(
        "--refresh", action="store_true",
        help=(
            "Sync the clone before scraping: ensure we're on `main` (checkout if "
            "not), run --auth-cmd if set (refreshes GitHub auth), then "
            "`git pull --ff-only origin main`. Each step is best-effort "
            "and logged; never edits code, commits, branches, or pushes. This is "
            "the skill's Phase-0 default so the audit sees the latest healing "
            "commits. Mutually exclusive with --read-only."
        ),
    )
    ap.add_argument(
        "--auth-cmd", default=DEFAULT_AUTH_CMD,
        help=(
            "Command run (via the interactive login shell, so shell aliases "
            "resolve) during --refresh to refresh GitHub authorization before the "
            "pull. Default: empty (skip the auth step)."
        ),
    )
    ap.add_argument(
        "--cleanup", action="store_true",
        help="Delete the workspace for --slug and exit (no collection).",
    )
    ap.add_argument(
        "--cleanup-all", action="store_true",
        help=(
            "Delete every /tmp/checksum-heals-audit-* workspace plus the legacy "
            "/tmp/checksum_heals_collect.py script copy, then exit."
        ),
    )
    args = ap.parse_args()

    if args.cleanup_all:
        result = cleanup_all()
        print(json.dumps({"mode": "cleanup-all", **result}, indent=2))
        return

    if args.cleanup:
        if not args.slug and not args.workspace:
            sys.exit("FATAL: --cleanup requires --slug or --workspace")
        ws = args.workspace or Path(f"{WORKSPACE_PREFIX}{args.slug}")
        removed = cleanup_workspace(ws)
        print(json.dumps({
            "mode": "cleanup",
            "workspace": str(ws),
            "removed": removed,
        }, indent=2))
        return

    if args.read_only and args.refresh:
        sys.exit("FATAL: --read-only and --refresh are mutually exclusive.")

    missing = [f for f in ("repo", "customer", "slug") if getattr(args, f) is None]
    if missing:
        sys.exit(f"FATAL: missing required args: {missing}. Pass --repo, --customer, --slug.")

    run_collection(args)


if __name__ == "__main__":
    # The skill is decommissioned; the code above is kept for reference only.
    sys.exit("DECOMMISSIONED: 30-day-healing-analysis was previously for internal use at Checksum "
             "and is now a non-functional skeleton kept on GitHub for "
             "demonstration purposes only. It no longer runs.")
