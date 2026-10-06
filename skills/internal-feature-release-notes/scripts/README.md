# Scripts for `checksum-feature-release-notes`

> **Decommissioned.** These scripts were previously for internal use at Checksum and are now a non-functional skeleton kept for demonstration only. `lib.sh` exits with a notice, so every script stops immediately.

These encapsulated the repetitive git / date / URL-mapping plumbing so the skill
doesn't re-derive it on every run. All are read-only against the docs repo and
work on both macOS (BSD) and Linux (GNU). They resolve `git` even when it's
missing from the sandbox `PATH`.

| Script           | Purpose                                                        |
|------------------|----------------------------------------------------------------|
| `lib.sh`         | Shared functions (sourced by the others): `resolve_git`, `find_repo`, `validate_repo`, `since_date`, `today_date`, `map_url`. Not meant to run directly. |
| `since-date.sh`  | `since-date.sh [DAYS]` → prints `SINCE=`/`TODAY=` (DAYS default 7). Isolates the window date-math from the system clock. |
| `find-repo.sh`   | `find-repo.sh [CANDIDATE]` → prints a validated docs-repo clone path, exit 1 if none. |
| `collect.sh`     | The workhorse. `collect.sh [--days N] [--repo PATH] [--diffs]` → one structured blob: `META`, `COMMITS`, `MOST_RECENT` (empty window), `PERCOMMIT` (file→URL), `DIFFS`. |

## Quick use

```bash
SK="$HOME/.claude/skills/checksum-feature-release-notes/scripts"
"$SK/collect.sh" --days 14 --diffs        # everything the report needs
```

## URL mapping rules (in `lib.sh:map_url`)

- `<dir>/<file>.mdx`  → `https://checksum.ai/docs/<dir>/<file>`
- `<dir>/index.mdx`   → `https://checksum.ai/docs/<dir>`  (trailing `/index` stripped)
- Non-published: `docs/internal/`, `.cursor/`, `docs.json`, `style.css`,
  `favicon.svg`, `README.md`, `run-dev.sh`, images, and any non-`.mdx` file.

Edit `lib.sh` if the site's publishing rules change — the other scripts inherit it.
