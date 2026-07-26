# Contract: Certainty Record (`grade-profile.json`)

Consumed by `skills/validate-evidence/scripts/grade_profile.py`. Generates the evidence profile
and summary-of-findings tables. Field definitions and rule-to-requirement mapping are in
[../data-model.md](../data-model.md).

## Invocation

```bash
python skills/validate-evidence/scripts/grade_profile.py grade-profile.json \
  --rob appraisal/risk-of-bias.json --strict
```

`--rob` supplies the appraisal record for traceability. It is **required** whenever any result
declares `basis: confirmed_rob`; omitting it under `--strict` is a violation, not a pass
(FR-018). It is a file path, never an import (FR-019).

## Example

Complete and runnable: this record exits 0 under `--strict` when paired with an appraisal
record covering P1/P3/P5/P7 at the named result. `tests/test_contract_examples.py` runs it
against `tests/fixtures/risk-of-bias.contract-example.json` on every commit, so the example
cannot drift away from the schema again.

Note `appraised_result`: it is required whenever a domain declares `confirmed_rob`, because an
appraisal targets one result rather than a whole study.

```json
{
  "schema_version": "1.0",
  "review_type": "systematic",
  "synthesis_mode": "outcome",
  "results": [
    {
      "id": "O1",
      "label": "Diagnostic accuracy at 12 months",
      "study_ids": ["P1", "P3", "P5", "P7"],
      "appraised_result": "diagnostic accuracy at 12 months",
      "design_mix": {"rct": 4, "nrsi": 0, "observational": 0, "case_series": 0},
      "starting_level": "high",
      "domains": {
        "risk_of_bias":     {"rating": 0,  "basis": "confirmed_rob", "note": "3/4 low, 1 some concerns"},
        "inconsistency":    {"rating": -1, "note": "effect direction consistent, magnitude varies widely"},
        "indirectness":     {"rating": 0,  "note": "populations match the protocol"},
        "imprecision":      {"rating": 0,  "note": "interval excludes the decision threshold"},
        "publication_bias": {"rating": 0,  "note": "comprehensive search, no small-study pattern"}
      },
      "final": "moderate",
      "certainty_statement": "Moderately confident the true effect lies close to the estimate."
    }
  ]
}
```

Arithmetic: `high(4) + (-1) = 3 = moderate`. ✅

## Rules

| # | Rule | Violation type |
|:--:|:--|:--|
| 1 | All five domain keys present | exit 1 — reported by name as missing, never read as `0` |
| 2 | `rating` ∈ {0, −1, −2} | exit 2 — outside vocabulary |
| 3 | Misspelled domain key | exit 2 — **not** treated as a missing domain |
| 4 | `starting_level` matches predominant `design_mix` entry, or carries `starting_level_justification` | exit 1 |
| 5 | `clamp(index(starting) + Σdomains + Σupgrades, 1, 4)` equals `index(final)` | exit 1 — reports both sides and the difference |
| 6 | Upgrades non-zero only when body is non-randomized **and** all domain ratings are `0` | exit 1 |
| 7 | Upgrade keys ⊆ {`large_effect`, `dose_response`, `opposing_confounding`} | exit 2 |
| 8 | No `overall_certainty` or any cross-result aggregate key | exit 2 |
| 9 | `basis` is `confirmed_rob` or `heuristic`; `heuristic` stamps output PROVISIONAL, and fails under `--strict` for `systematic` and `umbrella`; permitted for `rapid` only with `streamlined_method_disclosed` | exit 1 |
| 10 | With `--rob`: every `study_ids` entry resolves to a **confirmed** study, matched exactly | exit 1 |
| 11 | `basis: confirmed_rob` without `--rob` | exit 1 |
| 12 | Body-level `risk_of_bias` rating not contradicted by the per-study distribution, or carries `coherence_justification` | exit 1 |
| 13 | `study_ids` unique within a result; `results[].id` unique | exit 2 |
| 14 | `results` non-empty | exit 2 |

**Rule 12 predicate.** Contradiction is declared when the rating is `0` while more than half the
resolved studies are rated high risk, or when the rating is `-2` while every resolved study is
rated low risk. Only the clearly-contradictory ends are flagged; the wide middle is left to
judgement, because the check may only assert what is decidable (constitution Principle VI).

## Generated artifacts

1. **Evidence profile** — one row per result: study count, design mix, each domain judgment with
   its note, and the final certainty with its symbol.
2. **Summary of findings** — one row per result: the plain-language finding, the certainty symbol,
   and the certainty statement.

Both carry a header line stating whether certainty is keyed to outcomes or themes (FR-008), and a
provenance line naming the generating check and source record (constitution Principle VII).


## `appraised_result` (required with `confirmed_rob`)

Each certainty result names the appraised target it relies on. An appraisal covers
one result, so without this a study appraised for mortality could back a certainty
rating about quality of life.

| Rule | Violation |
|:--|:--|
| `appraised_result` present when any domain declares `confirmed_rob` | exit 1 |
| It names a result the appraisal record actually covers | exit 1 |
| Every `study_ids` entry resolves at `(study, appraised_result)` | exit 1 — studies appraised for a *different* result are reported separately from unresolved ones |
