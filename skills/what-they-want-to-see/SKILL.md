---
name: what-they-want-to-see
description: DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional demonstration skeleton; if invoked, reply only with the decommission notice in the skill body). Answer one question about a customer's most recent Fathom call — "what did they want to see from Checksum?" Reads the meeting summary + transcript via the Fathom MCP and returns a short, grounded breakdown of the capabilities the customer asked to see, the things they want proven before committing, the scope they ruled out, and the materials they asked for — each claim tied to the customer's own words with a timestamp deep link. Takes a customer name/identifier as its argument. Deliberately concise; no next steps, no sentiment section, no scorecard, no recommendations. Read-only; Fathom MCP is the ONLY data source. INVOKE when the user says "what-they-want-to-see", "what did they want to see", "what does <customer> want from Checksum", "what are <customer>'s requirements", "what did <customer> ask for", "what are they looking for", "what do they need to see", or names a customer and asks what they wanted out of Checksum on their last call.
user-invocable: true
---

# What Did They Want to See From Checksum?

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. It does not call any Checksum API or service, and any bundled scripts only print a notice.

## If this skill is invoked

Do not run any step, script, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `what-they-want-to-see` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Answer exactly one question about a customer's **most recent Fathom call**:
*what did they want to see from Checksum?*

The deliverable is a short prose-and-bullets breakdown of the customer's asks —
the capabilities they wanted demonstrated, the things they need proven before
they commit, what they took off the table, and what they asked to be sent. Every
claim is grounded in the customer's own words.

This skill is a companion to `last-fathom-call-steps`, not a replacement.
That skill answers *what happens next*; this one answers *what they want*. Keep
them separate — do **not** emit next steps or a sentiment quote here.

## Hard rules

- **Fathom MCP only.** The sole data source is the Fathom MCP server. Do NOT
  call `curl`, the webapp API, Slack, Playwright, the database, or any other
  MCP. No tokens, no setup.sh, no network calls outside Fathom.
- **Read-only.** Search, summarize, read transcript — nothing else.
- **Don't fabricate.** Every ask must be traceable to the meeting summary or
  transcript. If the customer didn't ask for it, it doesn't go in the list —
  even if it's an obvious thing a customer like this "would" want. Never
  upgrade a Checksum-initiated demo beat into a customer requirement: if
  Checksum showed it unprompted and the customer didn't react, it's not an ask.
- **Never ask for a Fathom URL.** Resolve the meeting from the customer
  argument via `search_meetings`. Only ask the user something if resolution
  genuinely fails (see Step 1).
- **One meeting.** Cover the single most recent matching **customer-facing**
  meeting. Don't blend multiple meetings together.
- **Stay concise.** This is a one-screen answer, not a report. See the
  Anti-scope-creep list at the bottom — it is a hard boundary, not a suggestion.

## Required input

**Customer** — a name or identifier passed as the argument (e.g. `Acme`,
`globex`, `IBM`). This is the search query.

## Fathom tools

The Fathom MCP tools are registered as `mcp__fathom__*`:

- `mcp__fathom__search_meetings(query, recorded_by, max_pages, created_after?)`
- `mcp__fathom__get_meeting_summary(recording_id)`
- `mcp__fathom__get_meeting_transcript(recording_id, url)`

(If this connector surfaces under a different prefix — e.g.
`mcp__claude_ai_Fathom__*` — use whichever Fathom tools are actually
registered. If no Fathom tool is available at all, STOP and tell the user to
enable the Fathom MCP via `/mcp` → Fathom → OAuth. Do not substitute another
source.)

## Steps

### 1. Resolve customer → most recent customer-facing meeting

```
mcp__fathom__search_meetings(query=<customer>, recorded_by="anyone", max_pages=3)
```

- Search uses **AND logic** over meeting title + summary and only scans recent
  pages by default. On **no match**, widen before giving up:
  - Bump `max_pages` to `20`.
  - Try **spelling variants**. Company names are often spelled differently on
    calendar invites than in internal tools (e.g. an app named `globexx`
    internally may be `Globex` in Fathom). Try dropping/adding a
    doubled letter, removing `-ai`/`Inc`/`Corp` suffixes, and phonetic variants.
- Pick the most recent **customer-facing** meeting. **Skip internal calls that
  merely mention the customer** — a "Weekly Sales Call", pipeline review, or
  internal sync will match the search because the customer is named in its
  summary, but the customer wasn't in the room, so it cannot tell you what they
  want. Prefer a title with the customer's name in it (demo, technical
  evaluation, kickoff, PoV sync, discovery).
- If the most recent match is internal and you fall back to an older
  customer-facing call, **say so in one line at the end of the output**.
- If **still zero matches** after widening + variants, ask the user for the
  exact name as it appears on the calendar invite — do not guess.
- If **several plausible different customers** appear (ambiguous query), show
  the candidates and ask which one. Never silently pick across customers.

Capture: `RECORDING_ID`, `TITLE`, `MEETING_DATE`, `URL`, and `CUSTOMER_TAG`
(the customer's display name, proper-cased from the argument — acronyms
uppercased, e.g. `ibm` → `IBM`; company names title-cased, e.g. `acme`
→ `Acme`).

### 2. Read the meeting

```
mcp__fathom__get_meeting_summary(recording_id=RECORDING_ID)
mcp__fathom__get_meeting_transcript(recording_id=RECORDING_ID, url=URL)
```

- Pull the **summary** first. Its "Specific Requirements", "Pain Points",
  "Objections", and "Questions They Asked" sections are the spine of the answer.
- Pull the **transcript** on every run — the summary flattens *who* asked for
  what and strips the customer's phrasing, and you need both. Transcripts are
  large; fetch **at most one per run**. If the transcript output is too large to
  read inline, it is persisted to a file — read that file with Bash
  (`python3 -c`, `grep`, `sed -n`) rather than re-fetching.
- **Speaker labels in Fathom transcripts are frequently offset by one segment**
  — the name attached to a block sometimes belongs to the previous speaker. Do
  not trust a label blindly. Confirm attribution from content (who is selling
  vs. who is evaluating, who says "our team" about which team) before you
  attribute an ask to a named person.

### 3. Separate the asks from the noise

Read for **what the customer pulled toward**, in four buckets. Not every call
fills every bucket — **omit an empty bucket entirely** rather than padding it.

1. **The headline ask** — the business outcome underneath the feature list. One
   short paragraph, led by a bolded phrase. This is what they're actually
   buying (e.g. *capacity without headcount*, *release confidence*, *cutting
   regression cycle time*), and it should be sourced to the exec or the person
   framing the problem, not inferred from the feature requests.
2. **Specific capabilities they asked to see** — bulleted, bolded lead-in per
   item. Only things the customer raised, pushed on, or asked a question about.
3. **What they wanted proven before committing** — objections, risks, and
   trust gaps stated as conditions (source-code access, security posture,
   accuracy in their environment, integration with their stack). This bucket
   is the highest-value part of the answer; don't fold it into bucket 2.
4. **Scope they ruled out** — anything the customer themselves took off the
   table. Include it: knowing what they *don't* need is as useful as what they do.
5. **Materials / enablement they asked for** — videos, docs, a session with the
   wider team. Usually one line; drop the bucket if nothing was requested.

Grounding: attach a `[[MM:SS]](<url>?timestamp=NNN)` deep link to the handful of
claims where the customer's own words carry the weight — the headline ask, a
capability they pushed hard on, a stated objection. **Do not** link every bullet;
2–5 links across the whole answer is right. Short verbatim fragments in quotes
are welcome where the customer's phrasing is sharper than a paraphrase.

### 4. Write the answer

Prose where prose reads better, bullets where the list is genuinely a list.
Lead with one sentence naming the call the answer is grounded in.

## Output format

Print **inline** to the user (do not save a file unless asked). This shape,
with empty buckets dropped:

```markdown
Grounded in the <YYYY-MM-DD> <short call descriptor>, what <Customer> wanted from Checksum:

**<Headline ask in three or four words>.** <One or two sentences of context in
the customer's framing, with a deep link.>

**Specific capabilities they asked to see:**

- **<Capability>** — <what they actually asked, one line>.
- **<Capability>** — <what they actually asked, one line>.

**<N> things they wanted proven before committing:**

- **<Condition>** — <the concern in their words, and how it was answered on the call>.
- **<Condition>** — <the concern in their words, and how it was answered on the call>.

**Scope they ruled out for themselves:** <one or two lines>.

**And materials to sell it internally** — <one line>.
```

## Quality bar

- The answer opens by naming the call it's grounded in (date + short descriptor).
- The headline ask is the **business outcome**, not a feature — and it comes
  from the customer's framing, not yours.
- Every bullet is something the **customer** raised. Nothing Checksum
  volunteered and the customer ignored appears as an ask.
- "What they wanted proven" is its own bucket, not merged into capabilities.
- 2–5 timestamp deep links total, on the claims that carry the most weight.
- Speaker attributions were verified against content, not taken from the
  transcript label alone.
- If an older call was used because the newest match was internal, that's noted
  in one closing line.
- Nothing in the output came from outside the one Fathom recording.
- The whole thing fits comfortably on one screen.

## Anti-scope-creep

The value here is that it's short and answers one question. Do **not** add:

- next steps, owners, or action items (that's `last-fathom-call-steps`)
- a customer-sentiment section or a sentiment quote
- deal mechanics — pricing, seats, budget, procurement steps, timelines,
  decision makers — unless the customer framed one as a thing they want to
  *see* (e.g. "show us a project-based pricing model")
- coaching, scoring, or advice on how to run the next call (that's `se-training`)
- a recommendation of what Checksum should do
- test-suite data, bug counts, pass rates, or anything from the Checksum app
- a saved file, a table of contents, or section numbering
