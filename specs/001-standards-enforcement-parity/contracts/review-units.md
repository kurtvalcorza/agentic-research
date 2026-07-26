# Contract: Review Units Record (`units.json`) — extension

Consumed by the existing `skills/verify-review/scripts/review_units.py`. This feature **extends**
an established contract; everything not listed here is unchanged.

## Existing configuration (unchanged)

```python
DEFAULT_WEIGHTS = {
    "U_cite_external": 3, "U_cite_internal": 1, "U_screen": 1,
    "U_extract": 1, "U_prisma": 1, "U_grade": 1, "U_consistency": 1,
}
GATE_KEYS      = ("H_rob", "H_screen_adj", "H_cite_manual", "H_numeric")
UNIVERSAL_FLOOR = ("U_cite_external", "U_cite_internal", "U_consistency")
CONSISTENCY_GATE = 75 ; PLATEAU_K = 3 ; CEILING = 25
```

## Additions

```python
DEFAULT_WEIGHTS["U_rob_trace"] = 1
DEFAULT_WEIGHTS["U_checklist"] = 1
```

`U_grade` keeps its weight of 1 and its key. Only its **definition** changes: from the undocumented
"themes not yet graded" to "results failing the certainty check under `--strict`" (FR-023).
`H_rob` keeps its key and its position in `GATE_KEYS`; only its **source** changes, from asserted
to computed by the appraisal check (FR-014).

`UNIVERSAL_FLOOR` is **not** extended. The floor is the set every review type must satisfy however
light; certainty, traceability, and reporting completeness are review-type dependent and belong in
the in-scope set instead.

## Unit definitions

| Unit | Weight | Produced by | Counts |
|:--|:--:|:--|:--|
| `U_grade` | 1 | certainty check | Results violating any certainty rule |
| `U_rob_trace` | 1 | certainty check with `--rob` | Referenced studies not resolving to a confirmed appraisal |
| `U_checklist` | 1 | checklist check | Rows neither located nor justified |
| `H_rob` | gate | appraisal check | Studies lacking confirmation |

## In-scope resolution by review type

Passed as `units_in_scope`, resolved once at classification and frozen for the run.

| Unit | systematic | umbrella | rapid | scoping | narrative |
|:--|:--:|:--:|:--:|:--:|:--:|
| `U_grade` | ✅ | ✅ | ✅ | ⬜ | ⬜ |
| `U_rob_trace` | ✅ | ✅ | ⬜ | ⬜ | ⬜ |
| `U_checklist` | ✅ | ✅ | ✅ | ✅ | ⬜ |
| `H_rob` | ✅ | ✅ | ⬜ | ⬜ | ⬜ |

`U_rob_trace` and `H_rob` are out of scope for rapid reviews because the heuristic basis is
permitted there (research.md D-009); a rapid review still grades certainty, so `U_grade` applies.
Scoping reviews report against the scoping checklist variant but do not grade certainty.

## Fail-closed behaviour (existing, extended to the new units)

The backend already refuses `VERIFIED` when a declared in-scope unit is absent from the map. The
new units inherit this without new machinery: a systematic review whose `units.json` omits
`U_checklist` lists it under `missing_units` and cannot be reported verified (FR-024).

Inapplicable units are **absent**, not zero-to-achieve (FR-025). The existing distinction between
"missing" and "out of scope" is what makes this correct, and it is not modified.

## Example

A complete record captured **mid-review**, with units still outstanding — two ungraded results,
one unresolved risk-of-bias reference, four unaddressed checklist rows. The verdict is therefore
not `VERIFIED` and the exit code is 1. That is the fail-closed behaviour above, shown working
rather than described. `tests/test_contract_examples.py` runs this record and pins that outcome.

```json
{
  "review_type": "systematic",
  "units_in_scope": ["U_cite_external", "U_cite_internal", "U_consistency",
                     "U_screen", "U_extract", "U_prisma",
                     "U_grade", "U_rob_trace", "U_checklist"],
  "units": {
    "U_cite_external": 0, "U_cite_internal": 0, "U_consistency": 0,
    "U_screen": 0, "U_extract": 0, "U_prisma": 0,
    "U_grade": 2, "U_rob_trace": 1, "U_checklist": 4
  },
  "gates": {"H_rob": 3, "H_screen_adj": 0, "H_cite_manual": 0, "H_numeric": 0},
  "cycle": 4
}
```

Verdict: **CONTINUE** — seven units outstanding across three checks, and three appraisals awaiting
human confirmation. `H_rob` is never auto-satisfied by further cycles (FR-026).
