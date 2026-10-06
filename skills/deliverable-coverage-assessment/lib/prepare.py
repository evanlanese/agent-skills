#!/usr/bin/env python3
"""
prepare.py — deterministic plumbing for the deliverable-coverage-assessment skill.

This script does NOT make any judgment about whether a deliverable was achieved.
It only does the boring, repeatable parts so the AI can spend its effort on the
evidence-grounded evaluation:

  1. resolve <slug>      -> find the customer's local Playwright/Checksum test repo
  2. sync <repo>         -> (best-effort) sync local `main` to origin before reading
  3. manifest <repo>     -> enumerate the test suite (stories + specs), grouped by area

Repo resolution and the sync recipe are deliberately shared with the sibling
`30-day-healing-analysis` skill: this script imports that skill's `config.py`
(`resolve_repo`) so a customer that is already configured/pinned there resolves
here too, and a single `customer_repos_base` config serves both.
Nothing here ever edits, commits, branches, or pushes — it is strictly read-only
apart from the best-effort fast-forward `git pull` in `sync`.

Usage:
    prepare.py resolve  <slug>
    prepare.py sync     <repo-path>
    prepare.py manifest <repo-path>

Output is JSON on stdout (except `resolve`, which prints a bare path or
`RESOLVE_FAILED: <reason>` on stderr with exit 3), so the AI can parse it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))

# Reuse the proven repo-resolution from the 30-day-healing-analysis skill so both
# skills share one config.local.json (customer_repos_base + per-customer pins).
SIBLING_CONFIG = HOME / ".claude" / "skills" / "30-day-healing-analysis" / "lib"

# Directories that never contain authored test source.
EXCLUDE_DIRS = {
    "node_modules", "test-results", "playwright-report", "dist", "build",
    ".next", ".turbo", "coverage", ".git", ".chk", "test-data",
}

STORY_SUFFIX = ".checksum.md"
SPEC_SUFFIXES = (".checksum.spec.ts", ".checksum.spec.js", ".spec.ts", ".spec.js")


# --------------------------------------------------------------------------- #
# resolve
# --------------------------------------------------------------------------- #
def resolve(slug: str) -> int:
    if str(SIBLING_CONFIG) not in sys.path:
        sys.path.insert(0, str(SIBLING_CONFIG))
    try:
        import config as sibling_config  # type: ignore
    except Exception as e:  # pragma: no cover - only if sibling skill is absent
        print(
            f"RESOLVE_FAILED: could not import the shared config helper at "
            f"{SIBLING_CONFIG}/config.py ({e}). Either install/keep the "
            f"30-day-healing-analysis skill, or pass an explicit repo path to "
            f"`sync` / `manifest` directly.",
            file=sys.stderr,
        )
        return 3
    path, reason = sibling_config.resolve_repo(slug)
    if path:
        print(path)
        return 0
    print(f"RESOLVE_FAILED: {reason}", file=sys.stderr)
    return 3


# --------------------------------------------------------------------------- #
# sync (best-effort; mirrors 30-day-healing-analysis refresh_repo)
# --------------------------------------------------------------------------- #
def _sh(cmd, cwd, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


# Optional command that refreshes GitHub auth before the pull (may be a shell
# alias). Empty by default, which skips the auth step.
AUTH_REFRESH_CMD = os.environ.get("AUTH_REFRESH_CMD", "")


def _run_login_shell(cmd_str: str, cwd, timeout: int = 180):
    # The auth command may be a shell alias, not a binary on PATH — run it via an
    # interactive login shell so the rc file (where the alias lives) is loaded.
    shell = os.environ.get("SHELL") or "/bin/zsh"
    try:
        proc = subprocess.run(
            [shell, "-ic", cmd_str], cwd=cwd,
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return 127, f"shell not found: {shell}"
    except subprocess.TimeoutExpired:
        return 124, f"`{cmd_str}` timed out after {timeout}s"


def sync(repo: str) -> int:
    """Ensure on main -> optional $AUTH_REFRESH_CMD -> git pull --ff-only.

    Every step is best-effort and logged. If the working tree is dirty, offline,
    or auth is unavailable, we degrade to reading whatever local `main` points at
    rather than aborting. Read-only apart from the fast-forward pull.
    """
    repo_p = Path(repo).expanduser()
    log: list[str] = []
    if not (repo_p / ".git").exists():
        print(json.dumps({"ok": False, "error": f"not a git repo: {repo}", "log": log}))
        return 1

    branch = _sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_p, check=False).stdout.strip()
    if branch == "main":
        log.append("on main: OK")
    else:
        log.append(f"current branch is '{branch}' — checking out main")
        try:
            _sh(["git", "checkout", "main"], repo_p)
            log.append("checked out main: OK")
        except subprocess.CalledProcessError as e:
            log.append(f"WARNING: checkout main failed ({(e.stderr or '').strip()}); reading local main as-is")
            sha = _sh(["git", "rev-parse", "--short", "main"], repo_p, check=False).stdout.strip()
            print(json.dumps({"ok": bool(sha), "synced": False, "sha": sha, "log": log}))
            return 0 if sha else 1

    if not AUTH_REFRESH_CMD:
        log.append("auth refresh: skipped (AUTH_REFRESH_CMD not set)")
    else:
        rc, out = _run_login_shell(AUTH_REFRESH_CMD, cwd=repo_p)
        tail = "\n".join(l for l in out.splitlines() if l.strip())[-400:]
        log.append(f"auth refresh (`{AUTH_REFRESH_CMD}`): OK" if rc == 0
                   else f"WARNING: `{AUTH_REFRESH_CMD}` exited {rc} — continuing; pull may fail. tail: {tail!r}")

    pull = subprocess.run(["git", "pull", "--ff-only", "origin", "main"],
                          cwd=repo_p, capture_output=True, text=True)
    if pull.returncode == 0:
        last = pull.stdout.strip().splitlines()[-1] if pull.stdout.strip() else "up to date"
        log.append(f"git pull --ff-only origin main: OK ({last})")
        synced = True
    else:
        log.append(f"WARNING: pull failed — reading local main as-is. stderr: {(pull.stderr or '').strip()[-300:]!r}")
        synced = False

    sha = _sh(["git", "rev-parse", "--short", "HEAD"], repo_p, check=False).stdout.strip()
    log.append(f"main @ {sha}")
    print(json.dumps({"ok": True, "synced": synced, "sha": sha, "log": log}))
    return 0


# --------------------------------------------------------------------------- #
# manifest
# --------------------------------------------------------------------------- #
def _frontmatter_title(md_path: Path) -> str:
    try:
        text = md_path.read_text(errors="replace")
    except OSError:
        return ""
    m = re.search(r'^title:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    return m.group(1).strip() if m else md_path.stem.replace(STORY_SUFFIX, "")


def _frontmatter_field(md_path: Path, field: str) -> str:
    try:
        text = md_path.read_text(errors="replace")
    except OSError:
        return ""
    m = re.search(rf'^{re.escape(field)}:\s*(\S.*)$', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _walk_test_files(tests_root: Path):
    for dirpath, dirnames, filenames in os.walk(tests_root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            yield Path(dirpath) / fn


def _find_tests_root(repo_p: Path) -> Path:
    # Prefer checksum/tests (Checksum's standard layout); else first `tests`/`e2e`
    # dir that actually contains .checksum.md or .spec files; else repo root.
    for rel in ("checksum/tests", "tests", "e2e"):
        cand = repo_p / rel
        if cand.is_dir():
            return cand
    return repo_p


def manifest(repo: str) -> int:
    repo_p = Path(repo).expanduser().resolve()
    if not repo_p.is_dir():
        print(json.dumps({"ok": False, "error": f"not a directory: {repo}"}))
        return 1
    tests_root = _find_tests_root(repo_p)

    stories: dict[str, dict] = {}   # base-stem -> {path,title,area,start_url}
    specs: list[dict] = []          # {path, area, stem}

    for f in _walk_test_files(tests_root):
        name = f.name
        rel = str(f.relative_to(repo_p))
        area = f.parent.name
        if name.endswith(STORY_SUFFIX):
            stem = name[: -len(STORY_SUFFIX)]
            stories[stem] = {
                "story_path": rel, "area": area,
                "title": _frontmatter_title(f),
                "checksum_id": _frontmatter_field(f, "checksumTestId"),
                "start_url": _frontmatter_field(f, "startUrl"),
            }
        elif name.endswith(SPEC_SUFFIXES):
            sfx = next(s for s in SPEC_SUFFIXES if name.endswith(s))
            specs.append({"spec_path": rel, "area": area, "stem": name[: -len(sfx)]})

    # Pair each spec to the story whose stem is the longest prefix of the spec stem
    # (spec stems carry a trailing " - <ID>" the story stem lacks).
    cases: list[dict] = []
    used_specs = set()
    for base, st in sorted(stories.items()):
        match = None
        for sp in specs:
            if id(sp) in used_specs:
                continue
            if sp["area"] == st["area"] and (sp["stem"] == base or sp["stem"].startswith(base)):
                if match is None or len(sp["stem"]) < len(match["stem"]):
                    match = sp
        entry = dict(st)
        if match:
            entry["spec_path"] = match["spec_path"]
            used_specs.add(id(match))
        else:
            entry["spec_path"] = None  # story exists but no generated/checked-in spec
        cases.append(entry)

    # Specs with no matching story (rare) still belong in the manifest.
    for sp in specs:
        if id(sp) not in used_specs:
            cases.append({"story_path": None, "spec_path": sp["spec_path"],
                          "area": sp["area"], "title": sp["stem"],
                          "checksum_id": "", "start_url": ""})

    by_area: dict[str, list] = {}
    for c in cases:
        by_area.setdefault(c["area"], []).append(c)

    out = {
        "ok": True,
        "repo": str(repo_p),
        "tests_root": str(tests_root.relative_to(repo_p)) if tests_root != repo_p else ".",
        "areas": {a: by_area[a] for a in sorted(by_area)},
        "totals": {
            "areas": len(by_area),
            "cases": len(cases),
            "stories": sum(1 for c in cases if c["story_path"]),
            "specs": sum(1 for c in cases if c["spec_path"]),
            "stories_without_spec": sum(1 for c in cases if c["story_path"] and not c["spec_path"]),
        },
    }
    print(json.dumps(out, indent=2))
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "resolve" and len(rest) == 1:
        return resolve(rest[0])
    if cmd == "sync" and len(rest) == 1:
        return sync(rest[0])
    if cmd == "manifest" and len(rest) == 1:
        return manifest(rest[0])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    # The skill is decommissioned; the code above is kept for reference only.
    sys.exit("DECOMMISSIONED: deliverable-coverage-assessment was previously for internal use at Checksum "
             "and is now a non-functional skeleton kept on GitHub for "
             "demonstration purposes only. It no longer runs.")
