# Validate Evidence

Evidence strength grading using GRADE (Grading of Recommendations Assessment, Development and Evaluation) and Oxford CEBM (Centre for Evidence-Based Medicine) frameworks.

## GRADE modes

The skill has two explicit certainty contracts:

- **Legacy / compatibility mode — `scripts/grade_profile.py`**: preserves schema `1.0`, result-level RoB traceability, five-domain completeness, legal upgrades, no cross-result aggregate certainty, fail-closed arithmetic, and the existing outcome/theme pathway. Existing reviews remain reproducible under the contract they were created with.
- **Current GRADE Book mode — `scripts/grade_profile_current.py`**: schema `2.0`, intended for new full outcome-level GRADE assessments. It adds versioned GRADE guidance provenance, a target of certainty, structured decision-threshold targets, structured relative/absolute effects, baseline risk for dichotomous outcomes, `-3` extremely-serious downgrades with explicit justification, explicit domain-overlap accounting, canonical `dissemination_bias`, and a fuller Summary of Findings table.

The current GRADE Book is a living source. Every `2.0` record therefore carries `grade_guidance.source`, `grade_guidance.profile`, and `grade_guidance.as_of`; old records are not silently reinterpreted under newer guidance.

> **Compatibility:** `publication_bias` is accepted by the current-mode parser as a legacy alias and is normalized to `dissemination_bias` with a migration note. A record containing both names is malformed. The legacy `1.0` checker remains the compatibility path.

## What It Does

- **Evidence-Body Classification**: summarizes the design mix contributing to each result.
- **Risk-of-Bias Synthesis**: a `confirmed_rob` basis is never accepted as a self-asserted string. Strict systematic/umbrella current-mode runs must supply `--rob` and resolve every cited study at the exact upstream `result_assessed` target. The same upstream appraisal schema used by the legacy checker is reused here.
- **Result-Level Grading**: assigns certainty (High, Moderate, Low, Very Low) to protocol outcomes. Legacy theme-level synthesis remains available for GRADE-inspired adaptations; current/full mode is outcome-level.
- **Decision Context**: current mode requires both free-text `target_of_certainty` and a structured `target_threshold` that names a declared threshold, effect basis, and whether the target claims that threshold is met.
- **Effect Context**: current mode represents participant/study counts and, where applicable, relative effects, baseline risk, absolute effects, and intervals.

## Risk-of-bias provenance boundary

GRADE risk-of-bias judgments are downstream of `appraise-risk-of-bias`, which applies the design-appropriate instrument and records the human confirmation. They are **not** ad hoc LLM judgments and must not be recreated inside the certainty engine.

For a current/full systematic or umbrella review, run the profile with the generated appraisal artifact:

```bash
python skills/validate-evidence/scripts/grade_profile_current.py grade-profile-v2.json \
  --rob ../appraise-risk-of-bias/appraisal/risk-of-bias.json --strict
```

The current checker resolves each `(study_id, appraised_result)` pair against that appraisal record, rejects unresolved or unconfirmed appraisals, and reconciles the resolved study designs against `design_mix`. This preserves the result-level traceability invariant from the legacy checker.

## Current GRADE Book profile

A current-mode result is conceptually:

```text
result
├── outcome + time point
├── appraised_result
├── effect
│   ├── measure
│   ├── relative estimate / interval (where applicable)
│   ├── baseline risk (dichotomous outcomes)
│   └── absolute estimate / interval (where applicable)
├── decision thresholds
├── target of certainty
├── target_threshold
│   ├── threshold_label
│   ├── effect_basis
│   └── claim: meets | does_not_meet
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
python skills/validate-evidence/scripts/grade_profile_current.py grade-profile-v2.json \
  --rob ../appraise-risk-of-bias/appraisal/risk-of-bias.json --strict
python skills/validate-evidence/scripts/grade_profile_current.py grade-profile-v2.json \
  --rob ../appraise-risk-of-bias/appraisal/risk-of-bias.json --strict --json
```

A `-3` domain downgrade is representable only as a whole step and requires a visible, non-empty justification. If two domains are explicitly declared to share the same cause, the current checker rejects a record that downgrades both for that same declared concern; it does not try to infer overlap from prose.

For dichotomous outcomes, current mode requires the decision-relevant chain needed for absolute effects: relative estimate and interval, baseline risk, absolute effect and interval. Continuous outcomes require a continuous estimate and interval. Narrative/no-pooled-estimate outcomes remain representable but must still identify contributing studies and participants.

The structured `target_threshold` is deliberately conservative. For one-sided `above`/`below` thresholds, the checker flags a contradiction only when the declared effect interval lies wholly on the opposite side from the target claim. If the interval crosses the threshold, or the threshold shape is not mechanically decidable from one scalar boundary, expert judgment remains explicit rather than inferred from prose.

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

## Result-level certainty invariant

**One certainty rating per protocol outcome or synthesis theme.** In full/current GRADE mode, that means one rating per protocol outcome/result; the legacy theme path remains an explicit GRADE-inspired adaptation rather than being silently broken by the current profile.

GRADE levels remain:

- **High** — very high confidence relative to the declared target/range/threshold.
- **Moderate** — moderate confidence; the true effect may differ in a decision-relevant way.
- **Low** — limited confidence; a decision-relevant difference is plausible.
- **Very Low** — very little confidence about the declared target.

### Legacy/domain-adapted evidence profiles

The legacy contract can still be used for clinical, AI/ML, social-science, and policy evidence summaries that intentionally use result- or theme-level GRADE-inspired adaptations. Those adaptations must remain labelled as such rather than being represented as full current-GRADE assessments.

## Evidence Profile: All-cause mortality

An evidence profile is organized around the result being graded, not around an individual study. Its study-level risk-of-bias inputs remain traceable to the upstream appraisal artifact, while the certainty judgment is rendered once for the protocol outcome or declared synthesis theme.

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

This skill can be invoked independently. Use legacy mode only when preserving an existing `1.0` review contract or an explicitly labelled GRADE-inspired theme adaptation; prefer current GRADE Book mode for new full outcome-level GRADE work.
