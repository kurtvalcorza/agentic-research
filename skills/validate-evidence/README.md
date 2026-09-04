# Validate Evidence

Evidence strength grading using GRADE (Grading of Recommendations Assessment, Development and Evaluation) and Oxford CEBM (Centre for Evidence-Based Medicine) frameworks.

## GRADE modes

The skill now has two explicit certainty contracts:

- **Legacy / compatibility mode — `scripts/grade_profile.py`**: preserves existing schema `1.0`, result-level RoB traceability, five-domain completeness, legal upgrades, no cross-result aggregate certainty, and fail-closed arithmetic. Existing reviews remain reproducible under the contract they were created with.
- **Current GRADE Book mode — `scripts/grade_profile_current.py`**: schema `2.0`, intended for new full outcome-level GRADE assessments. It adds versioned GRADE guidance provenance, a target of certainty, decision thresholds, structured relative/absolute effects, baseline risk for dichotomous outcomes, `-3` extremely-serious downgrades with explicit justification, explicit domain-overlap accounting, canonical `dissemination_bias`, and a fuller Summary of Findings table.

The current GRADE Book is a living source. Every `2.0` record therefore carries `grade_guidance.source`, `grade_guidance.profile`, and `grade_guidance.as_of`; old records are not silently reinterpreted under newer guidance.

> **Compatibility:** `publication_bias` is accepted by the current-mode parser as a legacy alias and is normalized to `dissemination_bias` with a migration note. A record containing both names is malformed. The legacy `1.0` checker is unchanged.

## What It Does

- **Evidence-Body Classification**: summarizes the design mix contributing to each result.
- **Risk-of-Bias Synthesis**: current/full systematic-review records require `risk_of_bias.basis: confirmed_rob`; the legacy checker additionally resolves those claims against the upstream appraisal record when `--rob` is supplied.
- **Result-Level Grading**: assigns certainty (High, Moderate, Low, Very Low) to each protocol outcome; current/full mode is outcome-level rather than theme-level.
- **Decision Context**: current mode requires the target/range/threshold about which certainty is being rated.
- **Effect Context**: current mode represents participant/study counts and, where applicable, relative effects, baseline risk, absolute effects, and intervals.

## Current GRADE Book profile

A current-mode result is conceptually:

```text
result
├── outcome + time point
├── effect
│   ├── measure
│   ├── relative estimate / interval (where applicable)
│   ├── baseline risk (dichotomous outcomes)
│   └── absolute estimate / interval (where applicable)
├── decision thresholds
├── target of certainty
├── starting level
├── domains
│   ├── risk_of_bias
│   ├── inconsistency
│   ├── indirectness
│   ├── imprecision
│   └── dissemination_bias
├── explicit domain overlap / already-accounted-for records
├── legal upgrades
├── final certainty
└── certainty statement + footnotes
```

Run:

```bash
python skills/validate-evidence/scripts/grade_profile_current.py grade-profile-v2.json --strict
python skills/validate-evidence/scripts/grade_profile_current.py grade-profile-v2.json --strict --json
```

A `-3` domain downgrade is representable only as a whole step and requires a visible, non-empty justification. If two domains are explicitly declared to share the same cause, the current checker rejects a record that downgrades both for that same declared concern; it does not try to infer overlap from prose.

For dichotomous outcomes, current mode requires the decision-relevant chain needed for absolute effects: relative estimate and interval, baseline risk, absolute effect and interval. Continuous outcomes require a continuous estimate and interval. Narrative/no-pooled-estimate outcomes remain representable but must still identify contributing studies and participants.

## Summary of Findings

Current mode generates a result-level Summary of Findings table containing:

- outcome and time point;
- relative/continuous effect and interval as applicable;
- baseline risk and absolute effect for dichotomous outcomes;
- participants and contributing studies;
- the declared decision target and threshold context;
- certainty rating/symbol;
- certainty explanation and footnotes.

This is intentionally richer than the legacy certainty-summary table.

## Verification boundary

Both checkers validate **structure, traceability requirements that their contract can observe, legality, and arithmetic**. They do not decide whether an expert's threshold, effect estimate, or domain judgment is substantively correct. A clean result is a floor for an auditable GRADE assessment, not an automated expert certification.

Repository-level wording should therefore remain **GRADE-aligned** unless a specific review's declared GRADE profile has passed its applicable machine checks and required human judgments.

## Oxford CEBM

Oxford CEBM remains available as an alternative evidence hierarchy for use cases that are not performing a full GRADE certainty assessment.

## Related Skills

- `appraise-risk-of-bias` — upstream human-gated RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2 appraisal.
- `synthesize-research` — evidence synthesis and claim-strength use.
- `validate-citations` — attribution integrity.
- `validate-manuscript` — manuscript-level quality checks.
- `review-literature` — literature-review orchestration.

## Standalone use

This skill can be invoked independently. Use legacy mode only when preserving an existing `1.0` review contract; prefer current GRADE Book mode for new full outcome-level GRADE work.
