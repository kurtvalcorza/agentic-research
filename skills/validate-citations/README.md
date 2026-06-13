# Citation Validator

Validates citations in manuscript drafts against your extraction matrix to ensure every claim has proper source attribution.

## What It Does

- **Exact Match First**: Checks if citations exactly match entries in your extraction matrix
- **Fuzzy Auto-Fix**: Attempts to auto-correct minor variations (typos, formatting differences)
- **Validation Report**: Generates detailed report with invalid citations highlighted
- **Pass/Fail Grading**: PASS only if zero invalid citations remain
- **Critical Threshold**: More than 5 invalid citations triggers recommendation to re-draft

## When to Use

- After drafting a manuscript but before final review
- When you need to verify research integrity
- As part of the research pipeline before submission
- When reviewers question citation accuracy

## How It Works

1. Reads your manuscript draft
2. Extracts all citation references
3. Compares against your extraction matrix
4. Attempts fuzzy matching for near-misses
5. Produces validation report with:
   - Valid citations (✓)
   - Auto-fixed citations (⚠️)
   - Invalid citations (✗)
   - Critical failure warning if threshold exceeded

## Outputs

- **Validation Report**: Markdown file with detailed findings
- **Pass/Fail Status**: Clear indication of citation integrity
- **Auto-Fix Suggestions**: Recommended corrections for review

## Scope: Internal vs External

This skill checks citations against your **internal** extraction matrix **only** — it confirms a cited (Author, Year) exists in your own sources. It **cannot** tell whether a source is real or has been retracted, because a hallucinated citation can be perfectly consistent between the draft and the matrix. For **external truth** (does the source exist in the world? is it retracted? is the claim faithful to the source?), use the `verify-sources` skill. Run **both**: `validate-citations` for internal consistency, `verify-sources` for external truth.

## Related Skills

- `synthesize-research` - Generates manuscripts this skill validates
- `validate-manuscript` - Comprehensive quality suite including citation checks
- `validate-consistency` - Cross-phase consistency validation
- `verify-sources` - External citation verification (DOI existence, retraction/correction checks, claim-vs-source fidelity); complements this skill's internal-only check
