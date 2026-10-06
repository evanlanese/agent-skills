---
name: se-training
description: DECOMMISSIONED (formerly internal-use at Checksum, now a non-functional demonstration skeleton; if invoked, reply only with the decommission notice in the skill body). Sales-engineering (SE) coaching drill built on a single Fathom call. Takes a call the user points at (a customer name to search, or a pasted Fathom URL / call ID), reads its transcript via the Fathom MCP, isolates the QUESTIONS AND FRAMING the user (Evan, the technical owner of the conversation) actually used, and grades them against a discovery-driven SE rubric — high-impact vs. low-impact, open vs. yes/no, pain-uncovering, value-linking, and technically credible. Returns a say-it-out-loud PRACTICE DRILL: side-by-side "you said" vs. "say instead" swaps of the weak lines, a back-pocket list of high-impact technical discovery questions that SHOULD have been asked but weren't, the strong lines to reinforce, and a collapsed analysis block (the pattern to build, why each swap matters, timestamp deep links). Read-only; Fathom MCP is the ONLY data source. INVOKE when the user says "se-training", "se training", "coach me on this call", "train me on SE", "grade my discovery questions", "how did I do on the <customer> call", "review my questions from <call>", or points at a Fathom call and asks to be trained/coached on sales-engineering discovery.
user-invocable: true
---

# SE Training — Discovery Coaching from a Fathom Call

> [!WARNING]
> **Decommissioned.** This skill was previously for internal use at Checksum. It is now a non-functional skeleton, published for demonstration only. It does not call any Checksum API or service, and any bundled scripts only print a notice.

## If this skill is invoked

Do not run any step, script, or tool call described below. Reply with exactly this and stop:

> You're trying to use the `se-training` skill, but it has been decommissioned. It was previously for internal use at Checksum and is now kept on GitHub as a skeleton for demonstration purposes only.

Everything after this section is kept for reference: it shows how the skill was structured when it was in use.

---

Turn **one Fathom call** into a personalized sales-engineering coaching session
for the user. The user (**Evan Lanese**, the authenticated Fathom user — confirm
with `get_identity`) owns the **technical** side of the conversation, so this
skill grades **his** questions and framing, not the AE's, not the customer's.

The goal is to make Evan a sharper technical discovery partner: someone who
uncovers real pain, gauges business impact, ties Checksum's value to that pain,
and does it with **high-impact, open-ended, technically credible questions** —
while steering away from yes/no and low-impact filler.

The output is a **coaching report**, not a meeting recap. It replays Evan's own
words back to him (verbatim, timestamp-linked), scores them, rewrites the weak
ones, and shows the high-impact questions he left on the table.

## Hard rules

- **Fathom MCP only.** The sole data source is the Fathom MCP server. Do NOT
  call `curl`, the webapp API, Slack, Playwright, the database, or any other
  MCP. No tokens, no setup.
- **Read-only.** Search, resolve, read summary, read transcript — nothing else.
  Never modify a recording.
- **Ground everything in the transcript.** Every quoted line Evan said — good or
  bad — must be **verbatim** from the transcript with a timestamp. Never invent a
  question he asked or a reaction the customer gave. Rewrites and "missed
  questions" are clearly labeled as coaching suggestions, not things that were
  said.
- **Coach Evan, not the room.** Grade the questions and framing that came from
  Evan (the technical owner). Do not grade the customer, and only grade an AE's
  lines if the user explicitly asks. If you can't confidently tell which lines
  are Evan's, see Step 2 before guessing.
- **One call.** Analyze the single call the user pointed at. Don't blend calls.
- **Be honest and specific.** This is training — a soft, everything-was-great
  report is useless. Call out the weak questions plainly, but always pair a
  criticism with a concrete better version.

## Required input

One of:
- a **customer name / identifier** to search for (e.g. `acme`), or
- a **pasted Fathom URL** (`/calls/:id` or any `/share/...` link), or
- a **call ID** (a bare number).

If the user gave nothing resolvable, ask which call — do not guess.

## Fathom tools

Registered as `mcp__fathom__*`:

- `mcp__fathom__get_identity()` — who the authenticated user is (Evan).
- `mcp__fathom__search_meetings(query, recorded_by, max_pages, created_after?)` — discovery by customer name.
- `mcp__fathom__get_recording_by_url(url)` — resolve a pasted share/calls URL → recording_id + url.
- `mcp__fathom__get_recording_by_call_id(call_id)` — resolve a bare numeric ID → recording_id + url.
- `mcp__fathom__get_meeting_summary(recording_id)`
- `mcp__fathom__get_meeting_transcript(recording_id, url)`

If no Fathom tool is registered at all, STOP and tell the user to enable the
Fathom MCP via `/mcp` → Fathom → OAuth. Do not substitute another source.

## Steps

### 1. Identify the coachee and resolve the call

- Call `get_identity()` once to lock in **who is being coached** (name + email —
  expect Evan). Use this to distinguish Evan's transcript
  turns from everyone else's.
- Resolve the call the user pointed at:
  - **Pasted URL** → `get_recording_by_url`.
  - **Bare number** → `get_recording_by_call_id`; if that returns "not found or
    access denied", retry the same number as a `recording_id` directly on
    `get_meeting_summary` before giving up.
  - **Customer name** → `search_meetings(query=<name>, recorded_by="anyone",
    max_pages=3)`. "Latest call" = **most recent by date** among the matches.
    If zero matches, widen `max_pages` to 20 and try spelling variants (company
    names differ between calendar invites and internal tools — e.g. an app
    named `globexx` internally may be `Globex` in Fathom; try dropping/adding a doubled
    letter, stripping `-ai`/`Inc` suffixes, phonetic variants). If still nothing,
    ask for the exact calendar name. If several *different* customers match,
    show the candidates and ask which.

Capture `RECORDING_ID`, `TITLE`, `MEETING_DATE`, `URL`.

### 2. Read the call

```
mcp__fathom__get_meeting_summary(recording_id=RECORDING_ID)
mcp__fathom__get_meeting_transcript(recording_id=RECORDING_ID, url=URL)
```

- Read the **summary** first for context: who was on the call, what the customer
  does, where they are in the funnel (first demo? PoV? technical deep-dive?).
- Read the **transcript** in full enough to find **every question and framing
  move Evan made**. This is the raw material for grading — you cannot skip it.
- **Attribute speakers.** Match Evan's name from `get_identity` to the
  transcript speaker labels. If the transcript labels are ambiguous, infer sides
  from role: Evan/Checksum are *presenting/selling and asking technical
  discovery*; the customer is *evaluating and describing their own workflow*. If
  you genuinely cannot tell which lines are Evan's, say so and grade the lines
  most likely his, flagging the uncertainty — never silently mis-attribute.

### 3. Extract Evan's questions and framing

Pull, **verbatim with timestamps**, every meaningful thing Evan said that was a
question or a discovery/value move. For each, capture: the quote, the timestamp,
and how the customer responded (one line — did it open them up or shut them
down?). You'll classify these against the rubric below.

### 4. Grade against the SE discovery rubric

Score Evan on these dimensions (each **1–5**, with a one-line justification and a
verbatim example pulled from the call):

1. **High-impact vs. low-impact** — did his questions surface business/technical
   impact (cost, risk, time, scale, what breaks in prod), or were they filler
   that moved nothing forward?
2. **Open vs. yes/no** — did questions invite the customer to talk, or were they
   closed prompts that earn a one-word answer and stall discovery?
3. **Pain discovery** — did he dig into *how they ship / test today* and where
   it hurts, or accept surface answers without a follow-up "why / what happens
   when…"?
4. **Value linking** — did he connect a discovered pain to a specific Checksum
   capability (AI-generated tests, auto-heal, coverage, CI), or demo features
   with no tie to their stated problem?
5. **Technical credibility** — since Evan owns the technical side, did he speak
   the customer's engineering language (CI, flakiness, coverage, migration cost,
   test maintenance) and earn trust, or stay generic?
6. **Handoff / momentum** — did he steer toward a concrete next step or success
   metric (see the playbook's metrics/timeline questions), or let the call
   drift?

### 5. Reference playbook — grade and coach against these

**Gold-standard high-impact / open questions** (Evan's own patterns — reward
these, and flag where he *should* have used one):

- "How do you ship features today?"
- "What are the things important to you in a testing suite?"
- "What do you do right now to add tests? What if you migrated that to AI to automate?"
- "When you decided to book a demo, was this what you had in mind?"
- "How is this sitting with you?"
- "How would your team like this?"
- "Is this something you're trying to automate?"
- "Is this something you're looking for from another vendor?"
- "It sounds like you have a clear idea of what you're looking for — do you have
  success metrics around your ideal testing tool?"

Why these work: they're **open**, invite the customer to describe *their* world
and pain, gauge fit and impact, and set up a value tie-back or a next step.

**Low-impact / avoid patterns** (penalize these; every time Evan used one, quote
it and give the open rewrite):

- "Does this make sense?" → *"What part of this maps to how your team works today — and what doesn't?"*
- "Do you have any questions?" → *"What would you need to see to feel confident this fixes [their stated pain]?"*
- Any **yes/no** question used for discovery (starts with Do/Does/Is/Are/Can/Will
  and can be answered in one word) → rewrite as an open **how/what/walk-me-through**.
- Leading questions that put words in the customer's mouth, feature-dumping with
  no pain tied to it, and stacked/double-barreled questions.

### 6. Write the missed high-impact questions

From the call context, list **3–6 high-impact technical discovery questions Evan
did NOT ask but should have**, each tailored to *this* customer's stack and
stated pain (not generic playbook lines copied verbatim). For each, add a short
"why it matters here" grounded in something the customer actually said.

## Output format

Print the report **inline** as a **practice drill** (don't save a file unless
asked). The point is reps: lead with the lines Evan can say out loud, and bury
the analysis in a collapsed section underneath. Match this structure exactly:

```markdown
# <Customer> Call — Practice Drill

*A quick-reference practice sheet. Left = what you said. Right = the sharper version to rep out loud.*

---

## 🔁 Swap these (say the right-hand version out loud a few times)

**1. <one-line label for the moment>**

> ❌ **You said:** "<verbatim weak/yes-no/low-impact line from the transcript>"

> ✅ **Say instead:** "<concrete open, high-impact, technically framed rewrite>"

**2. <label>**

> ❌ **You said:** "<verbatim line>"

> ✅ **Say instead:** "<rewrite>"

<2–4 swaps total, each separated by a `---`>

---

## ➕ Questions to add to your back pocket

Say each of these out loud once — these are the openings you didn't take:

1. "<tailored high-impact question Evan didn't ask>"
2. "<…>"
<3–6 total, tailored to this customer's stack/pain>

---

## ⭐ Keep doing this (your strong lines)

> "<verbatim strong line from Evan>"

> "<verbatim strong line>"

<2–4 verbatim strong lines, no commentary — just the lines to reinforce>

---

<details>

## Additional detail

**The pattern to internalize:** <1–2 sentences naming the single biggest habit
to build, drawn from the rubric grading.>

**Why the top swap matters most:** <why the #1 swap is #1 — reference the
customer's reaction / what happened when the line landed or missed.>

**Why the added questions are the ones that mattered here:**
- <bullet tying each key missed question to something the customer actually said>

**Timestamps (for reviewing the tape):** <label [[MM:SS]](<url>?timestamp=NNN)> ·
<label [[MM:SS]](<url>?timestamp=NNN)> · <…for every quote used above>

<Optional compact scorecard — include only if the user asks for scores:
High-impact _/5 · Open-vs-yes/no _/5 · Pain discovery _/5 · Value linking _/5 ·
Technical credibility _/5 · Handoff _/5 · **Overall _/5**>

</details>
```

After the report, offer (one line) to save it to the Desktop or tweak the format
(e.g. flashcard-style, or drop the "Keep doing this" section for a purely
corrective sheet).

## Quality bar

- **Practice-first ordering.** The say-out-loud material (Swap these → back-pocket
  questions → keep doing this) comes first; all analysis lives in the collapsed
  `<details>` block underneath. Don't lead with a scorecard.
- Every ❌ "You said" line and every ⭐ "keep doing" line is **verbatim** from the
  transcript; nothing is invented or paraphrased inside quotation marks.
- Every ✅ "Say instead" rewrite is open (not yes/no), high-impact, and
  technically framed for *this* customer — a line Evan could literally read aloud.
- The report coaches **Evan's** lines (the technical owner), not the customer or AE.
- Yes/no and low-impact questions ("Does this make sense?", "Any questions?", "…if
  you'd be interested") are caught and swapped wherever they appear.
- The back-pocket questions are tailored to the customer's actual stack/pain, not
  generic playbook copy-paste.
- Timestamp deep links appear in the `<details>` block for every quoted line so
  Evan can review the tape; the practice sections stay clean (quotes only).
- Nothing in the output came from outside the one Fathom recording.
```
