#!/usr/bin/env python3
"""
config.py — per-user, machine-local settings for 30-day-healing-analysis.

Everything that varies per user (where customer test-repo clones live, optional
per-customer path pins) is stored here instead of being hardcoded, so the skill
is portable across machines. The parent agent reads this in Phase 0; if a
required value is missing it ASKS the user and records the answer via `set`.

Config file (user-local, NOT committed — git-ignore it):
    ~/.claude/skills/30-day-healing-analysis/config.local.json

Schema:
    {
      "customer_repos_base": "/abs/dir/under/which/customer/clones/live",
      "customer_repos": { "<slug>": "/abs/path/to/that/customers/test/repo" }
    }

`customer_repos_base` is the one setting most users need. The audit resolves a
customer's repo by searching under it. `customer_repos[slug]` is an optional
explicit override that wins over the search (use when the layout is unusual).

CLI:
    config.py path                  -> prints the config file path
    config.py show                  -> prints the whole config as JSON
    config.py get <key>             -> prints value (empty string if unset)
    config.py set <key> <value>     -> persists a top-level key
    config.py set-customer <slug> <path>  -> pins one customer's repo path
    config.py resolve-repo <slug>   -> prints absolute repo path, or
                                       "RESOLVE_FAILED: <reason>" (exit 3)

resolve-repo is the important one. It returns the first candidate that is a git
repo AND has a package.json carrying a Playwright/Checksum signal — the same
gate collect.py's preflight applies — so a path it returns will pass preflight.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Rename-proof: the skill dir is this file's grandparent (lib/ -> skill root),
# so renaming the skill folder does NOT break config resolution and the config
# file travels with the folder.
CONFIG_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = CONFIG_DIR / "config.local.json"

PW_SIGNALS = ("@playwright/test", "playwright", "checksumai", "eslint-plugin-playwright")


def load() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")
    # config holds machine-local paths — restrict to the owner.
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def _is_test_repo(p: Path) -> bool:
    """True if p is a git repo (or submodule) with a Playwright/Checksum package.json."""
    if not p.is_dir():
        return False
    git = p / ".git"
    if not git.exists():  # .git is a dir (normal repo) or a file (submodule)
        return False
    pkg = p / "package.json"
    if not pkg.exists():
        return False
    try:
        text = pkg.read_text()
    except OSError:
        return False
    return any(sig in text for sig in PW_SIGNALS)


def resolve_repo(slug: str, cfg: dict | None = None) -> tuple[str | None, str]:
    """Return (abs_path, reason). abs_path is None on failure."""
    cfg = cfg if cfg is not None else load()

    # 1) explicit per-customer pin always wins
    pinned = (cfg.get("customer_repos") or {}).get(slug)
    if pinned:
        p = Path(pinned).expanduser()
        if _is_test_repo(p):
            return str(p.resolve()), "pinned"
        return None, f"pinned path for '{slug}' is not a valid test repo: {pinned}"

    base = cfg.get("customer_repos_base")
    if not base:
        return None, ("customer_repos_base is not configured — ask the user where "
                      "their customer test-repo clones live, then "
                      "`config.py set customer_repos_base <dir>`")
    base_p = Path(base).expanduser()
    if not base_p.is_dir():
        return None, f"customer_repos_base does not exist: {base}"

    # 2) search common layouts under the base, shallow-first
    candidates = [
        base_p / slug / f"{slug}-checksum-tests",
        base_p / f"{slug}-checksum-tests",
        base_p / slug,
    ]
    for c in candidates:
        if _is_test_repo(c):
            return str(c.resolve()), "matched a standard layout under customer_repos_base"

    # 3) fall back to a bounded glob: any *-checksum-tests / *<slug>* dir <=2 levels deep
    seen = set()
    for depth in ("*", "*/*"):
        for c in sorted(base_p.glob(depth)):
            if c in seen or not c.is_dir():
                continue
            seen.add(c)
            name = c.name.lower()
            if slug.lower() in name and _is_test_repo(c):
                return str(c.resolve()), f"glob match under customer_repos_base: {c.name}"

    return None, (f"no valid test repo for '{slug}' found under {base}. Confirm it is "
                  f"cloned, or pin it: `config.py set-customer {slug} <abs-path>`")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]

    if cmd == "path":
        print(CONFIG_PATH)
        return 0
    if cmd == "show":
        print(json.dumps(load(), indent=2))
        return 0
    if cmd == "get":
        if len(rest) != 1:
            print("usage: config.py get <key>", file=sys.stderr)
            return 2
        print(load().get(rest[0], ""))
        return 0
    if cmd == "set":
        if len(rest) != 2:
            print("usage: config.py set <key> <value>", file=sys.stderr)
            return 2
        cfg = load()
        cfg[rest[0]] = rest[1]
        save(cfg)
        print(json.dumps({"set": rest[0], "value": rest[1], "config": str(CONFIG_PATH)}))
        return 0
    if cmd == "set-customer":
        if len(rest) != 2:
            print("usage: config.py set-customer <slug> <path>", file=sys.stderr)
            return 2
        cfg = load()
        cfg.setdefault("customer_repos", {})[rest[0]] = rest[1]
        save(cfg)
        print(json.dumps({"set-customer": rest[0], "path": rest[1]}))
        return 0
    if cmd == "resolve-repo":
        if len(rest) != 1:
            print("usage: config.py resolve-repo <slug>", file=sys.stderr)
            return 2
        path, reason = resolve_repo(rest[0])
        if path:
            print(path)
            return 0
        print(f"RESOLVE_FAILED: {reason}", file=sys.stderr)
        return 3

    print(f"unknown command: {cmd}\n{__doc__}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    # The skill is decommissioned; the code above is kept for reference only.
    sys.exit("DECOMMISSIONED: 30-day-healing-analysis was previously for internal use at Checksum "
             "and is now a non-functional skeleton kept on GitHub for "
             "demonstration purposes only. It no longer runs.")
