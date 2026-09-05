# Research-profile integration in verify-review

This reference documents the opt-in methodology checks registered by the
`review_units.py` integration layer. The underlying loop remains the same bounded,
fail-closed verify-review engine; these entries make two independently developed
validators part of its mechanical verdict.

## Cochrane intervention profile

Declare the profile on the verification record:

```json
{
  "schema_version": "1.0",
  "review_type": "systematic",
  "profile": "cochrane_intervention",
  "cycle": 0,
  "units": {
    "U_cite_external": 0,
    "U_cite_internal": 0
  },
  "consistency": {"score": 90, "critical_breaks": 0},
  "gates": {},
  "checks": {
    "cochrane_profile": {"record": "cochrane-profile.json"}
  }
}
```

`profile: cochrane_intervention` automatically adds `U_cochrane` to the frozen
scope even when `units_in_scope` does not name it. The profile therefore cannot be
declared while its validator is silently omitted: without the `cochrane_profile`
check, `U_cochrane` is underived and `VERIFIED` is unreachable.

The profile is valid only with `review_type: systematic`. Generic systematic
reviews remain backward compatible because no Cochrane unit is added unless the
profile is explicitly selected.

## Current/full GRADE

Current GRADE is additive to the legacy GRADE contract. Opt in by declaring
`U_grade_current` in `units_in_scope` and the corresponding check:

```json
{
  "schema_version": "1.0",
  "review_type": "systematic",
  "cycle": 0,
  "units_in_scope": ["U_grade_current", "U_rob_trace"],
  "units": {
    "U_cite_external": 0,
    "U_cite_internal": 0
  },
  "consistency": {"score": 90, "critical_breaks": 0},
  "gates": {},
  "checks": {
    "grade_profile_current": {
      "record": "grade-profile-v2.json",
      "rob_record": "risk-of-bias.json"
    },
    "rob_appraisal": {"record": "risk-of-bias.json"}
  }
}
```

`grade_profile_current` derives `U_grade_current`. When it is given `rob_record`,
that path is covered by the same appraisal-identity invariant as legacy
`grade_profile`: a `rob_appraisal` check must run against the same resolved file,
otherwise the verification record is malformed rather than clean. This preserves
the human-gate closure while allowing the current certainty engine to perform its
own exact `(study, result)` traceability check.

Current GRADE is not auto-added by `review_type` because the repository deliberately
preserves two certainty contracts: legacy/schema-1.0 and current/full/schema-2.0.
The chosen certainty contract is therefore an explicit frozen-scope decision.

## Limits

The integration layer proves that the child validators ran and that their reported
units participate in the verdict. It does not authenticate a claimed human actor,
make a methodological judgment correct, or prove that a supplied artifact describes
the review that actually occurred. Those limits remain owned and documented by the
Cochrane, GRADE, and appraisal validators themselves.
