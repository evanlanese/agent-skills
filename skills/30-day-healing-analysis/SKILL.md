---
name: 30-day-healing-analysis
description: DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional demonstration skeleton; if invoked, reply only with the decommission notice in the skill body). Produced a single share-ready "customer digest" markdown report for a Checksum customer, saved to the user's Desktop as `<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md`. It has two parts. PART 1 — a 30-day test-suite MAINTENANCE audit from `main` git history: only commits authored by `checksum-ai`, `checksum-ai-test-suite-integration[bot]`, `checksum-lint`, or `Checksum AI Agent` (human commits excluded), classifying locator changes, flow tweaks, bug annotations, wait/timing, assertion updates, and stability fixes into a scorecard, impact table, and healing examples; new files and pure renames are ignored on purpose. PART 2 — appended at the end, a LIFETIME product-metrics digest from the test platform (data access removed in this skeleton): total tests generated, total test runs, and the distinct bug list. Before scraping, it syncs the customer clone to the latest `main` (checkout `main` → optional auth-refresh command → fast-forward `git pull`) so the audit sees the newest healing commits; it never edits code, commits, branches, or pushes. INVOKE when the user says "30-day healing analysis", "30-day-healing-analysis", "customer digest", "customer-digest", "generate a digest for <customer>", "audit Checksum heals", "is Checksum maintaining this suite", "30-day Checksum history", or points at a customer and asks for their Checksum maintenance + lifetime metrics in one report.
---

# /30-day-healing-analysis

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. All platform API access and credential handling have been removed, it does not call any Checksum API or service, and every script in `lib/` only prints a notice.

## If this skill is invoked

Do not run any phase, script, git command, subagent, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `30-day-healing-analysis` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Audit a customer's **Playwright (JS/TS) test suite** to determine whether **Checksum's bot/agent automation** is **actively healing and maintaining** it, by inspecting **git commits on `main` from the last 30 days** that **modify existing test files** AND are **authored by an approved Checksum identity**.

This is not a coverage audit and not a code-quality audit. It answers a single, narrower question:

> Is **Checksum's automation** still touching the customer's tests — fixing locators, adjusting flows, annotating bugs, stabilizing waits — or has it stopped running / regressed / never engaged?

Newly added files are **ignored on purpose**: a brand-new file proves authoring activity, not maintenance. Renames and pure deletions are also de-emphasized. The signal we want is "old test → still being healed by Checksum."

> **ULTRATHINK before classifying. A diff that adds a `getByTestId` in place of a CSS selector is a real maintenance signal; a diff that only renames a variable is noise. Don't over-count.**

---

## Hard rule — Checksum-authored commits ONLY

This audit measures **Checksum's** maintenance activity, not the customer's engineers'. Any commit whose author is not one of the four allowed Checksum identities is **excluded from every count and table** — no exceptions, no fuzzy matches, no "this commit message mentions Checksum so it counts."

**Allowed authors (case-insensitive name match):**

| Author name                               | Typical form                             |
| ----------------------------------------- | ---------------------------------------- |
| `checksum-ai`                             | bot user / commit `author.name`          |
| `checksum-ai-test-suite-integration[bot]` | GitHub App bot (note the `[bot]` suffix) |
| `checksum-lint`                           | linter bot                               |
| `Checksum AI Agent`                       | agent commit signature                   |

Every `git log` / `git show` invocation in this skill **must** include the author allowlist. Commits from individual human contributors (even Checksum employees committing under personal accounts) are out of scope.

---

## Hard rule — no branching, no PR, single-file output

This skill **does not** create a branch, modify the repo, or open a pull request. It reads `main`, classifies, and writes one markdown file to the user's Desktop:

```
~/Desktop/<customer-slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md
```

`<customer-slug>` is a lowercase, dash-separated form of the customer name (e.g. `acme-corp`). If unsure, ask via `AskQuestion`. **Do not** write into the customer repo, do not commit, do not push.

---

## Deliverable

**The output of this skill is exactly one markdown file**, saved to the user's Desktop:

```
~/Desktop/<customer-slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md
```

It has two parts in one file: **Part 1** — the 30-day git-history maintenance audit (scorecard -> How Checksum AI Agents Work -> Maintenance Impact -> Bugs Found -> Healing Examples), then **Part 2** (appended in Phase 2.7) — a `## Lifetime Testing Metrics — Checksum AI` section from the test platform.

The file is **self-contained and share-ready** — designed to be:

- Sent to a customer-success or engineering stakeholder via email / Slack / Notion
- Exported to PDF without further editing
- Pasted into a deck or wiki as-is
- Forwarded to the customer to demonstrate Checksum's ongoing healing activity

**Not in scope:** no branch creation, no PR, no commits to the customer repo, no modification of any tracked file.

**Quality bar:** every claim is backed by a commit SHA, the Checksum author, and a quoted diff line. No "Checksum seems to be…" prose. Numbers and evidence only.

The report layout, headings, and table schema are fixed (see [Report template](#report-template)) so multiple audits across different customers are directly comparable.

---

## What counts as "maintenance" in this skill

A modification to an existing test-suite source file (`.ts` or `.js`) **authored by a Checksum identity** where the diff shows real maintenance intent.

**File scope — author filter is primary, extension filter is the safety net:**

Because the four Checksum identities only ever commit to test-suite code in practice, the author filter does most of the work. The script then applies a permissive extension/path filter:

**Included** (when modified by a Checksum identity on `main` in the window):

1. `*.checksum.spec.ts` — Checksum-generated specs (the most common case by far).
2. `*.spec.ts` / `*.spec.js` — generic Playwright specs.
3. Any other `.ts` / `.js` file in the testing suite — **page object models, helpers, fixtures, utility files, shared functions, custom matchers, setup files, hooks**. Common locations: `pages/`, `pom/`, `helpers/`, `utils/`, `fixtures/`, `support/`, `tests/`, `e2e/`, `playwright/`, `specs/`, `__tests__/`, but the script does not require the path to match — if a Checksum bot touched it and it's `.ts`/`.js`, it's in.

**Excluded** (the script's deny list):

- Anything under `node_modules/`, `dist/`, `build/`, `.next/`, `.turbo/`, `coverage/`, `.git/`, `.github/`
- Config files: `*.config.{ts,js,mjs}`, `tsconfig*.json`, `playwright.config.*`
- Lockfiles & manifests: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- Type declarations: `*.d.ts`
- Anything that isn't `.ts` or `.js`

If a Checksum identity ever modifies a file outside this allowlist (e.g. a `.json` fixture, a `.md` doc), the script logs it under `aggregates.json → unusual_files` for human review but does **not** classify it. Surface anything in `unusual_files` to the user.

**Categories of maintenance signal:**

| Category                   | Example diff signal                                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Locator change**         | `page.locator('.btn-x')` → `page.getByTestId('submit')`; `getByRole('button', { name: /old/i })` → `/new/i`              |
| **Flow change**            | Steps reordered; an extra `click` / `fill` inserted before submit; navigation path updated                               |
| **Bug annotation**         | `test.fixme(...)`, `test.skip(...)`, `test.fail(...)`, `@bug`, `// TODO`, `// FIXME`, `// known issue`                   |
| **Wait / timing**          | `waitForTimeout` added/removed/retuned; `waitForLoadState('networkidle')` → `'domcontentloaded'`; explicit `expect.poll` |
| **Assertion update** _(classified, not counted)_ | New `expect(...)`; updated expected text/count; tightened `toHaveText` regex. Tagged so the evidence is captured, but it never becomes its own Maintenance Impact row or adds to the time-saved total — see "Per-category logic". |
| **Stability fix**          | `addLocatorHandler` added; retry block; `try/catch` around flaky step; `force: true` removed                             |
| **Data / fixture update**  | Hard-coded date refreshed; test user changed; API setup helper swapped                                                   |
| **Test framework upgrade** | `@playwright/test` version bumped in a way that requires test changes                                                    |
| **Re-enable / un-skip**    | `test.skip` → `test`; `test.fixme` removed                                                                               |

**Not maintenance** (filter these out or down-weight):

- Whitespace / formatter / lint-only diffs (Prettier, ESLint autofix)
- Pure file moves / renames with no content change
- Import path updates from a global rename
- Comment-only changes that aren't bug annotations
- `package-lock.json` / `yarn.lock` churn

---

## Setup & requirements (portable across machines)

Nothing in this skill is specific to one person's laptop. Everything machine-specific lives in a **local config file** the skill reads (and writes when something is missing):

```
$HOME/.claude/skills/30-day-healing-analysis/config.local.json
```

Managed by `lib/config.py` (stdlib only). It is per-user and must **not** be committed — add `config.local.json` to your global gitignore if the skill folder is ever tracked.

**What a machine needs to run this skill:**

| Requirement | Why | How the skill gets it |
| --- | --- | --- |
| `python3` (3.9+) | runs all four `lib/*.py` scripts | assumed present |
| `git` | reads the customer repo's history | assumed present |
| **A local clone of the customer's Playwright test repo** | Part 1 reads its commit history | the clone must already exist locally (if customer repos are git submodules of a shared repo, the submodule must be checked out); located via `config.json` → `customer_repos_base` (see below); the audit never clones for you |
| Network + GitHub auth (for the pre-scrape sync) | `--refresh` runs the optional `--auth-cmd` + `git pull --ff-only origin main` so the latest healing commits are scraped | best-effort: if offline or auth is unavailable, fall back to `--read-only` and the audit reads whatever local `main` already points at |
| `$HOME/Desktop` writable | the report is written there | assumed present (`mkdir -p` if missing) |

**The one setting that varies per user — `customer_repos_base`:**

This is the directory under which a user keeps their customer test-repo clones. It could be `~/code/customers` or anything else. The audit resolves a customer's repo from this base so the path is never hardcoded.

> **The clone must exist first.** If customer repos are git **submodules** of a shared customer-engineering repo, a customer whose submodule hasn't been checked out has no local clone, so `resolve-repo` will fail. If that happens, tell the user to check out that customer's submodule first, then re-run. The skill does not clone or initialize customers for you.

```bash
# read it (empty if unset):
python3 "$HOME/.claude/skills/30-day-healing-analysis/lib/config.py" get customer_repos_base
# record it once:
python3 "$HOME/.claude/skills/30-day-healing-analysis/lib/config.py" set customer_repos_base "<abs dir>"
# resolve a customer's repo (prints abs path, or exits 3 with RESOLVE_FAILED: <reason>):
python3 "$HOME/.claude/skills/30-day-healing-analysis/lib/config.py" resolve-repo "<slug>"
# pin one customer explicitly when the layout is unusual:
python3 "$HOME/.claude/skills/30-day-healing-analysis/lib/config.py" set-customer "<slug>" "<abs repo path>"
```

`resolve-repo` searches `customer_repos_base` for `<slug>/<slug>-checksum-tests`, `<slug>-checksum-tests`, `<slug>`, then a bounded glob — returning only a path that is a git repo **and** has a Playwright/Checksum `package.json` (the same gate Phase 0 preflight applies).

**Ask-and-record rule:** if a required value is missing, the parent agent ASKS the user once, records it via `config.py set` (or `set-customer`), and proceeds. It never guesses a path and never hardcodes one. Subsequent runs for the same machine won't ask again.

## Inputs to collect before running

Only three things vary per invocation. Everything else (branch, author allowlist, file scope rules, exclusion lists, output location) is baked into the script or the config file.

1. **Customer repo path** — resolved automatically via `config.py resolve-repo <slug>`. Only ask the user if resolution fails (missing `customer_repos_base`, or the clone isn't found).
2. **Customer name + slug** — used for the report title and the output filename (e.g. "Acme Corp" → `acme-corp`).
3. **Time window** — default **30 days**, accept overrides like `60 days ago`.

**Fixed (do not ask):**

- **Branch:** always `main`
- **Freshness:** default to `--refresh` on `collect.py` — it ensures the clone is on `main` (checkout if not), runs the optional `--auth-cmd` to refresh GitHub auth, then `git pull --ff-only origin main`, so the scrape sees the latest healing commits. It still never edits code, commits, branches, or pushes. Only fall back to `--read-only` (no checkout/auth/pull) when offline or no GitHub auth is available.
- **Author allowlist:** the four Checksum identities, hard-coded in the script
- **File scope:** any `.ts` / `.js` file modified by a Checksum identity, minus the exclusion list (see "What counts as maintenance")
- **Output location:** always `~/Desktop/<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md`

**If a required input is missing, ask via `AskQuestion`, then record it** (`config.py set …`) so the next run is non-interactive. Don't guess. The order in Phase 0 is: resolve repo from config → if `RESOLVE_FAILED`, ask the user for `customer_repos_base` (or the exact repo path) → record it → re-resolve.

---

## Workflow overview

The audit has six phases. **Phases 0, 1.5, 2.5, and 3 are fully automated** by deterministic Python scripts pre-stored inside this skill — the AI does not run git commands, build author filters, decide globs, perform arithmetic, lint the report's structure, or hand-craft cleanup commands. Phases 1 and 2 are where AI judgment is required (classification and synthesis).

| Phase                          | Done by                                                                                                                                  | Output                                                                                                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0. Data collection**         | `lib/collect.py` (pre-stored in skill)                                                                                                   | Workspace dir with `metadata.json`, `commits.jsonl`, `aggregates.json`, `diffs/*.diff`                                                                     |
| **0.5. Dormant short-circuit** | Parent agent (one check + templated write)                                                                                               | If `summary.checksum_commits == 0`: a templated **Dormant** report written to `~/Desktop/` and the pipeline STOPS. Phases 1, 1.5, 2, 2.5 skipped entirely. |
| **1. Classify diffs**          | AI (parallel subagents)                                                                                                                  | `classifications.jsonl`                                                                                                                                    |
| **1.5. Compute metrics**       | `lib/compute_metrics.py` (pre-stored in skill)                                                                                           | `metrics.json` — bugs found, per-category counts, time saved, all formatted strings                                                                        |
| **2. Synthesize report**       | AI (single synthesizer agent) — prompt includes `metrics.json` + `metadata.json` pasted verbatim as JSON code blocks; agent does no math | `~/Desktop/<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md`                                                                                                    |
| **2.5. Deterministic lint**    | `lib/lint_report.py` (pre-stored in skill)                                                                                               | `lint.json`. If any violations, parent re-dispatches Phase 2 with `lint.json` as feedback (max 2 retries) before falling through to the reviewer.          |
| **2.6. AI reviewer**           | AI (single reviewer agent + retry loop) — only runs once Phase 2.5 lint is clean                                                         | `review.md` per pass. Loop until `Excellent` / `Good` or exit-conditions ladder triggers ship.                                                             |
| **2.7. Append product-metrics digest** | `lib/customer_report.py --append` (one shell call)                                                                              | The `## Lifetime Testing Metrics — Checksum AI` section appended to the report (test-platform data). Runs for normal AND dormant reports.          |
| **3. Post-flight cleanup**     | `lib/collect.py --cleanup` (one shell call)                                                                                              | Workspace deleted; only the Desktop report remains                                                                                                         |

> **Phase 1.5 is mandatory** for non-dormant runs. The synthesizer (Phase 2) is forbidden from computing the bug count, the per-category time saved, or the total time saved — those numbers come from `metrics.json` only. AI is bad at arithmetic; the script is not.
>
> **Phase 2.5 is mandatory** for non-dormant runs. The lint catches forbidden headings, retired formatting (`**Files Changed:**`, numbered sections, footer lines), and bug-annotation removal language in milliseconds — saving the cost of a full reviewer round-trip for issues a regex can find. Re-dispatch the synthesizer with `lint.json` as structured feedback before invoking the AI reviewer.
>
> **Phase 0.5 short-circuits the whole pipeline** when Checksum didn't touch `main` during the window. The Dormant report template needs no AI synthesis — the parent agent writes it directly using `metadata.json` values and stops. Saves 4 classifier subagent dispatches and the synthesizer/reviewer rounds.

---

## Subagent strategy

Subagents are central to this skill, for three reasons:

1. **Context-window economy.** A 30-day audit can produce 100–500 (commit, file) pairs. If the parent agent read every `.diff` file, the context would explode. Subagents take diff-classification slices, return only structured JSONL, and never pollute the parent's context with raw diffs.
2. **Parallelism.** 4–6 classifier subagents finish in roughly 1× the time of the slowest agent, not 6×.
3. **Independent verification.** A reviewer subagent catches over-labeling, missing evidence, and template drift that the writer might miss.

### When to dispatch which subagent type

| Subagent type    | Purpose                                                                                            | Phase          | Count                                                      | Read-only?              |
| ---------------- | -------------------------------------------------------------------------------------------------- | -------------- | ---------------------------------------------------------- | ----------------------- |
| `explore`        | Phase 0 health check — read `metadata.json` / `aggregates.json`, confirm filter integrity          | 0 (opt.)       | 1                                                          | yes                     |
| `generalPurpose` | Phase 1 classifier — read a slice of `commits.jsonl` + corresponding diff files                    | 1              | 4–6 in parallel                                            | no (writes JSONL)       |
| `generalPurpose` | Phase 2 synthesizer — receive `metrics.json` + `metadata.json` inlined in prompt, write the report | 2              | 1 (+ up to 2 retries if Phase 2.5 lint reports violations) | no (writes report)      |
| `generalPurpose` | Phase 2.6 reviewer — read the just-written report, score it against the checklist                  | 2.6            | 1 per review pass                                          | no (writes review note) |
| `shell`          | Phase 0 / 2.5 / 3 script runner — only if the parent agent can't run Python directly               | 0/2.5/3 (opt.) | 1                                                          | no                      |

**Default mode of operation:** parent agent runs Phase 0 itself (one Shell call), checks the dormant short-circuit (`summary.checksum_commits == 0` → write Dormant report and STOP), then dispatches subagents for Phase 1, runs Phase 1.5 directly, dispatches the Phase 2 synthesizer, runs Phase 2.5 lint directly, re-dispatches Phase 2 if lint is dirty (up to 2 retries), then dispatches the Phase 2.6 reviewer. **No subagents are dispatched for dormant runs** — the parent writes the templated Dormant report and goes straight to Phase 3 cleanup.

### Dispatch rules

**Parallel dispatch (Phase 1):** issue all classifier subagent calls in a **single message** with multiple `Task` tool calls. Sequential dispatch wastes the parallelism win. Reference: see how `detect-tests` launches 4–6 agents at once.

**Chunking (Phase 1):** split `commits.jsonl` into contiguous row ranges of 50–80 rows each. Don't shuffle — let each agent reason about adjacent commits, which often touch the same file and tell a story together.

Example for 300 rows:

```
Agent A: rows   1– 60   (50–80 per agent)
Agent B: rows  61–120
Agent C: rows 121–180
Agent D: rows 181–240
Agent E: rows 241–300
```

Each agent gets the same prompt skeleton (see "Per-agent prompt skeleton") with its row range substituted, and appends results to `<workspace>/classifications.jsonl`. Use file locking or per-agent shard files (`classifications.<agent-id>.jsonl`) merged at the end — your call, but **agents must never overwrite each other's work**.

**Specialist subagent (Phase 1, optional):** if `aggregates.json → noise_candidates` is unusually large (>30% of pairs), dispatch ONE additional `generalPurpose` subagent dedicated solely to confirming/rejecting noise labels. It reads only the `noise_candidates` list and outputs `noise.jsonl` (one row per candidate with a `confirmed: true/false` flag). This keeps the main classifiers focused on signal.

### Reviewer loop (Phase 2.6)

**Precondition: Phase 2.5 lint must report `status: "clean"` (zero violations) before the AI reviewer is dispatched.** If `lint.json` still shows violations after the synthesizer's max-2 retry budget, ship the report as-is and tell the user — do NOT dispatch the reviewer to re-discover lint failures the regex already found.

After the lint passes clean, dispatch ONE `generalPurpose` reviewer subagent with:

- The written report path
- `<workspace>/lint.json` (so the reviewer can confirm structural cleanliness was already enforced)
- `<workspace>/metrics.json` and `<workspace>/metadata.json` inlined as JSON code blocks in the prompt (same pattern as the synthesizer prompt — the reviewer cross-checks scorecard cells against these blocks)
- The "Report template" section of this skill (verbatim)
- The "Anti-laziness checklist" (verbatim)

The reviewer writes a short scored review to `<workspace>/review.md` with one of: **Excellent / Good / Needs work** and a bulleted list of specific gaps (missing sample diffs, unsupported claims, broken table rendering, weak Healing Examples selection, etc.).

**Exit conditions (mirrors `detect-tests`):**

- **1st pass:** exit only if **Excellent**.
- **2nd pass:** exit if **Good or Excellent**.
- **3rd pass:** accept whatever — ship and tell the user the reviewer was not fully satisfied.

Between passes, dispatch the synthesizer again with the prior review as feedback PLUS the original `metrics.json` / `metadata.json` JSON blocks (re-paste them — never assume the synthesizer remembers them from a prior pass). Delete the prior `review.md` so each pass is independent. **Re-run Phase 2.5 lint after every synthesizer rewrite**, even on reviewer-driven rewrites — a fix for one reviewer gap can introduce a forbidden heading elsewhere.

### What subagents must NEVER do

- **Re-run git.** Phase 0 owns all git interaction.
- **Modify the script.** The script is the source of truth; if it has a bug, the parent fixes it and reruns Phase 0.
- **Touch the customer repo.** Read-only. No branches, no commits, no PRs.
- **Write outside the workspace + final report path.** No scratch files in `~`, no agent-internal scratchpads outside `<workspace>/`.
- **Re-classify rows another agent has already classified** unless the parent explicitly asks them to (e.g. during a re-dispatch on a rejected slice).

### Subagent failure handling

| Symptom                                                | Fix                                                                                                                                                                 |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agent returns 0 rows for its slice                     | Either the slice was empty or the agent misread the workspace. Verify slice bounds; re-dispatch.                                                                    |
| Two agents wrote overlapping rows                      | De-dupe in parent on `(commit, file)` key before Phase 2.                                                                                                           |
| Agent over-labeled `flow-change` on every diff         | Reject the slice. Re-dispatch with "Every label needs a quoted diff line" boldfaced.                                                                                |
| Reviewer scores "Needs work" three passes in a row     | Ship anyway. Tell the user in the chat which gaps remain (the customer report stays dry — no exec-summary or observations section exists to absorb a gap call-out). |
| Synthesizer wrote to `<repo>/` instead of `~/Desktop/` | Move the file, do NOT leave a copy in the repo. Dispatch a cleanup agent if needed.                                                                                 |

---

## Phase 0 — Run the data-collection script

**The script is pre-stored in the skill, not written to `/tmp/` per run.** Canonical path:

```
$HOME/.claude/skills/30-day-healing-analysis/lib/collect.py
```

The agent's job in Phase 0 is:

1. **Resolve the customer repo from config** (do not hunt the filesystem, do not hardcode):
   ```bash
   REPO=$(python3 "$HOME/.claude/skills/30-day-healing-analysis/lib/config.py" resolve-repo "<slug>")
   ```
   If this exits non-zero (`RESOLVE_FAILED: …`), the clone is missing — most often because the customer's submodule hasn't been checked out yet. Tell the user to check it out first, OR follow the **ask-and-record rule**: ask where their customer test-repo clones live (or the exact repo path), record it (`config.py set customer_repos_base <dir>` or `config.py set-customer <slug> <path>`), and re-resolve. Never guess.
2. Run the pre-stored script with `--refresh` so the clone is synced to the latest `main` before the scrape (see below), with the resolved repo + customer/slug.
3. Read the JSON summary that the script prints to stdout.
4. Confirm the workspace was created and sanity-check the headline numbers.

```bash
python3 "$HOME/.claude/skills/30-day-healing-analysis/lib/collect.py" \
  --repo "$REPO" \
  --customer "<Customer Name>" \
  --slug "<customer-slug>" \
  --days 30 \
  --refresh
```

`--refresh` syncs the clone before reading: it ensures the repo is on `main` (checking it out if not), runs the `--auth-cmd` (if one is set) to refresh GitHub authorization, then `git pull --ff-only origin main` to populate the latest commits — so the audit scrapes the newest healing activity, not a stale local snapshot. Every step is best-effort and logged to `preflight.log`; it never edits code, commits, branches, or pushes. If a step can't reach the network or auth (and as a degraded fallback), the script reads whatever local `main` already points at. **When the machine is offline or has no GitHub auth, pass `--read-only` instead** — it skips checkout/auth/pull entirely. (`--refresh` and `--read-only` are mutually exclusive. `--auth-cmd` is run through the interactive login shell so shell aliases resolve; it defaults to empty, which skips the auth step.)

The audit window is computed deterministically by `lib/audit_window.py` (a sibling module) as `today − timedelta(days=N)` through `today`, inclusive. Cross-month and cross-year boundaries are handled natively by `datetime.timedelta`. The computed dates flow into both the `git --since` query and the `metadata.json` fields that the report's "Audit window" cell, "Dated:" line, and filename slug all read from — so the report's stated window always reflects the FULL N-day calendar range, never just the date span of observed commits. Pass `--end-date YYYY-MM-DD` to reproduce a prior audit.

The script is self-contained (Python stdlib only) and exits non-zero on any pre-flight failure (not a git repo, no Playwright/Checksum dep, can't reach `main`, etc.). It auto-deletes any prior workspace at the same `--slug` path before writing new outputs, so re-running on the same customer never accumulates cruft mid-run.

> **Do NOT** copy the script to `/tmp/` and run from there. The pre-stored copy is the source of truth — every fix lives there, and Phase 3 cleanup assumes the legacy `/tmp/checksum_heals_collect.py` path will NOT exist.

### Reference: script CLI

```
usage: collect.py [--repo REPO] [--customer CUSTOMER] [--slug SLUG]
                  [--days N] [--end-date YYYY-MM-DD] [--workspace WORKSPACE]
                  [--refresh | --read-only] [--auth-cmd AUTH_CMD]
                  [--cleanup] [--cleanup-all]

Collection mode (default): requires --repo, --customer, --slug.

  Freshness (mutually exclusive):
    --refresh   Phase-0 default. Sync the clone before scraping: ensure on
                `main` (checkout if not) -> run --auth-cmd (if set) ->
                `git pull --ff-only origin main`. Each step best-effort +
                logged; never edits/commits/branches/pushes.
    --read-only Touch nothing (no checkout/auth/pull); read local `main` as-is.
                Use offline / when no GitHub auth is available.
    --auth-cmd  Command run via the login shell during --refresh to refresh
                GitHub auth (default: empty = skip).

  Audit window is computed by lib/audit_window.compute_audit_window(days=N,
  end_date=...) — default N=30, end_date=today. The computed start date is
  passed to git as --since=YYYY-MM-DD and stored in metadata.json under
  audit_window_start_date / audit_window_end_date / audit_window_days /
  report_date_iso / report_date_pretty for the synthesizer to paste into
  the report.

  Writes a workspace to /tmp/checksum-heals-audit-<slug>/ containing
  metadata.json, scope.json, aggregates.json, commits.jsonl, preflight.log,
  and diffs/<sha>__<file>.diff. Auto-deletes any prior workspace at the
  same path before writing.

Cleanup modes:
  --cleanup            Delete the workspace for --slug and exit. No collection.
  --cleanup-all        Delete every /tmp/checksum-heals-audit-* workspace plus
                       the legacy /tmp/checksum_heals_collect.py script copy.
```

### Reference: the script (for review only)

The full source lives at the canonical path above. The block below is **a snapshot for in-repo readability only** — never edit it here, edit the `.py` file. If the two ever drift, the `.py` file wins.

> **Sibling modules NOT shown in this snapshot:** `lib/audit_window.py` (Phase 0 window computation, called by `run_collection`), `lib/compute_metrics.py` (Phase 1.5 metrics computation), and `lib/lint_report.py` (Phase 2.5 deterministic linter). The snapshot below predates those additions and does not reflect the `from audit_window import compute_audit_window` integration, the `--days` / `--end-date` CLI args, or the `audit_window_*` / `report_date_*` fields written into `metadata.json`. Read the `.py` files for those, and treat the inline snippet as a historical reference for the core collection loop only.

```python
#!/usr/bin/env python3
"""
checksum_heals_collect.py — Phase 0 data collection for the
30-day-healing-analysis skill.

Reads the last N days of `main` branch git history in a customer test repo,
keeps only commits authored by one of the four allowed Checksum identities,
filters file modifications to `.ts` / `.js` test-suite files (specs, page
objects, helpers, utilities, fixtures), excludes newly-added files, dumps
each diff to disk, and emits structured JSON for downstream AI classification.

Usage:
  python3 checksum_heals_collect.py \\
      --repo /abs/path/to/customer/repo \\
      --customer "Acme Corp" \\
      --slug acme-corp \\
      [--since "30 days ago"] \\
      [--workspace /tmp/checksum-heals-audit-acme-corp]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

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


def sh(cmd, cwd=None, check=True):
    return subprocess.run(
        cmd, cwd=cwd, check=check, capture_output=True, text=True
    ).stdout


def is_in_scope(path: str) -> bool:
    """Permissive filter: any .ts/.js file Checksum touches, minus the deny list."""
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


def preflight(repo: Path, log: list) -> str:
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
    # `checksumai` (the Checksum SDK that pulls Playwright transitively) instead of
    # depending on `@playwright/test` directly.
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

    sh(["git", "fetch", "origin", "main"], cwd=repo)
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


def collect_commits(repo: Path, since: str) -> list[dict]:
    out = sh([
        "git", "log",
        "--regexp-ignore-case",
        *author_flags(),
        f"--since={since}",
        "--format=%H%x09%aI%x09%an%x09%s",
        "main",
    ], cwd=repo)
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
    # NOTE: `git show --no-patch --name-status` errors with
    # "options '--name-only', '--name-status', '--check', and '-s' cannot be used together"
    # on newer git. `git diff-tree` is the portable equivalent.
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--customer", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--since", default="30 days ago")
    ap.add_argument("--workspace", type=Path, default=None)
    args = ap.parse_args()

    repo = args.repo.resolve()
    ws = args.workspace or Path(f"/tmp/checksum-heals-audit-{args.slug}")
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    diffs_dir = ws / "diffs"
    diffs_dir.mkdir()

    log: list[str] = []
    head_sha = preflight(repo, log)

    log.append(f"\n== Collecting Checksum-authored commits (since {args.since!r}) ==")
    commits = collect_commits(repo, args.since)
    log.append(f"  {len(commits)} commits matched the author allowlist")

    # Author-filter integrity check
    seen_authors = sorted({c["author"] for c in commits})
    leaks = [a for a in seen_authors if a.strip().lower() not in ALLOWED_AUTHOR_NAMES_LOWER]
    if leaks:
        log.append(f"  WARNING: filter leak — non-Checksum authors slipped through: {leaks}")
    log.append(f"  Active Checksum identities: {seen_authors}")

    # Build (commit, file) pairs with status filtering
    pairs: list[dict] = []
    added: set[str] = set()
    modified: set[str] = set()
    renamed: set[str] = set()
    unusual: list[dict] = []

    for c in commits:
        for status, fp in files_for_commit(repo, c["sha"]):
            if not is_in_scope(fp):
                # Track unusual file types Checksum touched (e.g. .json, .md) for human review
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

    # Files added-then-modified in window are still "new" — exclude
    scope = sorted(modified - added)
    pairs = [p for p in pairs if p["file"] in set(scope)]

    log.append(f"\n== Building scope ==")
    log.append(f"  Files ADDED by Checksum (excluded): {len(added)}")
    log.append(f"  Files MODIFIED by Checksum: {len(modified)}")
    log.append(f"  Files RENAMED by Checksum: {len(renamed)}")
    log.append(f"  Final scope (modified − added): {len(scope)}")
    log.append(f"  (commit, file) pairs to classify: {len(pairs)}")
    log.append(f"  Unusual non-.ts/.js files touched (logged, not classified): {len(unusual)}")

    # Dump diffs
    log.append(f"\n== Dumping {len(pairs)} diffs to {diffs_dir} ==")
    for p in pairs:
        safe = safe_filename(p["file"].replace("/", "__"))
        diff_path = diffs_dir / f"{p['short_sha']}__{safe}.diff"
        diff_path.write_text(diff_for(repo, p["commit"], p["file"]))
        p["diff_path"] = str(diff_path)

    # Aggregates
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
        wk = d.strftime("%G-W%V")  # ISO week
        weekly[wk][p["author"]] += 1

    subjects = sorted(
        {(p["short_sha"], p["author"], p["subject"]) for p in pairs},
        key=lambda t: t[0],
    )

    # Detect likely-noise commits (purely whitespace / formatter)
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

    # Sanity baseline: total commits on main (any author) — for the report's context paragraph
    baseline = sh([
        "git", "log", f"--since={args.since}", "--oneline", "main"
    ], cwd=repo, check=False).strip().splitlines()

    # Window date range
    if commits:
        dates = sorted(c["date"] for c in commits)
        window_start, window_end = dates[0][:10], dates[-1][:10]
    else:
        window_start = window_end = None

    metadata = {
        "customer": args.customer,
        "slug": args.slug,
        "repo": str(repo),
        "branch": "main",
        "head_sha": head_sha,
        "since": args.since,
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
        "window_first_commit_date": window_start,
        "window_last_commit_date": window_end,
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

    # Stdout summary for the agent
    print(json.dumps({
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
            "window": [window_start, window_end],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
```

### Phase 0 gate

After the script exits 0, the agent **must** verify before proceeding:

- [ ] `summary.checksum_commits > 0`. **If zero, GO TO Phase 0.5 — Dormant short-circuit** (see below). DO NOT dispatch classifiers, DO NOT run `compute_metrics.py`, DO NOT dispatch a synthesizer. Write the Dormant report directly and proceed to Phase 3 cleanup.
- [ ] `summary.active_identities` is a subset of `{checksum-ai, checksum-ai-test-suite-integration[bot], checksum-lint, Checksum AI Agent}`. If anything else, the script's filter has a bug — investigate before continuing.
- [ ] `metadata.leaks_detected` is empty.
- [ ] `summary.scope_pairs` is non-zero. If commits exist but pairs are zero, all Checksum work was on out-of-scope files — report it as a finding to the user (not as a customer-facing section).
- [ ] `summary.unusual_files` reviewed; if non-empty, treat as a forensic-only signal — do **not** surface in the customer-facing report. The audit deliverable is value-prop, not pipeline diagnostics.
- [ ] `summary.total_test_files_in_suite` is non-zero. If zero, the spec-naming convention may be non-standard — inspect `git ls-tree -r HEAD --name-only` in the customer repo to confirm and adjust `is_spec_file()` if needed before re-running.
- [ ] `metadata.audit_window_start_date`, `metadata.audit_window_end_date`, and `metadata.audit_window_days` are populated. These are the CANONICAL window the report must surface — computed by `lib/audit_window.compute_audit_window()` as `today − timedelta(days=N)` through `today`, inclusive. They are NOT the same as `metadata.observed_first_commit_date` / `metadata.observed_last_commit_date` (which only span the dates of OBSERVED commits and will under-report the window when Checksum was quiet at the start or end). Sanity check: `audit_window_end_date - audit_window_start_date` (in days) should equal `audit_window_days`.
- [ ] `metadata.report_date_pretty` (e.g. `"May 28, 2026"`) and `metadata.report_date_iso` (e.g. `"2026-05-28"`) are populated — the synthesizer pastes the pretty form into the "Dated:" line and the parent uses the ISO form for the Desktop filename slug.
- [ ] `diffs/` directory exists and contains one `.diff` file per row in `commits.jsonl`.

If anything fails (other than the dormant condition, which has its own dedicated path below), STOP and report to the user. **Do not classify on a broken scope.**

---

## Phase 0.5 — Dormant short-circuit (when no Checksum activity)

When `summary.checksum_commits == 0`, the customer's Checksum integration either was paused, scoped to a non-`main` branch, or was never enabled for this repository. There is nothing for the classifier or synthesizer to do — running the full pipeline would burn 4+ subagent dispatches to produce a report full of zeros.

**Instead, the parent agent writes a templated Dormant report directly** (no subagent dispatch), then proceeds to Phase 3 cleanup.

The Dormant report is rendered by substituting `metadata.json` values into the template below and writing the result to `~/Desktop/<slug>_checksum_ai_maintenance_report_<metadata.report_date_iso>.md`:

```markdown
# Checksum AI Agentic Output — <metadata.customer>

## Commit History Analysis: Test Suite Maintenance

**Dated: <metadata.report_date_pretty>** · Window: last <metadata.audit_window_days> days of `main` (<metadata.audit_window_start_date> → <metadata.audit_window_end_date>)

---

## At a Glance

|             Tests Maintained             | Bugs Found | Change Events | Engineering Time Saved |
| :--------------------------------------: | :--------: | :-----------: | :--------------------: |
| **<metadata.total_test_files_in_suite>** |   **0**    |     **0**     |       **0 hrs**        |

|              |                                                                                                           |
| :----------- | :-------------------------------------------------------------------------------------------------------- |
| Customer     | <metadata.customer>                                                                                       |
| Repository   | `<derived from metadata.repo basename>`                                                                   |
| Branch       | `main` @ `<metadata.head_sha>`                                                                            |
| Audit window | <metadata.audit_window_start_date> → <metadata.audit_window_end_date> (<metadata.audit_window_days> days) |

> No Checksum AI activity was detected on `main` during the audit window. The Checksum integration may be paused, scoped to a non-`main` branch, or not yet enabled for this repository. Confirm with the customer whether this matches their expectation.

---

## How Checksum AI Agents Work

<verbatim copy of the standard report's "How Checksum AI Agents Work" section — see the Report template below for the full block to copy>
```

That's the entire Dormant report — no Maintenance Impact table (nothing to show), no Bugs Found section, no Healing Examples. Scorecard zeros + a one-line explanation + the standard educational block, period.

**After writing the Dormant report:**

1. Verify the file exists at `~/Desktop/<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md`.
2. Tell the user in the chat that the integration appears dormant, surface any context from `summary.total_main_commits_all_authors` (e.g. "the repo has 47 non-Checksum commits in the window, so the repo is active — Checksum just isn't connected") so they can route to the right CSM conversation.
3. Go straight to **Phase 3 cleanup** (`python3 lib/collect.py --slug <slug> --cleanup`). Skip the AI reviewer; a templated 30-line report doesn't need review.

The Dormant short-circuit must NEVER fall through to Phase 1. If you find yourself dispatching classifier subagents on a zero-commit window, you missed the gate — stop and back up.

---

## Phase 1 — Classify diffs

For every row in `commits.jsonl`, classify the corresponding diff (`diff_path` field points at the file) against the **maintenance categories table** at the top of this skill.

**Dispatch pattern:** see the [Subagent strategy](#subagent-strategy) section above. Summary: 4–6 parallel `generalPurpose` subagents in a single message, 50–80 contiguous rows per agent, each appending to its own shard file under `<workspace>/classifications.<agent-id>.jsonl`. Parent merges shards into `classifications.jsonl` after all agents return.

Optional: if `aggregates.json → noise_candidates` exceeds 30% of pairs, also dispatch ONE noise-specialist subagent (see Subagent strategy → Specialist subagent).

Each agent appends, per row, a JSON line to `<workspace>/classifications.jsonl`:

```json
{
  "commit": "<full sha>",
  "short_sha": "<7-char sha>",
  "date": "2026-05-04T14:23:11+00:00",
  "author": "checksum-ai",
  "file": "tests/checkout.checksum.spec.ts",
  "categories": ["locator-change", "stability-fix"],
  "evidence": [
    "- await page.locator('.cta-primary').click();",
    "+ await page.getByRole('button', { name: /pay now/i }).click();",
    "+ await page.addLocatorHandler(/* cookie banner */, ...);"
  ],
  "isNoise": false,
  "noiseReason": null
}
```

Rules every classifier agent **must** follow:

1. **Author allowlist is already enforced.** Don't re-check — the script did it. Just classify what you're given.
2. **Multi-label is fine.** A single diff can be both `locator-change` and `wait-timing`. Don't force one label.
3. **Quote real diff lines** in `evidence` (trimmed to ~120 chars). No paraphrasing without evidence.
4. **`isNoise: true`** for formatter-only / pure-rename / import-path-shuffle diffs. Always include `noiseReason`. Cross-reference `aggregates.json → noise_candidates` for hints — these are commits the script flagged as likely whitespace-only.
5. **Never invent categories.** If nothing in the table fits, use `"uncategorized"` and explain in `evidence`.
6. **Bug annotations** (`test.fixme`, `test.skip`, `@bug`) — capture the **direction** (added vs removed) as separate categories.
7. **Page object / helper / utility diffs** are first-class maintenance — classify them the same way as spec diffs. A locator constant moved from a `.spec.ts` to a `pages/CheckoutPage.ts` is still a `locator-change`.

### Phase 1 gate

Before writing the report, sanity-check the merged `classifications.jsonl`:

- [ ] Every row in `commits.jsonl` has a corresponding row in `classifications.jsonl` (or an `isNoise: true` reason).
- [ ] No category appears on >70% of non-noise rows without evidence — sign of lazy labeling.
- [ ] Every non-noise row has at least one quoted diff line.
- [ ] `test.fixme` / `test.skip` added vs removed are tallied separately.
- [ ] Page-object / helper / utility files are classified, not dismissed as "not a spec."
- [ ] Shard files merged cleanly — no duplicates on `(commit, file)` key.

**Re-dispatch on failure:** if a check fails for a specific slice, dispatch ONE replacement `generalPurpose` subagent for just that slice (e.g. "rows 121–180 were over-labeled — re-classify with stricter evidence requirement"). Do not regenerate the whole `classifications.jsonl` — that's wasted work.

---

## Phase 1.5 — Compute metrics (deterministic Python, no AI math)

Once `classifications.jsonl` is finalized, the parent agent runs the metric-computation script. **This is mandatory** — the synthesizer in Phase 2 must read its numbers from `metrics.json`, not compute them from scratch.

```bash
python3 $HOME/.claude/skills/30-day-healing-analysis/lib/compute_metrics.py \
  --workspace /tmp/checksum-heals-audit-<slug>
```

Two tunables (don't change without a stakeholder discussion — they anchor the customer-facing value-prop):

- `--per-fix-minutes` (default **30**) — saved review minutes per routine fix.
- `--per-bug-minutes` (default **60**) — saved review minutes per unique bug annotation. Bug review is longer than a routine fix because product investigation is required to confirm the underlying defect.

### The math contract (this is the bit that has to be exactly right)

Two kinds of change event, two rates:

| Change event       | Counting rule                                                            | Rate                             |
| ------------------ | ------------------------------------------------------------------------ | -------------------------------- |
| **Routine fix**    | One unique commit classified into a category = one fix in that category. | `--per-fix-minutes` (default 30) |
| **Bug annotation** | One unique `description: "..."` text added during the window = one bug.  | `--per-bug-minutes` (default 60) |

Important properties of the math:

- A commit that touches 5 files is **one fix** (per the categories it's in), not 5.
- Five separate commits each making a similar fix are **five fixes**, not one — they each represent distinct human-review time that would have been spent.
- A commit classified into two categories (e.g. both `locator-change` and `stability-fix`) is counted **once in each category row**. The per-category Time Saved cells therefore overlap on purpose — each row represents a distinct unit of human-review attention.
- The grand **Total** is the strict **sum** of every category row's Time Saved + the Bug Annotations row. No deduplication across categories. **The table always adds up exactly to the bottom row.**
- Bug annotations that are REMOVED during the window are **ignored** — only ADDS count. Removals are Checksum closing out work it already did, not value the customer is being shown.

### What the script computes (metrics.json shape)

```json
{
  "bugs_found": 3,
  "bug_descriptions": [
    "Saving the form with all required fields filled shows a generic error toast",
    "Entering a negative quantity shows the wrong validation message",
    "Filtering the list by status returns stale rows after a refresh"
  ],
  "bug_records": [
    {
      "description": "Saving the form with all required fields filled shows a generic error toast",
      "first_short_sha": "a1b2c3d",
      "first_date": "2026-05-04",
      "first_file": "checksum/tests/Orders/Create Order - Required Fields - Ab12C.checksum.spec.ts",
      "first_test_name": "Create Order - Required Fields - Ab12C"
    }
  ],
  "per_fix_minutes": 30,
  "per_bug_minutes": 60,
  "categories": [
    {
      "label": "Test Stability & Reliability",
      "commits": 18,
      "minutes_saved": 540,
      "hours_saved": 9.0,
      "time_saved_display": "~9 hrs"
    }
  ],
  "bugs_row": {
    "label": "Bug Annotations",
    "description": "Unique product bugs Checksum identified and tracked via `@bug` annotations",
    "commits": 3,
    "minutes_saved": 180,
    "hours_saved": 3.0,
    "time_saved_display": "~3 hrs"
  },
  "category_commits_subtotal": 56,
  "category_minutes_subtotal": 1680,
  "total_change_events": 59,
  "total_minutes_saved": 1860,
  "total_hours_saved": 31.0,
  "total_hours_saved_display": "~31 hrs",
  "total_hours_saved_headline": "31",
  "total_calculation_display": "56 fixes × 30 min + 3 bugs × 60 min"
}
```

### How `bugs_found` is counted (this is the change customers care about)

The script walks every non-noise classification row tagged `bug-annotation-added`, opens that row's diff file, extracts every `description: "..."` value found in **added (`+`) lines that also contain a `type: "bug"` marker**, and de-duplicates by **verbatim normalized text** across the entire window.

"Verbatim normalized" means:

- Leading and trailing whitespace stripped.
- Internal whitespace runs collapsed to a single space.
- Quote style is ignored — `"..."`, `'...'`, and `` `...` `` (template literals, including multi-line) are all extracted the same way.

So if **five different tests** all receive a `@bug` annotation whose description reads `Submitting the form with an invalid value leads to a server error page` (word-for-word), that's **one bug**. If they each get a different description, that's **five bugs**.

For every unique description, the script also captures the FIRST test it was observed in (file path + derived test name + commit SHA + date) and puts it in `metrics.bug_records`. That's the payload the synthesizer renders in the customer-facing "Bugs Found in Your Application" section.

### Per-category logic — additive on purpose

- Classifier categories are mapped to display categories: `wait-timing` and `stability-fix` are combined into "Test Stability & Reliability". `assertion-update` / `bug-annotation-added` / `bug-annotation-removed` / `uncategorized` do NOT get their own category row — bugs roll up into the dedicated **Bug Annotations** row computed from text-deduped descriptions, and `assertion-update` / uncategorized rows don't contribute to any visible total. **`assertion-update` is intentionally uncounted:** adjusting an expected text/count/role assertion is trivial work already baked into the per-fix (30 min) estimate of whatever fix it accompanies — it is not its own time-consuming exercise. The classifier still emits the label so the evidence is preserved, but an assertion-only commit adds nothing to the totals, and a commit that's `assertion-update` + a counted category (e.g. `stability-fix`) still counts once under that other category.
- Per-category `commits` is the number of **unique commit SHAs** with at least one row classified into that category. A commit in multiple categories shows up in multiple rows — that overlap is intentional.
- Per-category `minutes_saved = commits × per_fix_minutes`. `hours_saved` is rounded to the nearest 0.5. `time_saved_display` is the pre-formatted string (`"~10.5 hrs"`, `"~15 hrs"`, `"~1 hr"` — singular special-cased).
- Categories with `commits == 0` are dropped before the JSON is written.

### Grand total — strict sum, no fudge

`total_minutes_saved = sum(category.minutes_saved) + bugs_row.minutes_saved`. `total_change_events = sum(category.commits) + bug_count`. The report's bottom-line `~H hrs` figure is the simple sum of every visible row's Time Saved cell. If the synthesizer's report shows a Total that doesn't equal the column sum, the synthesizer did its own math — that's a defect.

`total_calculation_display` and `total_hours_saved_headline` remain in `metrics.json` for backward compatibility with older report templates, but the current customer-facing report does **not** use either field — the scorecard at the top surfaces `total_hours_saved_display` directly with no parenthetical breakdown, no prose blockquote. Don't add either field back into the report just because they exist in the JSON.

### Standalone math (the pure calculator)

The script's math layer is exposed as a single importable function:

```python
from compute_metrics import calculate_time_saved

calculate_time_saved(
    per_category_commits={"Test Stability & Reliability": 18, "Flow & Step Restructuring": 15, ...},
    bug_count=3,
    per_fix_minutes=30,
    per_bug_minutes=60,
)
# → returns the math half of metrics.json, no file I/O.
```

Useful for ad-hoc what-if analysis ("what if a bug is worth 90 min instead of 60?") without touching a workspace.

### Phase 1.5 gate

After the script exits 0, the parent agent **must** verify:

- [ ] `<workspace>/metrics.json` exists and is valid JSON.
- [ ] `metrics.bugs_found` is plausible — usually single digits to low double digits. If `0` while `bug-annotation-added` rows exist in `classifications.jsonl`, inspect the relevant `.diff` files; the bug-marker regex may have missed an unusual annotation shape. **Fix the script, don't fix the number by hand.**
- [ ] **The math adds up.** Confirm: `sum(metrics.categories[i].minutes_saved) + metrics.bugs_row.minutes_saved == metrics.total_minutes_saved`. If not, the script is broken — fix it before continuing.
- [ ] `metrics.categories` is non-empty (unless all maintenance was bug-annotation-only — flag that as a finding).
- [ ] `metrics.bug_records` has one entry per unique bug, each with a non-empty `description` and `first_test_name`. The synthesizer needs these to render the Bugs Found section.

---

## Phase 2 — Synthesize the maintenance health report

**Dispatch pattern:** one `generalPurpose` synthesizer subagent. The parent then runs **Phase 2.5 lint** directly (no subagent) and either ships, re-dispatches the synthesizer with `lint.json` as structured feedback (max 2 retries), or proceeds to **Phase 2.6 AI review** once the lint is clean. See [Subagent strategy → Reviewer loop](#reviewer-loop-phase-2) for the post-lint reviewer exit conditions.

The synthesizer's prompt **must include the full contents of `metrics.json` and `metadata.json` inlined verbatim as fenced JSON code blocks** (see "Inlining the source-of-truth JSON" below). The synthesizer must NOT be asked to "go read the workspace files" — that's the path that produces transcription typos. The parent agent reads both files into memory, pastes them into the prompt, and the synthesizer copies cell values directly from the inlined JSON.

The synthesizer additionally reads `classifications.jsonl` and `diffs/*.diff` from the workspace (those are too large to inline) for the Healing Examples narrative + code blocks, then writes the **final share-ready markdown report** to:

```
~/Desktop/<customer-slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md
```

(Use `$HOME/Desktop/...` if `~` is not expanded in the agent's shell.) The report must exactly match the template below.

### Inlining the source-of-truth JSON (mandatory)

When the parent agent builds the synthesizer's prompt, it **must** include two fenced JSON blocks at the top of the prompt, each preceded by an explicit "the values inside these blocks are the only acceptable source for the corresponding cells" instruction:

````text
SOURCE OF TRUTH — DO NOT TYPE NUMBERS BY HAND. COPY THEM FROM THESE BLOCKS.

metadata.json (use `metadata.total_test_files_in_suite` for the Tests Maintained scorecard cell):

```json
{ ...verbatim cat metrics.json output here... }
````

metrics.json (every other quantitative cell comes from here):

```json
{ ...verbatim cat metrics.json output here... }
```

````

**Why this matters:** earlier runs had the parent agent re-type per-category names and counts as bullets inside the prompt ("Stability had 18 commits worth ~9 hrs, Flow had 15 commits worth ~7.5 hrs, ..."). That re-spelling is the failure mode — a typo or a transposed value produces a report with numbers that don't trace back to `metrics.json` and the reviewer round-trip catches it 90 seconds later. Inlining the literal JSON eliminates that entire class of bug. The synthesizer's job becomes mechanical: locate the cell in the inlined JSON, paste it into the markdown. No transcription, no math, no judgment about formatting.

The parent agent reads both files with the standard file-read tool (they are small — `metadata.json` is < 1 KB, `metrics.json` < 5 KB) and pastes the full contents into the prompt. **Truncating or summarizing either file in the prompt is forbidden** — the inlined JSON must be byte-identical to the on-disk file so the synthesizer can locate every field by its JSON path.

### The synthesizer does NOT do math

Every quantitative claim in the report comes from `metrics.json`, verbatim. The synthesizer:

- **Does not** count bugs from `classifications.jsonl`.
- **Does not** dedupe bug descriptions, commits, or files.
- **Does not** multiply commit counts by 30 to estimate time saved.
- **Does not** sum per-category numbers to compute the grand total.
- **Does not** round, format, or pluralize hour figures.

If the synthesizer's report contains a number that doesn't appear in `metrics.json`, that's a defect. Re-dispatch with a stricter prompt or rerun `compute_metrics.py` if the data has actually changed.

### Field-by-field mapping (template placeholder → metrics.json field)

| Template placeholder                                            | Source                                                                                                                               |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| At-a-Glance scorecard — **Tests Maintained** cell               | `metadata.total_test_files_in_suite` (HEAD count, lives in `metadata.json`)                                                          |
| At-a-Glance scorecard — **Bugs Found** cell                     | `metrics.bugs_found`                                                                                                                 |
| At-a-Glance scorecard — **Change Events** cell                  | `metrics.total_change_events`                                                                                                        |
| At-a-Glance scorecard — **Engineering Time Saved** cell         | `metrics.total_hours_saved_display` (e.g. `~31 hrs`)                                                                                 |
| `<TOTAL_TEST_FILES>` placeholder (scorecard)                    | `metadata.total_test_files_in_suite`                                                                                                 |
| `<BUGS_FOUND>` placeholder (scorecard + Bugs Found intro prose) | `metrics.bugs_found`                                                                                                                 |
| `<TOTAL_CHANGE_EVENTS>` placeholder (scorecard)                 | `metrics.total_change_events`                                                                                                        |
| `<TOTAL_HOURS_DISPLAY>` placeholder (scorecard)                 | `metrics.total_hours_saved_display`                                                                                                  |
| `<REPORT_DATE_PRETTY>` placeholder (Dated line)                 | `metadata.report_date_pretty` (e.g. `"May 28, 2026"`)                                                                                |
| `<AUDIT_WINDOW_START>` placeholder (Dated line + window cell)   | `metadata.audit_window_start_date` (e.g. `"2026-04-28"`)                                                                             |
| `<AUDIT_WINDOW_END>` placeholder (Dated line + window cell)     | `metadata.audit_window_end_date` (e.g. `"2026-05-28"`)                                                                               |
| `<AUDIT_WINDOW_DAYS>` placeholder (Dated line + window cell)    | `metadata.audit_window_days` (e.g. `30`)                                                                                             |
| Report filename date slug `<YYYY-MM-DD>`                        | `metadata.report_date_iso`                                                                                                           |
| Maintenance Impact category-row Change Events cell              | `metrics.categories[i].commits`                                                                                                      |
| Maintenance Impact category-row Time Saved cell                 | `metrics.categories[i].time_saved_display`                                                                                           |
| Maintenance Impact category-row Description cell                | `metrics.categories[i].description`                                                                                                  |
| Maintenance Impact category-row order                           | order in `metrics.categories` (already sorted by commits desc)                                                                       |
| Maintenance Impact Bug-Annotations-row Change Events cell       | `metrics.bugs_row.commits` (= `metrics.bugs_found`)                                                                                  |
| Maintenance Impact Bug-Annotations-row Time Saved cell          | `metrics.bugs_row.time_saved_display`                                                                                                |
| Maintenance Impact Bug-Annotations-row Description cell         | `metrics.bugs_row.description`                                                                                                       |
| Maintenance Impact Total row Change Events cell                 | `metrics.total_change_events`                                                                                                        |
| Maintenance Impact Total row Time Saved cell                    | `metrics.total_hours_saved_display`                                                                                                  |
| Bugs Found section — one bullet per unique bug                  | iterate `metrics.bug_records` in order; each entry pastes `first_test_name`, `first_date`, `first_short_sha`, `description` verbatim |

If `metrics.bugs_row` is `null` (zero bugs in window):

- Omit the **Bug Annotations** row from the Maintenance Impact table.
- Omit the entire **Bugs Found in Your Application** section — heading and body. The scorecard already shows `0` in the Bugs Found cell; a dedicated "no bugs found" section is filler. Don't fabricate one.

The synthesizer's remaining responsibilities (which DO require AI judgment):

- **Conform to the exact template structure** — section headings (`At a Glance`, `How Checksum AI Agents Work`, `Maintenance Impact`, `Bugs Found in Your Application` (conditional), `Healing Examples`), table column order, scorecard layout, and metadata block must match so reports are comparable across customers. **The report has no Executive Summary section** — the scorecard at the top IS the summary; do not invent narrative prose to summarize what the data already shows.
- Confirm which Checksum identities (of the four) drove the activity, sourced from `aggregates.json → by_identity`, for internal SE awareness. **Do not surface the list in the customer report** — the metadata block no longer contains an "Active Checksum AI agents" row. The "How Checksum AI Agents Work" section already enumerates the agent ecosystem; repeating which were active this window adds noise to a dry report.
- Pick **5–7 representative commits TOTAL** across the entire report (not per category) for the **Healing Examples** section. Quote real before/after code from the `.diff` files. **Do not include a "Files Changed:" line.** The before/after block is the evidence.
  - Choose the strongest examples regardless of category — the most concrete heals, multi-round arcs, app-grounded fixes, and structural improvements. Aim for variety across categories when ties exist, but never pad with weak examples just to "cover" a category.
  - Group the chosen examples under the category sub-heading they belong to, in the same order as the Maintenance Impact table. **Skip any category that didn't produce a chosen example** — don't emit empty sub-headings.
  - The Maintenance Impact table already enumerates every category quantitatively; the examples section's job is to show what a heal looks like in code, not to catalog every commit.
- **No narrative summary, no executive summary, no observations, no smell signals, no concerns block, no closing narrative.** The report is dry by design: scorecard → How it works → Impact table → Bugs (conditional) → Healing Examples → footer. If something operational is genuinely material (e.g. only 1 of 4 identities active and that's notably different from prior windows), drop it from the customer report entirely — it lives in `aggregates.json` for SE follow-up.
- Produce a **self-contained, shareable** markdown file — no `/tmp/` references, no workspace paths, no JSONL leakage, no broken links. The reader of this file should not need to know the skill or workspace existed.
- **Not** write to the customer repo. **Not** create a branch. **Not** commit. **Not** open a PR. Just write the one file to the Desktop and report the path back to the user.

---

## Phase 2.5 — Deterministic lint pass (mandatory before reviewer)

After the synthesizer writes the report, the parent agent runs `lib/lint_report.py` directly. This is a deterministic regex scan that catches the cheapest, highest-confidence violations:

- **Structural:** forbidden section headings, retired formatting (`**Files Changed:**` lines, `## 1.` numbered sections), footer leakage (`_Report dated…_`, `_Questions? Contact your Checksum CSM._`), `/tmp/` path leaks.
- **Bug-annotation context:** REMOVAL language inside the `## Bugs Found in Your Application` section (with verbatim `>` blockquote lines stripped before matching so the lint never false-positives on customer-content bug descriptions).
- **Audit-window cross-check:** the report's `**Dated: <Month D, YYYY>** · Window: last N days of \`main\` (YYYY-MM-DD → YYYY-MM-DD)` header AND the metadata table's `| Audit window | YYYY-MM-DD → YYYY-MM-DD (N days) |` row both have to match `metadata.report_date_pretty`, `metadata.audit_window_start_date`, `metadata.audit_window_end_date`, and `metadata.audit_window_days` byte-for-byte. Mismatch → exit 1 with a specific `audit_window_*_mismatch_*` rule that names the wrong cell and points at the canonical field. This catches the historical bug where the synthesizer pasted `observed_first_commit_date → observed_last_commit_date` into the window cell and under-reported the audit period.

```bash
python3 $HOME/.claude/skills/30-day-healing-analysis/lib/lint_report.py \
  --report "$HOME/Desktop/<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md" \
  --workspace "/tmp/checksum-heals-audit-<slug>"
````

**Exit handling:**

- **Exit 0 (clean):** `lint.json` lists zero violations. Proceed to Phase 2.6 AI reviewer.
- **Exit 1 (dirty):** `lint.json` lists one or more violations. The parent **must re-dispatch the Phase 2 synthesizer** with `lint.json` pasted into the prompt as structured feedback (alongside the original `metrics.json` and `metadata.json` blocks) — instruct the agent to fix every listed violation and re-write the report at the same path. After the rewrite, re-run the lint. **Max 2 retries.** If still dirty after the second retry, ship the report as-is and tell the user which violations couldn't be auto-fixed — but do NOT dispatch the AI reviewer (the reviewer can only catch what the lint already caught, plus more — there's no point burning a reviewer call when known violations remain).

**Why this exists:** the AI reviewer is the right tool for catching subjective issues (weak commit-example selection, awkward category labels, narrative drift) but the wrong tool for catching pure-regex issues like "did you leave `## Executive Summary` in the report?". The lint runs in ~50 ms, the reviewer takes 30–90 seconds and burns one subagent call. Catching mechanical violations in the lint saves roughly 1 minute and 1 agent dispatch per occurrence.

**What the lint checks** (full list lives in `lib/lint_report.py`, source of truth):

- **Forbidden section headings** (`Executive Summary`, `Overview`, `Summary by Category`, `Maintenance Hotspots`, `Most-Touched Utility Files`, `Commit Timeline`, `Bug Annotation Ledger`, `Smell Signals`, `Observations`, `Concerns`, `Findings`, `Methodology`, `Appendix`, `Detailed Commit Breakdown` [retired name; must be `Healing Examples`], `Bug Annotations & Tagging`). Case-insensitive, matches `## X` / `### X` / numbered variants like `## 1. X`.
- **Numbered section headings** (`## 1.`, `## 2.`, etc.) — sections use plain titles only.
- **`**Files Changed:**` lines** — retired forensics format.
- **Footer leakage** — `_Report dated…_` and `_Questions? Contact your Checksum CSM._` lines anywhere in the report.
- **`/tmp/checksum-heals-audit-` paths** leaking into the customer deliverable.
- **Bug-annotation removal vocab** — inside the `## Bugs Found in Your Application` section ONLY, with `>` blockquote lines stripped first: `closed`, `removed`, `reopened`, `re-enabled`, `net delta`, `resolved`. This catches the synthesizer editorializing about bug-removal events while letting verbatim bug descriptions ("the modal closed unexpectedly") pass through unscathed.

If a check needs to be added or removed, edit `lib/lint_report.py` — the SKILL doc lists the categories but the script is the binding contract.

---

## Phase 2.6 — AI reviewer (runs only after Phase 2.5 is clean)

Dispatch ONE `generalPurpose` reviewer subagent that reads `<workspace>/lint.json` (must be `status: "clean"` — otherwise the lint loop above wasn't completed), the just-written report, and the customer-facing checklist embedded in this skill, and scores the report `Excellent` / `Good` / `Needs work`. See [Subagent strategy → Reviewer loop](#reviewer-loop-phase-2) for the post-review exit conditions and the synthesizer-feedback dispatch pattern.

---

## Phase 2.7 — Append the lifetime product-metrics digest

> Data access for this phase has been removed from the public skeleton. `lib/customer_report.py` now only prints a decommission notice; it keeps the section's rendering shape for reference.

After the report file existed on the Desktop and (for non-dormant runs) the reviewer scored it `Good`/`Excellent`, a deterministic script appended **Part 2** — lifetime product metrics from the test platform (no AI math, same philosophy as Phase 1.5).

It appended a `---` separator and a `## Lifetime Testing Metrics — Checksum AI` section: a 3-cell table (Total Tests Generated · Total Test Runs · Total Bugs Found) plus the bug list **grouped by word-for-word description** — each distinct issue listed once with the affected test IDs nested beneath it. Notes:

- **Exact customer match only** — name variants were never guessed.
- **Idempotent** — re-running replaced an existing Part 2 rather than duplicating it.
- **Ran for dormant reports too** — even with no git maintenance, the lifetime digest still added value.
- **Lint-safe** — the appended section introduced no forbidden headings, footers, or `/tmp/` paths.
- **Never fabricated** — if the platform was unreachable, Part 1 shipped alone and the user was told Part 2 was skipped.

## Phase 3 — Post-flight cleanup (mandatory)

Once the report has been written to `~/Desktop/`, the reviewer has scored it `Good` or `Excellent` (or, for dormant runs, the Dormant report has been written and acknowledged in the chat), **and** the path has been reported back to the user, the agent MUST clean up the scratch workspace from `/tmp/`. The customer-facing deliverable is the Desktop report; everything in `/tmp/` (including `metadata.json`, `metrics.json`, `classifications.jsonl`, `lint.json`, `review.md`, and the `diffs/` directory) is throwaway.

```bash
python3 $HOME/.claude/skills/30-day-healing-analysis/lib/collect.py \
  --slug "<customer-slug>" --cleanup
```

This deletes `/tmp/checksum-heals-audit-<slug>/` (and all artifacts inside it) and exits. Safe to run even if the workspace is already gone (it just reports `removed: false`). Dormant runs still need cleanup — the Phase 0 workspace contains the same metadata/scope/diffs even when no commits matched the author filter.

### When to skip cleanup

Skip Phase 3 **only** if one of the following is true:

- The reviewer scored "Needs work" on the final pass AND the user asked to see the workspace for debugging.
- Phase 2.5 lint reported violations that the synthesizer couldn't auto-fix within the 2-retry budget AND the user asked to inspect `lint.json` for the unresolved issues.
- The user explicitly said "leave the workspace in place" earlier in the conversation.

In every other case, cleanup is mandatory. Confirm the cleanup ran by checking that the printed JSON has `"mode": "cleanup"` and `"removed": true`.

### Optional: nuke prior runs from other customers

If the user mentions that prior audits have left workspaces behind (or you see `/tmp/checksum-heals-audit-*` directories that don't belong to the current run), offer to run:

```bash
python3 $HOME/.claude/skills/30-day-healing-analysis/lib/collect.py --cleanup-all
```

This nukes every `/tmp/checksum-heals-audit-*` workspace AND the legacy `/tmp/checksum_heals_collect.py` script copy (left behind by older versions of this skill that wrote the script to `/tmp/` per run). Ask before running this — it's destructive across all customers.

---

## Per-agent prompt skeleton

Pass absolute paths — agents have no conversation context. Subagents read from the Phase 0 workspace; they never run git themselves.

There are three distinct prompt variants depending on the subagent's role:

1. **Phase 1 classifier** — reads a row slice, writes a JSONL shard. (Default skeleton below.)
2. **Phase 2 synthesizer** — receives `metadata.json` + `metrics.json` **inlined as JSON code blocks** at the top of the prompt (the parent agent reads them and pastes them in verbatim), plus the workspace path for `classifications.jsonl` + `diffs/*.diff`. Writes the report. (Variant after the classifier skeleton.)
3. **Phase 2.6 reviewer** — reads the just-written report, writes a scored review. (Variant at end of this section.)

### Classifier skeleton

```
Phase <1|2> of /30-day-healing-analysis for <Customer Repo Name>.

CONTEXT: Playwright (JS/TS) test suite. We are auditing the last 30 days of
`main` branch git history for MAINTENANCE activity by CHECKSUM AUTOMATION on
EXISTING test-suite files (specs, page objects, helpers, utilities, fixtures).
Phase 0 has already been completed by `checksum_heals_collect.py`. All raw
data lives in the workspace described below — DO NOT re-run git, DO NOT
re-build scope. Just classify what you're given.

WORKSPACE (READ ONLY): <absolute path, e.g. /tmp/checksum-heals-audit-acme-corp/>
Files you will use:
  metadata.json         — customer, repo, head sha, active identities,
                          total_test_files_in_suite (HEAD spec count),
                          audit_window_start_date / audit_window_end_date /
                          audit_window_days (the CANONICAL audit window —
                          computed deterministically by lib/audit_window.py,
                          paste verbatim into the "Audit window" cell),
                          report_date_pretty (for the "Dated:" line),
                          report_date_iso (for the Desktop filename slug)
  scope.json            — list of files in scope (already filtered)
  aggregates.json       — hotspots, by_identity, weekly_activity, noise_candidates
  commits.jsonl         — one row per (commit, file) pair you must classify
  diffs/<sha>__<file>.diff — actual diff content (path is in each commits.jsonl row)
  metrics.json          — Phase 2 ONLY. Source of truth for ALL numbers in the report.
                          Synthesizer pastes its values verbatim and does NO arithmetic.

YOUR SLICE (Phase 1 only): rows <start>..<end> of commits.jsonl

YOUR JOB:
<phase-specific instructions here>

CATEGORIES (must match exactly):
- locator-change
- flow-change
- bug-annotation-added
- bug-annotation-removed
- wait-timing
- assertion-update
- stability-fix
- data-fixture
- framework-upgrade
- uncategorized

OUTPUT FORMAT (Phase 1): append JSONL to <workspace>/classifications.jsonl,
one row per (commit, file) pair, schema:
  {
    "commit": "<full sha>",
    "short_sha": "<7-char>",
    "date": "<ISO date>",
    "author": "<one of the four Checksum identities>",
    "file": "<repo-relative path>",
    "categories": ["<one or more from list above>"],
    "evidence": ["<quoted diff line>", "..."],
    "isNoise": <bool>,
    "noiseReason": "<string or null>"
  }

OUTPUT FORMAT (Phase 2): single markdown report at
  ~/Desktop/<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md
  matching the Report Template exactly.

RULES:
- DO NOT re-run git. The script already did. If you think you need git, you don't.
- DO NOT change the author allowlist. The script enforces it.
- DO NOT label a diff as a category without a quoted diff line as evidence.
- Page-object / helper / utility / fixture diffs are first-class maintenance.
  Classify them the same way as spec diffs.
- Whitespace/lint-only diffs → isNoise: true, with noiseReason. Cross-reference
  aggregates.json → noise_candidates for hints.
- Multi-label per row is fine and encouraged when the diff genuinely spans
  multiple categories.
- Never invent categories outside the list above.

Report: <what the agent must hand back>
```

### Synthesizer skeleton (Phase 2)

The parent agent reads `metadata.json` and `metrics.json` into memory and pastes them VERBATIM inside the fenced JSON blocks below. **Do not summarize, truncate, or re-spell either file** — the synthesizer copies cell values directly from these blocks instead of being asked to "go read the workspace files", which is the path that produces transcription typos. Use this skeleton for fresh synthesizer dispatches AND for re-dispatches triggered by Phase 2.5 lint failures or Phase 2.6 reviewer feedback (re-paste both JSON blocks every time — never assume the synthesizer remembers prior context).

````
Phase 2 of /30-day-healing-analysis for <Customer Repo Name>.

ROLE: synthesizer. Write the customer-facing maintenance health report.

==============================================================================
SOURCE OF TRUTH — DO NOT TYPE NUMBERS BY HAND. COPY THEM FROM THE TWO JSON
BLOCKS BELOW.

The two blocks below are byte-for-byte copies of <workspace>/metadata.json and
<workspace>/metrics.json. Every quantitative cell in the report maps to a
specific field in one of these blocks — see the field-mapping table in the
skill. If a number you're about to write does not appear inside one of these
blocks, STOP — you are doing forbidden arithmetic.
==============================================================================

metadata.json (Tests Maintained scorecard cell, customer/repo/branch/window
metadata-table rows):

```json
<verbatim contents of <workspace>/metadata.json, pasted by the parent agent>
```

metrics.json (Bugs Found / Change Events / Engineering Time Saved scorecard
cells, all Maintenance Impact table cells, Bugs Found section bullets):

```json
<verbatim contents of <workspace>/metrics.json, pasted by the parent agent>
```

==============================================================================
WORKSPACE (READ ONLY): <absolute path, e.g. /tmp/checksum-heals-audit-acme/>
Files the synthesizer reads from disk (too large to inline):
  classifications.jsonl — one row per (commit, file) you may cite as a Healing
                          Example. Each row has `categories`, `evidence`, and
                          the diff file's path.
  diffs/<sha>__<file>.diff — actual diff content for any commit you cite. Quote
                             real before/after code from these — never invent.

(metadata.json and metrics.json are also on disk at the workspace path, but
prefer the inlined blocks above for cell values to eliminate transcription
risk. The on-disk copies are the source of truth IF the inlined block looks
truncated or malformed — in that case, abort and ask the parent to re-paste.)
==============================================================================

OUTPUT: write a single markdown file to
  ~/Desktop/<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md
matching the "Report template" section of the skill EXACTLY:

  ## At a Glance (4-cell scorecard + 4-row metadata table — no prose blockquote)
  ## How Checksum AI Agents Work
  ## Maintenance Impact (table from metrics.categories + Bug Annotations row + Total)
  ## Bugs Found in Your Application (ONLY when metrics.bugs_found > 0)
  ## Healing Examples (5–7 representative commits TOTAL — not per category)

NO Executive Summary, NO Observations, NO closing footer, NO numbered headings,
NO Files Changed lines, NO "Active Checksum AI agents" / "Test framework" rows
in the metadata table.

PRIOR-PASS FEEDBACK (paste verbatim when re-dispatching after a lint/reviewer
failure; leave blank on the first pass):
  <empty on first pass>
  <on retry: paste lint.json violations + reviewer.md gaps verbatim here. Fix
   EVERY listed item before re-writing the file at the same path.>

RULES:
- DO NOT do arithmetic. Every number comes from the inlined JSON blocks above.
- DO NOT re-spell category names — copy them from `metrics.categories[i].label`.
- DO NOT add sections that aren't in the template (Executive Summary,
  Observations, Smell Signals, Concerns, Findings, Methodology, Appendix — all
  forbidden; the Phase 2.5 lint will reject the report if any appear).
- DO NOT include `**Files Changed:**` lines under Healing Examples — the
  before/after code IS the evidence.
- DO NOT add a `_Report dated…_` or `_Questions? Contact your Checksum CSM._`
  footer — the report ends with the last Healing Example.
- DO NOT narrate bug-annotation REMOVALS in the Bugs Found section. Verbatim
  bug descriptions in `> blockquotes` are fine; synthesizer prose mentioning
  "closed", "removed", "resolved", "reopened", "re-enabled", or "net delta"
  near a bug annotation is an auto-fail.

Report back: the absolute path to the file you wrote.
````

### Reviewer skeleton (Phase 2.6 only)

Use this when dispatching the Phase 2 reviewer subagent.

````
Phase 2 REVIEW pass <N> of /30-day-healing-analysis for <Customer Repo Name>.

YOUR ROLE: review-only. You are NOT classifying or rewriting the report.
You read the just-written report and score it against the template + checklist.

INPUTS (READ ONLY):
  REPORT:            <absolute path to the .md file on Desktop>
  WORKSPACE:         <absolute path to the workspace dir>
  LINT:              <workspace>/lint.json (must be status: "clean" — if it
                     shows violations, the parent skipped the lint loop; reject
                     the dispatch and tell the parent to re-run lint_report.py)
  METRICS:           <workspace>/metrics.json (the source of truth for ALL
                     numbers; ALSO inlined verbatim as a JSON code block below
                     so you can cross-check scorecard cells without leaving the
                     prompt)
  METADATA:          <workspace>/metadata.json (the source of truth for the
                     Tests Maintained scorecard cell and customer/repo/branch/
                     window metadata; ALSO inlined verbatim below)
  TEMPLATE & RULES:  <verbatim "Report template" section from the skill>
  CHECKLIST:         <verbatim "Anti-laziness checklist" section from the skill>

INLINED metadata.json:

```json
<verbatim contents pasted by the parent agent>
```

INLINED metrics.json:

```json
<verbatim contents pasted by the parent agent>
```

YOUR JOB:
1. Read the report end-to-end.
2. Score it against the template (structure conformance, all sections present,
   table column order correct, etc.) and against the anti-laziness checklist.
3. For each unchecked checklist item, cite the specific gap with file + line.
4. Spot-check 3 random Before/After code blocks against the underlying `.diff`
   files in <workspace>/diffs to confirm the quoted code is real, not paraphrased.
5. **Cross-reference every number in the report against `metrics.json`.** Any
   number in the report that doesn't match the corresponding metrics.json field
   is an auto-fail (synthesizer did unauthorized math). See "CUSTOMER-FACING
   CHECKS" below for the exact field mapping.
6. Decide a single overall score: Excellent | Good | Needs work.

CUSTOMER-FACING CHECKS (auto-fail if any of these are violated):
- Report has the customer-PDF-style title: `# Checksum AI Agentic Output — <Customer>`
  followed by `## Commit History Analysis: Test Suite Maintenance`.
- **The report has NO Executive Summary section.** No `## Executive Summary`, no
  `## 1. Executive Summary`, no narrative summary paragraph anywhere. The scorecard
  IS the summary. If the synthesizer added prose to "set up" the data, auto-fail.
- The At-a-Glance section is a **scorecard table with exactly four cells in a single
  row**, headed `Tests Maintained | Bugs Found | Change Events | Engineering Time
  Saved`, followed by a small two-column metadata block. NO prose blockquote
  headline, NO intro paragraph above the scorecard, NO narrative sentence framing
  the numbers — the four numbers stand on their own.
- **Numbers in the report match the source of truth exactly.** Spot-check at minimum:
    • At-a-Glance scorecard **Tests Maintained** cell == `metadata.total_test_files_in_suite`
    • At-a-Glance scorecard **Bugs Found** cell == `metrics.bugs_found`
    • At-a-Glance scorecard **Change Events** cell == `metrics.total_change_events`
    • At-a-Glance scorecard **Engineering Time Saved** cell == `metrics.total_hours_saved_display`
    • each Maintenance Impact category row's Change Events cell == `metrics.categories[i].commits`
    • each Maintenance Impact category row's Time Saved cell == `metrics.categories[i].time_saved_display`
    • Bug Annotations row's Change Events cell == `metrics.bugs_row.commits` (= `metrics.bugs_found`)
    • Bug Annotations row's Time Saved cell == `metrics.bugs_row.time_saved_display`
    • Total row's Time Saved cell == `metrics.total_hours_saved_display`
  If any of these disagree with the source, this is an auto-fail — the synthesizer
  did its own math (forbidden), used wrong fields, or the script wasn't rerun after
  Phase 1 changed.
- **The Maintenance Impact table's math adds up.** Sum the Time Saved column for
  every category row plus the Bug Annotations row (if present) — the result must
  equal the Total row's Time Saved cell exactly. If not, auto-fail.
- **The "Bugs Found in Your Application" section is conditional.** When
  `metrics.bugs_found > 0`, the heading is present AFTER `Maintenance Impact` and
  BEFORE `Healing Examples`, with one bullet per `metrics.bug_records` entry. When
  `metrics.bugs_found == 0`, the heading and body are OMITTED ENTIRELY — no
  placeholder line, no "no bugs found this window" sentence. The scorecard `0` is
  the answer.
- **The report NEVER mentions bug-annotation removals.** No language like "the bug
  was reopened/closed/removed/re-enabled", no commit examples showing a `@bug` tag
  being deleted, no "net delta" of annotations opened vs closed. Removals are
  Checksum closing out resolved work — they are not value-prop content. The
  classifier still tracks `bug-annotation-removed` internally, but it never
  surfaces in the customer report.
- The metadata table (below the scorecard) includes EXACTLY these four rows in
  this order: Customer, Repository, Branch, Audit window. NO "Test framework" row
  (Playwright is implicit in the audit's existence and is already named in the
  "How Checksum AI Agents Work" section), NO "Active Checksum AI agents" row (the
  ecosystem table in "How Checksum AI Agents Work" already enumerates the four
  identities), NO "Generator", "Human-authored commits (excluded)", "Author scope
  (Checksum identities only)", "Author-filter leaks", "Noise commits", "Existing
  test files maintained" (the legacy windowed count), "Total maintenance edits",
  "Maintenance commits", "Bugs found by Checksum", "Maintenance change events",
  "Estimated engineering hours saved", or "Total test files in suite" rows — the
  scorecard already surfaces the value-prop numbers, so duplicating them in the
  metadata block adds noise.
- "How Checksum AI Agents Work" appears as a top-level section IMMEDIATELY AFTER
  At-a-Glance. Customers who don't know how Checksum works need this context before
  any data.
- The next section is "Maintenance Impact" — a table with columns
  Category | Change Events | Time Saved | Description, ending with a Bug Annotations
  row (only when bugs > 0) and a bold **Total** row. NO "Summary by Category"
  header anywhere.
- NO sections titled "Executive Summary", "Maintenance Hotspots", "Most-Touched
  Utility Files", "Commit timeline", "Bug annotation ledger", "Smell signals",
  "Observations", "Methodology", "Appendix A", or "Appendix B".
- "Bug Annotations & Tagging" does NOT appear as a sub-section in the Healing
  Examples — bug content is fully covered by the dedicated Bugs Found section.
- The last main section is named **`## Healing Examples`** (NOT "Detailed Commit
  Breakdown" — that name is retired). It uses ```ts / ```js Before/After code
  blocks — NOT ```diff fences with +/- prefixes.
- Each commit entry under Healing Examples has: bold commit subject in backticks,
  italics identity, 1–2 sentence narrative, before/after code block. **NO "Files
  Changed:" line** — that's internal forensics, not customer-facing value.
- **The report has at most 5 main sections** (At a Glance → How Checksum AI Agents
  Work → Maintenance Impact → Bugs Found in Your Application [conditional] → Healing
  Examples) and ZERO numbered headings. No `## 1.`, no `## 4.`, no closing
  narrative section of any kind.
- **The report has NO footer.** It ends with the last example in the Healing
  Examples section. No `_Report dated…_` line, no `_Questions? Contact your
  Checksum CSM._` line, no horizontal rule trailing the last example. The dated
  line at the top of the report (`**Dated: <Month DD, YYYY>**` under the H2) is
  sufficient — repeating the date at the bottom is noise. Auto-fail if any closing
  italicized line is present.

OUTPUT: write a markdown review to <workspace>/review.md with this shape:

  # Phase 2 Review — pass <N>

  **Overall:** Excellent | Good | Needs work

  ## Strengths
  - <bullet>
  - <bullet>

  ## Gaps
  - <bullet citing specific section / line / claim>
  - <bullet>

  ## Required fixes before next pass (if Needs work)
  1. <actionable>
  2. <actionable>

  ## Evidence sampling
  - Sample 1: claim "<short quote from report>" — verified against <diff path>. PASS|FAIL.
  - Sample 2: ...
  - Sample 3: ...

RULES:
- DO NOT edit the report. Reviewer is read-only on the deliverable.
- DO NOT lower your standards across passes. The exit-conditions ladder
  (Excellent → Good → ship anything) is the PARENT'S decision, not yours.
  You score honestly each time.
- DO NOT score "Excellent" if any anti-laziness checklist box is unchecked.
- Spot-checking the evidence is mandatory. A report with fabricated quoted
  diffs is "Needs work" no matter how polished it looks.
````

---

## Report template

The Phase 2 agent writes the report to `~/Desktop/<customer-slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md`. Below is the exact template — copy it verbatim, replacing every `<placeholder>` and `N`. **Do not add sections, do not rename sections, do not change column order.**

### Customer-facing rules

This report goes to the **customer** as a value-prop artifact — its purpose is to make Checksum's automated maintenance value visible and quantifiable. Therefore:

- **Lead with the four headline numbers.** The first thing the reader sees after the title is a **scorecard table** with four cells in one row: `Tests Maintained | Bugs Found | Change Events | Engineering Time Saved`. No prose, no blockquote, no intro sentence — the numbers stand alone.
- **Dry, not narrative.** This report is data, not storytelling. No Executive Summary, no closing Observations, no "the agents grounded their fixes in app truth" prose paragraphs. Headings, tables, bulleted bug descriptions, and before/after code blocks — that's it.
- **Numbers are the spine.** Tests maintained, bugs found, change events, hours saved, per-category breakdown — every quantitative claim is grounded in `metrics.json` / `metadata.json` and shown to the reader.
- **Education before data.** "How Checksum AI Agents Work" sits BEFORE the Maintenance Impact table because customers reading this cold often don't know the architecture, and the impact numbers don't land without that context.
- **No internal language.** Never mention "the skill", "the workspace", "human-authored commits (excluded)", "filter leaks", "noise candidates", JSONL, scratch files, `/tmp/`, or anything that exposes how the report was produced.
- **No deficit framing.** No "smell signals" section, no "concerns" section, no "observations" section, no "executive summary". If something operational is genuinely material (lint silent, identity concentration, quiet stretches), drop it from the customer report entirely — it lives in `aggregates.json` for SE follow-up.
- **No operational forensics.** No "commit timeline" weekly-bucket table, no "bug annotation ledger" table, no "Maintenance Hotspots" file-by-file ranking, no "Most-Touched Utility Files" appendix, no "Methodology" appendix, no "Observations" closing block, no "Executive Summary" opening paragraph. These are SE-debugging artifacts or filler, not customer deliverables.
- **No "Files Changed:" lines.** The before/after code block IS the evidence. File-path enumeration is internal forensics — drop it from every commit entry in the Healing Examples section.
- **The Bugs Found section is conditional.** When `metrics.bugs_found > 0`, the section sits between Maintenance Impact and Healing Examples with one bullet per unique bug description. When `bugs_found == 0`, the heading and body are OMITTED ENTIRELY — the scorecard `0` is the answer; don't pad with a "no bugs found" placeholder.

The outer fence below uses a quad-backtick so the inner `ts / `js code fences render correctly. The agent should emit plain markdown, not a fenced block.

````markdown
# Checksum AI Agentic Output — <Customer Name>

## Commit History Analysis: Test Suite Maintenance

**Dated: <REPORT_DATE_PRETTY>** · Window: last <AUDIT_WINDOW_DAYS> days of `main` (<AUDIT_WINDOW_START> → <AUDIT_WINDOW_END>)

---

## At a Glance

|    Tests Maintained    |    Bugs Found    |       Change Events       |  Engineering Time Saved   |
| :--------------------: | :--------------: | :-----------------------: | :-----------------------: |
| **<TOTAL_TEST_FILES>** | **<BUGS_FOUND>** | **<TOTAL_CHANGE_EVENTS>** | **<TOTAL_HOURS_DISPLAY>** |

|              |                                                                      |
| :----------- | :------------------------------------------------------------------- |
| Customer     | <Customer Name>                                                      |
| Repository   | `<org/repo>`                                                         |
| Branch       | `main` @ `<short-sha>`                                               |
| Audit window | <AUDIT_WINDOW_START> → <AUDIT_WINDOW_END> (<AUDIT_WINDOW_DAYS> days) |

---

## How Checksum AI Agents Work

Checksum AI Agents are continuous, cloud-based automation that maintains your Playwright test suite without engineer input. They run on a daily schedule, observe every test in real time, and act when a failure occurs — analyzing the root cause, applying a fix, and committing it to your repository for review.

### How it works

1. **Daily scheduled regression testing.** Your test suite runs on a daily schedule in the cloud. Every test is monitored in real time.
2. **Real-time flakiness detection.** During the run, if a failure occurs, an AI agent wakes up immediately to analyze the failure, determine the root cause, and take corrective action so the suite can continue.
3. **Post-run analysis & suite updates.** After the run finishes, agents review the full results. If failures persist, agents update the test suite or open a `@bug` annotation against the application. Every change is systematic and traceable.

### The agent ecosystem

| Identity                                  | Role                                                                                                   |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `checksum-ai`                             | Primary maintenance agent — locator updates, wait tuning, flow restructuring                           |
| `Checksum AI Agent`                       | Complex / multi-round heals where the primary agent could not auto-recover                             |
| `checksum-ai-test-suite-integration[bot]` | Lifecycle bot — opens `@bug` annotations on persistent failures, removes them once the fix is verified |
| `checksum-lint`                           | Linting and small-style fixes; framework-level normalizations                                          |

### Version control & transparency

All agent changes are pushed as **Pull Requests** to your repository, stored as JavaScript / TypeScript code in the Playwright framework, and fully reviewable. Engineers retain final approval authority — every change goes through your normal review process. This report is one such audit.

---

## Maintenance Impact

Fixes are valued at **30 min** each (the human time to reproduce, diagnose, patch, and re-verify a Playwright failure). Bug annotations are valued at **60 min** each (investigate, isolate, write up, route).

| Category                                          | Change Events | Time Saved | Description                                                                |
| ------------------------------------------------- | ------------: | ---------: | -------------------------------------------------------------------------- |
| _<one row per `metrics.categories[i]`, in order>_ |             N |     ~N hrs | _from `metrics.categories[i].description`_                                 |
| **Bug Annotations**                               |             N |     ~N hrs | Unique product bugs Checksum identified and tracked via `@bug` annotations |
| **Total**                                         |         **N** | **~H hrs** | Engineering hours that did **not** come out of your team's budget          |

> Cells sum exactly to the Total row. A commit classified into two categories (e.g. both a locator update and a stability fix) is counted in both rows — each represents distinct human-review effort that would have been required.

---

## Bugs Found in Your Application

<EMIT THIS ENTIRE SECTION (heading included) **only when `metrics.bugs_found > 0`**. When the count is zero, OMIT the heading and the body completely — the scorecard already shows `0` and the customer doesn't need a "no bugs" placeholder. When non-zero, render the short intro sentence below and then one bullet per row in `metrics.bug_records`, in the order they appear in the JSON. DO NOT mention bug annotations that were REMOVED — those reflect Checksum closing out an issue and are not value-prop content for this report.>

Checksum identified **<BUGS_FOUND>** unique product bug(s) during this window and annotated the corresponding test(s) with a `@bug` tag so the failure is tracked transparently rather than silently skipped.

- **`<bug_records[i].first_test_name>`** _(first observed <bug_records[i].first_date>, commit `<bug_records[i].first_short_sha>`)_
  > <bug_records[i].description>

---

## Healing Examples

<Pick **5–7 representative commits TOTAL across the whole section** (not per category) — the strongest, most concrete heals from the window. The Maintenance Impact table above already covers the full scope quantitatively; this section's job is to show the customer what a Checksum heal actually looks like in code. Group the chosen examples under the category sub-heading they belong to, in the same order as the Maintenance Impact table, and skip any category that didn't produce a chosen example (don't emit empty sub-headings). For each commit:>
<- The actual commit-message subject as a bold heading (verbatim, in backticks).>
<- The Checksum identity that authored it, in italics.>
<- A 1–2 sentence narrative description of the change — what changed and why it mattered.>
<- A `// Before` / `// After` code block showing the meaningful change.>
<DO NOT include a "Files Changed:" line. DO NOT enumerate paths. The before/after code is the evidence; file paths are an internal detail.>

<The skeleton below shows the SHAPE of one example so the formatting is unambiguous. The actual report has only 5–7 examples TOTAL, not one per category. Most categories will have 0 or 1 examples; one or two of the most active categories may have 2. Categories that did not produce a chosen example are OMITTED ENTIRELY — no empty sub-headings.>

### <Category Name from `metrics.categories[i].label` — only include if at least one chosen example falls in this category>

**`<commit subject from git log>`** · _<Checksum identity>_

<One- or two-sentence narrative description of the change and why it mattered.>

```ts
// Before
this.autocompleteItems = page.locator(".tt-suggestion");

// After
this.autocompleteItems = page.locator('[role="listbox"] [role="option"]');
```

---

<Repeat the example block above for each chosen commit, grouped under its category sub-heading. Total across the entire section: 5–7 examples. No more.>
````

### Formatting rules for the generated report

The agent producing the final report **must** follow these rules so the file is customer-share-ready out of the box:

**Customer-facing voice:**

- **The audience is the customer**, not Checksum's SE team. Read every sentence and ask "would I send this to my customer?"
- **Never reference how the report was produced** — no mentions of "the skill", "the workspace", "Phase 0", "the classifier", "the synthesizer", "subagents", "JSON files", or anything that exposes the pipeline.
- **Do NOT include** "Generator: 30-day-healing-analysis skill", "Human-authored commits (excluded by design)", "Author-filter leaks", "Noise candidates flagged", or any other forensic / pipeline artifact in the metadata table.
- **No "Smell signals" / "Concerns" / "Observations" / "Executive Summary" section.** Material operational signals are dropped from the customer-facing report entirely (there is no narrative section to absorb them) and live only in `aggregates.json` for SE follow-up. If the SE wants to flag something to the customer, that goes in the chat / call wrapping the report — not in the report itself.
- **No "Commit timeline" weekly-bucket table, no "Bug annotation ledger" table, no "Maintenance Hotspots" table, no "Most-Touched Utility Files" section, no "Methodology" appendix, no "Observations" closing block.** These are SE-debugging artifacts.

**Visual / structural:**

- **Title format follows the customer PDF** — `# Checksum AI Agentic Output — <Customer>` then `## Commit History Analysis: Test Suite Maintenance` as the H2 right under it.
- **At-a-Glance opens with a four-cell scorecard table** (`Tests Maintained | Bugs Found | Change Events | Engineering Time Saved`), followed by a small two-column metadata block containing EXACTLY four rows: Customer, Repository, Branch, Audit window. NO prose blockquote, NO intro sentence, NO narrative framing.
- **The metadata block does NOT include "Test framework" or "Active Checksum AI agents".** Playwright is implicit in the audit's existence and is already mentioned in "How Checksum AI Agents Work"; the four identities are enumerated in that section's ecosystem table. Repeating either in the metadata block adds noise.
- **The metadata block does NOT duplicate scorecard numbers.** No "Bugs found by Checksum" row, no "Maintenance change events" row, no "Estimated engineering hours saved" row, no "Total test files in suite" row, no "Existing test files maintained" (the legacy windowed count), no "Total maintenance edits". Those four numbers are already in the scorecard; repeating them adds noise.
- **The report has NO Executive Summary.** No `## Executive Summary`, no `## 1. Executive Summary`, no narrative summary paragraph. The scorecard IS the summary.
- **The report has NO numbered section headings.** Use plain H2 titles: `## At a Glance`, `## How Checksum AI Agents Work`, `## Maintenance Impact`, `## Bugs Found in Your Application` (conditional), `## Healing Examples`. No `## 1.`, `## 2.`, `## 3.`, `## 4.` prefixes.
- **"How Checksum AI Agents Work" appears immediately after At-a-Glance.** NOT as an Appendix at the bottom.
- **"Maintenance Impact" replaces "Summary by Category"** — same kind of table, but with a `Time Saved` column and a bold **Total** row showing total commits and `~H hrs`. Do not call this section "Summary by Category".
- **"Bugs Found in Your Application" is conditional.** Heading and body appear ONLY when `metrics.bugs_found > 0`, positioned between Maintenance Impact and Healing Examples. When zero, omit the entire section.
- **The last main section is `## Healing Examples`** (the old name "Detailed Commit Breakdown" is retired). Group commits by category in the same order as the Maintenance Impact table. Each commit entry has: the actual git-log subject as a bold heading in backticks, the Checksum identity in italics, a 1–2 sentence narrative description, and a `// Before` / `// After` TypeScript fenced code block (use `js` for `.js` files). **DO NOT include a `**Files Changed:**` line.**
- **No "Bug Annotations & Tagging" sub-section** in the Healing Examples — bug data is consolidated into the dedicated Bugs Found section and the scorecard.
- **Code blocks** use plain `ts or `js fences with `// Before` and `// After` comments — NOT ```diff fences. The customer PDF shows code inline, not git diff format.
- **The report ends with the last commit example in Healing Examples — NO footer.** No `_Report dated…_` line, no `_Questions? Contact your Checksum CSM._` line, no italicized closing sentence, no trailing horizontal rule, no Executive Summary, no appendices, no Observations / Smell signals / Concerns block, no closing narrative section of any kind. The dated line at the top of the report is sufficient.
- **All tables right-align numeric columns** (`|---:|`).
- **All commit SHAs in backticks** (`` `a1b2c3d` ``), trimmed to 7 characters.
- **All file paths in backticks** (`` `tests/checkout.spec.ts` ``), repo-relative.
- **No `/tmp/` paths** in the final report.
- **No emojis** unless the customer's own brand uses them.
- **No external links** that require auth, unless the user explicitly configured a GitHub base URL.
- **Customer name spelled correctly** — verify against the user's prior message; do not abbreviate.

### Optional: link commits to GitHub

If — and only if — the user provides a GitHub base URL (e.g. `https://github.com/<org>/<repo>`), enrich every commit SHA reference in the report with a markdown link:

```markdown
[`a1b2c3d`](https://github.com/<org>/<repo>/commit/a1b2c3d)
```

Do not guess the URL. Ask via `AskQuestion` if it isn't provided.

---

## Anti-pattern reference — lazy thought → real fix

### ❌ "There are 47 commits, that's plenty — call it maintained"

**Fix:** 47 commits could be 1 author renaming imports across the suite. Read the categories distribution. If 90% are `noise` or `uncategorized`, the suite is **not** being maintained — it's being touched by mass refactors.

### ❌ "I'll include the new .spec.ts files too, they're test files"

**Fix:** The user was explicit: **ignore new files**. New authoring ≠ maintenance. A team can ship 30 new tests and never touch the old ones — that's a leading indicator of rot, not health. Track new files only in the "context" section.

### ❌ "test.skip was added — that's bad maintenance"

**Fix:** Adding `test.skip` IS maintenance activity — the team noticed a broken test and triaged it. It's a _worse_ signal than a fix, but it's a real signal. Don't conflate "skip added" with "no maintenance." The smell is `test.skip` added with **no follow-up commit removing it** within the window.

### ❌ "I'll just count lines changed"

**Fix:** Lines changed is dominated by formatter runs, import shuffles, and dependency bumps. Classify the _intent_ of the diff, not its size.

### ❌ "The agent gave me a category but no evidence"

**Fix:** Reject the row. Re-dispatch. Every classification line **must** quote an actual diff line. No quote, no count.

### ❌ "Customer uses Cypress / Selenium but ships a .spec.ts file"

**Fix:** This skill is Playwright-specific. The pre-flight check `grep '@playwright/test' package.json` exists for a reason. If it fails, STOP and tell the user — the category set will not match.

### ❌ "I'll include human-authored commits too — they're maintaining the suite as well"

**Fix:** This audit's purpose is to measure **Checksum's** healing activity, not the customer engineering team's. Including human commits inflates the numbers and breaks the value proposition (the audit becomes "the suite is being maintained" — useless to the customer who already knows that). Hard rule: filter on the four Checksum identities, period.

### ❌ "I'll re-run the git commands myself to double-check"

**Fix:** Phase 0 is fully automated. Re-running git is a sign you don't trust the script's outputs — if you don't trust them, read `metadata.leaks_detected` and `metadata.active_identities` instead. The script's whole purpose is to be the single source of truth so you don't have to construct author/glob filters from scratch each invocation.

### ❌ "Page objects and helpers aren't tests, I'll skip them"

**Fix:** Page object models, helpers, fixtures, and utility files are first-class test-suite code. Checksum heals locators in POMs all the time. The script includes them by design — classify them. A locator constant moved from `tests/checkout.spec.ts` to `pages/CheckoutPage.ts` is still a `locator-change`.

### ❌ "checksum-lint is just a linter, I'll skip it"

**Fix:** `checksum-lint` commits often contain real maintenance — relocking flaky selectors, retuning waits, removing dead test code. Classify on **diff content**, not author. The only auto-noise filter is "diff is >95% whitespace OR no semantic change."

### ❌ "Branch was main but only 2 of the 4 identities showed up"

**Fix:** That's not a bug, it's a finding — but it's **not customer-facing**. The customer report has no Observations, Concerns, or Executive Summary section to absorb it. Drop it from the report entirely; it lives in `aggregates.json` for SE follow-up. If the gap is genuinely material, raise it with the customer in the chat / call wrapping the report — never embed deficit framing ("smell signal", "concern", "only 1 of 4 agents was active") in the customer deliverable.

### ❌ "I checked `--days 30` but the customer uses a feature branch"

**Fix:** This skill is **`main`-only by design**. If the customer's Checksum integration only writes to feature branches, that itself is a finding — but the customer report has no executive summary to absorb it. Raise it with the user (and ultimately the customer) in the chat / call wrapping the report ("No Checksum activity on main; integration may be configured to write to PRs only"). Do not switch branches without re-confirming with the user, and do not invent an Executive Summary section just to surface this.

### ❌ "I'll put the first and last observed commit dates in the Audit window cell so the report matches what actually happened"

**Fix:** No. The "Audit window" cell + the "Dated:" line MUST reflect the canonical 30-day search window — `metadata.audit_window_start_date → metadata.audit_window_end_date (metadata.audit_window_days days)` — paste them verbatim. Those fields are computed by `lib/audit_window.compute_audit_window()` as `today − timedelta(days=N)` through `today`, inclusive, and they are the SAME dates the git query used. If you instead paste `metadata.observed_first_commit_date → metadata.observed_last_commit_date`, the report will under-report the window whenever Checksum was quiet at the start or end (e.g. reading "2026-05-06 → 2026-05-28" — only 22 days — when the audit actually covered 2026-04-28 → 2026-05-28 = 30 days). The observed-activity fields exist for SE forensics only; they are NOT the customer-facing window. This was a real bug, fixed once, and the field naming (`audit_window_*` vs `observed_*`) is intentional — use the right pair.

### ❌ "There were renames, I'll treat the new path as the file"

**Fix:** Use `git log --follow` for the per-file history, but **only count content-changing commits**. Pure renames (`R100`) are not maintenance.

### ❌ "I'll keep the 'Smell signals' / 'Bug annotation ledger' / 'Commit timeline' / 'Maintenance Hotspots' / 'Most-Touched Utility Files' / 'Methodology' / 'Observations' sections — the data is useful"

**Fix:** This report is a **customer-facing value-prop artifact**. The customer doesn't want an SE-debugging dossier; they want to see what Checksum did for them, quantified in the scorecard and the impact table, with Before/After code as evidence. Cadence, identity distribution, file hotspots, and operational signals do **not** belong in the customer report at all — there is no Observations or Executive Summary section to absorb them. Drop them entirely from the report. The raw forensics live in `<workspace>/aggregates.json` for SE follow-up; anything you'd want the customer to know goes in the chat / call wrapping the report.

### ❌ "I'll add a 'Files Changed:' line under each commit so the customer knows what was touched"

**Fix:** Don't. The Before/After code block IS the evidence — it shows the customer the actual change. Listing 11 file paths under a refactor commit is internal forensics, and on a refactor that touches 11 files it dwarfs the actual narrative. The customer-facing template explicitly drops this line.

### ❌ "I'll keep 'Bug Annotations & Tagging' as a category in the impact table — bug work IS maintenance"

**Fix:** Bug work IS maintenance, but for the customer story it belongs at the TOP of the report as a headline number ("Checksum found N bugs"), not as a row in the impact table. The classifier still tracks `bug-annotation-added` / `bug-annotation-removed` so the headline count is accurate; those rows just don't get displayed as their own category line.

### ❌ "Total time saved should be `sum of per-category counts × 30 min`"

**Fix:** No — that double-counts commits classified into multiple categories. The Total row in the Maintenance Impact table uses the **unique commit count** (de-duplicated on commit SHA, excluding noise rows) × 30 min. Per-category time-saved cells are still computed `category_count × 30 min` because they're showing per-category contribution; the bottom-line total uses the de-duplicated commit count.

### ❌ "I'll add a short Executive Summary at the top so the customer has context for the data"

**Fix:** This report has **no Executive Summary**. The four-cell scorecard (Tests Maintained | Bugs Found | Change Events | Engineering Time Saved) IS the summary — customers skim numbers, not prose. If you find yourself writing an `## Executive Summary` heading, an `## Overview` heading, an intro paragraph above the scorecard, or a narrative blockquote framing the numbers, stop and delete it. The report goes: title → scorecard → How Checksum AI Agents Work → Maintenance Impact → Bugs Found (conditional) → Healing Examples → footer. That's the entire shape; nothing else gets inserted.

### ❌ "The scorecard numbers need an explanatory sentence above or below them so the customer knows what they mean"

**Fix:** The column headers (`Tests Maintained`, `Bugs Found`, `Change Events`, `Engineering Time Saved`) are the explanation. The "How Checksum AI Agents Work" section immediately below explains the underlying mechanism for any cell that needs context. Don't add a sentence like "The numbers below show…" or a blockquote like "In summary, Checksum…". The scorecard stands on its own.

### ❌ "I'll count the bugs by walking `classifications.jsonl` myself and seeing how many unique files have a `bug-annotation-added` category"

**Fix:** Wrong on two counts. (1) "Unique" means **verbatim annotation description text**, not unique file — five tests with the same word-for-word `description: "..."` are one bug, not five. (2) The synthesizer doesn't count anything: `compute_metrics.py` already produced `metrics.bugs_found` and `metrics.bug_descriptions` in `metrics.json`. Read those values and paste them into the report. If `metrics.bugs_found` looks wrong, the **script** has a bug — fix it in `lib/compute_metrics.py`, rerun Phase 1.5, and re-synthesize. Don't paper over a wrong number with AI math.

### ❌ "30 commits × 30 min = 900 min = 15 hrs — I'll write `~15 hrs`"

**Fix:** Don't do arithmetic. `metrics.total_hours_saved_display` already says `~15 hrs` — that's the scorecard cell, paste it verbatim. If you find yourself reaching for a calculator, you've already made a mistake — go read `metrics.json` again. (The legacy `metrics.total_calculation_display` field is no longer surfaced in the customer report; ignore it.)

### ❌ "I'll sum the per-category commit counts for the Total row"

**Fix:** The Total row's Change Events and Time Saved cells come from `metrics.total_change_events` and `metrics.total_hours_saved_display`. They are already strict sums of every visible row (categories + Bug Annotations) because the script computes them that way on purpose. Don't recompute — copy the pre-computed values verbatim. The math is GUARANTEED to add up exactly when you do this.

### ❌ "The Maintenance Impact totals don't match the category sums — let me adjust the Total row to match"

**Fix:** No. If the math doesn't add up, the BUG is upstream — either `compute_metrics.py` has a defect or the synthesizer is making up numbers. Don't paper over a broken table by tweaking the Total row. Confirm `sum(metrics.categories[i].minutes_saved) + metrics.bugs_row.minutes_saved == metrics.total_minutes_saved` (the Phase 1.5 gate enforces this). If they're equal in metrics.json but unequal in the report, the synthesizer mistyped a number — fix the report. If they're unequal in metrics.json, the script is broken — fix the script.

### ❌ "Two commits removed bug annotations in the window — I should mention them as 'closed bugs' in the Bugs Found section"

**Fix:** NEVER. The customer-facing report only ever mentions bugs that were **added** during the window. Bug removals are internal cleanup work (Checksum closing out resolved issues) and have zero customer-value content. No "closed N annotations", no "net delta of +N / -N", no "the bug was reopened then re-enabled", no commit examples showing a `@bug` tag being removed. The classifier still tracks `bug-annotation-removed` rows internally so we have full audit data — they just don't surface in the report.

### ❌ "I'll deduplicate bugs by file — one bug per test file"

**Fix:** Wrong dedup key. Bugs are deduplicated by **verbatim normalized description text**. Five tests with the same word-for-word `description: "..."` = ONE bug. Five tests with five different descriptions = FIVE bugs. `compute_metrics.py` does this correctly; the synthesizer reads `metrics.bugs_found` and `metrics.bug_records` and pastes them.

### ❌ "A bug is just another fix — 30 minutes saved"

**Fix:** Routine fix = 30 min. Bug annotation = **60 min** (`--per-bug-minutes`, default 60). Identifying, confirming, and tracking an actual product defect involves more work than tweaking a locator. The script applies the right rate automatically; the synthesizer just pastes `metrics.bugs_row.time_saved_display`. If you find yourself multiplying anywhere in the report, stop.

### ❌ "I'll show 2–3 examples per category so every category is represented"

**Fix:** No. The Healing Examples section is **5–7 examples TOTAL across the entire report**, not per category. Most categories will have 0 or 1 examples; one or two of the busiest categories may have 2. Categories without a chosen example are omitted entirely — no empty sub-headings, no "padding" with a weak commit just to keep a category visible. The Maintenance Impact table already enumerates every category quantitatively; this section's job is to show what a heal actually looks like in code, not to mirror the impact table.

### ❌ "I picked the most-recent commits in each category as my examples"

**Fix:** Recency is not a strength criterion. Pick examples for **narrative interest** — multi-round heal arcs, app-source-grounded fixes, same-day re-enables, structural improvements that ripple across the suite. A boring import-path bump is the wrong example even if it's the most recent thing in its category. If two candidates are equally strong, then break the tie by recency or category coverage — but the primary signal is "would a customer find this impressive?"

### ❌ "I'll use ```diff fences for the code samples"

**Fix:** Use `ts (or `js for `.js` files) with `// Before` and `// After` comment headers. The customer PDF templates show code as inline TypeScript / JavaScript blocks, not as git-format diffs. This is a deliberate readability choice — `+/-` prefixes look like a code review, while Before/After blocks read as a story.

### ❌ "I'll include every classified commit so the customer has full data"

**Fix:** Pick the **5–7 strongest representatives total** across the entire report. The customer doesn't want to read 63 commit summaries; they want a story. The Maintenance Impact table already covers the full scope quantitatively, and the full data is reproducible from `main` git history any time — the breakdown's job is to highlight a handful of the most narratively interesting heals, not to catalog the window.

### ❌ "I'll mention the workspace path / `metadata.json` / 'how the script ran' for transparency"

**Fix:** Don't. The customer-facing report mentions zero implementation details. There is no Methodology appendix in the customer-facing template — the pipeline is invisible to the reader. If the customer asks how the numbers were derived, that's a CSM conversation, not a section of the report.

---

## Failure mode table — infra / tool issues

| Failure                                                      | Cause                                                               | Fix                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Script exits `FATAL: not a git repo`                         | Wrong `--repo` path                                                 | Confirm absolute path; user passes a clone, not a tarball / zip                                                                                                                                                                                                                                     |
| Script exits `FATAL: no Playwright/Checksum dependency`      | Not a Playwright suite                                              | STOP. Tell user this skill is Playwright-specific. (Customer repos that use `checksumai`, `playwright`, or `eslint-plugin-playwright` ARE supported — the preflight already accepts them.)                                                                                                          |
| `preflight.log` shows `auth refresh ... exited` / `git pull ... failed` WARNING | `--refresh` couldn't rotate auth or pull (stale token, private repo, offline) | Not fatal — the scrape continued on local `main`, so it may be stale. Have the user refresh auth manually (e.g. `gh auth login -h github.com`), then rerun with `--refresh`. If the machine has no auth/network, rerun with `--read-only` and note the data is as-of the last manual pull.          |
| `preflight.log` shows `git checkout main failed` WARNING     | Dirty working tree in the customer clone                            | The clone has uncommitted local changes blocking the checkout. The audit fell back to the local `main` ref. Ask the user to clean/stash the clone (the skill never touches their working tree), then rerun.                                                                                          |
| `summary.checksum_commits == 0`                              | Checksum inactive in window                                         | Not a script failure — it IS the finding. Report "Dormant" verdict with the all-authors baseline as context.                                                                                                                                                                                        |
| `metadata.leaks_detected` non-empty                          | Script regex broken / git oddity                                    | Inspect the leaking name; if it's a custom Checksum identity the user mentioned, add it to `ALLOWED_AUTHORS` in the script and rerun                                                                                                                                                                |
| Only 1 of 4 Checksum identities active                       | Partial integration / paused service                                | Not a bug — raise with the customer in the chat / call wrapping the report. Do NOT add a "Smell signals", "Observations", or "Executive Summary" section to the customer report to surface it (none of those sections exist); the deliverable stays dry, the human conversation absorbs the nuance. |
| `summary.unusual_files` non-empty                            | Checksum touched a `.json` / `.md` / non-code file                  | Review `aggregates.json → unusual_files`; usually safe to ignore. Do NOT surface in the customer report (no Observations section exists). Internal SE note only.                                                                                                                                    |
| `aggregates.json.noise_candidates` >50% of pairs             | Mass formatter run dominates the window                             | Real healing signal is much lower than headline. Inspect `noise_candidates` before classifying; if they're truly cosmetic, the classifier should mark them `isNoise: true` and they'll be excluded from `metrics`. Don't add a customer-facing call-out — flag it to the user in the chat instead.  |
| Classifier agents over-label noise as `flow-change`          | Prompt didn't enforce evidence rule                                 | Restate "Every label needs a quoted diff line" at top of the prompt; reject and re-dispatch                                                                                                                                                                                                         |
| Same row classified by two agents                            | Chunking overlap                                                    | De-dupe in Phase 2 on `(commit, file)` key                                                                                                                                                                                                                                                          |
| Huge diff truncated by the agent's context                   | Single commit changed many lines in one file                        | Read the `.diff` file in slices; the diff file on disk is the full version                                                                                                                                                                                                                          |
| `~/Desktop` not writable or doesn't exist                    | Non-macOS env / sandboxed agent                                     | Resolve `$HOME/Desktop`; if absent, create it (`mkdir -p ~/Desktop`); confirm path back to user                                                                                                                                                                                                     |
| `rm` blocked / aliased to something unexpected               | User's shell aliases `rm` (e.g. to `npm cache clean --force`)       | Prefer `unlink <file>` for single-file deletions. Never use `rm -rf` in any agent-driven cleanup. Workspace cleanup is optional; leave files in `/tmp/` and they'll be GC'd.                                                                                                                        |
| `git show --no-patch --format= --name-status <sha>` errors   | Recent git versions reject `--no-patch` + `--name-status` combo     | Use `git diff-tree -r --no-commit-id --name-status <sha>` instead. The script ships with this fix.                                                                                                                                                                                                  |
| Custom Checksum identity present (e.g. `checksum-ai-canary`) | Customer's pipeline uses an additional bot identity                 | Edit `ALLOWED_AUTHORS` in `lib/collect.py` to add the new name; rerun. The script's allowlist is intentionally explicit — no silent acceptance of "checksum-\*" wildcards.                                                                                                                          |
| `command not found` for the auth command in `preflight.log`  | Alias not defined in this shell, or `--auth-cmd` wrong               | `--refresh` runs the auth command through the interactive login shell so `~/.zshrc` aliases resolve; if it still isn't found, confirm it's defined for the user, or pass `--auth-cmd "<full command>"`. The pull is attempted regardless and may still succeed on existing auth.                       |
| `/tmp/` accumulating workspaces from prior runs              | Phase 3 cleanup was skipped, or an older skill version ran          | Run `python3 $HOME/.claude/skills/30-day-healing-analysis/lib/collect.py --cleanup-all`. Nukes every `/tmp/checksum-heals-audit-*` workspace plus the legacy `/tmp/checksum_heals_collect.py` script copy left behind by earlier skill versions.                                            |
| Legacy `/tmp/checksum_heals_collect.py` script copy on disk  | An older version of this skill wrote the script to `/tmp/` each run | Same `--cleanup-all` removes it. New runs use the pre-stored copy at `~/.claude/skills/30-day-healing-analysis/lib/collect.py` and never touch `/tmp/` for code.                                                                                                                                  |

---

## What this audit DOES and DOES NOT tell you

✅ Whether **Checksum's automation** is actively healing existing tests on `main`
✅ Which of the four Checksum identities are pulling weight (and which are silent)
✅ Which test files are Checksum's **healing hotspots** (frequent heals = flaky or business-critical)
✅ Whether **bug annotations are accumulating** under Checksum's hand (skips added vs removed)
✅ Whether Checksum's activity is **concentrated in one folder** (partial coverage)
✅ Whether Checksum is **stabilizing** (waits, locator hardening, `addLocatorHandler`)

❌ Whether the customer's **human engineers** are maintaining the suite — excluded by design
❌ Whether coverage is **comprehensive** — that's `/detect-tests`
❌ Whether tests are **passing in CI** — needs CI log access, separate skill
❌ Whether tests are **well-written** — code review, not history audit
❌ Whether the product itself is **stable** — needs product telemetry
❌ Whether **new** test authoring (by Checksum or humans) is healthy — out of scope by design

---

## Anti-laziness checklist (final gate)

Before declaring the audit done, every box must be checked:

**Phase 0 (script ran cleanly):**

- [ ] `checksum_heals_collect.py` exited 0
- [ ] `metadata.json.leaks_detected` is `[]` (no human authors slipped through the filter)
- [ ] `metadata.json.active_identities` is a subset of the four allowed names
- [ ] `summary.checksum_commits > 0`. **If zero, Phase 0.5 dormant short-circuit was triggered** — the parent wrote the templated Dormant report directly, skipped Phases 1, 1.5, 2, 2.5, 2.6, and went straight to Phase 3 cleanup. Verify the Dormant report exists on the Desktop and is the abbreviated 4-section shape (scorecard + dormant blockquote + How Checksum AI Agents Work — nothing else). NO classifier subagents should have been dispatched.
- [ ] `diffs/` contains one `.diff` per row in `commits.jsonl`
- [ ] `aggregates.json.unusual_files` reviewed for SE awareness only — **not** mentioned in the customer report (there is no Observations section to absorb it)
- [ ] `metadata.total_test_files_in_suite` is non-zero — this powers the suite-size headline + metadata-table row

**Classification quality (Phase 1):**

- [ ] Every row in `commits.jsonl` has a corresponding row in `classifications.jsonl`
- [ ] Every non-noise row in `classifications.jsonl` has a **quoted diff line** in `evidence`
- [ ] Every non-noise row's `author` field is one of the four allowed identities (sanity belt-and-suspenders)
- [ ] No single category covers >70% of non-noise rows without justification
- [ ] `test.skip` / `test.fixme` / `@bug` annotation added vs removed counted **separately**
- [ ] `uncategorized` rows reviewed — if >10% of total, re-dispatch with the missing patterns
- [ ] Page-object / helper / utility / fixture diffs are classified (not skipped because "they're not specs")

**Metrics computation (Phase 1.5):**

- [ ] `python3 .../lib/compute_metrics.py --workspace <ws>` exited 0
- [ ] `<workspace>/metrics.json` exists and is valid JSON
- [ ] `metrics.bugs_found` reviewed for plausibility — if `0` while `classifications.jsonl` has `bug-annotation-added` rows, inspect the relevant diffs and (if the script's regex is undercounting) fix the script before continuing
- [ ] `metrics.bug_records` has one entry per unique bug — needed for the customer-facing Bugs Found section
- [ ] **Math adds up:** `sum(metrics.categories[i].minutes_saved) + metrics.bugs_row.minutes_saved == metrics.total_minutes_saved`. If not, the script is broken — fix it before Phase 2.
- [ ] `metrics.per_fix_minutes == 30` and `metrics.per_bug_minutes == 60` (defaults, unchanged unless explicitly overridden)

**Synthesizer prompt construction (Phase 2):**

- [ ] Synthesizer prompt includes the FULL contents of `metadata.json` inlined as a fenced JSON code block at the top — byte-for-byte identical to the on-disk file, NOT summarized, NOT re-spelled as bullets
- [ ] Synthesizer prompt includes the FULL contents of `metrics.json` inlined as a fenced JSON code block at the top — byte-for-byte identical to the on-disk file, NOT summarized, NOT re-spelled as bullets
- [ ] Synthesizer prompt explicitly instructs "DO NOT TYPE NUMBERS BY HAND — COPY THEM FROM THE TWO JSON BLOCKS BELOW" so the agent has no excuse to hallucinate cell values
- [ ] On retries (after Phase 2.5 lint failure or Phase 2.6 reviewer rejection), the parent re-pastes BOTH JSON blocks into the new prompt — never assume the synthesizer remembers them from a prior pass

**Deterministic lint (Phase 2.5):**

- [ ] `python3 .../lib/lint_report.py --report <path> --workspace <ws>` was run AFTER the synthesizer wrote the report
- [ ] `<workspace>/lint.json` exists and `status` is `"clean"` (zero violations)
- [ ] If lint reported violations, the synthesizer was re-dispatched with `lint.json` pasted into the prompt as structured feedback (max 2 retries before falling through)
- [ ] AI reviewer was NOT dispatched until Phase 2.5 lint reported clean — the reviewer is too expensive to burn on issues a regex already caught

**Report quality (customer-facing):**

- [ ] Title is `# Checksum AI Agentic Output — <Customer>` followed by `## Commit History Analysis: Test Suite Maintenance`
- [ ] At-a-Glance opens with a **four-cell scorecard table** in one row: `Tests Maintained | Bugs Found | Change Events | Engineering Time Saved`. NO prose blockquote above or below, NO intro sentence, NO narrative framing.
- [ ] Scorecard cell **Tests Maintained** == `metadata.total_test_files_in_suite` (verbatim)
- [ ] Scorecard cell **Bugs Found** == `metrics.bugs_found` (verbatim)
- [ ] Scorecard cell **Change Events** == `metrics.total_change_events` (verbatim)
- [ ] Scorecard cell **Engineering Time Saved** == `metrics.total_hours_saved_display` (verbatim)
- [ ] Metadata block (immediately below the scorecard) is a two-column table containing EXACTLY these four rows in order: Customer, Repository, Branch, Audit window. NO "Test framework" row, NO "Active Checksum AI agents" row, NO scorecard duplicates (no "Bugs found by Checksum" / "Maintenance change events" / "Estimated engineering hours saved" / "Total test files in suite" rows), NO "Generator" / "Author-filter leaks" / "Noise commits" / "Existing test files maintained" rows
- [ ] **"Audit window" cell renders the CANONICAL window** — `<metadata.audit_window_start_date> → <metadata.audit_window_end_date> (<metadata.audit_window_days> days)` pasted verbatim from `metadata.json`. NOT `metadata.observed_first_commit_date → metadata.observed_last_commit_date` (those are forensic-only and will under-report the window). The day-count parenthetical must equal `metadata.audit_window_days` exactly (e.g. `30`).
- [ ] **"Dated:" line under the H2** uses `metadata.report_date_pretty` (e.g. `May 28, 2026`) — NOT a date typed by hand, NOT the current chat-message timestamp, NOT `metadata.observed_last_commit_date`.
- [ ] **Report filename** is `~/Desktop/<slug>_checksum_ai_maintenance_report_<metadata.report_date_iso>.md` (the ISO date matches the window's end date)
- [ ] **Every number in the report matches `metrics.json` / `metadata.json` verbatim** — scorecard cells, per-category counts and time-saved cells, Bug Annotations row cells, Total row cells. The synthesizer is forbidden from doing math; if any number disagrees with the source, fix the report (or rerun `compute_metrics.py` if data has changed).
- [ ] **The Maintenance Impact table adds up exactly.** Sum the Time Saved column across every category row + Bug Annotations row (when present) → must equal Total row's Time Saved cell.
- [ ] Maintenance Impact table includes a **Bug Annotations row** between the last category row and the Total row when `metrics.bugs_found > 0`; omitted entirely when zero
- [ ] **Bugs Found in Your Application** section is present (after Maintenance Impact, before Healing Examples) with one bullet per `metrics.bug_records` entry IFF `metrics.bugs_found > 0`. When zero, the entire heading and body are OMITTED — no placeholder, no "no bugs found" line
- [ ] **No mention of bug-annotation removals anywhere in the report** — no "closed", "removed", "reopened", "re-enabled", "net delta of bugs". Bug-removal events are internal cleanup work and never surface in the customer report.
- [ ] "How Checksum AI Agents Work" appears as a top-level section IMMEDIATELY AFTER At-a-Glance — NOT as an appendix
- [ ] "Maintenance Impact" section follows "How Checksum AI Agents Work" — table has columns Category | Change Events | Time Saved | Description, with a bold **Total** row
- [ ] **No section titled "Executive Summary"**, "Summary by Category", "Maintenance Hotspots", "Most-Touched Utility Files", "Commit timeline", "Bug annotation ledger", "Smell signals", "Observations", "Methodology", "Appendix A", or "Appendix B"
- [ ] **No numbered section headings** — sections are `## At a Glance`, `## How Checksum AI Agents Work`, `## Maintenance Impact`, `## Bugs Found in Your Application` (conditional), `## Healing Examples`. No `## 1.`, `## 2.`, `## 3.`, `## 4.` prefixes
- [ ] The final main section is named **`## Healing Examples`** (not "Detailed Commit Breakdown") and shows **5–7 representative commits TOTAL** across the entire report — not per category. Categories that didn't produce a chosen example are omitted entirely (no empty sub-headings).
- [ ] Each Healing Examples entry has: bold actual git-log subject in backticks, italicized identity, 1–2 sentence narrative, before/after code block. **NO "Files Changed:" line.**
- [ ] Code blocks use `ts / `js with `// Before` and `// After` — NOT ```diff fences with +/-
- [ ] **No closing narrative section** — no "Observations", "Smell signals", "Concerns", "Findings", "Executive Summary", or anything similar after Healing Examples
- [ ] Report ends with the last commit example in Healing Examples — NO footer. No `_Report dated…_` line, no `_Questions? Contact your Checksum CSM._` line, no italicized closing sentence, no appendices, no observations block, no closing narrative below it

**Shareability (the report is the deliverable):**

- [ ] Tables right-align numeric columns
- [ ] All commit SHAs in backticks, trimmed to 7 chars
- [ ] All file paths in backticks, repo-relative
- [ ] No `/tmp/` paths, no JSONL leakage, no mention of "the skill" / "the workspace" / "the synthesizer" / "Phase N"
- [ ] No emojis (unless customer brand uses them)
- [ ] Customer name spelled correctly and consistently
- [ ] Report renders cleanly when previewed (no broken tables, no orphan fences)
- [ ] **File saved to** `~/Desktop/<slug>_checksum_ai_maintenance_report_<YYYY-MM-DD>.md` (NOT inside the customer repo)
- [ ] **No branch was created, no commit was made, no PR was opened** in the customer repo
- [ ] Final Desktop path reported back to the user as the last line of the assistant message
- [ ] **Phase 3 cleanup ran** — `python3 .../lib/collect.py --slug <slug> --cleanup` exited cleanly, `/tmp/checksum-heals-audit-<slug>/` is gone (unless the user explicitly asked to keep the workspace for debugging)
- [ ] No `/tmp/checksum_heals_collect.py` legacy script copy on disk (the script lives in the skill folder, never in `/tmp/`)

**If any box is unchecked: dispatch another agent. Do not declare done.**

Ask yourself two final questions:

1. _"If a sales engineer attached this report to a customer email **as-is**, would they cringe at any sentence?"_ — if "yes," **keep going.** Every sentence should pass the cringe test.
2. _"If I exported this file to PDF and the customer read it cold, would they understand what Checksum did for them and how Checksum AI works?"_ — if "no," **fix the scorecard wording or the How Checksum AI Agents Work section.** (Do not "fix" it by adding an Executive Summary — that section does not exist by design.)
