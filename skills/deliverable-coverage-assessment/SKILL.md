---
name: deliverable-coverage-assessment
description: DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional demonstration skeleton; if invoked, reply only with the decommission notice in the skill body). Assess how closely a Checksum customer's existing test suite achieves a stated DELIVERABLE (a scope/coverage commitment), and give a short, honest analysis of how that achieved coverage improves a stated CURRENT STATE (a pain point / problem). Takes three inputs — the customer name, the deliverable text, and the current-state text. Goes into the customer's local Playwright/Checksum test repo (same repo-resolution + best-effort `main` sync as 30-day-healing-analysis; strictly read-only — no edits, commits, branches, or pushes), reads the checked-in tests under `/tests` (both the `.checksum.md` stories and the generated `.checksum.spec.ts` specs), and maps each piece of the deliverable to concrete test evidence (file path, line, quoted assertion). Renders a per-sub-goal verdict — Covered / Partially covered / Not covered / UNSURE — and writes one share-ready markdown report to the user's Desktop as `<slug>_deliverable_coverage_assessment_<YYYY-MM-DD>.md`. HARD RULE: never guess whether a goal was met; if the evidence is ambiguous or insufficient, the verdict MUST be "UNSURE — human review required" and say why. INVOKE when the user says "deliverable coverage assessment", "deliverable-coverage-assessment", "did we achieve the deliverable for <customer>", "how close is <customer>'s suite to <deliverable>", "assess coverage against this deliverable", "evaluate this scope against the test suite", or gives a customer name plus a deliverable statement and a current-state statement and asks how well the suite meets it.
---

# /deliverable-coverage-assessment

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. It does not call any Checksum API or service, and any bundled scripts only print a notice.

## If this skill is invoked

Do not run any step, script, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `deliverable-coverage-assessment` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Given a **customer**, a **deliverable** (what Checksum committed to cover), and a **current state** (the problem the customer has today), inspect that customer's **existing checked-in test suite** and produce one honest, evidence-grounded report answering two questions:

1. **How close did the suite get to the deliverable?** — decompose the deliverable into discrete, checkable sub-goals and, for each, render a verdict backed by a real test file, line, and quoted assertion.
2. **How does the achieved coverage improve the current state?** — a short analysis tying the *confirmed* coverage back to the stated pain.

This is a **read-only assessment of what is already in the repo**. It does not author tests, run tests, heal, branch, commit, or push. It reads `main` and writes one markdown file to the Desktop.

---

## ⛔ HARD RULE #1 — Never guess. When unsure, say so and defer to a human.

This is the single most important rule in this skill and it overrides every other instinct.

- If the test evidence for a sub-goal is **ambiguous, indirect, partial, or absent**, you do **NOT** declare it Covered and you do **NOT** declare it Not-covered. The verdict is **`UNSURE — human review required`**, and you state *exactly why* you couldn't tell (e.g. "the spec clicks `Apply` on a promo code but never asserts the discounted total, so I can't confirm the discount is verified").
- Do **NOT** infer that a goal was achieved because a test *file name*, a *test title*, or a *`.checksum.md` step* mentions the right words. A title is an intention, not a verification. Coverage is only confirmed by an **actual assertion / observable check** in the executable spec (`expect(...)`, a thrown error on failure, a `toBeVisible`, a verified network/transcript condition, etc.).
- Do **NOT** round "probably" up to "yes" or down to "no." A confident verdict requires you to be able to **quote the line** that proves it. If you cannot quote it, you are not confident — mark it UNSURE.
- It is **correct and expected** for a report to contain several UNSURE verdicts. A report full of confident-but-unverifiable claims is a failure; a report that honestly flags what a human must check is a success.
- The same rule applies to the current-state analysis: only claim the coverage improves the current state where you can point to confirmed evidence. Where the causal link is plausible but unproven, say "this likely helps, but a human should confirm" — don't assert it.

> Put plainly: **the cost of a wrong "yes" is far higher than the cost of an honest "I'm not sure."** The whole point of this report is that a human can trust its confident verdicts precisely because it openly flags everything it couldn't verify.

---

## ⛔ HARD RULE #2 — Read-only. No mutation of the customer repo.

This skill **does not** create a branch, edit a file, run the test suite, generate tests, commit, or push. The only write it performs against the repo is a **best-effort fast-forward `git pull`** during the optional `main` sync (Phase 0), exactly like `30-day-healing-analysis`. Everything else is reads. The only file it creates is the report on the user's Desktop.

---

## ⛔ HARD RULE #3 — Evidence or it didn't happen.

Every `Covered` or `Partially covered` verdict **must** cite:

- the **file path** (relative to the repo root), and
- the **line number(s)**, and
- a **quoted line** from the executable spec (or `.checksum.md` step where that is genuinely the right artifact) that proves the check exists.

No evidence → not a confident verdict → `UNSURE`. "Seems covered" / "should be tested" prose is banned.

---

## Inputs (three things, collected up front)

1. **Customer name** → used for the title, the repo slug, and the output filename. Derive the slug as the lowercase, dash-separated form (e.g. "Acme Corp" → `acme-corp`). If the slug is ambiguous, ask via `AskUserQuestion`.
2. **Deliverable** — the scope/coverage commitment, pasted verbatim. Example:
   > "Checksum AI extends automated test coverage to Acme's checkout flows (cart, pricing, payment, confirmation). In scope: verifying cart quantity updates, promo-code application, saved payment methods, shipping-address persistence, and order-confirmation emails where a test inbox is available."
3. **Current state** — the problem the customer has today, pasted verbatim. Example:
   > "Checkout regressions surface in production rather than in staging. A recent pricing change let expired promo codes apply at checkout; no automated regression coverage caught it."

Record the deliverable and current-state text **verbatim** in the report so the assessment is self-contained and re-checkable.

---

## Tooling

A single stdlib-only helper does the deterministic plumbing so your effort goes into judgment, not git/glob mechanics:

```
$HOME/.claude/skills/deliverable-coverage-assessment/lib/prepare.py
```

| Command | What it does |
| --- | --- |
| `prepare.py resolve <slug>` | Prints the absolute path to the customer's local test repo, or `RESOLVE_FAILED: <reason>` (exit 3). Reuses `30-day-healing-analysis`'s `config.py` so a customer configured/pinned there resolves here (shared `customer_repos_base` + per-customer pins). |
| `prepare.py sync <repo>` | Best-effort sync of local `main` to origin before reading: ensure on `main` → optional `$AUTH_REFRESH_CMD` (refresh GitHub auth) → `git pull --ff-only`. JSON `{ok, synced, sha, log}`. Read-only apart from the fast-forward pull; degrades gracefully offline. |
| `prepare.py manifest <repo>` | Enumerates the suite under `checksum/tests` (or `tests`/`e2e`), pairing each `.checksum.md` story with its generated `.checksum.spec.ts` spec, grouped by area, with titles / checksum IDs / start URLs and totals. JSON. |

If `resolve` fails because the customer isn't configured, the customer repo may be a **git submodule** that hasn't been checked out yet — tell the user to check it out (or pin the path via the sibling skill's `config.py set-customer <slug> <abs-path>`), then re-run. Don't guess a path.

---

## Workflow

### Phase 0 — Locate and sync the repo (read-only)

1. `REPO=$(python3 .../prepare.py resolve <slug>)`. On `RESOLVE_FAILED`, surface the reason and stop (or ask for the path / initiation, then retry).
2. `python3 .../prepare.py sync "$REPO"` — best-effort `main` sync so you assess the latest state. If `synced:false`, note in the report that you read the local `main` ref as-is (and the short SHA). Never abort on a failed sync.
3. Record the repo path and the `main` short SHA — the report states exactly which commit was assessed.

### Phase 1 — Decompose the deliverable into checkable sub-goals

Read the deliverable and break it into the **smallest discrete, independently-verifiable claims**. Each becomes a row in the scorecard. For the example deliverable that's roughly:

- cart quantity updates
- promo-code application
- saved payment methods
- shipping-address persistence
- order-confirmation emails (where a test inbox is available)
- general checkout UI behavior

Keep the customer's own wording. Don't invent sub-goals the deliverable didn't state, and don't merge two distinct commitments into one row. If the deliverable is vague about what "covered" means for a sub-goal, note that ambiguity now — it will likely drive an UNSURE verdict later.

### Phase 2 — Gather evidence from the existing tests

1. `python3 .../prepare.py manifest "$REPO"` to get the map of areas and story↔spec pairs.
2. For each sub-goal, find the candidate tests. Use the manifest's area grouping and titles to narrow, then **read the actual files** — both the `.checksum.md` (intent) and, crucially, the `.checksum.spec.ts` (what is actually verified). Use `Grep` across the tests root for concrete signals, e.g.:
   - cart: `cart`, `quantity`, `toHaveCount`, line-item totals
   - promo codes: `promo`, `coupon`, `discount`, `Apply`, total-after-discount assertions
   - payment: `payment`, `card`, `saved`, `default`
   - persistence: `reload`, `goto` again + `expect(... ).toHaveValue`, save-then-reopen flows
   - email: `inbox`, `mail`, `confirmation`, `toContainText` on message bodies
3. For each candidate, determine **what is actually asserted**, not what the test is named. A test titled "Apply Promo Code" that clicks `Apply` but only asserts a success toast appears does **not** by itself confirm "discount applied to the total" — note precisely what it does and does not verify.
4. Note **stories without a spec** (manifest `stories_without_spec`): these are authored intentions with no executable verification yet — strong UNSURE / Not-covered signal for the sub-goal they target.

> **ULTRATHINK at the assertion level.** The deliverable is met for a sub-goal only when an executable check would actually fail if that behavior regressed. Ask of each candidate: "If this exact behavior broke in production, would this test go red?" If you can't answer a confident yes from a quotable line, the sub-goal is UNSURE.

### Phase 3 — Verdict per sub-goal (no guessing)

Assign each sub-goal exactly one verdict:

| Verdict | When |
| --- | --- |
| **Covered** | A spec contains an assertion that would fail if this behavior regressed, and you can quote it. Cite file + line + quoted assertion. |
| **Partially covered** | The behavior is exercised but the verification is incomplete (e.g. the action is performed but the *outcome* isn't asserted; covered for one path but not the stated scope). Cite what exists and state precisely what's missing. |
| **Not covered** | You searched the suite and found **no** test exercising this sub-goal at all. State where you looked (areas/greps) so the negative is credible. |
| **UNSURE — human review required** | Evidence is ambiguous, indirect, or you can't tell whether the assertion truly verifies the stated behavior. State exactly what a human should look at to resolve it. **Default here whenever you are not confident.** |

Apply HARD RULE #1 ruthlessly. Better an honest UNSURE than a wrong Covered/Not-covered.

### Phase 4 — Current-state impact analysis (short, honest)

In a few tight paragraphs, connect the **confirmed** coverage to the stated current state:

- Which confirmed sub-goals would now catch a regression of the kind described in the current state? Cite the test.
- Where the current state names a specific failure (e.g. "expired promo codes applied at checkout after a pricing change"), check whether the suite actually has a test that would catch *that class* of regression. If yes, cite it. If no, say so plainly — that's a coverage gap worth surfacing. If you can't tell, UNSURE.
- Be explicit about residual risk: what in the current state is **still not** protected by confirmed coverage.
- Don't overclaim causation. "These confirmed tests would catch X" only where a quotable assertion supports it; otherwise "likely helps — human should confirm."

### Phase 5 — Write the report

Compute the date with `date +%F` and write exactly one file:

```
~/Desktop/<slug>_deliverable_coverage_assessment_<YYYY-MM-DD>.md
```

Use the template below. Then tell the user the path and give a 2–3 line summary including the count of Covered / Partial / Not-covered / UNSURE.

---

## Report template

```markdown
# Deliverable Coverage Assessment — <Customer Name>

**Date:** <YYYY-MM-DD>
**Repo:** <repo path> @ `main` `<short-sha>` <(synced to origin | read local main as-is)>
**Assessed by:** Checksum AI (automated, read-only) — confident verdicts are evidence-backed; UNSURE items require human review.

## Deliverable (verbatim)
> <deliverable text exactly as provided>

## Current state (verbatim)
> <current-state text exactly as provided>

---

## Scorecard

| # | Sub-goal (from the deliverable) | Verdict | Confidence | Evidence (file:line) |
|---|----------------------------------|---------|-----------|----------------------|
| 1 | promo-code application | Covered / Partial / Not covered / **UNSURE** | High / Medium / — | `checksum/tests/checkout/....spec.ts:NN` |
| … | …                                | …       | …         | …                    |

**Totals:** Covered N · Partially covered N · Not covered N · **UNSURE N** (out of <total> sub-goals)

---

## Findings (one block per sub-goal)

### 1. <sub-goal> — <VERDICT>
**Evidence:**
- `checksum/tests/checkout/<file>.checksum.spec.ts:NN`
  ```ts
  await expect(page.getByTestId("order-total")).toHaveText("$90.00");
  ```
**What this verifies:** <one line — what would go red if it regressed>
**What it does NOT verify / why UNSURE (if applicable):** <precise gap or ambiguity>

<repeat for every sub-goal>

---

## ⚠️ Items requiring human review (UNSURE)

A consolidated list so a human can act on it directly. For each: the sub-goal, why it's unresolved, and the exact file/assertion to inspect.

- **<sub-goal>** — <why unsure>. Look at `<file:line>` and confirm whether <specific question>.

---

## How this improves the current state

<2–4 short paragraphs. Tie CONFIRMED coverage to the stated pain. Name the specific
regression class from the current state and state, with evidence, whether the suite
would now catch it — or honestly that it would not / that you can't tell. Close with
residual risk: what in the current state remains unprotected by confirmed coverage.>

---

## Method & limits
- Read-only assessment of checked-in tests on `main` @ `<sha>`. No tests were executed; verdicts are from static reading of `.checksum.md` stories and `.checksum.spec.ts` specs, not from a live run.
- "Covered" means a quotable assertion would fail on regression — it does **not** guarantee the test currently passes in CI.
- UNSURE verdicts are deliberate: where evidence was ambiguous or insufficient, no guess was made. Those items are for a human to resolve.
```

---

## Quality bar

- Every confident verdict quotes a real line from a real file at a real line number. No exceptions.
- UNSURE is used liberally and without apology wherever confidence is lacking.
- The deliverable and current state are reproduced verbatim; sub-goals trace directly to the deliverable's wording.
- The report is self-contained and share-ready (email / Slack / PDF) — but it is an **assessment aid for a human**, never the final word on a confident-but-unverified claim.
- No repo mutation beyond the best-effort fast-forward pull. No branch, no commit, no push, no test execution.
