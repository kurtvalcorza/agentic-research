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

---

## Runnable check — `scripts/grade_profile.py`

The certainty record is the **source of truth**; the evidence profile and summary-of-findings
tables are **generated from it**. Do not hand-write the tables alongside the record — maintaining
both guarantees they eventually disagree, and the disagreement would be invisible.

```bash
python scripts/grade_profile.py grade-profile.json --rob ../appraise-risk-of-bias/appraisal/risk-of-bias.json --strict
```

**Exit codes**: `0` clean (or violations found without `--strict`) · `1` method violation under
`--strict` · `2` malformed input, in which case **no artifact is emitted** — a record that cannot
be read must not produce a document that looks authoritative.

**`--json`** replaces the artifact with the machine-readable counts envelope that `verify-review`
consumes to DERIVE its unit counts rather than trust the ones its own record asserts. This check is
the only one producing **two** units — `U_grade` (results that fail) and `U_rob_trace` (appraisal
references that do not resolve) — and they overlap on purpose, so neither may be derived from the
other. `U_rob_trace` is emitted **only with `--rob`**: without an appraisal record nothing was
traced, and reporting `0` would claim every reference resolved. The flag does not change the exit
code. Full shape in `specs/001-standards-enforcement-parity/contracts/cli-contract.md`.

`--rob` supplies the appraisal record. It is **required** whenever a result declares
`basis: confirmed_rob`: claiming confirmed appraisal without supplying it is a violation, not a
pass. It is a file path, never an import, so this skill stays copyable on its own.

### What the check enforces

| | Rule |
|:--|:--|
| 1 | All five downgrade domains present. A missing domain is reported **by name**, never read as "no concern" |
| 2 | Ratings are `0`, `-1` or `-2` — whole steps only |
| 3 | A **misspelled** domain key is malformed input, not a missing domain |
| 4 | `starting_level` matches the **predominant** design, unless justified |
| 5 | `clamp(start + Σdomains + Σupgrades, 1, 4)` equals `final`, with the discrepancy reported |
| 6 | Upgrades only on non-randomized bodies **that declare a starting level below `high`**, with no downgrade applied. Two bars: the design, and the declared level a justification may have moved |
| 7 | Upgrade reasons limited to the three GRADE defines — "importance of findings" is unrepresentable |
| 8 | Any cross-result aggregate certainty is **rejected**; GRADE defines none |
| 9 | `basis` is `confirmed_rob` or `heuristic`; heuristic marks output PROVISIONAL and fails for systematic and umbrella reviews |
| 10 | Referenced studies resolve to **confirmed** appraisals, matched exactly |
| 11 | A body-level risk-of-bias judgment contradicted by its own studies is flagged unless justified |

### ⚠️ What this check CANNOT verify

It establishes that a certainty assessment is **complete, legal under GRADE, and arithmetically
consistent**. It does not — and cannot — establish that a judgment was *correct*. That
"inconsistency: serious" was the right call requires expertise the script has no access to.

It also cannot confirm that the cited studies exist; only that they appear in the appraisal record
you supplied. A clean result is a floor, not a warrant.

---

## References & Details

Full details, examples, and templates are in [Details](references/DETAILS.md).
