---
name: last-fathom-call-steps
description: DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional demonstration skeleton; if invoked, reply only with the decommission notice in the skill body). Recap a customer's most recent Fathom call (typically a Proof-of-Value sync or kickoff) using ONLY the Fathom MCP. Produces two things — a high-level, shareable "Next steps;" list where each item is tagged [Checksum] or [<CustomerName>] by owner (the customer side uses the customer's actual name, never the literal word "Customer"; no leading "- " bullet, no status icons, timestamps, or detail lines), and a "Customer sentiment" line led by a verbatim, name-attributed customer quote capturing how they feel the PoV is going with Checksum. Takes a customer name/identifier as its argument. Read-only; no webapp API, no Slack, no other data source. INVOKE when the user says "last fathom call steps", "last-fathom-call-steps", "next steps from the last <customer> call", "recap the last <customer> Fathom call", "what happened in the last <customer> meeting", "summarize <customer>'s last sync", or gives a customer name and asks for next steps + sentiment from their latest Fathom call.
user-invocable: true
---

# Last Fathom Call — Next Steps

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. It does not call any Checksum API or service, and any bundled scripts only print a notice.

## If this skill is invoked

Do not run any step, script, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `last-fathom-call-steps` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Produce a tight recap of a customer's **most recent Fathom call** (typically
their PoV weekly sync or kickoff) using **only the Fathom MCP**. The output has
exactly two sections:

1. **Next steps** — a high-level list, each item tagged `[Checksum]` or `[<Customer>]` by owner (the customer side uses the customer's actual name, e.g. `[Acme]`), with no leading `- ` bullet.
2. **Customer sentiment** — led by a verbatim, name-attributed customer quote about how the PoV is going.

This skill is deliberately narrow. It does **not** pull tests, bugs, Slack, or
any other source — its only job is to turn one Fathom recording into the
breakdown above. If you find yourself wanting any other data source, you're in
the wrong skill.

## Hard rules

- **Fathom MCP only.** The sole data source is the Fathom MCP server. Do NOT
  call `curl`, the webapp API, Slack, Playwright, the database, or any other
  MCP. No tokens, no setup.sh, no network calls outside Fathom.
- **Read-only.** Never modify a recording. Search, summarize, read transcript — nothing else.
- **Don't fabricate.** Every claim — action-item status and especially the
  sentiment quote — must be grounded in the meeting summary or transcript. The
  customer quote must be **verbatim** from the transcript, never paraphrased or
  invented. If the meeting doesn't support a claim, say so or omit it. Never
  invent an action item, a status, or a feeling the customer didn't express.
- **Never ask for a Fathom URL.** Resolve the meeting from the customer
  argument via `search_meetings`. Only ask the user something if resolution
  genuinely fails (see Step 1).
- **One meeting.** Cover the single most recent matching meeting. Don't blend
  multiple meetings together.

## Required input

1. **Customer** — a name or identifier passed as the argument
   (e.g. `acme`, `globex`). This is the search query.

## Fathom tools

The Fathom MCP tools are registered as `mcp__fathom__*`:

- `mcp__fathom__search_meetings(query, recorded_by, max_pages, created_after?)`
- `mcp__fathom__get_meeting_summary(recording_id)`
- `mcp__fathom__get_meeting_transcript(recording_id, url)`

(If this connector ever surfaces under a different prefix — e.g.
`mcp__claude_ai_Fathom__*` — use whichever Fathom tools are actually
registered. If no Fathom tool is available at all, STOP and tell the user to
enable the Fathom MCP via `/mcp` → Fathom → OAuth. Do not substitute another
source.)

## Steps

### 1. Resolve customer → most recent meeting

```
mcp__fathom__search_meetings(query=<customer>, recorded_by="anyone", max_pages=3)
```

- The search uses **AND logic** over the meeting title + summary and only
  scans recent pages by default. If you get **no match**, widen and retry
  before giving up:
  - Bump `max_pages` to `20` to look further back.
  - Try **spelling variants** of the customer name. Company names are often
    spelled differently in calendar invites than in internal tools (e.g. an
    app named `globexx` internally may be `Globex` in Fathom).
    Try dropping/adding a doubled letter, removing `-ai`/`Inc`/`Corp`
    suffixes, and the obvious phonetic variants.
- From the matches, **pick the most recent** by date. If two are equally
  recent, prefer the one whose title looks like a PoV sync / weekly sync /
  kickoff over an internal or sales call.
- If **still zero matches** after widening + variants, ask the user for the
  exact name as it appears on the calendar invite — do not guess.
- If there are **several plausible different customers** in the matches (the
  query was ambiguous), show the candidates and ask which one. Never silently
  pick across distinct customers.

Capture: `RECORDING_ID`, `TITLE`, `MEETING_DATE` (the meeting's date), the
**weekday** of that date (e.g. `Tuesday` — derive it from `MEETING_DATE`),
`URL`, and `CUSTOMER_TAG` — the customer's display name, proper-cased from the
argument the skill was invoked with (acronyms uppercased, e.g. `ibm` → `IBM`;
company names title-cased, e.g. `acme` → `Acme`). This is what you put in
the owner tag for customer-owned next steps — never the literal word `Customer`.

### 2. Read the meeting

```
mcp__fathom__get_meeting_summary(recording_id=RECORDING_ID)
mcp__fathom__get_meeting_transcript(recording_id=RECORDING_ID, url=URL)
```

- Pull the **summary** first — its "Key Takeaways" / "Topics" / "Next Steps"
  sections are usually enough for the action items.
- Pull the **transcript** for two things the summary often flattens:
  1. **Next-step ownership** — who committed to each item, so you can tag it
     `[Checksum]` vs `[Customer]` by side.
  2. **Sentiment** — the customer's actual words about how the PoV is going.
     You **must** read the transcript on every run, because the sentiment
     section requires a verbatim customer quote that only the transcript
     contains. Transcripts are large; read enough to find a representative
     customer line and confirm who owns each next step. Fetch at most one
     transcript per run.
- If the summary has a clearly delimited "Next Steps" / "Action Items"
  section, use it as the spine for Step 3 and only consult the transcript to
  resolve ownership and sentiment.

### 3. List the next steps

A clean, **high-level** list under a `## Next steps;` heading — built to
be pasted into Slack, an email, or a deck and understood by anyone. One line
per agreed next step.

**Do not** prefix the lines with a markdown bullet (`- `). Output each step as
a bare line so the user can paste them in and build their own bullet list.

Each line is **just two things**: an owner tag, then a short plain-language
description of the step. Nothing else.

```
[Checksum] Enable the Slack reporter
[Acme] Review the test suite in GitHub and send grouping/architecture feedback ASAP
```

Owner tag — exactly one per line:

- **`[<CUSTOMER_TAG>]`** — anything the customer committed to, was asked to
  provide, or owns (e.g. sharing files, reviewing the suite, hosting a build,
  giving feedback). Use the **customer's name** as the tag — the `CUSTOMER_TAG`
  captured in Step 1 (e.g. `[IBM]`, `[Acme]`). Attribute by side, not by
  individual name. NEVER use the literal word `[Customer]`.
- **`[Checksum]`** — every other next step (work Checksum / the CE owns).

Keep each line to a single high-level line. **Do not** add a leading `- `
bullet, status icons (✅/🟡/⏳/🔴), a status note, an `evidence:` field, a
timestamp, a quote, a sub-line, or an owner's personal name. Those details are
deliberately dropped — the value here is a scannable, shareable checklist. If a
step is a notable blocker, you may say so in three or four words inline (e.g.
"once the web build is hosted"), but never add a separate detail line.

Order the lines `[Checksum]` first, then `[<CUSTOMER_TAG>]`, so each side can
see its own column at a glance. Within each group, keep the meeting's order.

### 4. Write the customer sentiment

Lead with a **verbatim, name-attributed customer quote** that captures how the
**customer** (not Checksum) feels the Proof of Value is going — then, on the
next line, one short sentence of context. The model for the quote line is
exactly how the CE jots it down:

```
> "So far this is pretty much what we were hoping to see." — Sam
```

Rules:

- **The quote is verbatim** — copy the customer's actual words from the
  transcript, trimmed only at clean sentence boundaries (don't stitch together
  distant fragments). Attribute it to the **speaker's first name** as it
  appears in the transcript, after an em dash. Add a timestamp deep link after
  the attribution, e.g. `— Sam [[20:03]](<url>?timestamp=1203)`.
- **Pick the most representative customer line** — the one that best sums up
  their read on the PoV. Prefer a sentiment-bearing line (satisfaction,
  enthusiasm, skepticism, hesitation, urgency) over a logistical one. If the
  customer voiced a concern as well as approval, the context sentence is where
  you note the nuance (e.g. "positive on Week-1 output, but reserving the real
  verdict for the end-of-month release").
- **Speaker must be the customer**, never a Checksum employee. If you're unsure
  who's on which side, the customer is whoever is being sold to / evaluating —
  not the person presenting Checksum's work.
- **If the transcript carries no real customer sentiment** (e.g. they barely
  spoke, or only logistics), say so plainly in one line instead of forcing a
  quote — do not manufacture or paraphrase a feeling into quotation marks.

## Output format

Print the recap **inline** to the user (do not save a file unless asked).
Match this structure exactly:

```markdown
# PoV Recap — <Customer>

**Meeting:** <WEEKDAY>, <MEETING_DATE> · <TITLE> · [Fathom](<URL>)

## Next steps;

[Checksum] <high-level step>
[Checksum] <high-level step>
[<CUSTOMER_TAG>] <high-level step>
[<CUSTOMER_TAG>] <high-level step>

## Customer sentiment

> "<verbatim customer quote>" — <Customer first name> [[MM:SS]](<url>?timestamp=NNN)

<one short sentence of context / nuance>
```

## Quality bar

- The Meeting line leads with the weekday (e.g. `Tuesday, 2026-06-09`).
- The Next steps heading reads `## Next steps;` (with the trailing semicolon).
- Every next step is one high-level line tagged exactly one of `[Checksum]` or
  `[<CUSTOMER_TAG>]` — with **no leading `- ` bullet**, no status icons, no
  `evidence:`, no timestamps, no quotes, no sub-lines, no personal names. The
  lines are bare so the user can paste them in and build their own bullet list.
- `[<CUSTOMER_TAG>]` tags only items the customer owns; everything else is
  `[Checksum]`. Lines are grouped `[Checksum]` first, then `[<CUSTOMER_TAG>]`.
  The customer tag is the customer's actual name (e.g. `[IBM]`, `[Acme]`),
  never the literal word `[Customer]`.
- The sentiment quote is **verbatim** from the transcript, attributed to a
  named **customer** speaker, and timestamp-linked — not a paraphrase, not a
  generic "things are going well," and never attributed to a Checksum person.
- Nothing in the output came from outside the one Fathom recording.
