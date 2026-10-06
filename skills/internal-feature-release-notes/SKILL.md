---
name: checksum-feature-release-notes
description: >-
  DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional
  demonstration skeleton; if invoked, reply only with the decommission notice
  in the skill body).
  Compile a feature release-notes report from the Checksum public docs repo
  (<org>/<docs-repo>, the Mintlify source behind
  https://checksum.ai/docs). Scans git history for the last X days, groups
  changes into new features / doc fixes / internal-tooling, and includes the
  DIRECT live doc URL for every page touched. Saves a dated markdown report to
  the user's Desktop. Requires a local clone of the docs-repo repo; if it
  can't be found, the skill asks the user to clone it and point to its path.
  INVOKE when the user says "release notes", "feature release notes", "release
  updates", "what changed in the docs", "docs updates last N days", "compile a
  docs changelog", "checksum-feature-release-notes", or asks for a report of
  recent documentation/feature changes over a time window.
---

# Checksum Feature Release Notes

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. It does not call any Checksum API or service, and any bundled scripts only print a notice.

## If this skill is invoked

Do not run any step, script, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `checksum-feature-release-notes` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Generate a share-ready markdown report of what changed in the Checksum public
documentation over a user-specified time window, with a direct live URL for
every page that was added or updated.

## Inputs

- **Days (X):** number of days to look back. Parse from the user's request
  (e.g. "last 14 days" → 14). **Default to 7** if unspecified.
- **Repo path:** the local clone of `<org>/<docs-repo>`. This is a
  hard dependency — see **Prerequisites** below. Use a user-supplied path if
  given; otherwise discover it. Never assume a single hardcoded location.

## Helper scripts (use these instead of re-deriving the plumbing)

This skill ships with scripts under `scripts/` that encapsulate every bit of
repo-discovery, date-math, git, and URL-mapping logic so you do **not** have to
reconstruct those commands each run. They are portable (BSD/macOS + GNU/Linux),
resolve `git` even when it's missing from the sandbox `PATH`, and are read-only
against the docs repo. Call them with their absolute path — this skill lives at
`~/.claude/skills/checksum-feature-release-notes`:

```bash
SK="$HOME/.claude/skills/checksum-feature-release-notes/scripts"

"$SK/since-date.sh" [DAYS]            # prints SINCE=/TODAY= (DAYS default 7)
"$SK/find-repo.sh" [CANDIDATE_PATH]   # prints validated repo path, exit 1 if none
"$SK/collect.sh" [--days N] [--repo PATH] [--diffs]   # the main driver
```

**`collect.sh` is the workhorse — prefer it over running git by hand.** One call
emits a single structured blob with these sections:

- `META` — `REPO`, `GIT`, `WINDOW_DAYS`, `SINCE`, `TODAY`, `COMMIT_COUNT`
- `COMMITS` — `hash|date|author|subject` per commit in the window (`--all`)
- `MOST_RECENT` — only when `COMMIT_COUNT=0`, the last 3 commits for context
- `PERCOMMIT` — per commit, each touched file as
  `status<TAB>path<TAB>URL-or-NONPUBLISHED:<reason>` (renames resolve to the new
  path; the live-URL mapping and the non-published exclusions are already applied)
- `DIFFS` — only with `--diffs`, the full diff of every published `.mdx` touched

Typical flow: `collect.sh --days <X> --diffs` gives you everything needed for the
report in one shot. Exit codes: `0` ok (including the empty-window case), `1` no
valid repo, `2` bad args.

## Prerequisites — locate the docs-repo repo (do this FIRST)

This skill is portable and does **not** assume any one machine's layout. Resolve
the repo via the helper, which searches common clone locations and a home-tree
fallback, then validates `docs.json` + the `docs-repo` remote:

```bash
SK="$HOME/.claude/skills/checksum-feature-release-notes/scripts"
# User named a path? validate just that one:
"$SK/find-repo.sh" "<user-supplied-path>"
# Otherwise auto-discover:
"$SK/find-repo.sh"
```

`collect.sh` performs this same resolution internally, so in practice you can go
straight to it and only fall back to `find-repo.sh` for a clearer error message.

**If no valid clone is found** (`find-repo.sh`/`collect.sh` exit 1), STOP and
tell the user, e.g.:

   > I couldn't find a local clone of the Checksum docs repo
   > (`<org>/<docs-repo>`), which this skill needs to read git
   > history. Please either:
   > - clone it and tell me where:
   >   `git clone <docs-repo URL>`
   > - or, if it's already on this machine, give me the path and I'll use it.
   >
   > Once you point me to it, I'll generate the report from there.

   Do not fabricate a report without a real repo. When the user provides a
   path, re-validate it (pass it to `find-repo.sh`/`collect.sh --repo`) before
   proceeding.

From here on, treat the validated path as `<repo>`.

## Critical environment note

The Write tool is sandboxed to the current working directory, so writing
directly to `$HOME/Desktop/...` **silently fails** (reports success, no file
appears). To save to the Desktop you MUST either:

- write the file inside the working dir first, then `cp` it to the Desktop with
  a Bash call using `dangerouslyDisableSandbox: true`, **or**
- write the whole file via a Bash heredoc with `dangerouslyDisableSandbox: true`.

If the Desktop path is itself a macOS Finder alias rather than a real
directory, resolve the alias target with `osascript` before writing into it.

After saving, ALWAYS verify with `ls -la <final_path>` (sandbox disabled) and
report the real path. Never claim a file was saved without this check.

## Procedure

### 1. Gather everything in one call

Run the collector for the requested window (default 7 days), with `--diffs` so
you also get the content needed to describe features:

```bash
SK="$HOME/.claude/skills/checksum-feature-release-notes/scripts"
"$SK/collect.sh" --days <X> --diffs
# add --repo "<path>" if the user supplied one
```

Read the `META` section for `SINCE`/`TODAY`/`COMMIT_COUNT` (the window is
computed from the real system clock — no manual date math).

**If `COMMIT_COUNT=0`,** write a short report saying so (cite the window and
repo) and surface the `MOST_RECENT` commits the collector printed so the user
can decide whether to widen the window. Then stop.

### 2. Read the diffs for substantive commits

The `DIFFS` section already contains the full diff of every published `.mdx`
touched. Read the actual added/changed content — don't rely on commit subjects
alone. You need enough detail to describe each feature in 2–5 bullets (what it
does, how to use it, key flags/endpoints/requirements).

### 3. Use the URL mapping the collector already computed

The `PERCOMMIT` section lists every touched file as
`status<TAB>path<TAB>URL-or-NONPUBLISHED:<reason>`. The Mintlify mapping and the
non-published exclusions are **already applied** for you:

- published pages →  `https://checksum.ai/docs/<path-without-.mdx>` (trailing
  `/index` stripped)
- `NONPUBLISHED:internal/tooling` — `docs/internal/`, `.cursor/`
- `NONPUBLISHED:config/meta` — `docs.json`, `style.css`, `favicon.svg`,
  `README.md`, `run-dev.sh`
- `NONPUBLISHED:image/asset` — `images/` and image files
- `NONPUBLISHED:non-mdx` — anything else not publishable

Use those URLs directly. Roll the `NONPUBLISHED:*` entries into the internal /
tooling section, clearly marked "not published". (Logic lives in
`scripts/lib.sh:map_url` if you ever need to confirm an edge case.)

### 4. Classify each change

- **New Features Documented** — new pages or substantial new capability docs.
  Each entry: a `### N. <Feature>` heading, a `🔗 **Live page(s):**` line with the
  direct URL(s), the source file(s) in parentheses, then 2–5 bullets.
- **Documentation Changes / Fixes** — rewrites, corrections, removals,
  consistency fixes, nav changes (cite commit hashes).
- **Tooling / Internal (not public-facing)** — `.cursor/` skills/hooks,
  `docs/internal/`, config.

### 5. Assemble the report

Use this structure (adapt the window/counts):

```
# Checksum AI Docs — Feature Release Notes (Last <X> Days)

**Repo:** <org>/<docs-repo> (Mintlify — powers https://checksum.ai/docs)
**Window:** <since-date> → <today>
**Commits in window:** <N>

> URL mapping: published pages live at https://checksum.ai/docs/<path> ...

## TL;DR
<numbered one-liners of the headline changes>

## New Features Documented
### 1. <Feature>
🔗 **Live page:** <url>  (`<source path>`)
- ...

## Documentation Changes / Fixes (non-feature)
- ... (`<hash>`)

## Tooling / Internal (not public-facing pages)
- ...

## Commit Log (last <X> days)
| Date | Hash | Summary |
...

---
*Report generated <today> from `git log` of <repo path>.*
```

### 6. Save and verify

- Filename: `docs-release-notes-last-<X>-days.md` on the Desktop
  (`$HOME/Desktop/`).
- Save using the sandbox-aware method above, then `ls -la` to confirm.
- Report the final absolute path and a brief summary of the headline changes to
  the user.

## Notes

- Keep feature descriptions grounded in the actual diff content — quote real
  flag names, endpoint paths, and requirements rather than paraphrasing loosely.
- If the same page is touched by several commits, list its URL once in the
  feature section and roll the fixes into the changes section.
- This skill is read-only against the docs repo; never modify or commit to it.
