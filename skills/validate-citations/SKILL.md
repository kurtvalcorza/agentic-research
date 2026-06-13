---
name: validate-citations
description: "Validate citations with fuzzy-search auto-recovery. Use when checking that all draft citations match the extraction matrix, auditing bibliography accuracy, or running citation QA before submission."
---








# Specialist: Citation Validator

## Purpose
Ensure every citation in the draft exists in the extraction matrix.

## Scope: internal vs external
This skill verifies citations against the **INTERNAL** extraction matrix **only**. It confirms that a cited `(Author, Year)` exists in your own sources (draft-vs-matrix consistency) — nothing more. It **cannot** detect a **fabricated** or **retracted** source, because a hallucinated citation can be perfectly consistent between the draft and the matrix (the same bad entry appears in both, so the internal check still PASSes).

For **external truth** — does the source actually exist in the world? is it retracted/corrected? is the claim faithful to what the source says? — use the **`verify-sources`** skill, which resolves each citation against bibliographic databases (scite MCP / CrossRef / OpenAlex), checks DOI existence, author/year match, retraction status, and claim-vs-source fidelity.

**Run BOTH:** `validate-citations` for internal consistency, **and** `verify-sources` for external truth. They are different, complementary layers — neither replaces the other.

## Inputs

Two research pipelines feed this validator, each with its own artifact-naming scheme. Detect and accept whichever pair is present — the validation workflow is identical regardless of source.

| Role | `synthesize-research` (4-phase pipeline) | `review-literature` (8-phase pipeline) |
| :--- | :--- | :--- |
| Draft under validation | `outputs/phase3-draft.md` | `outputs/phase4-literature-review-draft.md` |
| Source / extraction matrix | `outputs/phase2-matrix.md` | `outputs/phase2-extraction-matrix.md` (synthesis variant: `outputs/phase2-synthesis-matrix.md`) |

> **Input conventions:** The `phase3-draft.md` / `phase2-matrix.md` names come from the `synthesize-research` 4-phase pipeline; the `phase4-literature-review-draft.md` / `phase2-extraction-matrix.md` names come from the `review-literature` 8-phase pipeline. Both are legitimate inputs — do not assume a single scheme; check which files actually exist. `references/detailed-guide.md` uses the `review-literature` names throughout.

## Outputs
- `outputs/phase4-validation.md` (the `review-literature` pipeline names the equivalent report `outputs/phase5-citation-validation.md`)

## Workflow

### 1. Verification
- Check inputs exist.

### 2. Extraction
- Regex extract all `(Author, Year)` patterns from Draft.

### 3. Validation Loop
For each Citation:
1.  **Exact Match**: Check if `(Author, Year)` exists in Matrix.
2.  **Auto-Fix (Fuzzy)**: If exact match fails:
    - Search Matrix for `Author`.
    - Search Matrix for `Year`.
    - If a unique candidate is found (e.g., mismatch "Smith 2024" vs "Smith 2024a"), **Log Warning** but PASS.
3.  **Fail Condition**: If no match found -> **Mark as INVALID**.

### 4. Reporting
- Generate `outputs/phase4-validation.md`.
- **Status**: PASS only if 0 INVALID citations.

## Error Handling
- **Critical Failure**: If >5 citations are invalid, recommend "Re-Drafting".


## Internal Metadata
- **capabilities**: [file-read, file-write, command-exec, file-search, content-search]
- **domain**: research
- **status**: active
- **version**: 2.0
- **type**: specialist