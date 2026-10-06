---
name: checksum-docs-update
description: >-
  DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional
  demonstration skeleton; if invoked, reply only with the decommission notice
  in the skill body).
  Watch the public Checksum docs (https://checksum.ai/docs) for new or changed
  topics and report what's new since the last check. Maintains a local baseline
  index of every documentation page (title, URL, section, description) derived
  from the site's Mintlify machine-readable index (/docs/llms.txt). On each run
  it re-fetches the live index, diffs it against the saved baseline, and tells
  the caller exactly what changed — pages ADDED, pages REMOVED, and pages whose
  title or description CHANGED — with the direct live URL and site section for
  each. Then it updates the baseline so the next run compares against today's
  state. Read-only against the site; the only thing it writes is its own local
  baseline. INVOKE when the user says "checksum-docs-update", "check the docs
  for updates", "what's new in the checksum docs", "did the docs change",
  "any new docs pages", "diff the docs site", or asks whether new topics have
  appeared on the Checksum documentation site.
---

# Checksum Docs Update

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. It does not call any Checksum API or service, and any bundled scripts only print a notice.

## If this skill is invoked

Do not run any step, script, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `checksum-docs-update` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Detect and report new or changed topics on the public Checksum documentation
site, then keep a local baseline current for the next check.

## How it works

The docs at `https://checksum.ai/docs` are a Mintlify site. Mintlify publishes a
canonical, machine-readable index of every page at
`https://checksum.ai/docs/llms.txt` — one line per page with its title,
canonical URL, and frontmatter description. This skill treats that file as the
authoritative list of "topics on the site" and diffs it against a saved
baseline.

Everything is driven by `scripts/docs_index.py`:

- `python3 scripts/docs_index.py` → `--check` (default): fetch the live index,
  diff against the baseline, print a JSON report. **Writes nothing.**
- `python3 scripts/docs_index.py --sync` → same diff, then overwrite the
  baseline with the live index.
- `python3 scripts/docs_index.py --init` → (re)create the baseline from the
  live site. No diff. Only needed if the baseline is missing or you want a hard
  reset.

The baseline lives in `reference/`:
- `reference/docs-index.json` — parsed baseline (what the diff compares against)
- `reference/llms.txt` — raw snapshot of the last-seen index

## What to do when invoked

1. **Check for changes.** From the skill directory, run:
   ```bash
   cd "$(dirname "$0")" 2>/dev/null; python3 scripts/docs_index.py
   ```
   (Use the skill's own directory: `~/.claude/skills/checksum-docs-update`.)
   Parse the JSON it prints.

2. **If `has_changes` is false**, tell the user plainly that the Checksum docs
   are unchanged since the baseline (`baseline_captured_at`), and report the page
   count. Then **STOP**. Do **not** run `--sync`. Do **not** write, touch, or
   modify anything in `reference/` — the baseline is already current and must be
   left exactly as-is. A no-change run makes zero writes.

3. **If `has_changes` is true**, report the changes clearly, grouped:
   - **🆕 New pages** (`added`) — for each: title, site section (`area`), and the
     clickable live URL (`page_url`). These are the "new topics."
   - **🗑 Removed pages** (`removed`) — title + `page_url` (may be a rename/move;
     cross-check against the added list).
   - **✏️ Changed pages** (`changed`) — title + `page_url`, and for each delta
     show what changed. A `description` delta means the page's summary/frontmatter
     was edited (a content-update signal); a `title` delta means it was renamed.
     Show before → after concisely.

   For every item, give the user the direct link (`page_url`) so they can open it
   on the site, and name the section (`area`) so they know where it lives.

4. **Update the baseline** so the next run compares against today's state:
   ```bash
   python3 scripts/docs_index.py --sync
   ```
   Do this **after** you've reported the changes to the user (step 3), so the
   report reflects the diff, and confirm to the user that the baseline is now
   updated. If there were no changes (step 2), skip this — the baseline is
   already current.

## Reporting format

Lead with a one-line verdict ("3 new pages, 1 renamed since 2026-07-22" or "No
changes"). Then the grouped lists above. Keep URLs as full clickable links.
Close by confirming the baseline was updated (or that no update was needed).

## Scope & limitations (be honest about these)

- Detection is **index-level**: it catches pages added, removed, renamed, or
  whose description changed. It does **not** diff the full body text of a page,
  so a content edit that leaves the title and frontmatter description untouched
  won't be flagged. If the user wants to confirm a specific page's body changed,
  fetch its `.md` (append `.md` to the `page_url`, or use the `url` field) with
  `curl -sSL -A "<browser UA>"` and compare.
- The site is behind Cloudflare. `scripts/docs_index.py` fetches with a browser
  User-Agent via `curl`, which returns 200. If a fetch ever fails, verify
  `curl -sSL -A "Mozilla/5.0 ..." https://checksum.ai/docs/llms.txt` works before
  assuming the site is down.
- Read-only against the site. The only writes are to this skill's own
  `reference/` baseline files.
