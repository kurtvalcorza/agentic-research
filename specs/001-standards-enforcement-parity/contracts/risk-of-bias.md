# Contract: Appraisal Record (`risk-of-bias.json`)

Consumed by `skills/appraise-risk-of-bias/scripts/rob_appraisal.py`. Generates the per-appraisal
table and traffic-light summary, and reports the outstanding human gate.

## Invocation

```bash
python skills/appraise-risk-of-bias/scripts/rob_appraisal.py risk-of-bias.json --strict
```

## Instrument domain keys

These keys are the schema. `references/instruments.md` is updated to carry the same list, so
guidance and schema cannot drift (FR-012).

### `rob2` — randomized trials (5 domains)

`randomization`, `deviations`, `missing_data`, `measurement`, `selection_of_result`

Values: `low` | `some_concerns` | `high`. Overall algorithm: approximately the worst domain.

### `robins_i` — non-randomized studies of interventions (7 domains)

`confounding`, `participant_selection`, `intervention_classification`, `deviations`,
`missing_data`, `outcome_measurement`, `selection_of_result`

Values: `low` | `moderate` | `serious` | `critical` | `no_information`. Overall: the worst domain.

### `nos` — cohort and case-control (3 star-blocks)

`selection` (max 4), `comparability` (max 2), `outcome_or_exposure` (max 3)

Values: integers within each block's maximum. Overall derived from the total of 9: `low` risk at
7–9, `moderate` at 4–6, `high` at 0–3. The thresholds are conventional rather than definitional,
so the check reports the total alongside the band and permits an `overall_justification` to
override the band.

### `quadas2` — diagnostic test accuracy (4 domains)

`patient_selection`, `index_test`, `reference_standard`, `flow_and_timing`

Each carries `risk_of_bias` with values `low` | `high` | `unclear`. The first three additionally
carry `applicability` with the same vocabulary. Overall risk of bias: `high` if any domain is
high, else `unclear` if any is unclear, else `low`.

## Example

`result_assessed` is required: identity is the pair `(id, result_assessed)`, not the study id.
This record is complete and runs clean under `--strict`; `tests/test_contract_examples.py`
executes it on every commit.

```json
{
  "schema_version": "1.0",
  "studies": [
    {
      "id": "P1",
      "design": "rct",
      "instrument": "rob2",
      "result_assessed": "diagnostic accuracy at 12 months",
      "domains": {
        "randomization": "low",
        "deviations": "low",
        "missing_data": "some_concerns",
        "measurement": "low",
        "selection_of_result": "low"
      },
      "evidence": {
        "randomization": "p.4: 'computer-generated allocation sequence, sealed opaque envelopes'",
        "missing_data": "p.7: 18% attrition, reasons not reported by arm"
      },
      "overall": "some_concerns",
      "confirmed_by": "K. Valcorza",
      "confirmed_at": "2026-07-26"
    }
  ]
}
```

## Rules

| # | Rule | Violation type |
|:--:|:--|:--|
| 1 | `instrument` corresponds to `design` (`rct`→`rob2`, `nrsi`→`robins_i`, `observational`→`nos`, `dta`→`quadas2`) | exit 1 |
| 2 | Exactly the instrument's domain keys present — no missing, no extra | exit 2 for unknown key; exit 1 for missing |
| 3 | Each domain value in that instrument's vocabulary | exit 2 |
| 4 | `overall` in the instrument's vocabulary | exit 2 |
| 5 | `overall` not more favourable than the worst domain, unless `overall_justification` present | exit 1 |
| 6 | `confirmed_by` and `confirmed_at` present and non-empty | exit 1, counted into `H_rob` |
| 7 | `(id, result_assessed)` unique within `studies` — the study id alone is **not** unique, see [Identity](#identity-study-result-not-study) | exit 2 |
| 8 | `studies` non-empty | exit 2 |
| 9 | `design` agrees across every appraisal of the same `id` | exit 2 |
| 10 | `evidence`, when present, is an object whose keys are that instrument's domains and whose values are non-empty strings | exit 2 |

**Rule 10 is optional-but-typed.** Absent or `{}` is legal — evidence is not required. Supplying
it in any other shape is not: `null`, a string, a list or an integer previously passed through
untouched and the record exited 0 under `--strict`, then went on to back a `confirmed_rob`
certainty rating. On the instrument-mismatch path the keys are not checked, because the declared
instrument is the wrong yardstick to measure them against; the object-and-string requirements
still apply.

## Generated artifacts

1. **Per-appraisal table** — id, design, instrument, result assessed, each domain judgment,
   overall, confirmation status. One row per appraisal, so a study contributing to two results
   appears twice. The header states both figures — *N appraisals of M studies* — because they
   differ, and the study count is the manuscript-facing one.
2. **Traffic-light summary** — (study, result) × domain grid. Every row names the result it
   assesses, so a study appraised for two outcomes does not render as two identically-labelled
   rows carrying different judgments. Encoded with **both** a symbol and a text label rather than
   colour alone, so the artifact remains legible in print, to screen readers, and to colour-blind
   readers.

Both artifacts carry a provenance line naming the generating check and source record, as the
certainty and checklist artifacts do (constitution Principle VII).

Output states the `H_rob` count of appraisals and, per FR-015, carries this line verbatim:

> This check establishes that a confirmation record is present. It cannot establish that a human
> made the judgment, or who that person was.


## Identity: (study, result), not study

RoB 2 and ROBINS-I appraise **a specific result**, not a study as a whole. A study
contributing to two outcomes therefore carries **two appraisals** with two different
risk-of-bias judgments.

- `result_assessed` is **required**, and uniqueness is on `(id, result_assessed)`.
- Appraising the same study twice for the **same** result is ambiguous → exit 2.
- A study's **design** may not differ between its own appraisals: design is a
  property of the study, only the judgment varies by result → exit 2.

Keying identity on the study id alone made the correct representation
**inexpressible** — the second appraisal was rejected as a duplicate — while the
consuming check resolved on study id and could back a certainty rating with an
appraisal targeting a different outcome.
