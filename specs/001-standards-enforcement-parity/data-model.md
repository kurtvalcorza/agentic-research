# Phase 1 Data Model: Standards Enforcement Parity

Four record types, each a single JSON document consumed by one check. Field-level contracts and
worked examples live in [contracts/](./contracts/); this document defines the entities, their
relationships, and the validation rules with their originating requirements.

## Rules applying to every record

| Rule | Requirement |
|:--|:--|
| A `schema_version` string is required. Absent or unrecognised → malformed input (exit 2). | FR-044 |
| Unknown keys at any level are rejected, never ignored. | FR-028 |
| An empty primary collection (`results`, `studies`, `items`) is a failure, not a pass. | FR-029 |
| Counts must be whole non-negative numbers; booleans and non-integral floats are rejected. | Edge cases |
| Study identifiers are compared byte-for-byte; no case or whitespace normalisation. | FR-042 |

`schema_version` is `"1.0"` for all four records in this feature.

---

## Entity: Certainty Record

One document per review. Consumed by the certainty check.

| Field | Type | Rules |
|:--|:--|:--|
| `schema_version` | string | Required, must be recognised (FR-044) |
| `review_type` | enum | `systematic` \| `scoping` \| `rapid` \| `umbrella` \| `narrative`. Drives FR-009 |
| `synthesis_mode` | enum | `outcome` \| `theme`. Required; labels the generated artifact (FR-008) |
| `streamlined_method_disclosed` | string | Required **only** when `review_type` is `rapid` and any basis is `heuristic` (FR-009) |
| `results` | array of Result | Non-empty (FR-029) |

An `overall_certainty` key — or any aggregate across results under any name — is rejected as
malformed input (FR-007, D-016). This is a rejection rather than an omission: the concept must be
inexpressible, not merely undocumented.

### Nested: Result

| Field | Type | Rules |
|:--|:--|:--|
| `id` | string | Unique within `results` |
| `label` | string | Human-readable; appears in the generated profile |
| `study_ids` | array of string | Non-empty; unique within the result (FR-042) |
| `design_mix` | object | Counts by design: `rct`, `nrsi`, `observational`, `case_series`. Whole non-negative numbers |
| `starting_level` | enum | `high` \| `moderate` \| `low` \| `very_low` |
| `starting_level_justification` | string | Required when `starting_level` disagrees with the predominant entry in `design_mix` (FR-004) |
| `domains` | object | Exactly the five keys below — all required, none defaulted (FR-001) |
| `upgrades` | object | Optional; keys restricted to the three permitted reasons (FR-006) |
| `final` | enum | Same vocabulary as `starting_level`; must satisfy the arithmetic rule (FR-003) |
| `certainty_statement` | string | Prose reported alongside the rating |

### Nested: Domain Judgment

Keys are exactly `risk_of_bias`, `inconsistency`, `indirectness`, `imprecision`,
`publication_bias`. A missing key is reported by name as missing — never read as "no concern"
(FR-001). A misspelled key is malformed input, not a missing domain (FR-028).

| Field | Type | Rules |
|:--|:--|:--|
| `rating` | integer | `0`, `-1`, or `-2` only. No partial steps (FR-002) |
| `note` | string | Justification for the judgment |
| `basis` | enum | **`risk_of_bias` only**: `confirmed_rob` \| `heuristic` (FR-009) |
| `coherence_justification` | string | **`risk_of_bias` only**: required when the rating contradicts the per-study distribution (FR-043) |

### Nested: Upgrades

Permitted keys, each `0`, `1`, or `2`: `large_effect`, `dose_response`, `opposing_confounding`.
Any other key is malformed input, which is what makes "importance of findings" unrepresentable
(FR-006). A non-zero upgrade is legal only when the body is non-randomized **and** every domain
rating is `0` (FR-005).

### Validation: certainty arithmetic

```
level_index: very_low=1, low=2, moderate=3, high=4
computed = clamp(index(starting_level) + Σ domain ratings + Σ upgrades, 1, 4)
computed must equal index(final)                                      (FR-003)
```

A mismatch reports both sides and the difference, in the manner `prisma_flow.py` reports a failed
reconciliation.

---

## Entity: Appraisal Record

One document per review. Consumed by the appraisal check.

| Field | Type | Rules |
|:--|:--|:--|
| `schema_version` | string | Required |
| `studies` | array of Study Appraisal | Non-empty (FR-029) |

### Nested: Study Appraisal

| Field | Type | Rules |
|:--|:--|:--|
| `id` | string | Study identifier. **Not unique on its own** — a study contributing to two results carries two appraisals (FR-042) |
| `design` | enum | `rct` \| `nrsi` \| `observational` \| `dta`. A property of the study, so it MUST agree across that study's own appraisals |
| `instrument` | enum | Must correspond to `design` per the table below (FR-011) |
| `result_assessed` | string | **Required.** Which result this appraisal applies to — RoB 2 and ROBINS-I assess a result, not a study. `(id, result_assessed)` is the identity; it is unique within `studies` (FR-042) |
| `domains` | object | Exactly the instrument's domain keys, each a legal value (FR-012) |
| `evidence` | object | Domain key → quoted supporting text with location |
| `overall` | enum | Instrument's overall vocabulary |
| `overall_justification` | string | Required when `overall` is more favourable than the worst domain (FR-013) |
| `confirmed_by` | string | Non-empty (FR-014) |
| `confirmed_at` | string | Non-empty date |

### Instrument vocabularies

| Design | Instrument | Domains | Domain and overall values |
|:--|:--|:--:|:--|
| `rct` | `rob2` | 5 | `low`, `some_concerns`, `high` |
| `nrsi` | `robins_i` | 7 | `low`, `moderate`, `serious`, `critical`, `no_information` |
| `observational` | `nos` | 3 star-blocks | Integer stars within each block's maximum |
| `dta` | `quadas2` | 4 | `low`, `high`, `unclear` — risk of bias for all four, applicability for the first three |

Exact domain keys per instrument are enumerated in
[contracts/risk-of-bias.md](./contracts/risk-of-bias.md) and mirrored into
`references/instruments.md`, so that guidance and schema cannot drift (FR-012).

**State transition.** A study appraisal is *provisional* until `confirmed_by` and `confirmed_at`
are both non-empty, at which point it is *confirmed*. There is no reverse transition and no
automated path into the confirmed state (FR-026). The count of provisional studies is reported as
the outstanding human gate (FR-014). The check establishes that a confirmation record exists; it
cannot establish who wrote it (FR-015).

---

## Entity: Reporting Checklist Record

| Field | Type | Rules |
|:--|:--|:--|
| `schema_version` | string | Required |
| `variant` | enum | `prisma_2020` (27 numbered items expanding to **42 addressable rows**) \| `prisma_scr` (row set and count **to be transcribed from source**, not asserted here) — selected by review type (FR-022) |
| `items` | array of Checklist Item | Non-empty; must cover every **row** the variant defines, not every top-level number |

### Nested: Checklist Item

| Field | Type | Rules |
|:--|:--|:--|
| `number` | string | Item identifier as published, e.g. `"7"`, `"13a"` |
| `location` | string | Where addressed — section and page. Mutually exclusive with `not_applicable` |
| `not_applicable` | string | Justification for non-applicability. Mutually exclusive with `location` |

An item with neither field, or with both, is unaddressed and is listed by number in the output;
under `--strict` this fails the check (FR-020). Item topic labels are supplied by the check from
its own table rather than by the record, and official item wording is referenced rather than
reproduced (D-013).

---

## Entity: Review Units Record (extended, not new)

Consumed by the existing verification-loop backend. This feature adds three units and changes one
gate from asserted to computed.

| Unit | Weight | Source | Counts |
|:--|:--:|:--|:--|
| `U_grade` | 1 | certainty check | Results failing any certainty rule — replaces "not yet graded" (FR-023) |
| `U_rob_trace` | 1 | certainty check `--rob` | Referenced studies not resolving to a confirmed appraisal (FR-017) |
| `U_checklist` | 1 | checklist check | Items neither located nor justified (FR-020) |
| `H_rob` | gate | appraisal check | Studies without confirmation — now computed, previously asserted (FR-014) |

### Applicability by review type

| Unit | systematic | umbrella | rapid | scoping | narrative |
|:--|:--:|:--:|:--:|:--:|:--:|
| `U_grade` | ✅ | ✅ | ✅ | ⬜ | ⬜ |
| `U_rob_trace` | ✅ | ✅ | ⬜ (heuristic basis permitted) | ⬜ | ⬜ |
| `U_checklist` | ✅ | ✅ | ✅ | ✅ (scoping variant) | ⬜ |
| `H_rob` | ✅ | ✅ | ⬜ | ⬜ | ⬜ |

An applicable unit absent from the record is reported as **missing**, and the review cannot be
declared verified (FR-024). An inapplicable unit is **absent**, not zero-to-achieve (FR-025) —
the distinction the existing backend already draws for its declared scope.

---

## Relationships

```
Certainty Record ──references──> Appraisal Record
     (study_ids[], appraised_result)   (studies[].id, studies[].result_assessed)
     exact match on the PAIR, unique within each record  (FR-042)
     a study appraised for a DIFFERENT result does not resolve
     resolution required when domains.risk_of_bias.basis == confirmed_rob   (FR-017)
     path supplied at invocation, never imported                            (FR-019)

Certainty Record ──produces──> evidence profile + summary of findings       (FR-010)
Appraisal Record ──produces──> per-study table + traffic-light summary      (FR-016)
Checklist Record ──produces──> completed reporting checklist                (FR-021)

All three ──feed──> Review Units Record ──> verification verdict            (FR-023)
```

The certainty record depends on the appraisal record only through identifiers supplied at
invocation. Neither skill knows the other exists at rest, which is what keeps each directory
independently copyable.
