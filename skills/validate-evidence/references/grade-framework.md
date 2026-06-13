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

| Study Design | Starting Level |
|--------------|----------------|
| Randomized Controlled Trials (RCTs) | HIGH |
| Observational studies | LOW |
| Case series, case reports | VERY LOW |

---

## Downgrade Factors

### 1. Risk of Bias (-1 or -2)
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

**Indicators:**
- CI crosses clinical decision threshold
- Total events <300
- Total sample <400

### 5. Publication Bias (-1 or -2)
- Funnel plot asymmetry
- Small study effects
- Sponsor bias

**Indicators:**
- Missing negative studies
- Industry funding patterns
- Unpublished data

---

## Upgrade Factors (Observational Only)

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
