---
name: validate-consistency
description: "Cross-phase consistency validation with progressive scoring and auto-repair suggestions. Use when checking traceability across synthesis, outline, and draft phases, or running the final quality gate before completing a multi-phase workflow."
---








# Cross-Phase Consistency Validation (Enhanced)

## Purpose

**FINAL QUALITY CONTROL GATE** for multi-phase workflows. Validates traceability and consistency across:
- 📋 **Synthesis→Outline** - All themes appear in structure
- 📝 **Outline→Draft** - All sections properly developed
- 🔗 **Synthesis→Draft** - Evidence chains intact
- 🎯 **Draft→Contributions** - Claims grounded in evidence
- ✅ **End-to-End** - Corpus-to-output traceability

**Success Metric:** Consistency score ≥75/100

**Blocks Workflow If:** Critical consistency breaks OR score <75

---

## Dependencies

### Required Skills
None (standalone skill)

### Required Capabilities
- `file-read` - Read phase outputs
- `file-write` - Generate consistency report
- `content-search` - Extract themes and citations
- `file-search` - Find related files

### Input Files
**Core Requirements (Minimum 3):**
- Synthesis output (e.g., `phase2-synthesis-matrix.md`)
- Outline output (e.g., `phase3-argument-outline.md`)
- Draft output (e.g., `phase4-literature-review-draft.md`)

**Optional Enhancement:**
- Contribution framing output (e.g., `phase6-contribution-framing.md`)
- Extraction matrix (for deeper traceability)

### Output Directories
**Auto-created if missing:**
- `{project-dir}/outputs/` - Consistency report saved here

---

## Use Cases

1. **Literature Review Quality Gate** - Validate LRA Phase 7 before publication
2. **Technical Report Validation** - Ensure requirements→design→implementation consistency
3. **Grant Proposal Validation** - Background→objectives→methodology alignment
4. **Presentation Validation** - Research→slides→talking points consistency
5. **Thesis/Dissertation Gate** - Chapter-to-chapter consistency

---

## Inputs Required

**Required Parameters:**
- `project_path` - Path to project directory containing outputs
- `validation_mode` - Type of consistency check:
  - `full` - All 5 validation dimensions (default)
  - `synthesis-outline` - Only check synthesis→outline alignment
  - `outline-draft` - Only check outline→draft development
  - `end-to-end` - Only check corpus→draft traceability
  - `quick` - Fast check (3 dimensions, skip deep traceability)

**Optional Parameters:**
- `threshold` - Minimum passing score (default: 75)
- `auto_repair` - Suggest fixes for issues (default: true)
- `strictness` - Validation strictness:
  - `strict` - HALT on score <75 or critical issues (default)
  - `moderate` - WARN on score 65-74, HALT only on <65
  - `lenient` - Report only, never halt

---



## References & Details

Full details, examples, and templates have been moved to [Details](references/DETAILS.md).
