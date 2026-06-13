---
name: validate-evidence
description: "Evidence strength grading using GRADE and Oxford CEBM frameworks with quality assessment. Use when grading evidence strength in a manuscript, assessing study quality and bias risk, or validating evidence claims before submission."
---

# Evidence Strength Validation

## Purpose

**EVIDENCE-BASED PRACTICE VALIDATION** for research synthesis. Validates evidence strength claims using internationally recognized frameworks:
- 🏥 **GRADE** (Grading of Recommendations Assessment, Development and Evaluation)
- 📊 **Oxford CEBM** (Centre for Evidence-Based Medicine Levels of Evidence)
- 🔬 **Study Design Classification** (RCT, Cohort, Case-Control, Case Series, Expert Opinion)
- ⚖️ **Bias Risk Assessment** (High/Moderate/Low)

**Key Feature:** Evidence grading using internationally recognized frameworks (GRADE and Oxford CEBM).

> **Risk-of-bias input — consume `appraise-risk-of-bias`, do not re-judge ad hoc.** GRADE has five downgrade domains: **risk of bias, inconsistency, indirectness, imprecision, publication bias.** The **risk-of-bias** domain should be driven by the **per-study risk-of-bias appraisal** produced upstream by the **`appraise-risk-of-bias`** skill — using the design-appropriate validated instrument (**RoB 2** for RCTs, **ROBINS-I** for non-randomized interventions, **Newcastle-Ottawa** for observational, **QUADAS-2** for diagnostic accuracy) and **human-confirmed**. This skill **consumes those confirmed overall ratings** as the risk-of-bias input rather than forming an ad hoc LLM judgment of how each study was conducted (LLM RoB appraisal accuracy is ~0.62 — the pipeline's weakest link, hence the human gate). The other four domains (inconsistency, indirectness, imprecision, publication bias) remain assessed here across the body of evidence as before.

---

## Dependencies

### Required Skills
None (standalone skill)

### Required Capabilities
- `file-read` - Read research corpus and synthesis outputs
- `file-write` - Generate evidence grading report
- `content-search` - Extract study design information
- `file-search` - Find corpus files

### Input Files
**Minimum Requirements:**
- Source corpus (PDFs OR extraction matrix)
- Synthesis output (for theme-level evidence assessment)

**Optional Enhancement:**
- Full-text PDFs (for deeper methodology assessment)
- Extraction matrix (for pre-extracted study designs)
- **Confirmed risk-of-bias appraisal** (`appraisal/risk-of-bias.md` from `appraise-risk-of-bias`) — the human-confirmed per-study overall RoB ratings that drive the GRADE risk-of-bias downgrade domain. Strongly recommended for rigorous reviews; if absent, RoB falls back to the heuristic estimate, which should be flagged as provisional.

### Output Directories
**Auto-created if missing:**
- `{project-dir}/outputs/` - Evidence grading report saved here

---

## Use Cases

1. **Literature Review Evidence Grading** - Assess evidence quality for systematic reviews
2. **Clinical Guideline Development** - Grade recommendations using GRADE framework
3. **Policy Briefing Validation** - Ensure claims match evidence strength
4. **Grant Proposal Assessment** - Validate background evidence quality
5. **Systematic Review Quality Gate** - Pre-publication evidence assessment

---

## Inputs Required

**Required Parameters:**
- `corpus_path` - Path to research corpus (PDFs or extraction matrix)
- `synthesis_path` - Path to synthesis output (with themes and claims)
- `framework` - Evidence grading framework to use:
  - `grade` - GRADE system (default for clinical/health research)
  - `oxford-cebm` - Oxford CEBM levels (alternative for clinical research)
  - `both` - Apply both frameworks and compare

**Optional Parameters:**
- `domain` - Research domain for domain-specific grading:
  - `clinical` - Healthcare/medicine (default)
  - `ai-ml` - AI/ML technical research
  - `social-science` - Social science research
  - `policy` - Public policy research
- `output_format` - Report format:
  - `detailed` - Full grading with justifications (default)
  - `summary` - Theme-level grades only
  - `table` - Compact grading table

---

## References & Details

Full details, examples, and templates have been moved to [Details](references/DETAILS.md).
