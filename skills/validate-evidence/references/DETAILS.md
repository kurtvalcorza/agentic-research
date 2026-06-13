## Expected Outputs

### Evidence Grading Report
**File:** `{project-name}-evidence-grading.md`

**Structure (GRADE Framework):**
```markdown
# Evidence Strength Grading Report (GRADE Framework)

**Project:** Project Atlas AI in Healthcare Review
**Framework:** GRADE (Grading of Recommendations Assessment, Development and Evaluation)
**Corpus:** 25 papers
**Graded:** 2026-01-17 16:30

---

## Executive Summary

**Overall Evidence Quality:** MODERATE (⊕⊕⊕◯)

**Distribution:**
- HIGH quality evidence: 8 papers (32%)
- MODERATE quality evidence: 12 papers (48%)
- LOW quality evidence: 4 papers (16%)
- VERY LOW quality evidence: 1 paper (4%)

**Key Findings:**
- ✅ Strong evidence base for AI diagnostic accuracy (Theme A)
- ⚠️ Moderate evidence for implementation barriers (Theme B)
- ❌ Weak evidence for long-term outcomes (Theme C)

---

## GRADE Assessment by Theme

### Theme A: AI Diagnostic Accuracy
**Evidence Grade:** HIGH (⊕⊕⊕⊕)

**Justification:**
- 7/7 papers are RCTs or high-quality cohort studies
- Consistent results across studies (minimal heterogeneity)
- Large sample sizes (combined n=15,234)
- Low risk of bias (Cochrane assessment)
- Direct outcomes (diagnostic accuracy, not proxies)

**Study Design Breakdown:**
| Paper | Study Design | Sample Size | Risk of Bias | Grade Contribution |
|-------|--------------|-------------|--------------|-------------------|
| P1 (Smith 2024) | RCT | n=1,200 | Low | ⊕⊕⊕⊕ |
| P3 (Jones 2023) | RCT | n=850 | Low | ⊕⊕⊕⊕ |
| P5 (Brown 2025) | Cohort (prospective) | n=3,450 | Low | ⊕⊕⊕◯ |
| P7 (Lee 2024) | RCT | n=2,100 | Moderate | ⊕⊕⊕◯ |
| P12 (Martinez 2024) | Cohort (prospective) | n=4,200 | Low | ⊕⊕⊕◯ |
| P15 (Taylor 2023) | RCT | n=1,800 | Low | ⊕⊕⊕⊕ |
| P18 (Wang 2025) | Cohort (prospective) | n=1,634 | Moderate | ⊕⊕◯◯ |

**Consensus:** STRONG CONSENSUS (7/7 papers positive, effect sizes 12-25%)

**GRADE Decision:**
- Starting point: HIGH (RCT evidence)
- Downgrade for risk of bias? NO (mostly low-risk studies) — *RoB ratings sourced from `appraise-risk-of-bias` (RoB 2 / cohort instruments, human-confirmed), not ad hoc LLM judgment*
- Downgrade for inconsistency? NO (consistent findings)
- Downgrade for indirectness? NO (direct outcomes measured)
- Downgrade for imprecision? NO (large sample sizes, tight confidence intervals)
- Downgrade for publication bias? UNLIKELY (comprehensive search, no funnel plot asymmetry)
- **Final Grade: HIGH ⊕⊕⊕⊕**

**Certainty Statement:**
"We are very confident that the true effect lies close to the estimate of effect. AI diagnostic systems improve accuracy by 12-18% in controlled clinical settings."

---

### Theme B: Implementation Barriers
**Evidence Grade:** MODERATE (⊕⊕⊕◯)

**Justification:**
- 5/5 papers report barriers, but study designs vary
- 2 RCTs, 2 cohort studies, 1 cross-sectional survey
- Some inconsistency in barrier rankings across studies
- Moderate risk of bias (2/5 studies have selection bias)
- Indirect outcomes (self-reported barriers, not measured impact)

**Study Design Breakdown:**
| Paper | Study Design | Sample Size | Risk of Bias | Grade Contribution |
|-------|--------------|-------------|--------------|-------------------|
| P2 (Johnson 2023) | RCT | n=600 | Low | ⊕⊕⊕⊕ |
| P4 (Miller 2024) | Cohort (retrospective) | n=1,200 | Moderate | ⊕⊕◯◯ |
| P8 (Garcia 2024) | Cross-sectional survey | n=450 | Moderate | ⊕⊕◯◯ |
| P11 (Kim 2025) | RCT | n=800 | Low | ⊕⊕⊕⊕ |
| P14 (Patel 2023) | Cohort (prospective) | n=950 | Low | ⊕⊕⊕◯ |

**Consensus:** MODERATE CONSENSUS (barriers identified: cost [4/5], workflow [5/5], training [3/5])

**GRADE Decision:**
- Starting point: HIGH (some RCT evidence)
- Downgrade for risk of bias? YES (-1) (2/5 studies moderate risk)
- Downgrade for inconsistency? MINOR (-0.5) (barrier rankings vary)
- Downgrade for indirectness? YES (-0.5) (self-reported, not measured)
- Downgrade for imprecision? NO (adequate sample sizes)
- **Final Grade: MODERATE ⊕⊕⊕◯**

**Certainty Statement:**
"We are moderately confident in the effect estimate. The true effect is likely close to the estimate, but may be substantially different. Implementation barriers (cost, workflow integration) are consistently reported, though their relative impact varies by context."

---

### Theme C: Long-Term Outcomes
**Evidence Grade:** LOW (⊕⊕◯◯)

**Justification:**
- Only 2/2 papers report long-term outcomes (>12 months)
- Both are cohort studies (no RCTs available)
- Small sample sizes (combined n=380)
- High risk of attrition bias (30-40% dropout)
- Inconsistent outcome measures across studies

**Study Design Breakdown:**
| Paper | Study Design | Sample Size | Follow-up | Risk of Bias | Grade Contribution |
|-------|--------------|-------------|-----------|--------------|-------------------|
| P21 (Martinez 2025) | Cohort (prospective) | n=180 | 24 months | Moderate | ⊕⊕◯◯ |
| P23 (Lee & Park 2024) | Cohort (retrospective) | n=200 | 18 months | High | ⊕◯◯◯ |

**Consensus:** INSUFFICIENT EVIDENCE (only 2 papers, inconsistent findings)

**GRADE Decision:**
- Starting point: LOW (observational evidence only, no RCTs)
- Downgrade for risk of bias? YES (-1) (high attrition, selection bias)
- Downgrade for inconsistency? YES (-1) (contradictory findings)
- Downgrade for indirectness? MINOR (-0.5) (surrogate outcomes used)
- Downgrade for imprecision? YES (-1) (small samples, wide confidence intervals)
- **Final Grade: VERY LOW ⊕◯◯◯** (initially calculated), **upgraded to LOW** due to importance of findings
- **Final Grade: LOW ⊕⊕◯◯**

**Certainty Statement:**
"We have very limited confidence in the effect estimate. The true effect may be substantially different from the estimate. Long-term sustainability of AI diagnostic accuracy improvements remains uncertain due to limited longitudinal evidence."

---

## Overall Evidence Profile

**Weighted Evidence Quality:** MODERATE (⊕⊕⊕◯)

**Calculation:**
```
Weighted average across themes:
- Theme A (HIGH, 7 papers): 4.0 × 7 = 28.0
- Theme B (MODERATE, 5 papers): 3.0 × 5 = 15.0
- Theme C (LOW, 2 papers): 2.0 × 2 = 4.0

Total: 47.0 / 14 papers = 3.36 ≈ MODERATE (⊕⊕⊕◯)
```

**Interpretation:**
- Strong evidence for **core claims** (diagnostic accuracy)
- Moderate evidence for **implementation challenges**
- Weak evidence for **long-term sustainability**

---

## Recommendations by Stakeholder

### For Clinicians
✅ **Adopt with Confidence:** AI diagnostics in controlled settings (HIGH evidence)
⚠️ **Prepare for Barriers:** Workflow integration challenges are real (MODERATE evidence)
❓ **Monitor Long-Term:** Evidence for sustained accuracy beyond 12 months is limited (LOW evidence)

### For Policymakers
✅ **Support Deployment:** Evidence supports piloting AI diagnostics in controlled clinical contexts
⚠️ **Resource Allocation:** Budget for implementation support (cost, training, workflow redesign)
❌ **Mandate Caution:** Do NOT mandate long-term deployment without stronger longitudinal evidence

### For Researchers
🔬 **Priority Research Needed:**
1. Long-term RCTs (>24 months follow-up) to address LOW evidence for Theme C
2. Implementation science studies to quantify barrier impact (upgrade Theme B to HIGH)
3. Real-world effectiveness studies (non-controlled settings)

---

## Evidence Gaps Identified

### Critical Gaps (LOW/VERY LOW Evidence)
1. **Long-term accuracy sustainability** (Theme C)
   - Current: 2 papers, LOW evidence
   - Needed: 5+ RCTs with ≥24 month follow-up

2. **Real-world effectiveness** (not yet synthesized as theme)
   - Current: 0 papers in corpus
   - Needed: Pragmatic trials in routine practice settings

3. **Health equity impacts** (not yet synthesized as theme)
   - Current: 0 papers in corpus
   - Needed: Studies in low-resource settings, diverse populations

### Moderate Gaps (MODERATE Evidence)
4. **Quantified barrier impact** (Theme B)
   - Current: 5 papers, MODERATE evidence (self-reported barriers)
   - Needed: Studies measuring actual cost/time impact of barriers

---

## Study Design Quality Summary

**By Design Type:**
| Study Design | Count | % of Corpus | Typical GRADE Contribution |
|--------------|-------|-------------|---------------------------|
| RCT | 9 | 36% | ⊕⊕⊕⊕ (HIGH starting point) |
| Cohort (prospective) | 7 | 28% | ⊕⊕⊕◯ (MODERATE starting point) |
| Cohort (retrospective) | 3 | 12% | ⊕⊕◯◯ (LOW starting point) |
| Cross-sectional | 4 | 16% | ⊕⊕◯◯ (LOW starting point) |
| Case series | 2 | 8% | ⊕◯◯◯ (VERY LOW starting point) |

**Bias Risk Distribution:**
| Risk Level | Count | % of Corpus |
|------------|-------|-------------|
| Low | 14 | 56% |
| Moderate | 9 | 36% |
| High | 2 | 8% |

---

## Comparison: GRADE vs Oxford CEBM

**NOTE:** This comparison available only if `framework: both` specified

| Theme | GRADE | Oxford CEBM | Agreement? |
|-------|-------|-------------|------------|
| A: Diagnostic Accuracy | HIGH (⊕⊕⊕⊕) | Level 1a (Systematic review of RCTs) | ✅ YES |
| B: Implementation Barriers | MODERATE (⊕⊕⊕◯) | Level 2b (Individual cohort studies) | ⚠️ PARTIAL |
| C: Long-Term Outcomes | LOW (⊕⊕◯◯) | Level 4 (Case series) | ✅ YES |

**Interpretation:** High agreement (2/3 themes) - Both frameworks converge on evidence quality assessment.

---

## Next Steps

1. **Acknowledge Evidence Limitations** in manuscript (Section 6: Limitations)
   - Explicitly state Theme C has LOW evidence
   - Note insufficient evidence for long-term outcomes

2. **Moderate Language Accordingly**
   - Theme A: Use confident language ("demonstrates", "shows")
   - Theme B: Use cautious language ("suggests", "indicates")
   - Theme C: Use very cautious language ("limited evidence suggests", "uncertain")

3. **Identify Future Research Priorities** (Section 5.2)
   - Theme C gap: "Long-term RCTs needed"
   - Real-world effectiveness gap: "Pragmatic trials in routine settings"
   - Equity gap: "Studies in diverse populations and low-resource contexts"

4. **Re-Validate After Revisions** (Optional)
   - Run validate-evidence again after manuscript revisions
   - Confirm language matches evidence strength

---

## Evidence-Based Certainty Achieved ✅

**Use this grading to:**
- ✅ Justify claim language in draft
- ✅ Inform contribution framing (strong vs. preliminary contributions)
- ✅ Guide future research recommendations
- ✅ Support policy/practice recommendations

**GRADE: The Gold Standard for Evidence Assessment** 🏅
```

---

## Execution Model

### Step 1: Extract Study Designs from Corpus

```markdown
For each paper in corpus:

  # Method 1: From Extraction Matrix (if available)
  IF extraction_matrix exists:
    study_design = extraction_matrix[paper]["study_design"]
    sample_size = extraction_matrix[paper]["sample_size"]
    risk_of_bias = extraction_matrix[paper]["bias_assessment"]

  # Method 2: From PDF Text (if no extraction matrix)
  ELSE:
    Read PDF abstract + methods section

    # Detect study design keywords
    IF "randomized controlled trial" OR "RCT" OR "randomization":
      study_design = "RCT"

    ELIF "cohort" AND ("prospective" OR "followed"):
      study_design = "Cohort (prospective)"

    ELIF "cohort" AND "retrospective":
      study_design = "Cohort (retrospective)"

    ELIF "cross-sectional" OR "survey":
      study_design = "Cross-sectional"

    ELIF "case-control":
      study_design = "Case-control"

    ELIF "case series" OR "case report":
      study_design = "Case series"

    ELSE:
      study_design = "Expert opinion" (lowest evidence level)

    # Extract sample size
    sample_size = extract_n_value(methods_section)

    # Assess bias risk (basic)
    risk_of_bias = assess_bias_heuristic(study_design, sample_size, methods_quality)

Store:
  paper_inventory = {
    "P1": {
      "study_design": "RCT",
      "sample_size": 1200,
      "risk_of_bias": "Low",
      "follow_up_duration": "12 months" (if applicable)
    },
    ...
  }
```

### Step 2: Apply GRADE Framework (Theme-Level)

For each theme in synthesis:

```python
def calculate_grade(theme):
  papers = theme["papers"]

  # Step 1: Determine starting evidence level
  study_designs = [paper_inventory[p]["study_design"] for p in papers]

  IF any(d == "RCT" for d in study_designs):
    starting_grade = 4  # HIGH (⊕⊕⊕⊕)
  ELIF any(d.startswith("Cohort") for d in study_designs):
    starting_grade = 2  # LOW (⊕⊕◯◯)
  ELSE:
    starting_grade = 1  # VERY LOW (⊕◯◯◯)

  # Step 2: Assess 5 downgrade criteria
  #   (risk of bias, inconsistency, indirectness, imprecision, publication bias)

  # 2a. Risk of Bias
  #
  # SOURCE OF THE RoB RATING — consume appraise-risk-of-bias, do not re-judge ad hoc:
  #   The per-study risk_of_bias value should come from the CONFIRMED overall ratings
  #   produced by the `appraise-risk-of-bias` skill (appraisal/risk-of-bias.md), using
  #   the design-appropriate validated instrument — RoB 2 (RCT), ROBINS-I (non-randomized
  #   intervention), Newcastle-Ottawa (observational), QUADAS-2 (diagnostic accuracy) —
  #   and HUMAN-CONFIRMED. Map each instrument's overall judgment to High/Moderate/Low:
  #     RoB 2:        High -> High | Some concerns -> Moderate | Low -> Low
  #     ROBINS-I:     Critical/Serious -> High | Moderate -> Moderate | Low -> Low
  #     Newcastle-Ottawa: <=4 stars -> High | 5-6 -> Moderate | 7-9 -> Low (study-area dependent)
  #     QUADAS-2:     any domain High -> High | any Unclear -> Moderate | all Low -> Low
  #   Only if appraise-risk-of-bias output is unavailable, fall back to the heuristic
  #   (Step 1) estimate and FLAG the resulting RoB downgrade as provisional.
  IF rob_appraisal_available:
    risk_of_bias = confirmed_overall_rob[p]   # from appraise-risk-of-bias (human-confirmed)
  ELSE:
    risk_of_bias = paper_inventory[p]["risk_of_bias"]  # heuristic fallback (flag as provisional)

  high_bias_count = sum(1 for p in papers if risk_of_bias_of(p) == "High")
  moderate_bias_count = sum(1 for p in papers if risk_of_bias_of(p) == "Moderate")

  IF high_bias_count >= len(papers) / 2:
    starting_grade -= 2  # Serious bias
  ELIF moderate_bias_count >= len(papers) / 2:
    starting_grade -= 1  # Some bias

  # 2b. Inconsistency
  findings = [paper_inventory[p]["finding"] for p in papers]
  IF findings_are_contradictory(findings):
    starting_grade -= 1  # Serious inconsistency
  ELIF findings_are_heterogeneous(findings):
    starting_grade -= 0.5  # Some inconsistency

  # 2c. Indirectness
  outcomes = [paper_inventory[p]["outcome_type"] for p in papers]
  IF any(o == "surrogate" for o in outcomes):
    starting_grade -= 0.5  # Indirect outcomes

  # 2d. Imprecision
  total_sample_size = sum(paper_inventory[p]["sample_size"] for p in papers)
  IF total_sample_size < 400:
    starting_grade -= 1  # Serious imprecision
  ELIF total_sample_size < 1000:
    starting_grade -= 0.5  # Some imprecision

  # 2e. Publication Bias
  IF corpus_search_was_limited OR funnel_plot_asymmetry:
    starting_grade -= 1  # Likely publication bias

  # Step 3: Cap at valid range [1, 4]
  final_grade = max(1, min(4, starting_grade))

  # Step 4: Map to GRADE symbols
  grade_symbols = {
    4: "⊕⊕⊕⊕ HIGH",
    3: "⊕⊕⊕◯ MODERATE",
    2: "⊕⊕◯◯ LOW",
    1: "⊕◯◯◯ VERY LOW"
  }

  return {
    "numeric_grade": final_grade,
    "symbol": grade_symbols[final_grade],
    "certainty_statement": generate_certainty_statement(final_grade),
    "justification": generate_justification(theme, final_grade)
  }
```

### Step 3: Apply Oxford CEBM Levels (Alternative Framework)

```python
def calculate_oxford_cebm(theme):
  papers = theme["papers"]

  # Hierarchical levels (1a = strongest, 5 = weakest)

  # Level 1a: Systematic review of RCTs
  IF theme_is_systematic_review AND all_rcts(papers):
    return "1a"

  # Level 1b: Individual RCT with narrow CI
  ELIF any_rct(papers) AND narrow_confidence_intervals:
    return "1b"

  # Level 2a: Systematic review of cohort studies
  ELIF theme_is_systematic_review AND all_cohort(papers):
    return "2a"

  # Level 2b: Individual cohort study
  ELIF any_cohort(papers):
    return "2b"

  # Level 3a: Systematic review of case-control studies
  ELIF theme_is_systematic_review AND all_case_control(papers):
    return "3a"

  # Level 3b: Individual case-control study
  ELIF any_case_control(papers):
    return "3b"

  # Level 4: Case series
  ELIF any_case_series(papers):
    return "4"

  # Level 5: Expert opinion
  ELSE:
    return "5"
```

### Step 4: Generate Evidence Grading Report

```markdown
For each theme:
  1. Calculate GRADE score
  2. (Optional) Calculate Oxford CEBM level
  3. Generate justification with:
     - Study design breakdown table
     - Consensus assessment
     - Downgrade decision tree
     - Certainty statement

Overall assessment:
  1. Weighted average of theme grades
  2. Evidence gaps identified (LOW/VERY LOW themes)
  3. Recommendations by stakeholder type
  4. Study quality summary tables
```

---

## Success Criteria

Grading successful when:

1. ✅ All papers classified by study design
2. ✅ Bias risk assessed for each paper
3. ✅ GRADE scores calculated for all themes
4. ✅ Certainty statements generated
5. ✅ Evidence gaps identified
6. ✅ Stakeholder recommendations provided
7. ✅ Grading report saved

---

## Integration Points

### Upstream: Risk-of-Bias Appraisal (feeds the GRADE RoB domain)

```markdown
Canonical pipeline order:
  extract-synthesis -> appraise-risk-of-bias (human-gated) -> validate-evidence (GRADE)

appraise-risk-of-bias produces appraisal/risk-of-bias.md with the design-appropriate,
human-confirmed per-study overall ratings (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2).
validate-evidence CONSUMES those confirmed overall ratings as the GRADE "risk of bias"
downgrade domain (Step 2a) — it does NOT re-derive RoB by ad hoc LLM judgment.
The remaining GRADE domains (inconsistency, indirectness, imprecision, publication bias)
are assessed here across the body of evidence.
```

### LRA Phase 2 Enhancement

```markdown
After Phase 2 (Extraction & Synthesis) and appraise-risk-of-bias (RoB appraisal):
  Optionally invoke: validate-evidence

  Parameters:
    corpus_path: 01_Projects/Project Atlas/research/corpus/approved/
    synthesis_path: outputs/phase2-synthesis-matrix.md
    rob_appraisal_path: appraisal/risk-of-bias.md   # confirmed RoB ratings -> GRADE RoB domain
    framework: grade
    domain: clinical

  Output: phase2-evidence-grading.md

  Use grading to:
    - Label themes with evidence strength
    - Inform Phase 4 drafting language
    - Guide Phase 6 contribution framing
```

---

## Related Skills

- **[[../appraise-risk-of-bias/SKILL|Appraise Risk of Bias]]** - Upstream, human-gated. Produces the per-study, design-appropriate (RoB 2 / ROBINS-I / Newcastle-Ottawa / QUADAS-2), human-confirmed RoB ratings that drive the GRADE risk-of-bias downgrade domain here.
- **[[../validate-citations/SKILL|Validate Citations]]** - Citation accuracy
- **[[../validate-consistency/SKILL|Validate Consistency]]** - Cross-phase validation
- **[[../frame-contributions/SKILL|Frame Contributions]]** - Use evidence grades to calibrate contribution claims

---

## Version History

**v1.0 (2026-01-17)** - Initial implementation
- GRADE framework implementation
- Oxford CEBM levels implementation
- Study design auto-detection
- Bias risk assessment
- Domain-specific grading
- Stakeholder-specific recommendations

---

## Key Principles

1. **Evidence Hierarchy** - Study design determines starting grade
2. **Systematic Downgrading** - 5 GRADE criteria applied rigorously
3. **Certainty Over Precision** - Acknowledge limitations explicitly
4. **Stakeholder Tailoring** - Different recommendations for clinicians/policymakers/researchers
5. **Gap Identification** - Low evidence themes = future research priorities

**Evidence-Based Practice, Validated** 🔬




## References & Details

Full details, examples, and templates have been moved to [Details](references/DETAILS.md).
