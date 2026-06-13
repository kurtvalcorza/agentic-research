# Consistency Validation Protocol

Comprehensive protocol for cross-phase consistency checking in multi-phase research workflows.

---

## Overview

Consistency validation ensures that claims, evidence, and contributions flow coherently across all phases of a research workflow. This protocol defines the five validation dimensions and their scoring criteria.

---

## The Five Dimensions

### Dimension 1: Synthesis → Outline Alignment

**Purpose:** Ensure all synthesis themes appear in the outline structure.

**Check Process:**
1. Extract all themes from synthesis matrix
2. Scan outline for theme coverage
3. Flag themes missing from outline

**Scoring:**
| Coverage | Score | Status |
|----------|-------|--------|
| 100% themes represented | 100/100 | PASS |
| 90-99% coverage | 85-99/100 | WARN |
| <90% coverage | <85/100 | FAIL |

**Common Issues:**
- **Theme dropped**: A synthesis theme doesn't appear in any outline section
- **Theme underrepresented**: Theme appears but allocated insufficient sections
- **Theme split**: One theme fragmented across unrelated sections

**Auto-Repair Suggestions:**
```
IF theme_dropped:
  SUGGEST: "Add section for [Theme X] after Section 3"
  PROVIDE: Section stub with theme connection

IF theme_underrepresented:
  SUGGEST: "Expand Section 2.3 to fully address [Theme X]"
  PROVIDE: Sub-section structure
```

---

### Dimension 2: Outline → Draft Development

**Purpose:** Ensure outline sections are properly developed in the draft.

**Check Process:**
1. Map outline sections to draft headings
2. Measure paragraph count per section
3. Flag underdeveloped or overdeveloped sections

**Scoring:**
| Development | Score | Status |
|-------------|-------|--------|
| All sections proportionally developed | 100/100 | PASS |
| Minor imbalances (<20% variance) | 80-99/100 | WARN |
| Major gaps (>20% variance or missing) | <80/100 | FAIL |

**Development Heuristics:**
- Major outline section: Expect 3-5 paragraphs minimum
- Sub-section: Expect 1-3 paragraphs minimum
- Bullet point in outline: Expect at least mention in draft

**Common Issues:**
- **Section stub**: Outline section exists but draft has <100 words
- **Section missing**: Outline section has no corresponding draft content
- **Section ballooned**: Draft section significantly exceeds outline scope

---

### Dimension 3: Evidence Chain Integrity

**Purpose:** Ensure claims in draft have traceable evidence support.

**Check Process:**
1. Extract claims from draft (sentences with assertions)
2. Trace each claim to synthesis evidence
3. Flag claims without evidence anchors

**Evidence Traceability Requirements:**
```
For each claim in draft:
  1. Claim text → Identifies in draft
  2. → Traces to theme in synthesis matrix
  3. → Theme supported by papers in corpus
  4. → Papers have valid citations

If ANY link breaks: FLAG as "Evidence Gap"
```

**Scoring:**
| Traceability | Score | Status |
|--------------|-------|--------|
| 100% claims traceable | 100/100 | PASS |
| 90-99% traceable | 80-99/100 | WARN |
| <90% traceable | <80/100 | FAIL |

**Common Issues:**
- **Orphan claim**: Assertion in draft not grounded in synthesis
- **Citation missing**: Claim references synthesis but lacks citation
- **Evidence gap**: Theme claims more than evidence supports

---

### Dimension 4: Contribution Grounding

**Purpose:** Ensure stated contributions are grounded in identified gaps.

**Check Process:**
1. Extract contribution statements from draft/framing
2. Cross-reference with gap identification in synthesis
3. Flag contributions not anchored to gaps

**Contribution Validity Check:**
```python
for contribution in draft.contributions:
  if contribution.claim NOT IN synthesis.identified_gaps:
    FLAG: "Contribution Drift"
    SHOW: What gap was supposed to anchor this contribution

  if contribution.evidence_grade > synthesis.evidence_grade:
    FLAG: "Overclaim"
    SUGGEST: Downgrade language to match evidence
```

**Scoring:**
| Grounding | Score | Status |
|-----------|-------|--------|
| All contributions gap-anchored | 100/100 | PASS |
| 1 contribution drifted | 80-95/100 | WARN |
| Multiple drifts or overclaims | <80/100 | FAIL |

---

### Dimension 5: End-to-End Traceability

**Purpose:** Verify complete traceability from corpus to final claims.

**Check Process:**
1. Sample 5-10 claims from draft conclusion
2. Trace each backward through all phases
3. Calculate traceability success rate

**Full Chain Validation:**
```
Conclusion Claim
  ↓ traces to
Draft Body Section
  ↓ traces to
Outline Section
  ↓ traces to
Synthesis Theme
  ↓ traces to
Extraction Matrix Entry
  ↓ traces to
PDF Corpus Paper

If ALL links valid: ✅ PASS
If ANY link broken: ❌ FAIL for that claim
```

**Scoring:**
| End-to-End | Score | Status |
|------------|-------|--------|
| 100% sample traceable | 100/100 | PASS |
| 80-99% traceable | 75-99/100 | WARN |
| <80% traceable | <75/100 | FAIL |

---

## Aggregate Scoring

### Dimension Weights

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Synthesis → Outline | 20% | Foundation for structure |
| Outline → Draft | 20% | Development completeness |
| Evidence Chains | 25% | Core validity |
| Contribution Grounding | 20% | Strategic accuracy |
| End-to-End | 15% | System integrity |

### Overall Score Calculation

```python
overall_score = (
  synthesis_outline * 0.20 +
  outline_draft * 0.20 +
  evidence_chains * 0.25 +
  contribution_grounding * 0.20 +
  end_to_end * 0.15
)
```

### Pass/Fail Thresholds

| Overall Score | Status | Action |
|---------------|--------|--------|
| ≥75 | **PASS** | Ready for submission |
| 65-74 | **WARN** | Review suggested fixes, may proceed |
| <65 | **FAIL** | Must fix before proceeding |

---

## Strictness Levels

### Strict Mode
- **Behavior:** Halt workflow on any dimension <75 or critical issue
- **Use when:** Final submission, thesis defense, high-stakes publication
- **Tolerance:** Zero

### Moderate Mode (Default)
- **Behavior:** Warn on 65-74, halt only on <65 or multiple issues
- **Use when:** Standard manuscript preparation
- **Tolerance:** Low

### Lenient Mode
- **Behavior:** Report all issues, never halt
- **Use when:** Exploratory drafts, internal review
- **Tolerance:** High

---

## Issue Categories

### Critical Issues (Always halt in strict mode)
- Evidence claim with ZERO traceability
- Contribution contradicts synthesis gap
- Missing citations for key claims
- Section entirely missing from draft

### Major Issues (Halt in strict/moderate)
- Theme dropped from outline
- Evidence chain broken for >10% claims
- Contribution drift detected
- Section stub (<100 words where >500 expected)

### Minor Issues (Report only)
- Citation format inconsistency
- Theme ordering differs from synthesis
- Paragraph count variance 10-20%
- Non-critical section underdeveloped

---

## Auto-Repair Protocol

When issues are detected, the skill generates repair suggestions:

### For Theme Drops
```markdown
**Issue:** Theme "Implementation Barriers" missing from outline

**Suggested Repair:**
Add after Section 3 (Accuracy Findings):

### 4. Implementation Barriers
- 4.1 Cost Considerations (Theme B.1)
- 4.2 Workflow Integration (Theme B.2)
- 4.3 Training Requirements (Theme B.3)

**Evidence:** Synthesis themes B.1-B.3, 5 papers
```

### For Evidence Gaps
```markdown
**Issue:** Claim "AI diagnostics improve equity" has no evidence support

**Options:**
1. **Remove claim** - Delete unsupported assertion
2. **Hedge claim** - Revise to "May improve equity (evidence gap)"
3. **Add evidence** - Locate supporting papers and add to synthesis
```

### For Contribution Drift
```markdown
**Issue:** Contribution "Establishes deployment framework" not anchored to identified gap

**Analysis:**
- Synthesis identified gap: "Implementation barriers unclear"
- Draft claims: "Framework for deployment"
- Drift: Gap about barriers, not deployment guidance

**Suggested Repair:**
Revise contribution: "Identifies implementation barriers informing deployment planning"
```

---

## Integration with LRA

When invoked as LRA Phase 7:

```
Phase 6 (Frame Contributions) completes
  ↓
Invoke validate-consistency
  ↓
Parameters:
  synthesis_file: phase2-synthesis-matrix.md
  outline_file: phase3-argument-outline.md
  draft_file: phase4-literature-review-draft.md
  strictness: moderate
  ↓
Run 5 dimension checks
  ↓
Generate consistency-validation.md
  ↓
IF overall ≥75: PASS → Ready for export
IF 65-74: WARN → Show fixes, ask user
IF <65: FAIL → Must fix before proceeding
```

---

## Checklist for Manual Review

Use when automated check produces WARN:

- [ ] All synthesis themes appear in outline sections
- [ ] Each outline section has proportional draft content
- [ ] Key claims have traceable evidence citations
- [ ] Contributions match identified gaps (not drift)
- [ ] Conclusion claims traceable to corpus papers
- [ ] No overclaiming (language matches evidence grade)
- [ ] Limitations acknowledge evidence weaknesses

---

*Consistency is the final quality gate before submission.*
