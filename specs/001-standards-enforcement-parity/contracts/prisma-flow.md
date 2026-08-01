# Contract: Flow Counts Record (`counts.json`)

Consumed by `skills/prisma-flow/scripts/prisma_flow.py`. Generates the PRISMA 2020 flow diagram
and reconciles the arithmetic end to end. Shared CLI behaviour is in
[cli-contract.md](./cli-contract.md).

This contract was written **after** the check it describes. The flow check predates this feature,
and its schema lived only in a Python docstring — which made it the one check whose documented
example nothing executed, and therefore the only one that could drift the moment the schema
changed. It changed twice in this feature (see below), so the example now lives here and
`tests/test_contract_examples.py` runs it on every commit.

## Invocation

```bash
python skills/prisma-flow/scripts/prisma_flow.py counts.json --strict
```

## Example

Template 1 — databases and registers only. Reconciles end to end, exits 0 under `--strict`.

```json
{
  "schema_version": "1.0",
  "identified_databases": {"OpenAlex": 412, "CrossRef": 88},
  "identified_registers": {"PROSPERO": 0},
  "duplicates_removed": 96,
  "removed_other_reasons": 0,
  "records_screened": 404,
  "records_excluded_title_abstract": 328,
  "reports_sought": 76,
  "reports_not_retrieved": 4,
  "reports_assessed": 72,
  "reports_excluded": {"wrong population": 18, "not empirical": 9, "wrong outcome": 7},
  "studies_included_databases": 38,
  "studies_included_total": 38
}
```

Arithmetic: `500 identified − 96 removed = 404 screened − 328 excluded = 76 sought − 4 not
retrieved = 72 assessed − 34 excluded = 38 included`. ✅

That record reports `✅ Counts reconcile — 5 of 5 stages checked: identification, screening,
retrieval, eligibility, merge` — every applicable stage, because it supplies every count they
read. A record omitting an operand is told which stages could not be reached, in the artifact
itself rather than only in the skill documentation, because `prisma-flow.md` is what gets
published and read.

## The two arms

PRISMA 2020 ships two flow templates and the check renders whichever the counts describe. Adding
any non-zero `identified_other` / `other_reports_*` / `studies_included_other` value selects
Template 2, whose parallel arm runs its own sought → assessed → excluded chain and merges at
*studies included*. The arms are reconciled **independently** and then merged: other-methods
reports enter at the report level, never pooled into title/abstract screening.

## Rules

| # | Rule | Violation type |
|:--:|:--|:--|
| 1 | `schema_version` present and recognised | exit 2 |
| 2 | Only the keys enumerated below; a misspelled count is malformed input | exit 2 |
| 3 | Every count is a whole, non-negative JSON number — booleans, quoted numbers, fractions and non-finite values all rejected | exit 2 |
| 3b | An edge is reconciled when **every count it reads** is present — not merely the two its name mentions; a count recorded as `0` is checked, not skipped. Omitting any operand skips that edge: an incomplete record, not a contradictory one. Two operands are groups (`identified_databases`/`identified_registers`, and `duplicates_removed`/`removed_other_reasons`) and count as supplied when any member is, because omitting one member states that category is zero while omitting the group states nothing. Rule 8 bounds the other end: omitting *every* identification or *every* inclusion count is malformed input | — |
| 4 | Databases/registers arm: `identified − removed = screened`, `screened − excluded(t/a) = sought`, `sought − not_retrieved = assessed`, `assessed − excluded(full-text) = included` | exit 1 — reports both sides and the difference |
| 5 | Other-methods arm, when present: `identified = sought`, `sought − not_retrieved = assessed`, `assessed − excluded = included` | exit 1 |
| 6 | `studies_included_databases + studies_included_other = studies_included_total`, checked when the grand total and **every arm the record describes** are supplied. Each arm total is required only when that arm is described — neither is required unconditionally, so an other-methods-only flow needs `studies_included_other` and not `studies_included_databases`. An arm is described when the record says anything at all about it, zeros included | exit 1 |
| 7 | The five breakdown keys — `identified_databases`, `identified_registers`, `identified_other`, `reports_excluded`, `other_reports_excluded` — map a source or reason to its own count and must be objects. A bare number is malformed input, not a total | exit 2 |
| 8 | At least one identification key (`identified_databases`, `identified_registers`, `identified_other`) **and** at least one inclusion key (`studies_included_databases`, `studies_included_other`, `studies_included_total`) must be supplied. Supplied means carrying a count: `null` and `{}` are not | exit 2 |
| 9 | The reconciliation line reports how many of the **applicable** stages were checked and names any it could not reach, on every branch — clean, failing, or nothing-checked. Applicable means the stages belonging to the arms the record describes: **five** for a databases-only flow (four stages plus the merge), **four** for an other-methods-only one (three plus the merge), **eight** when it describes both. The diagram renders the same arms, so the artifact and the verdict cannot describe different flows. A record passing rule 8 that still checks no stage says so, and does not print ✅ | — |

Permitted keys: `schema_version`, `identified_databases`, `identified_registers`,
`identified_other`, `duplicates_removed`, `removed_other_reasons`, `records_screened`,
`records_excluded_title_abstract`, `reports_sought`, `reports_not_retrieved`, `reports_assessed`,
`reports_excluded`, `studies_included_databases`, `other_reports_sought`,
`other_reports_not_retrieved`, `other_reports_assessed`, `other_reports_excluded`,
`studies_included_other`, `studies_included_total`.

## Three deliberate breaking changes to a shipped script

All are behavioural changes to code that was already working, made because
[cli-contract.md](./cli-contract.md) binds this check as much as the three added by this feature —
"a check that deviates is non-conforming regardless of whether its own rules are correct".

1. **Quoted counts are rejected** rather than coerced (D-019). A record using `"3"` for a count
   now exits 2.
2. **`schema_version` is required and unknown keys are rejected** (D-020). Rules 1 and 2 above.
   Previously a record with a misspelled count key — `recrods_screenedd` — dropped that count
   silently, reconciled over what remained, and printed an authoritative ✅ over a number nobody
   had checked. That is the exact fail-open FR-028's unknown-key rule exists to prevent, in the
   artifact the README leads with.
3. **A record must name both ends of the flow, and breakdown keys must be objects** (issues #9,
   #10). Rules 7 and 8 above. Closing the key set said which keys may appear and never what may
   appear under them, nor that any must — so a record carrying nothing but `schema_version`
   produced a full diagram with every node at `n=0` and the line "counts reconcile end to end",
   exit 0 even under `--strict`. Nothing was wrong with the arithmetic: with nothing supplied no
   edge is checked, and the check could not distinguish "no edge was checked" from "no edge was
   broken". Absent counts defaulted to zero, which Principle IV forbids in as many words.

   Rule 8 was walked around twice while being written, each time by something present that says
   nothing — `null`, then `{}` — which is why it tests for a carried count rather than a key.
   Rule 9 exists because rule 8 alone was not enough: a record can satisfy it and still check no
   stage, and the ✅ was unconditional on any stage having been checked.

Existing records need `"schema_version": "1.0"` added, any stray keys removed, and at least one
identification and one inclusion count present.

**Bring-your-own-corpus runs.** When the acquisition front-end was not used there is no database
search to report, and rule 8 still applies. Declare the corpus itself as the identification
source — `"identified_databases": {"pre-collected corpus": N}`, with `"duplicates_removed": 0`
when no de-duplication was performed. Both are real counts rather than invented ones.

The corpus goes in the databases/registers arm, not `identified_other`, despite not being a
database search. Two reasons, and the label carries the meaning the arm does not: that arm is the
only one with a title/abstract screening stage, which is the stage this workflow actually uses;
and putting the corpus in the other-methods arm renders two disconnected subgraphs — an
identification box reading `n=0` feeding a screening box reading `n=N`, beside an identification
box reading `n=N` feeding a dead-end sought box reading `n=0`. Both reviewers on PR #15 raised
that independently.

`synthesize-research` and `orchestrate-research` carry the same instruction. There is no
screening-only mode, and two skill documents previously implied one.

## What this cannot check

Whether the counts are **true**. Reconciliation proves the numbers are mutually consistent, not
that they describe what happened: a run that screened 400 records and recorded 380 reconciles
perfectly and is still wrong. The counts must come from the stages that own them — `acquire-corpus`,
`dedupe-records`, `screen-literature` — and must never be adjusted to make this check pass.
Adjusting a count to satisfy the arithmetic converts a detectable error into an undetectable one.
