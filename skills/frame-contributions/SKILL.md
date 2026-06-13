---
name: frame-contributions
description: "Contribution framing with integrated Tools for Thought provocation mode. Use when articulating research contributions, framing implications for policy or practice, or drafting the contributions section of a manuscript."
---








# Contribution & Implications Framing (Enhanced with Provocation)

## Purpose

**STRATEGIC CONTRIBUTION FRAMING** for research synthesis with integrated **Tools for Thought provocation mode**. Helps researchers articulate:
- 🎯 **What this work contributes** (relative to existing knowledge)
- 💡 **What it implies** (for practice, policy, research)
- ⚠️ **What limitations exist** (what remains uncertain)
- 🔬 **What future research should address** (grounded in identified gaps)

**Key Enhancement:** Provokes rather than suggests, enabling deeper strategic thinking through integrated Tools for Thought mode.

---

## Dependencies

### Required Skills
- **[[../../tools-for-thought/SKILL|Tools for Thought]]** - Provocation mode for strategic clarity

### Required Capabilities
- `file-read` - Read draft, synthesis, and outline
- `file-write` - Generate contribution framing document

### Input Files
**MUST exist before execution:**
- Draft manuscript (`phase4-literature-review-draft.md`)
- Synthesis matrix (`phase2-synthesis-matrix.md`)
- Argument outline (`phase3-argument-outline.md`)

**Optional Enhancement:**
- Evidence grading report (`phase2-evidence-grading.md`) - For evidence-calibrated contributions

### Output Directories
**Auto-created if missing:**
- `{project-dir}/outputs/` - Contribution framing saved here

---

## Use Cases

1. **Literature Review Contribution Framing** (LRA Phase 6)
2. **Grant Proposal Positioning** - Frame novel contributions for funding
3. **Thesis Contribution Chapter** - Articulate research contributions
4. **Policy Brief Impact Framing** - Implications for policymakers
5. **Technical Report Executive Summary** - Contribution distillation

---

## Inputs Required

**Required Parameters:**
- `project_path` - Path to project directory containing draft and synthesis
- `provocation_mode` - Enable Tools for Thought provocations:
  - `full` - Deep provocation at every step (default)
  - `targeted` - Provoke only on weak/vague contributions
  - `minimal` - Basic framing, minimal provocation

**Optional Parameters:**
- `audience_focus` - Primary audience for implications:
  - `balanced` - All three audiences (practitioners/policymakers/researchers) (default)
  - `practitioners` - Focus on practice implications
  - `policymakers` - Focus on policy implications
  - `researchers` - Focus on research implications
- `overclaim_sensitivity` - How strict to check for overclaiming:
  - `high` - Flag any claim not directly supported (strict)
  - `moderate` - Flag only significant overclaims (default)
  - `low` - Allow generous interpretation

---



## References & Details

Full details, examples, and templates have been moved to [Details](references/DETAILS.md).
