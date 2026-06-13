# Validate Evidence

Evidence strength grading using GRADE (Grading of Recommendations Assessment, Development and Evaluation) and Oxford CEBM (Centre for Evidence-Based Medicine) frameworks.

## What It Does

- **Study Design Classification**: Identifies study type (RCT, cohort, case-control, etc.)
- **Bias Risk Assessment**: Evaluates methodological quality
- **Evidence Grading**: Assigns strength rating (High, Moderate, Low, Very Low)
- **Domain-Specific**: Adapts criteria for clinical, AI/ML, social science, or policy research

> **Where the "risk of bias" downgrade comes from.** GRADE has five downgrade domains: risk of bias, inconsistency, indirectness, imprecision, publication bias. The **risk-of-bias** domain is driven by the per-study appraisal from the **`appraise-risk-of-bias`** skill — the design-appropriate validated instrument (RoB 2, ROBINS-I, Newcastle-Ottawa, QUADAS-2), human-confirmed — and this skill **consumes those confirmed overall ratings** rather than forming an ad hoc LLM judgment (LLM RoB accuracy is ~0.62, the pipeline's weakest link). The other four domains are assessed here across the body of evidence.

## Grading Frameworks

**GRADE System** (default for clinical/health)
- **High**: RCTs with low risk of bias
- **Moderate**: RCTs with limitations or strong observational studies
- **Low**: Observational studies with consistent findings
- **Very Low**: Case reports, expert opinion, inconsistent data

**Oxford CEBM Levels** (alternative for evidence hierarchies)
- **Level 1**: Systematic reviews of RCTs
- **Level 2**: Individual RCTs or observational studies with dramatic effect
- **Level 3**: Non-randomized controlled cohort studies
- **Level 4**: Case-series, case-control, or historically controlled studies
- **Level 5**: Mechanism-based reasoning

## Supported Domains

**Clinical Research**
- Standard GRADE criteria
- Focus on patient outcomes
- Bias assessment for interventions

**AI/ML Research**
- Adaptation for model performance
- Dataset quality assessment
- Generalizability evaluation

**Social Science**
- Qualitative rigor
- Mixed methods integration
- Context transferability

**Policy Research**
- Real-world applicability
- Implementation fidelity
- External validity

## Output Formats

**Detailed Report**
- Study design breakdown
- Bias risk assessment
- Grade rationale
- Limitations noted

**Summary Table**
- Quick reference grid
- Grade per study
- Key quality indicators

**Evidence Profile**
- Aggregated across studies
- Overall recommendation strength
- Certainty assessment

## When to Use

- During literature extraction (Phase 2)
- When assessing claim strength
- For systematic reviews
- When grading recommendations
- During peer review preparation

## Example Output

```markdown
## Evidence Assessment: Study XYZ (2024)

**Study Design**: Randomized Controlled Trial
**Domain**: Clinical (intervention study)
**Sample**: N=450, multi-center

**Risk of Bias Assessment**:
- Randomization: Low risk (computer-generated)
- Blinding: Some concerns (single-blind only)
- Attrition: Low risk (5% dropout, ITT analysis)
- Selective reporting: Low risk (pre-registered)

**GRADE Assessment**: MODERATE
- Started as HIGH (RCT)
- Downgraded 1 level (lack of double-blinding)

**Recommendation**: Can support claims with moderate confidence
```

## Related Skills

- `appraise-risk-of-bias` - Upstream, human-gated. Supplies the per-study, human-confirmed risk-of-bias ratings (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2) that drive the GRADE risk-of-bias downgrade domain.
- `synthesize-research` - Uses evidence grades for claim strength
- `validate-citations` - Ensures proper attribution
- `validate-manuscript` - Includes evidence quality checks
- `review-literature` - Phase 2 integration

## Standalone Use

This skill can be invoked independently to grade evidence for any research context, not just literature reviews.
