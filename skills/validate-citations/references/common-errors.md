# Common Citation Errors and Fixes

Reference for auto-repair suggestions in validate-citations.

---

## Critical Errors (HALT validation)

### 1. Fabricated Citation
**Pattern:** Citation not found in corpus
**Example:** "(Johnson, 2025)" but no Johnson 2025 in sources
**Fix Options:**
- Remove citation
- Find actual source and add to corpus
- Replace with correct attribution

### 2. Author Mismatch
**Pattern:** Wrong author credited for claim
**Example:** "Smith (2023) found X" but X is from Jones (2022)
**Fix:** Replace with correct author

### 3. Year Mismatch
**Pattern:** Wrong publication year
**Example:** "(Chen, 2021)" but paper is Chen, 2022
**Fix:** Correct the year

---

## Warning Errors (Flag but continue)

### 4. Misattribution of Claim
**Pattern:** Claim doesn't match what paper actually says
**Example:** "AI reduces costs by 50% (Lee, 2023)" but Lee says "up to 30%"
**Fix Options:**
- Correct the claim to match source
- Find source that supports original claim
- Add hedge: "up to 50%" or "significantly reduces"

### 5. Over-generalization
**Pattern:** Narrow finding presented as broad claim
**Example:** "Machine learning improves outcomes (Park, 2024)" but Park studied only one specific context
**Fix:** Add context: "in K-12 education (Park, 2024)"

### 6. Missing Page Number
**Pattern:** Direct quote without page reference
**Example:** "The data clearly shows..." (Wang, 2023)
**Fix:** Add page number: (Wang, 2023, p. 45)

---

## Minor Errors (Report only)

### 7. Inconsistent Formatting
**Pattern:** Mixed citation styles
**Example:** "(Smith, 2023)" and "(Jones 2022)" in same document
**Fix:** Standardize to one format

### 8. Duplicate Citations
**Pattern:** Same source cited multiple times with slight variations
**Example:** "(Smith et al., 2023)" and "(Smith, Chen, & Lee, 2023)"
**Fix:** Standardize to one form (usually shorter)

### 9. Missing DOI
**Pattern:** Journal article without DOI when available
**Fix:** Add DOI to reference list

### 10. Incorrect Et Al. Usage
**Pattern:** "Et al." used for 2-author paper
**Example:** "(Smith et al., 2023)" but only Smith & Jones
**Fix:** List all authors for 2-author works

---

## Auto-Repair Suggestions

When an error is detected, the skill generates repair suggestions:

```markdown
## Issue #1: Misattribution (CRITICAL)

**Location:** Section 2.1, paragraph 3
**Current text:** "AI tutoring improves test scores by 40% (Chen, 2023)"
**Problem:** Chen 2023 reports 15-25% improvement, not 40%

**Suggested fixes:**
1. Correct to match source: "improves test scores by 15-25% (Chen, 2023)"
2. Find different source that supports 40%
3. Hedge the claim: "can improve test scores significantly (Chen, 2023)"

**Action required:** Select fix option or provide custom correction
```

---

## Evidence Strength Matching

Citations should match evidence strength:

| Claim Language | Required Evidence |
|----------------|-------------------|
| "X causes Y" | Experimental study, RCT |
| "X is associated with Y" | Correlational study |
| "X may influence Y" | Observational study |
| "X is theorized to Y" | Theoretical paper |
| "X suggests Y" | Single study |
| "Studies show X" | Multiple studies |

**Error:** Using strong language ("causes") with weak evidence (correlational)
**Fix:** Downgrade language to match evidence

---

## Citation Balance Checks

### Over-reliance
**Pattern:** 5+ citations from same author/paper
**Risk:** Narrow perspective, potential bias
**Suggestion:** Diversify sources

### Under-citation
**Pattern:** Major claim with single citation
**Risk:** Weak support
**Suggestion:** Add supporting citations

### Self-citation
**Pattern:** Excessive citations to own prior work
**Risk:** Perception of self-promotion
**Guideline:** Self-citations should be <15% of total

---

*Last updated: 2026-01-18*
