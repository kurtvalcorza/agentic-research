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
| 3b | An edge is reconciled when **both** its counts are present; a count recorded as `0` is checked, not skipped. Omitting a count skips its edge — that is an incomplete record, not a contradictory one | — |
| 4 | Databases/registers arm: `identified − removed = screened`, `screened − excluded(t/a) = sought`, `sought − not_retrieved = assessed`, `assessed − excluded(full-text) = included` | exit 1 — reports both sides and the difference |
| 5 | Other-methods arm, when present: `identified = sought`, `sought − not_retrieved = assessed`, `assessed − excluded = included` | exit 1 |
| 6 | `studies_included_databases + studies_included_other = studies_included_total` | exit 1 |

Permitted keys: `schema_version`, `identified_databases`, `identified_registers`,
`identified_other`, `duplicates_removed`, `removed_other_reasons`, `records_screened`,
`records_excluded_title_abstract`, `reports_sought`, `reports_not_retrieved`, `reports_assessed`,
`reports_excluded`, `studies_included_databases`, `other_reports_sought`,
`other_reports_not_retrieved`, `other_reports_assessed`, `other_reports_excluded`,
`studies_included_other`, `studies_included_total`.

## Two deliberate breaking changes to a shipped script

Both are behavioural changes to code that was already working, made because
[cli-contract.md](./cli-contract.md) binds this check as much as the three added by this feature —
"a check that deviates is non-conforming regardless of whether its own rules are correct".

1. **Quoted counts are rejected** rather than coerced (D-019). A record using `"3"` for a count
   now exits 2.
2. **`schema_version` is required and unknown keys are rejected** (D-020). Rules 1 and 2 above.
   Previously a record with a misspelled count key — `recrods_screenedd` — dropped that count
   silently, reconciled over what remained, and printed an authoritative ✅ over a number nobody
   had checked. That is the exact fail-open FR-028's unknown-key rule exists to prevent, in the
   artifact the README leads with.

Existing records need `"schema_version": "1.0"` added and any stray keys removed.

## What this cannot check

Whether the counts are **true**. Reconciliation proves the numbers are mutually consistent, not
that they describe what happened: a run that screened 400 records and recorded 380 reconciles
perfectly and is still wrong. The counts must come from the stages that own them — `acquire-corpus`,
`dedupe-records`, `screen-literature` — and must never be adjusted to make this check pass.
Adjusting a count to satisfy the arithmetic converts a detectable error into an undetectable one.
