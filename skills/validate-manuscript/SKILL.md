---
name: validate-manuscript
description: "Batch validation suite for comprehensive manuscript quality assurance. Runs citations, evidence, contributions, and consistency checks in one go. Use when running QA on a completed draft, checking a manuscript before submission, or validating academic paper quality."
---








# Validate Manuscript (Batch Mode)

## Purpose
Single-invocation orchestrator that runs all validation skills in sequence, producing a consolidated validation report.
**Time Savings:** 75% (20 min → 5 min).

## When to Use
- After completing drafting.
- Before submission of academic papers.
- Quality gate before sharing with reviewers.

---

## Dependencies
- **[[../validate-citations/SKILL|Validate Citations]]** (internal: draft-vs-extraction-matrix consistency)
- **[[../verify-sources/SKILL|Verify Sources]]** (external: bibliographic-record verification — real? retracted? faithful?)
- **[[../validate-evidence/SKILL|Validate Evidence]]**
- **[[../validate-consistency/SKILL|Validate Consistency]]**
- **[[../frame-contributions/SKILL|Frame Contributions]]** (Optional: framing for contributions section)
- **Steering:** [[../../steering/ai-research-provenance|AI Research Provenance]] (per-decision provenance stamping + mandatory `ai-disclosure.md` artifact)

---

## Workflow

### Phase 1: Detection
1.  **Detect manuscript**: Look for `*-draft.md`, `manuscript.md`.
2.  **Detect supporting files**: `synthesis-notes.md`, `argument-outline.md`.

### Phase 2: Execution Loop

1.  **Citations (internal layer)**: Run `validate-citations`.
    - Output: `validation/citations-report.md`
    - Gate: Score <75 flags warning.
    - Scope: checks **internal** draft-vs-extraction-matrix consistency (do the in-text citations match the extraction matrix?). It cannot tell whether a cited source is real or retracted.

1b. **Source verification (external layer)**: Run `verify-sources` **alongside** `validate-citations` (different layer — run both).
    - Output: `verification/source-verification.md`
    - Scope: resolves each citation against the **external** bibliographic record (scite MCP preferred, else CrossRef/OpenAlex) — checks DOI existence + author/year match, retraction/correction/concern status, and claim-vs-source fidelity. Emits per-citation status (VERIFIED / RETRACTED / UNVERIFIED / FLAGGED / MISMATCH) and a PASS/FAIL gate.
    - Gate: **PASS requires zero RETRACTED, zero UNVERIFIED, zero un-reviewed MISMATCH.** See consolidated gate logic below — a verify-sources FAIL is a HARD fail of the manuscript gate.

2.  **Evidence**: Run `validate-evidence` (GRADE framework).
    - Output: `validation/evidence-report.md`
    - Info only.

3.  **Consistency**: Run `validate-consistency` (Cross-check Draft vs Outline vs Synthesis).
    - Output: `validation/consistency-report.md`
    - Gate: Score <75 flags error.

### Phase 3: Consolidation
Generate `validation-report.md` (Executive Summary).

**Consolidated gate logic.** A `verify-sources` **FAIL** (any citation marked RETRACTED or UNVERIFIED) is a **HARD fail** of the manuscript gate — it overrides any otherwise-passing dimension scores and **cannot be silently passed**. The consolidated status is `BLOCKED` until every RETRACTED/UNVERIFIED citation is resolved, or a human override is logged. Any override of this gate MUST be recorded as a `human_override` event per [[../../steering/ai-research-provenance|ai-research-provenance]] (model + model_version + prompt_id + human_override on the decision); an un-logged override is not a valid pass.

**AI disclosure artifact.** Every run also emits `ai-disclosure.md` per [[../../steering/ai-research-provenance|ai-research-provenance]] (PRISMA-trAIce 2025 aligned; ICMJE/COPE — disclose substantive AI assistance, never list AI as author), documenting the AI assistance used across the validation pass.

```markdown
# Manuscript Validation Report
**Overall Score:** 84.5/100
**Status:** PASS / NEEDS ATTENTION

| Dimension | Score | Status |
|-----------|-------|--------|
| Citations | 87/100| PASS   |
| Consistency| 82/100| PASS   |
| Evidence  | Mod   | INFO   |

## Critical Issues
1. [Issue 1]
2. [Issue 2]
```

---

## Configuration
- `quick_mode`: true/false (If true, skips Evidence grading).
- `strictness`: moderate (default).

## Success Criteria
- Citation Score ≥ 75
- Consistency Score ≥ 75
- All critical issues addressed.


## Internal Metadata
- **tags**: [validation, batch, orchestrator, manuscript]
- **domain**: validation
- **status**: active
- **version**: 1.0
- **created**: 2026-01-26
- **updated**: 2026-01-26