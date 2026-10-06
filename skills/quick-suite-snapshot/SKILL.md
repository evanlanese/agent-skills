---
name: quick-suite-snapshot
description: DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional demonstration skeleton; if invoked, reply only with the decommission notice in the skill body). Produced a fast, share-ready "quick suite snapshot" for one or more Checksum customers — LIFETIME totals (tests generated, test runs, bugs found) plus PASS RATES over the most recent ~30 runs (run-level and test-level). Accepted a single customer or a comma-separated list. INVOKE when the user says "quick suite snapshot", "quick-suite-snapshot", "pass rate for <customer>", "what's <customer>'s pass rate", "run-level / test-level pass rate", or "last 30 runs pass rate".
---

# /quick-suite-snapshot

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. Its data-access layer and all credential handling have been removed, it does not call any Checksum API or service, and `lib/snapshot.py` only prints a notice.

## If this skill is invoked

Do not run any script, API call, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `quick-suite-snapshot` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

## What it produced

A fast read on a customer's test suite, from the test platform alone (no git history, no repo clone). Two parts:

1. **Lifetime totals** (same definitions as `30-day-healing-analysis`): total tests generated, total test runs, total bugs found.
2. **Pass rates over the most recent ~30 runs** (newest-first, no date filtering):
   - **Run-level pass rate** = runs with `status == "passed"` / runs analyzed.
   - **Test-level pass rate** = `Σpassed / Σ(passed+failed)` across runs that carry per-test counts.

## Rules it followed

- **Read-only.** Never wrote anything back to the platform or touched a git repo.
- **Exact customer name only.** Close variants were listed but never guessed; with no exact match, the customer was skipped and the variants shown.
- **No date math.** "Last 30 runs" meant exactly the default page of recent runs, not a date window.
- **Batch-friendly.** A comma-separated list produced one snapshot per customer, in order. A failure on one customer marked it SKIPPED without aborting the rest.

## How the pass rates were computed

Each run record carried `status` (`passed`/`failed`) plus per-test counts `passed` / `failed` / `healed` / `bug`. The calculation is kept in `lib/snapshot.py` → `compute_pass_rates()`.

- **Run-level**: runs whose `status == "passed"`, divided by total runs.
- **Test-level**: sum of `passed` over sum of `passed + failed`, across only the runs with those counts populated.
- **Infra-failed runs** (a job that died before reporting) have `null` per-test counts. They were **excluded from the test-level ratio** but **still counted as failures at the run level**, which is why the two rates can differ. `healed` and `bug` totals were shown alongside for context.

## Output shape

```
acme

Lifetime
  Total tests generated: 15
  Total test runs:       111
  Total bugs found:      5

Last 30 runs
  Run-level pass rate:   40.0%  (12 passed / 30 runs)
  Test-level pass rate:  42.7%  (38 passed / 89 pass+fail across 25 runs with per-test counts)
  Healed: 0   Bugs flagged in runs: 8
```

A `--md` mode rendered the same data as markdown tables.

## Presentation rules

- Report **the data only**: the per-customer blocks and, for a batch, one consolidated table.
- **No analysis, commentary, or "What stands out" / "Takeaways" section.** No interpretation, no recommendations.
