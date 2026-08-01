# Validate Evidence

Evidence strength grading using GRADE (Grading of Recommendations Assessment, Development and Evaluation) and Oxford CEBM (Centre for Evidence-Based Medicine) frameworks.

## What It Does

- **Evidence-Body Classification**: Summarizes the design mix contributing to each result
- **Risk-of-Bias Synthesis**: Consumes human-confirmed, per-result study appraisals
- **Result-Level Grading**: Assigns certainty (High, Moderate, Low, Very Low) to each protocol outcome or synthesis theme
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
- Evidence-body design breakdown
- Risk-of-bias synthesis
- Grade rationale
- Limitations noted

**Summary Table**
- Quick reference grid
- One certainty rating per protocol outcome or synthesis theme
- Key quality indicators

**Evidence Profile**
- Aggregated across all studies contributing to each result
- Domain judgments for the evidence body
- Result-level certainty assessment

## When to Use

- During literature extraction (Phase 2)
- When assessing claim strength
- For systematic reviews
- When grading recommendations
- During peer review preparation

## Example Output

```markdown
## Evidence Profile: All-cause mortality

**Evidence body**: 8 studies (5 randomized, 3 non-randomized)
**Result assessed**: All-cause mortality at 12 months
**Risk-of-bias basis**: Human-confirmed appraisals for the contributing studies

**GRADE domains**:
- Risk of bias: Serious (downgrade 1)
- Inconsistency: Not serious
- Indirectness: Not serious
- Imprecision: Not serious
- Publication bias: Undetected

**Certainty**: MODERATE
```

## Related Skills

- `appraise-risk-of-bias` - Upstream, human-gated. Supplies the per-study, human-confirmed risk-of-bias ratings (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2) that drive the GRADE risk-of-bias downgrade domain.
- `synthesize-research` - Uses evidence grades for claim strength
- `validate-citations` - Ensures proper attribution
- `validate-manuscript` - Includes evidence quality checks
- `review-literature` - Phase 2 integration

## Standalone Use

This skill can be invoked independently to grade evidence for any research context, not just literature reviews.
