# Validate Consistency

Cross-phase consistency validation for research workflows. Ensures synthesis, outline, draft, and contributions align with no contradictions or dropped claims.

## What It Checks

**Synthesis → Outline**
- All synthesis themes appear in outline
- No orphaned findings
- Section structure matches synthesis organization

**Outline → Draft**
- Every outline point is developed in draft
- No missing sections
- Depth matches outline intent

**Synthesis → Draft**
- Claims in draft have synthesis support
- No invented findings
- Evidence chains intact

**Draft → Contributions**
- Contributions justified by draft content
- No overclaiming
- Limitations acknowledged

**End-to-End Traceability**
- Full chain from raw data → synthesis → draft → contributions
- No broken links
- Consistent terminology

## Scoring System

**Score Range**: 0-100 points
- **90-100**: Excellent consistency
- **75-89**: Good, minor issues
- **60-74**: Moderate gaps, needs revision
- **Below 60**: Critical breaks, blocks workflow

**Threshold**: ≥75 required to pass

## What Happens on Failure

**Score < 75**: Workflow is blocked until issues resolved

Auto-generated repair suggestions:
- Missing sections to add
- Contradictions to reconcile
- Orphaned claims to integrate or remove
- Terminology inconsistencies to fix

## Validation Report Structure

```markdown
## Consistency Validation Report

**Overall Score**: 78/100 (PASS)

### Synthesis → Outline (25/25)
✅ All synthesis themes present
✅ Structure aligned

### Outline → Draft (22/25)
⚠️ Section 3.2 underdeveloped
⚠️ Missing example for finding #7

### Synthesis → Draft (20/25)
✅ All claims supported
✅ No invented findings

### Draft → Contributions (20/25)
⚠️ Contribution #2 overstated
⚠️ Limitation missing for RQ3

### End-to-End (18/25)
✅ Terminology consistent
⚠️ Weak link between Theme 2 → Section 4

## Repair Suggestions
1. Expand Section 3.2 with synthesis finding #7
2. Add concrete example for finding #7
3. Soften claim in Contribution #2
4. Add limitation about sample size for RQ3
5. Strengthen connection Theme 2 → Section 4
```

## When to Use

- After Phase 4 (drafting) before submission
- Before final review
- When reviewers question claim support
- During revision rounds
- As part of `validate-manuscript` suite

## Auto-Repair Capability

For minor issues (score 70-74), skill can attempt auto-repair:
- Add missing cross-references
- Flag contradictions for review
- Suggest text to bridge gaps
- Highlight orphaned content

## Related Skills

- `validate-manuscript` - Comprehensive quality suite (includes this)
- `validate-citations` - Citation integrity
- `validate-evidence` - Evidence strength grading
- `review-literature` - Phase 7 integration

## Typical Issues Caught

- Claims in discussion not in results
- Contributions not justified by findings
- Outline sections missing from draft
- Synthesis themes dropped during writing
- Terminology drift across sections
- Limitations contradicting findings
