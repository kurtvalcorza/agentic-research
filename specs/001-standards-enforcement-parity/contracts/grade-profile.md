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
| 1 | All five domain keys present | exit 1 — reported by name as missing, never read as `0`. Every independently decidable rule below still runs, so one absent domain cannot conceal the rest of the result's problems |
| 2 | `rating` ∈ {0, −1, −2} | exit 2 — outside vocabulary |
| 3 | Misspelled domain key | exit 2 — **not** treated as a missing domain |
| 4 | `starting_level` matches predominant `design_mix` entry, or carries `starting_level_justification` | exit 1 |
| 5 | `clamp(index(starting) + Σdomains + Σupgrades, 1, 4)` equals `index(final)` | exit 1 — reports both sides and the difference |
| 6 | Upgrades non-zero only when the predominant design starts **below high** (so not `rct` and not `dta`) **and** all domain ratings are `0` | exit 1 |
| 7 | Upgrade keys ⊆ {`large_effect`, `dose_response`, `opposing_confounding`}; `large_effect` is `0`/`1`/`2`, while the other two are `0`/`1` only | exit 2 |
| 8 | No `overall_certainty` or any cross-result aggregate key | exit 2 |
| 9 | `basis` is `confirmed_rob` or `heuristic`; `heuristic` stamps output PROVISIONAL, and fails under `--strict` for `systematic` and `umbrella`; permitted for `rapid` only with `streamlined_method_disclosed` | exit 1 |
| 10 | With `--rob`: every `study_ids` entry resolves to a **confirmed** study, matched exactly | exit 1 |
| 11 | `basis: confirmed_rob` without `--rob` | exit 1 |
| 12 | Body-level `risk_of_bias` rating not contradicted by the per-study distribution, or carries `coherence_justification` | exit 1 |
| 13 | `study_ids` unique within a result; `results[].id` unique | exit 2 |
| 14 | `results` non-empty | exit 2 |
| 15 | Every result has a non-empty string `certainty_statement` for the generated summary of findings | exit 2 |
| 16 | With `--rob`: optional `evidence`, when present, is an object keyed only by that instrument's domains with non-empty string values | exit 2 |
| 17 | With `--rob`: an appraisal a result relies on that breaks a rule of [risk-of-bias.md](./risk-of-bias.md) — an absent domain, an overall more favourable than its worst domain, a Newcastle-Ottawa band mismatch, an overall of `low` over a `no_information` domain | exit 1 — reported per study with the appraisal's own message, and the appraisal cannot back a `confirmed_rob` basis |

**Rule 17 and the exit-code split.** This check reads the appraisal record itself, because it may
not import the sibling skill (constitution Principle III). It must therefore classify what it finds
the way that skill does: a record that is READABLE but breaks a rule is exit 1 with diagnostics,
and only a record that cannot be interpreted at all is exit 2. Treating an incomplete or incoherent
appraisal as unreadable made the two checks agree that a file was bad and disagree about what kind
of bad — and the reader lost the diagnostics one of them prints. `appraised_result` is likewise
matched **verbatim**: a padded reference is reported as a near-miss, never normalised into a match.

**Scope.** Rule 17 covers **every** appraisal in the supplied record, cited or not. Reporting only
the cited ones split the file's own entries against each other: a misspelled domain name in an
uncited appraisal exited 2 while a *missing* domain in that same appraisal was accepted silently.
A violation in an appraisal a result relies on additionally says it cannot back that result's
`confirmed_rob` basis.

The one thing scoped to cited appraisals is **human confirmation** (Rule 10). Whether a judgment
has been signed off governs whether a rating may *rest* on it, so it is checked where a rating
does. An appraisal awaiting sign-off for some other result is `rob_appraisal.py`'s `H_rob` to
report, not a reason to fail this certainty record.

**Rule 12 predicate.** Contradiction is declared when the rating is `0` while more than half the
resolved studies are rated high risk, or when the rating is `-2` while every resolved study is
rated low risk. Only the clearly-contradictory ends are flagged; the wide middle is left to
judgement, because the check may only assert what is decidable (constitution Principle VI).

## Generated artifacts

1. **Evidence profile** — one row per result: its **id**, study count, design mix, each domain
   judgment with its note, and the final certainty with its symbol. A `starting_level` permitted
   only by a `starting_level_justification` is marked `†` and the justification is printed with
   the notes, so the departure never appears unexplained.
   The `†` marks a **departure that a justification permits** — not merely that a justification
   was recorded. An unjustified departure carries no marker, because it is reported as a violation
   instead; a marker there would point at a footnote the record never wrote.

   Applied `upgrades` get their own column and are named with their levels in the notes: they are
   the only adjustment that RAISES certainty, so a row without them cannot be reconciled. Where the
   sum runs past high or below very low, the bound is marked `⌁` and explained, since a clamped row
   otherwise simply does not add up on the page.

   A `coherence_justification`, an appraisal's `overall_justification` where a rating rests on it,
   and `streamlined_method_disclosed` are all rendered for the same reason: **an exception the
   record needs in order to be legal must be visible to the reader of the artifact.**

2. **Summary of findings** — one row per result: its **id**, the plain-language finding, the
   certainty symbol, and the certainty statement.

Below the check, `U_grade: N` reports the number of RESULTS carrying at least one violation — the
count `verify-review` consumes. It is emitted rather than left to be counted off the diagnostics
because one result can raise four, and a loop counting messages books four units of outstanding
work for one broken result. Violations belonging to the `--rob` record rather than to a result are
reported separately and excluded from that count.

Both tables carry the result id because only `id` is required to be unique — two results may share
a label, and every diagnostic names the id, so a table without it cannot be matched to the check
output beneath it.

Both carry a header line stating whether certainty is keyed to outcomes or themes (FR-008), and a
provenance line naming the generating check and source record (constitution Principle VII).


## `appraised_result` (required with `confirmed_rob`)

Each certainty result names the appraised target it relies on. An appraisal covers
one result, so without this a study appraised for mortality could back a certainty
rating about quality of life.

| Rule | Violation |
|:--|:--|
| `appraised_result` present when any domain declares `confirmed_rob` | exit 1 — absent and blank alike; a blank names nothing, which is what omitting it does, and the message says which of the two it was. Read **only** when the basis is `confirmed_rob`, so a leftover blank on a `heuristic` result is not a failure |
| It names a result the appraisal record actually covers, compared **verbatim** | exit 1 — a near-miss names its nearest neighbour rather than resolving to it |
| Every `study_ids` entry resolves at `(study, appraised_result)` | exit 1 — studies appraised for a *different* result are reported separately from unresolved ones |
