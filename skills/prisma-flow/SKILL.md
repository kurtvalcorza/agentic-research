---
name: prisma-flow
description: Assemble a PRISMA 2020 flow diagram from the REAL counts produced by the review pipeline (identification per source, duplicates removed, screened, excluded with reasons, included) and verify the numbers reconcile end to end. Use when reporting a systematic/scoping/literature review, or whenever a PRISMA flow diagram is required. Replaces hand-drawn or hollow flow diagrams with one computed from actual run data.
---

# prisma-flow

## Purpose

The PRISMA 2020 flow diagram is the single visual audit trail of a review's selection process — and mismatched or invented numbers are the most common reason reviewers flag a review as non-reproducible. This skill assembles the flow diagram from the **actual counts** produced by the pipeline (`acquire-corpus` identification, `dedupe-records` duplicates removed, `screen-literature` screened/excluded/included) and **fails if the arithmetic does not reconcile**. No more hollow "PRISMA flow" artifacts whose duplicate/screening numbers came from nowhere.

## When to use

- Reporting any systematic, scoping, or literature review (PRISMA 2020 / PRISMA-ScR).
- As the reporting step after screening completes in `orchestrate-research` / `synthesize-research`.
- Any time someone asks for "the PRISMA flow diagram".

## Procedure

Collect the real counts from the run into a JSON object (full schema in `scripts/prisma_flow.py`). PRISMA 2020 has two identification arms and the script renders whichever the counts describe:

- **Databases & registers** (left column): identification per database/register, duplicates removed, records screened, excluded at title/abstract, reports sought / not retrieved / assessed, reports excluded **with reasons**, studies included.
- **Other methods** (right column, optional): records identified via citation searching / websites / organisations, then their own sought / not retrieved / assessed / excluded chain — these reports enter at the report level, *not* title/abstract screening.

The two arms reconcile **independently** and merge at *studies included in review*. Omit the other-methods fields for a databases-only (Template 1) flow. Registers belong in the databases/registers arm, not "other methods".

```
python scripts/prisma_flow.py counts.json            # renders Mermaid + reconciliation
python scripts/prisma_flow.py counts.json --strict   # exit 1 if counts do not reconcile
```

The script renders a Mermaid flowchart (GitHub/Markdown-renderable) and runs a **reconciliation check** on each arm:
- *Databases/registers:* identified − duplicates removed = screened; screened − excluded(title/abstract) = sought; sought − not retrieved = assessed; assessed − excluded(full-text) = studies included (databases).
- *Other methods:* identified = sought; sought − not retrieved = assessed; assessed − excluded = studies included (other).
- *Merge:* studies included (databases) + studies included (other) = studies included in review.

Any break is reported with the exact discrepancy. Fix the counts (usually a miscount or a stage where records were silently dropped) before publishing — a flow diagram that does not reconcile is the classic reviewer red flag.

## Output

- `prisma-flow.md` — the Mermaid PRISMA 2020 flow diagram + the reconciliation result (✅/⚠️).
- Full-text exclusion reasons are tabulated (PRISMA 2020 requires citing full-text exclusions **with reasons**).

## Companion check — `scripts/prisma_checklist.py`

The flow diagram is one of PRISMA 2020's two reporting artifacts; the other is the **checklist**.
This skill ships both.

```bash
python scripts/prisma_checklist.py checklist.json --strict
```

### ⚠️ 27 numbered items, 42 addressable rows

PRISMA 2020 is customarily cited as "27 items", but several expand into lettered sub-items
(10a–b, 13a–f, 16a–b, 20a–d, 23a–d, 24a–c). **Completeness is evaluated over the 42 rows.**
Only **21** of the 27 customary numbers exist as rows; the other six (`10`, `13`, `16`, `20`,
`23`, `24`) exist *only* as their lettered rows. So a record listing a bare `13` is not an
incomplete record — it is malformed input (exit 2), because `13` is not an addressable row. A
record addressing those 21 plus the FIRST letter of each expanding item is 27/42 complete, and the
check reports the fifteen gaps rather than passing.

> **The flow record now requires `"schema_version": "1.0"` and rejects unknown keys.** A
> misspelled count key used to drop silently out of the record while the remaining arithmetic
> reconciled and the diagram printed ✅. Both rules are shared with every other check
> (`contracts/cli-contract.md`); the full schema is in `contracts/prisma-flow.md`.

> **The record must also name both ends of the flow, and each breakdown key must be an
> object.** A record supplying no counts used to produce a full diagram with every node at
> `n=0` and the line "counts reconcile end to end", exit 0 even under `--strict` — because
> with nothing supplied no edge is checked, and the check could not tell "no edge was
> checked" from "no edge was broken". It now requires at least one of
> `identified_databases` / `identified_registers` / `identified_other` **and** at least one
> of `studies_included_databases` / `studies_included_other` / `studies_included_total`,
> and rejects the record otherwise (exit 2, no artifact). Presence is what is required, not
> magnitude: a review that identified nothing and included nothing is a real outcome and
> still passes, as long as it says so.
>
> Separately, the five breakdown keys — the three `identified_*` and the two
> `*reports_excluded` — map each source or reason to its own count, so they must be
> objects. Given a bare number they used to raise `AttributeError` and exit 1; they now
> report the expected shape and exit 2.

Each row needs either a `location` in the manuscript or an explicit `not_applicable`
justification — an empty value addresses nothing. Unaddressed rows are listed **above** the table
with a count, because in forty-two rows a gap shown only as a blank cell is a gap nobody sees.

Item numbers and topic labels come from Page MJ, et al. *BMJ* 2021;372:n71 (CC BY 4.0). The
official wording is **referenced, not reproduced** — the generated checklist links to the source.

### PRISMA-ScR is deliberately not implemented

The scoping variant refuses with an explanation rather than running. Its item table could not be
transcribed from an accessible copy of the source (the official site serves PDFs only; the Annals
article is subscription-gated). An approximated table would make **every** completeness verdict
wrong while appearing authoritative — worse than having no check at all. To enable it, transcribe
the table from Tricco et al., *Ann Intern Med* 2018;169:467-473, add it to the script, and update
the README standards row.

### ⚠️ What this check CANNOT verify

That the cited location **actually addresses** the item. "Methods, p.4" satisfies the check
whether or not page 4 says anything relevant. It verifies that a location or justification was
recorded — not that the reporting is adequate.

## ⚠️ What the flow check CANNOT verify

**That the counts are true.** Reconciliation proves the numbers are mutually consistent, not that
they describe what actually happened — a run that screened 400 records but recorded 380 reconciles
perfectly and is still wrong.

The counts must come from the stages that own them and **must never be adjusted to make the check
pass**. Editing a count to satisfy the arithmetic converts a detectable error into an undetectable
one, which is strictly worse than the failing check you started with.

**That the record is complete.** Requiring an identification and an inclusion count establishes
that the flow has two named ends; it does not establish that everything between them was
reported. An edge is checked only when **every count it reads** was supplied, so a partially
reported flow is incomplete rather than contradictory, and the check says nothing either way
about the stages left out.

What it will no longer do is pretend otherwise. The reconciliation line reports how many of the
**applicable** stages were checked and **names the ones it could not reach**; a record where
none were checked says so outright rather than printing a tick — "Nothing was reconciled … This
diagram reports the counts given; it does not attest to them." A bare ✅ over a flow nothing had
examined was the fail-open behind #9. Applicable means the stages belonging to the arms the
record actually describes: four plus the merge for a databases-only flow, three plus the merge
for an other-methods-only one, all eight when it describes both.

**Which stages it did not check.** An edge is compared only when **every** count it reads was
supplied — not merely the two its name mentions. So an omitted count leaves its stage unexamined
rather than assumed to be zero, and the reconciliation line names how many of the applicable
stages were checked. A record reporting "2 of 5 stages checked" reconciles as far as it was
asked to; it says nothing about the three it could not reach.

Two operands are groups rather than single keys, and a group counts as supplied when any member
is: identification sums `identified_databases` and `identified_registers`, and the removal box
sums `duplicates_removed` and `removed_other_reasons`. Omitting one member states that category
is zero, which is a real claim about the run; omitting the whole group states nothing.

## Boundaries

- This reports the flow; it does not produce the counts — they come from the upstream pipeline skills. If a count is missing, get it from the stage that owns it, don't invent it.
- The script auto-selects PRISMA 2020 Template 1 (databases/registers only) or Template 2 (with the other-methods arm) from the counts. This is the *new-review* structure; for an updated review, adapt to the updated-review template.
- Scoping reviews use PRISMA-ScR (same flow shape, no certainty assessment).

## Related

- `acquire-corpus` (identification counts), `dedupe-records` (duplicates removed), `screen-literature` (screening/eligibility counts)
- `orchestrate-research`, `synthesize-research`, `review-literature` (call this at the reporting step)
