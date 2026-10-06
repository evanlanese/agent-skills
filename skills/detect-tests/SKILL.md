---
name: detect-tests
description: DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional demonstration skeleton; if invoked, reply only with the decommission notice in the skill body). Comprehensive happy-path E2E test discovery for an existing web app. Three-phase parallel workflow with honest-evaluation gates, grounded in BOTH source code (when available) AND live-site exploration (via proxy when needed). Lands hundreds of test story files (.checksum.md) in a single PR matching team conventions. Designed to resist the "stop early" failure mode. INVOKE when user says "detect tests", "discover test cases", "comprehensive E2E coverage", "find untested features", "audit test gaps", or similar — especially for projects with existing partial coverage.
---

# /detect-tests

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. It does not call any Checksum API or service, and any bundled scripts only print a notice.

## If this skill is invoked

Do not run any step, script, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `detect-tests` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Discover **comprehensive happy-path** E2E test stories for a test repo, grounded in the application source code AND/OR the live site.

This skill exists because the default discovery flow **stops too early**. A single round of agents covers the obvious collections and calls it done, leaving you with 30–40% of real happy-path coverage. This skill forces three phases with honest evaluation gates between them.

> **ULTRATHINK between phases. Don't stop early. Re-read the anti-laziness checklist every time you're tempted to declare "done."**

---

## Two modes (combinable)

- **Mode A — Source-grounded.** You have read-only access to the app repo (e.g. `.../<app>/app/components/`). Best for depth.
- **Mode B — Black-box.** You only have a running URL + credentials (often behind a proxy). Best for iframe-heavy apps, legacy features, SaaS without source.
- **Mode C — Both.** Triangulate: source tells you what EXISTS; live site tells you what the USER SEES (iframes, modals, hidden sub-routes). **Strongest option.**

---

## Inputs to collect before running

1. **Source code path** (Mode A/C) — read-only path to app repo
2. **Test repo path** — receives new `.checksum.md` files
3. **Live site URL + credentials** (Mode B/C) — including proxy if needed (check `.env`)
4. **Branch name** — include date/timestamp (e.g. `detect-tests-expansion-2026-04-16`)
5. **No-touch rule confirmation** — existing `.checksum.md` files with a `.checksum.spec.ts` sibling are **untouchable** (editing source MD breaks the spec contract)

Unclear? Ask via `AskUserQuestion`. Don't guess.

---

## Pre-flight

```bash
# 1. Enumerate source component dirs (Mode A/C) — MUST DO FIRST
ls <source>/app/components | sort
# Skipping this step costs 8+ feature areas per run.

# 2. Current collection sizes — find "light" (< 12 tests) collections
for d in <test-repo>/checksum/tests/*/; do
  printf "%-30s %s\n" "$(basename "$d")" \
    "$(find "$d" -name '*.checksum.md' | wc -l | tr -d ' ')"
done

# 3. Untouchable files (have .spec.ts sibling)
git ls-files <test-repo>/checksum/tests | grep '\.checksum\.spec\.ts$'

# 4. Check .env for proxy + creds (Mode B/C)
grep -iE "proxy|url|user|pass" <test-repo>/.env

# 5. Existing test IDs (for dedup)
grep -rh "checksumTestId:" <test-repo>/checksum/tests --include="*.checksum.md" | sort
```

If `gh auth` is stale you'll hit `Invalid username or token` on push — user runs `gh auth login -h github.com`, then retry.

---

## The three-phase workflow

Each phase = **parallel `Agent` subagents** → honest-evaluation gate → commit. **Do not skip phases.**

### Phase 1 — Expand existing + obvious new collections

Launch in a **single message with multiple `Agent` tool calls** (3–7 agents in parallel):

- **A (Explore):** Read every existing `.checksum.md` — extract YAML frontmatter format, folder conventions, naming patterns, file format variants (detailed vs simple-bullet).
- **B (Explore):** Read test infrastructure — playwright config, auth helpers, utilities, `agents_kb/` or docs.
- **C (Explore):** Read app routes, sidebar nav, feature dirs in source.
- **D (general-purpose, Mode B/C):** Live-site exploration via Playwright MCP (snippet below).
- **E–G (general-purpose):** For each existing collection, add +10–20 new happy-path stories that don't duplicate. Group 2–4 collections per agent.

#### Live-site snippet (Mode B/C)

```javascript
async (page) => {
  const browser = page.context().browser();
  const ctx = await browser.newContext({
    proxy: { server: 'http://<HOST>:<PORT>', username: '<USER>', password: '<PASS>' }
  });
  const p = await ctx.newPage();
  await p.goto('<URL>', { timeout: 60000, waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(3000);

  // login (adjust selectors)
  // await p.click('<switch-to-password-login selector>');  // if the login page needs it
  await p.fill('#username', USER);
  await p.fill('#password', PASS);
  await p.click('button:has-text("Log in")');
  await p.waitForURL('**/app/**', { timeout: 60000 });
  await p.waitForTimeout(8000);

  // enumerate every interactive element
  const elements = await p.evaluate(() => {
    return Array.from(document.querySelectorAll(
      'button, a, input, select, h1, h2, h3, h4, [role], iframe, [class*="tile"]'
    )).map(el => ({
      tag: el.tagName, role: el.getAttribute('role'),
      text: el.innerText?.trim()?.substring(0, 120),
      href: el.getAttribute('href'), ariaLabel: el.getAttribute('aria-label'),
      id: el.id || undefined, src: el.getAttribute('src')?.substring(0, 200)
    })).filter(e => e.text || e.ariaLabel || e.id || e.src);
  });

  // iframe contents (critical — legacy features hide here)
  const iframeElements = await p.frameLocator('<iframe selector>').locator('body').evaluate(body => {
    return Array.from(body.querySelectorAll('button, input, select, [role], [id]'))
      .map(el => ({ id: el.id, text: el.innerText?.substring(0, 80), type: el.type }));
  });

  await p.close(); await ctx.close();
  return { elements, iframeElements };
}
```

**Exploration checklist per page:**
- [ ] Full `document.body.innerText` capture
- [ ] Every `button / a / input / select / [role] / iframe` enumerated
- [ ] Every iframe entered via `frameLocator`
- [ ] Every dropdown opened (list all options)
- [ ] Every button clicked that opens a dialog/modal
- [ ] User menu opened
- [ ] Sidebar collapse, banner toggle, language switch exercised
- [ ] Breadcrumbs inspected
- [ ] Footer scrolled (every external link listed)
- [ ] Sub-routes guessed and tried: `/profile`, `/contactus`, `/releasenotes`, `/settings`, etc.

**Save raw data into memory.** Don't re-explore — rate limits bite.

If the browser MCP gets stuck: `pkill -f mcp-chrome; pkill -f chromium; sleep 2` then navigate to `about:blank`.

#### Phase 1 gate

After Phase 1: **~100–300 stories.** Answer out loud:

> Have I enumerated every dir under `<source>/app/components/`? Every page in the sidebar + every guessed sub-route? For each, is there a collection, OR have I deliberately skipped it with a reason?

Any "no" / "not sure" → Phase 2.

### Phase 2 — Source/site-area gap fill

For every component dir or live-site feature without a collection, create a new collection. **Typical gaps in a complex SaaS app:** `dashboard/`, `reports/`, `activity/`, `charts/`, `account/`, `settings/`, `user-profile/`, `admin/`, `user-menu/`, `system-pages/`, `login/`.

Also backfill any "light" collections (< 12 tests) where source/site clearly supports more flows.

Dispatch **4–6 parallel `general-purpose` agents** with the prompt skeleton below.

#### Phase 2 gate

After Phase 2: **~150–450 stories.** Each "no" = a Phase 3 agent:

1. **Variant tests** — same flow × different types / roles / currencies / locales / field types?
2. **Marquee journeys** — 8–15 steps spanning 4+ features?
3. **Per-widget / per-modal focused tests** — each widget/modal has its own test?
4. **Multi-condition filters** — AND/OR groups, nested, date ranges, deep-linkable URLs?
5. **Navigation depth** — top nav, breadcrumbs, deep-link tab params, permission-gated items?
6. **CRUD completeness** — all 4 ops × every variant for every CRUD feature?
7. **Dialog/modal enumeration** — open/submit/cancel per dialog?
8. **Dropdown coverage** — multiple options tested per dropdown, not just the first?
9. **Validation states** — required-field behavior per form?
10. **Accessibility paths** — skip-to-content, keyboard nav, ARIA labels?

### Phase 3 — Variants, marquee, widgets, filters, nav, micro-enumeration

Dispatch 4–6 parallel agents, one per axis:

1. **Variants** — same flow × types / roles / currencies / locales / field types. Adds to existing collections. **Highest bug-yield axis** — production bugs hide in cross-cuts.
2. **Marquee** — new `marquee/` collection, 15–25 cross-feature journeys, 8–15 actions each.
3. **Widgets + modals** — new `widgets/` collection enumerating every component in `widgets/`, `modals/`, `dialogs/`, `forms/` (or every dialog found on live site).
4. **Filters + nav + leftover** — new `filters/`, `navigation/`, `details/` collections. Grep `filters/`, `nav/`, `entity/`, `plugins/` for untested behaviors.
5. **CRUD + dialog micro-enumeration** — Create × each variant, Edit × each variant, Delete, Filter × each axis, Validation × each form, Dialog × (open/submit/cancel).
6. **Language/locale + accessibility** — switcher persistence, RTL, ARIA, keyboard shortcuts.

Final landing: **250–650+ stories** depending on app size.

---

## Strict no-touch rule

**Every agent prompt must include this verbatim at the top:**

```
STRICT RULE: DO NOT modify or delete any existing .checksum.md file.
ONLY create new files. Many existing files have generated .checksum.spec.ts
companions and editing the source MD breaks the spec contract.
```

Verify after each phase commit:
```bash
git status --short | grep -v "^??" | grep -v "^A " | wc -l   # must output 0
```

If not 0, revert:
```bash
git diff <base>..HEAD --name-status -- 'checksum/tests/**/*.checksum.md' \
  | awk '$1=="M" || $1=="D" {sub(/^[MD]\t/,""); print}' > /tmp/touched.txt
while IFS= read -r f; do git checkout <base> -- "$f"; done < /tmp/touched.txt
```

---

## Per-agent prompt skeleton

Pass absolute paths — agents have no conversation context.

```
Phase <N> of test detection for <App Name>.

STRICT RULE: DO NOT modify or delete any existing .checksum.md file.
ONLY create new files.

SOURCE CODE (READ ONLY): <absolute path, if Mode A/C>
TEST REPO: <absolute path>
LIVE SITE URL: <url, if Mode B/C>

YOUR SCOPE — <NEW | EXPAND | BACKFILL | VARIANT | MARQUEE | WIDGETS | FILTERS | NAV>:
1. <collection> — <source dir or live-site feature>
2. <collection> — <source dir or live-site feature>

Read existing .checksum.md files in each target collection FIRST.
Don't duplicate. Add NEW stories that fill gaps.

Source/site areas to ground in:
- <component path or URL>
- <models, selectors, routes>

Topics per collection (verify each in source/site first):
- <topic 1>
- <topic 2>

REQUIREMENTS:
- READ source code OR live-site snapshots FIRST. Verify each feature exists.
- 3–7 actions + strong data-backed assertions per test.
- Self-contained: API data setup + cleanup where required.
- Proper YAML frontmatter (title, checksumTestId, startUrl, appId, envUser).
- checksumTestId must be unique — verify against existing IDs first.
- Relative startUrls only (no absolute https URLs).
- Read 2–3 existing high-quality .checksum.md to copy frontmatter format.
- Only .checksum.md files. NO .ts files.
- DO NOT edit any existing file.

Report: list of new files written + brief coverage summary.
```

---

## Reviewer loop (recommended)

After each phase:

1. Dispatch ONE `general-purpose` reviewer with all new files as scope.
2. Reviewer writes report to `<test-repo>/checksum/tests/_reviews/review.md`.
3. Exit conditions:
   - 1st review: exit only if **Excellent**
   - 2nd review: exit if **Good or Excellent**
   - 3rd review: accept whatever
4. Between reviews, dispatch one more discoverer with the review as feedback, delete old review, re-run.

---

## Output deliverables

1. **PR** to the test repo — match team conventions by running `gh pr view <recent-similar-PR> --json title,body` + `git log --oneline -20` BEFORE creating. Mirror branch pattern, commit prefix, title format, body template.
2. **CSV coverage matrix** at `<test-repo>/checksum/tests/test-coverage-matrix.csv`
3. **Final review report** (kept locally, not committed)

### CSV script (Python — shell escaping breaks on titles with quotes/commas):

```python
import os, re, csv
tests_dir = '<path>'
rows = []
for root, _, files in os.walk(tests_dir):
    for f in files:
        if not f.endswith('.checksum.md'): continue
        with open(os.path.join(root, f)) as fh: content = fh.read()
        collection = os.path.relpath(root, tests_dir)
        title = re.search(r'title:\s*"?([^\n"]+)', content).group(1).strip()
        tid = re.search(r'checksumTestId:\s*(\S+)', content).group(1)
        url = re.search(r'startUrl:\s*(\S+)', content).group(1)
        role_m = re.search(r'envUser:\s*\n\s*(?:role:\s*(\S+)\s*\n\s*)?username:\s*(\S+)', content)
        role = role_m.group(1) if role_m and role_m.group(1) else ''
        user = role_m.group(2) if role_m else ''
        steps = len(re.findall(r'^\d+\.\s', content, re.MULTILINE)) or len(re.findall(r'^\*\s', content, re.MULTILINE))
        has_setup = 'Data Setup' in content and 'Not Required' not in content.split('Data Setup')[1][:50]
        has_cleanup = 'Data Cleanup' in content and 'Not Required' not in content.split('Data Cleanup')[1][:50]
        has_spec = any(tid + '.checksum.spec.ts' in sf for sf in os.listdir(root))
        rows.append([collection, tid, title, url, f, role, user, steps, has_setup, has_cleanup, 'Automated' if has_spec else 'Story Only'])
rows.sort(key=lambda r: (r[0], r[1]))
with open('test-coverage-matrix.csv', 'w', newline='') as out:
    w = csv.writer(out)
    w.writerow(['Collection','Test ID','Title','Start URL','Filename','Role','Username','Steps','Has Setup','Has Cleanup','Status'])
    w.writerows(rows)
print(f'Wrote {len(rows)} rows')
```

---

## Anti-pattern reference — lazy thought → real fix

### ❌ "Site is blocked, I'll use codebase analysis only"
**Fix:** Check `.env` for proxy/auth. Use Playwright MCP `browser_run_code` with a custom context. Don't give up on a 403.

### ❌ "I have N tests, that should be enough"
**Fix:** Numbers are meaningless without a feature matrix. For every page/feature, justify coverage or identify the gap. "311 tests" for a complex SaaS is ~50%.

### ❌ "Happy path means I skip validation"
**Fix:** Happy path = the successful user journey. Form validation (required fields) IS part of "what happens when the user submits." Don't use "happy path" as an excuse.

### ❌ "I explored the page, moving on"
**Fix:** Scanning `innerText` once isn't exploration. Click every dropdown, open every modal, toggle every tab. Iframes contain entire sub-apps — explore separately via `frameLocator`.

### ❌ "Only 1 item type tested but 5 exist — moving on"
**Fix:** THE most common gap. If a dropdown has 5 options, test multiple OR at minimum write a "dropdown options visible" test.

### ❌ "I skipped the source enumeration step"
**Fix:** `ls <source>/app/components | sort` takes 3 seconds. Skipping it cost 8 feature areas on the original run. Always run it.

### ❌ "I wrote tests from memory, not from verified features"
**Fix:** Every test must be grounded in source OR a live-site snapshot. "I think the app has X" → verify first.

### ❌ "User approved the plan, job done"
**Fix:** Plans are estimates. As you execute, you discover more. Come back and add.

---

## Failure mode table — infra / tool issues

| Failure | Cause | Fix |
|---|---|---|
| 403 on site visit | Proxy not configured | `.env` has creds; use `browser_run_code` w/ custom context |
| Browser MCP hangs | Stale chromium process | `pkill -f mcp-chrome; pkill -f chromium; sleep 2`; nav `about:blank` |
| `Invalid username or token` on push | Expired token in remote URL | `gh auth login -h github.com`, retry |
| Hardcoded fixture IDs in tests | Agent relied on seeded data | Reviewer flags; pass review back + demand API data setup |
| Cross-collection duplicates | Parallel agents didn't coordinate | Reviewer dedupes; canonical version in the focused collection |
| Agent wrote `.ts` files | Ignored no-`.ts` rule | Restate rule at top of prompt; `find ... -name "*.ts"` to verify |
| Agent edited existing `.checksum.md` | Missed strict rule | Restate at top of every prompt; `git status --short \| grep -v "^??"` after each phase |
| Duplicate `checksumTestId` | Agents generated IDs blind | `grep -rh "checksumTestId:" \| sort \| uniq -d` after each dispatch |
| Absolute `https://` URLs in startUrl | Didn't follow relative rule | Restate "Relative startUrls only" prominently |
| Foreign-language locators | Didn't read existing specs | Require "Read 2–3 existing .checksum.md first" in prompt |

---

## What "comprehensive happy-path" actually means

✅ All major feature areas covered with depth
✅ Variant coverage across roles / types / currencies / locales
✅ Marquee cross-feature journeys (8+ steps, 4+ features each)
✅ Per-widget, per-modal focused tests
✅ Filter logic + navigation depth
✅ CRUD completeness × every variant
✅ Dialog/modal enumeration (open/submit/cancel)
✅ Dropdown option coverage (not just first)

❌ Negative-path / error-handling
❌ Network failure / concurrency
❌ Performance / load
❌ Visual regression / cross-browser
❌ Security / pentest
❌ Deep a11y audits (beyond ARIA label tests)

If requester wants those, separate effort (QA flows, perf benchmarks, a11y audits).

---

## Anti-laziness checklist (final gate)

The original run of this skill produced 311 stories on first pass and declared comprehensive. It wasn't — user pushed three times to reach 590. My own run: 20 → 67 → 91 → 101, each bump only after a user challenge. **Resist this.**

Before saying "done":

**Coverage breadth:**
- [ ] Enumerated every dir under `<source>/app/components/` — either have a collection or a justified skip
- [ ] Visited every sidebar page + every guessed sub-route (`/profile`, `/contactus`, `/settings`, etc.)
- [ ] Entered every iframe and extracted its interactive elements
- [ ] At least one collection per major feature area
- [ ] No collection < 12 tests unless source is genuinely thin

**Coverage depth:**
- [ ] `marquee/` collection with 15+ cross-feature journeys
- [ ] `widgets/` collection with one focused test per major widget
- [ ] `filters/` collection with multi-condition logic
- [ ] `navigation/` collection with deep-link + permission tests
- [ ] 30+ variant stories across major axes (types / roles / currencies / field types)
- [ ] CRUD: all 4 ops × every variant verified
- [ ] Dropdowns: multiple options tested per dropdown
- [ ] Tabs: content tests (not just switch tests)
- [ ] Dialogs: open/submit/cancel flows
- [ ] Forms: required-field validation

**Output quality:**
- [ ] Zero duplicate `checksumTestId` (verified via grep)
- [ ] Zero modifications/deletions to existing `.checksum.md` (`git status --short \| grep -v "^??" \| grep -v "^A "` = 0)
- [ ] Reviewer score Good or Excellent on final pass
- [ ] CSV coverage matrix generated
- [ ] PR conventions match (title, branch, commit prefix, body — verified via `gh pr view <recent>`)

**If any box is unchecked: dispatch another agent. Do not declare done.**

Ask yourself: *"If I added another 20 tests right now, would they feel meaningful or padding?"* — if "meaningful," **keep going.**
