# GRADE Evidence Framework Reference

Grading of Recommendations Assessment, Development and Evaluation (GRADE) framework for evidence quality assessment.

---

## Overview

GRADE rates evidence quality on four levels:
- **HIGH** (4/4) - Very confident the true effect is close to the estimate
- **MODERATE** (3/4) - Moderately confident; true effect likely close but may be different
- **LOW** (2/4) - Limited confidence; true effect may be substantially different
- **VERY LOW** (1/4) - Little confidence; true effect likely substantially different

---

## Starting Points

Anchored to the design that **predominates** in the body of evidence for that result — not to the
strongest single study present. One randomized trial among eight cross-sectional studies does not
start the body at HIGH.

| Predominant study design | Starting Level |
|--------------------------|----------------|
| Randomized Controlled Trials (RCTs) | HIGH |
| Observational studies | LOW |
| Case series, case reports | VERY LOW |

Judgement may depart from the predominant design where the evidence warrants it — but the
departure must be recorded as an explicit justification, not applied silently.

---

## Downgrade Factors

### 1. Risk of Bias (-1 or -2)

> **Source this domain from the confirmed appraisal**, not from an ad hoc reading. The per-study
> ratings come from `appraise-risk-of-bias` using the design-appropriate instrument and are
> human-confirmed. The indicators below describe what those instruments assess; they are not a
> licence to re-judge each study here.

- Selection bias (randomization issues)
- Performance bias (blinding issues)
- Detection bias (outcome assessment)
- Attrition bias (incomplete data)
- Reporting bias (selective reporting)

**Indicators:**
- No allocation concealment
- Unblinded participants/assessors
- High dropout rates (>20%)
- Missing outcome data
- Protocol deviations

### 2. Inconsistency (-1 or -2)
- Heterogeneous results across studies
- Wide confidence intervals
- Conflicting effect directions

**Indicators:**
- I² >50% (moderate heterogeneity)
- I² >75% (high heterogeneity)
- Effects vary by subgroup

### 3. Indirectness (-1 or -2)
- Population differs from target
- Intervention differs from question
- Outcome is surrogate
- Indirect comparisons

**Indicators:**
- Different demographics
- Different settings
- Different doses/durations
- Surrogate endpoints

### 4. Imprecision (-1 or -2)
- Wide confidence intervals
- Small sample size
- Few events

**Primary basis — judge on these:**
- The **confidence interval** around the pooled estimate relative to the decision threshold:
  downgrade when the interval spans both appreciable benefit and appreciable harm
- The **Optimal Information Size (OIS)**: does the total sample reach what a single adequately
  powered trial would require? Downgrade when it falls well short

**Fallback only — when no interval or OIS is available:**
- Total events <300
- Total sample <400

> These absolute thresholds are a **crude fallback**, not the rule. They are convenient and
> frequently misapplied: a tight interval around a null effect from 250 events is not imprecise,
> and a 500-participant study with a interval spanning benefit and harm is. Where the synthesis
> is narrative and no pooled interval exists, use the fallback and **say so** — the judgment is
> then weaker, and a reader is entitled to know that.

*Consistent with the imprecision guidance in [`DETAILS.md`](./DETAILS.md); if these two files
ever disagree again, DETAILS.md governs and this file is the defect.*

### 5. Publication Bias (-1 or -2)
- Funnel plot asymmetry
- Small study effects
- Sponsor bias

**Indicators:**
- Missing negative studies
- Industry funding patterns
- Unpublished data

---

## Upgrade Factors (Observational Only, and Only Below the Ceiling)

### 1. Large Effect (+1 or +2)
- RR >2 or <0.5 (no bias) → +1
- RR >5 or <0.2 (no bias) → +2

### 2. Dose-Response (+1)
- Clear gradient relationship
- Plausible biological mechanism

### 3. Confounders Reduce Effect (+1)
- All plausible confounders would reduce effect
- Effect still observed

---

## GRADE Quality Symbols

| Level | Symbol | Meaning |
|-------|--------|---------|
| HIGH | ⊕⊕⊕⊕ | Very confident |
| MODERATE | ⊕⊕⊕◯ | Moderately confident |
| LOW | ⊕⊕◯◯ | Limited confidence |
| VERY LOW | ⊕◯◯◯ | Little confidence |

---

## Example Grading

```markdown
## Theme: AI Tutoring Effectiveness

**Evidence Base:** 7 RCTs (n=3,500)

**Starting Level:** HIGH (RCTs)

**Downgrade Assessment:**
- Risk of Bias: -1 (3 studies unblinded)
- Inconsistency: 0 (I²=35%, low heterogeneity)
- Indirectness: 0 (populations match)
- Imprecision: 0 (narrow CI, >300 events)
- Publication Bias: -1 (funnel asymmetry)

**Final Grade:** MODERATE ⊕⊕⊕◯

**Interpretation:** Moderately confident that AI tutoring improves
test scores. Some concerns about blinding and potential missing studies.
```

---

## Language Recommendations by Grade

| Grade | Recommended Language |
|-------|---------------------|
| HIGH | "X causes Y" / "X improves Y" |
| MODERATE | "X likely improves Y" / "X probably causes Y" |
| LOW | "X may improve Y" / "X might cause Y" |
| VERY LOW | "X might improve Y" / "Evidence is uncertain" |

---

## Domain-Specific Considerations

### Clinical/Health
- Focus on patient-important outcomes
- Consider minimal clinically important difference (MCID)
- Account for adverse effects

### Education
- Consider learning transfer vs. immediate gains
- Account for implementation fidelity
- Consider long-term retention

### Policy
- Consider generalizability across contexts
- Account for implementation barriers
- Consider cost-effectiveness

---

*Reference: GRADE Working Group (www.gradeworkinggroup.org)*
*Last updated: 2026-01-18*
