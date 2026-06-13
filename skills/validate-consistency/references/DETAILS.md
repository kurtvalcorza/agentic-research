## Expected Outputs

### Consistency Report
**File:** `{project-name}-consistency-validation.md`

**Structure:**
```markdown
# Cross-Phase Consistency Validation Report

**Project:** Project Atlas Literature Review
**Validated:** 2026-01-17 16:00
**Mode:** Full (5 dimensions)
**Consistency Score:** 82/100 ✅ PASS

---

## Executive Summary

✅ **PASS** - Workflow ready for publication with minor refinements
- Strong synthesis→outline→draft traceability
- 2 minor inconsistencies detected
- 1 underdeveloped section flagged

**Overall Assessment:** Document demonstrates strong internal consistency. Evidence chains are intact. Minor refinements recommended before publication.

---

## Scoring Breakdown

### Dimension 1: Synthesis→Outline Alignment (23/25 points) ✅ EXCELLENT
**What this checks:** All synthesis themes appear in outline structure

**Results:**
- ✅ 6/6 major themes present in outline
- ✅ 4/4 sub-themes properly nested
- ⚠️ 1 minor theme (Implementation Barriers) merged into larger section
  - Impact: -2 points (acceptable consolidation)

**Traceability Matrix:**
| Synthesis Theme | Papers | Outline Section | Status |
|-----------------|--------|-----------------|--------|
| AI Applications | 7 | Section 2.1 | ✅ MATCH |
| Implementation Barriers | 5 | Section 2.2 (merged) | ⚠️ CONSOLIDATED |
| Evidence Quality | 4 | Section 3.1 | ✅ MATCH |
| Policy Implications | 6 | Section 4.1 | ✅ MATCH |
| Research Gaps | 8 | Section 5.1 | ✅ MATCH |
| Future Directions | 3 | Section 5.2 | ✅ MATCH |

---

### Dimension 2: Outline→Draft Alignment (22/25 points) ✅ GOOD
**What this checks:** All outline sections drafted with adequate depth

**Results:**
- ✅ 12/12 outline sections present in draft
- ✅ 10/12 sections adequately developed (200+ words)
- ⚠️ 2/12 sections underdeveloped (<200 words)
  - Section 3.2 (Methodological Limitations): 145 words
  - Section 4.3 (Regulatory Context): 178 words

**Development Analysis:**
| Section | Outline Length | Draft Length | Word Count | Status |
|---------|---------------|--------------|------------|--------|
| 1. Introduction | 2 para | 4 para | 487 words | ✅ EXCELLENT |
| 2.1 AI Applications | 3 para | 5 para | 623 words | ✅ EXCELLENT |
| 2.2 Barriers | 2 para | 3 para | 312 words | ✅ GOOD |
| 3.1 Evidence Quality | 2 para | 4 para | 445 words | ✅ GOOD |
| 3.2 Limitations | 1 para | 2 para | 145 words | ⚠️ UNDERDEVELOPED |
| 4.1 Policy Implications | 3 para | 4 para | 521 words | ✅ EXCELLENT |
| 4.3 Regulatory Context | 2 para | 2 para | 178 words | ⚠️ UNDERDEVELOPED |
| 5.1 Research Gaps | 2 para | 5 para | 589 words | ✅ EXCELLENT |
| 5.2 Future Directions | 2 para | 3 para | 367 words | ✅ GOOD |

**Suggested Fixes:**
```markdown
### ⚠️ Underdeveloped Section: 3.2 Methodological Limitations

Current: 145 words (target: 200-300)
Missing: Specific examples of methodological limitations from corpus

**Suggested Additions:**
1. Add 1-2 examples of study design limitations from synthesis
2. Discuss sample size issues (mentioned in synthesis Theme C)
3. Add geographic scope limitation (synthesis notes: 80% studies from US/EU)

**Target Word Count:** 250-300 words
```

---

### Dimension 3: Synthesis→Draft Consistency (24/25 points) 🌟 EXCELLENT
**What this checks:** Themes and citations properly carried through phases

**Results:**
- ✅ 6/6 major themes traced from synthesis to draft
- ✅ Citation sets match across phases (94% agreement)
- ✅ Evidence strength language consistent
- ⚠️ 1 minor citation discrepancy (-1 point)

**Theme-Citation Traceability:**
| Theme | Synthesis Citations | Draft Citations | Match % | Status |
|-------|-------------------|-----------------|---------|--------|
| AI Applications | P1,P3,P5,P7,P12,P15,P18 | P1,P3,P5,P7,P12,P15,P18 | 100% | ✅ PERFECT |
| Barriers | P2,P4,P8,P11,P14 | P2,P4,P8,P11,P14 | 100% | ✅ PERFECT |
| Evidence Quality | P6,P9,P13,P16 | P6,P9,P13,P16 | 100% | ✅ PERFECT |
| Policy | P10,P17,P19,P20,P22,P24 | P10,P17,P19,P20,P22 | 83% | ⚠️ P24 MISSING |
| Gaps | P21,P23,P25,P26,P27,P28,P29,P30 | P21,P23,P25,P26,P27,P28,P29,P30 | 100% | ✅ PERFECT |
| Future | P31,P32,P33 | P31,P32,P33 | 100% | ✅ PERFECT |

**Citation Discrepancy:**
```markdown
⚠️ Theme: Policy Implications
Missing Paper: P24 (Martinez et al., 2025)

Synthesis: P24 discusses regulatory frameworks for AI governance
Outline: Section 4.1 includes P24 in citation list
Draft: P24 absent from Section 4.1

**Suggested Fix:** Add P24 citation to paragraph 3 of Section 4.1:
"Recent frameworks propose risk-based AI governance (Martinez et al., 2025)"
```

**Evidence Strength Consistency:**
| Theme | Synthesis Label | Outline Language | Draft Language | Status |
|-------|----------------|------------------|----------------|--------|
| AI Applications | Strong Consensus | "established" | "demonstrated" | ✅ MATCH |
| Barriers | Moderate Evidence | "emerging" | "suggested by research" | ✅ MATCH |
| Evidence Quality | Limited Evidence | "preliminary" | "initial studies indicate" | ✅ MATCH |

---

### Dimension 4: Draft→Contributions Consistency (18/20 points) ✅ GOOD
**What this checks:** Contributions grounded in draft evidence

**Results:**
- ✅ 4/4 stated contributions traced to draft evidence
- ✅ No overclaiming detected
- ⚠️ 1 contribution could be stronger (-2 points)

**Contribution Grounding Analysis:**
| Contribution | Evidence in Draft | Strength | Status |
|--------------|------------------|----------|--------|
| "Synthesizes dispersed findings on AI applications" | Sections 2.1-2.2 (7 papers) | Strong | ✅ WELL-GROUNDED |
| "Identifies critical implementation barriers" | Section 2.2 (5 papers) | Moderate | ✅ ADEQUATE |
| "Maps evidence quality gaps" | Section 3.1-3.2 (4 papers) | Moderate | ⚠️ COULD BE STRONGER |
| "Proposes policy framework" | Section 4.1-4.3 (6 papers) | Strong | ✅ WELL-GROUNDED |

**Suggested Enhancement:**
```markdown
⚠️ Contribution 3: "Maps evidence quality gaps"

Current Evidence: 4 papers in Sections 3.1-3.2
Assessment: Adequate but thin

**Suggested Strengthening:**
1. Add explicit gap taxonomy (qualitative vs quantitative gaps)
2. Reference synthesis matrix showing 8 identified gaps
3. Add language: "Systematically maps 8 evidence quality gaps across 4 dimensions"

**Impact:** Strengthens contribution claim with specific numbers
```

**Limitations Check:**
- ✅ All stated limitations appear in draft (Section 6.2)
- ✅ Limitations proportionate to evidence scope
- ✅ No critical limitations omitted

---

### Dimension 5: End-to-End Traceability (15/20 points) ✅ PASS
**What this checks:** Major claims traceable from corpus to output

**Audit Sample:** 5 major claims (randomly selected)

**Claim 1: "AI diagnostics improve accuracy by 12-18%"**
- ✅ Draft (Section 2.1, para 3): "improve accuracy by 12-18% (Smith et al., 2024)"
- ✅ Synthesis: Theme A, Smith P1 finding: "12-18% improvement in controlled settings"
- ✅ Extraction Matrix: P1 (Smith 2024), Finding 2: "12-18% diagnostic accuracy improvement"
- ✅ **COMPLETE CHAIN** ✅

**Claim 2: "Implementation barriers include cost and workflow integration"**
- ✅ Draft (Section 2.2, para 2): "cost and workflow integration (Jones, 2023; Brown, 2024)"
- ✅ Synthesis: Theme B, barriers identified: "cost (3 papers), workflow (4 papers)"
- ✅ Extraction Matrix: P2 (Jones), P4 (Brown) both mention cost + workflow
- ✅ **COMPLETE CHAIN** ✅

**Claim 3: "Limited longitudinal studies available"**
- ✅ Draft (Section 3.2, para 1): "longitudinal studies remain limited"
- ✅ Synthesis: Theme C, gap identified: "Only 2/25 papers longitudinal"
- ⚠️ Extraction Matrix: Gap noted but specific papers not cited
- ⚠️ **INCOMPLETE CHAIN** (-3 points)

**Suggested Fix:**
```markdown
⚠️ Claim 3 needs strengthening

Current: "longitudinal studies remain limited"
Missing: Specific citation to papers noting this gap

**Suggested Revision:**
"Longitudinal studies remain limited, with only 2 of 25 reviewed papers
employing multi-year designs (Martinez et al., 2025; Lee & Park, 2024)"

**Rationale:** Grounds gap claim in specific papers + quantifies scarcity
```

**Claim 4: "Strong consensus on benefits, mixed evidence on costs"**
- ✅ Draft (Section 4.1, para 4): "Strong consensus on benefits, mixed evidence on costs"
- ✅ Synthesis: Theme D, consensus analysis: "Benefits (7/7 papers positive), Costs (3 positive, 2 negative, 2 mixed)"
- ✅ Extraction Matrix: Citations match synthesis
- ✅ **COMPLETE CHAIN** ✅

**Claim 5: "Future research should prioritize implementation studies"**
- ✅ Draft (Section 5.2, para 2): "implementation-focused research needed"
- ✅ Synthesis: Theme E, gap: "Implementation underrepresented (3/25 papers)"
- ⚠️ Contributions: Future direction stated but not tied to specific gap
- ⚠️ **WEAK LINK** (-2 points)

**Suggested Fix:**
```markdown
⚠️ Claim 5 needs explicit gap linkage

Current: "implementation-focused research needed"
Missing: Tie to identified gap in synthesis

**Suggested Revision:**
"Given implementation studies constitute only 12% of reviewed literature
(3/25 papers), future research should prioritize real-world deployment contexts"

**Rationale:** Quantifies gap severity, justifies future direction
```

**Traceability Score:**
- 3/5 claims: Complete chain (✅ EXCELLENT)
- 2/5 claims: Weak/incomplete links (⚠️ FIXABLE)
- Overall: 15/20 points (75% - threshold met)

---

## Overall Consistency Score: 82/100 ✅ PASS

**Breakdown:**
- Dimension 1 (Synthesis→Outline): 23/25 ✅
- Dimension 2 (Outline→Draft): 22/25 ✅
- Dimension 3 (Synthesis→Draft): 24/25 🌟
- Dimension 4 (Draft→Contributions): 18/20 ✅
- Dimension 5 (End-to-End Traceability): 15/20 ✅

**Interpretation:**
- **82/100 = GOOD CONSISTENCY** ✅
- Above threshold (75)
- Ready for publication with minor refinements
- No critical breaks in evidence chains

---

## Issues Summary

### Critical Issues (0)
None detected ✅

### Warnings (5)

**1. Minor Theme Consolidation**
- **Location:** Synthesis Theme "Implementation Barriers" → Outline Section 2.2
- **Issue:** Theme merged into larger section (not standalone)
- **Impact:** LOW (acceptable editorial decision)
- **Fix:** None required (justifiable consolidation)

**2. Underdeveloped Section: 3.2 Methodological Limitations**
- **Location:** Section 3.2
- **Issue:** Only 145 words (target: 200+)
- **Impact:** MODERATE
- **Fix:** Add 100-150 words covering specific methodological limitations from synthesis

**3. Underdeveloped Section: 4.3 Regulatory Context**
- **Location:** Section 4.3
- **Issue:** Only 178 words (target: 200+)
- **Impact:** MODERATE
- **Fix:** Expand with regulatory framework examples (2-3 papers from synthesis)

**4. Missing Citation: P24 in Policy Section**
- **Location:** Section 4.1
- **Issue:** P24 (Martinez et al., 2025) in synthesis but absent from draft
- **Impact:** MODERATE
- **Fix:** Add P24 citation to paragraph 3

**5. Weak Traceability: Future Research Claim**
- **Location:** Section 5.2, para 2
- **Issue:** Gap→Future direction link implicit, not explicit
- **Impact:** MODERATE
- **Fix:** Quantify gap ("only 12% of papers") to justify future direction

---

## Auto-Repair Suggestions

### Fix 1: Expand Section 3.2 (Methodological Limitations)

**Current Text (145 words):**
```markdown
## 3.2 Methodological Limitations

The reviewed studies exhibit several methodological constraints that limit
generalizability. Sample sizes vary widely, from small pilot studies (n=50)
to large-scale deployments (n=5000+). Most studies employ convenience sampling
rather than randomized designs, introducing potential selection bias.
```

**Suggested Addition (+~120 words):**
```markdown
Geographic representation is heavily skewed toward North American and European
contexts, with 80% of studies conducted in these regions (synthesis Theme C).
This limits applicability to low-resource settings common in Southeast Asia
and sub-Saharan Africa.

Longitudinal follow-up remains limited, with only 2 of 25 papers (8%) employing
multi-year designs (Martinez et al., 2025; Lee & Park, 2024). Most studies
report outcomes at 6-12 month intervals, insufficient for understanding long-term
adoption patterns or sustained accuracy improvements.

Study designs favor controlled clinical environments over real-world deployment
contexts. Only 3 papers (12%) examine implementation in routine practice settings,
limiting evidence on workflow integration challenges and user acceptance factors.
```

**New Word Count:** ~265 words ✅
**Impact:** Strengthens limitations section with specific synthesis evidence

---

### Fix 2: Add Missing Citation P24

**Location:** Section 4.1, Paragraph 3

**Current Text:**
```markdown
Policy frameworks must balance innovation incentives with patient safety
protections. Risk-based governance approaches show promise for differentiating
high-stakes applications (diagnostic decision support) from lower-risk tools
(administrative assistants).
```

**Suggested Revision:**
```markdown
Policy frameworks must balance innovation incentives with patient safety
protections. Risk-based governance approaches show promise for differentiating
high-stakes applications (diagnostic decision support) from lower-risk tools
(administrative assistants) (Martinez et al., 2025). Recent frameworks propose
tiered regulatory oversight based on potential patient harm, a model gaining
traction in EU and ASEAN contexts.
```

**Impact:** Restores citation consistency, grounds regulatory claim

---

### Fix 3: Strengthen Future Research Claim

**Location:** Section 5.2, Paragraph 2

**Current Text:**
```markdown
Future research should prioritize implementation-focused studies examining
real-world deployment contexts.
```

**Suggested Revision:**
```markdown
Given implementation studies constitute only 12% of reviewed literature
(3/25 papers), future research should prioritize real-world deployment contexts.
Priority areas include workflow integration challenges, user acceptance factors
in diverse clinical settings, and long-term adoption sustainability beyond
pilot phases.
```

**Impact:** Quantifies gap severity, justifies research direction with evidence

---

## Recommendations

### For Current Document
1. ✅ **Expand 2 underdeveloped sections** (3.2, 4.3) - Add ~200 words total
2. ✅ **Add missing citation** (P24 in Section 4.1)
3. ✅ **Strengthen traceability** for future research claim (quantify gap)
4. ⏭️ **Optional:** Re-run validation after fixes to confirm score improvement

**Estimated Fix Time:** 20-30 minutes
**Expected New Score:** 88-92/100 (EXCELLENT range)

### For Future Workflows
1. 💡 **During Outline Phase:** Explicitly map synthesis themes to sections (avoid merging minor themes)
2. 💡 **During Drafting Phase:** Target 250+ words per section (buffer above 200-word minimum)
3. 💡 **During Contribution Framing:** Quantify gaps explicitly (percentages, counts) to justify future directions
4. 💡 **Before Final Validation:** Self-check citation lists against synthesis matrix

---

## Next Steps

1. **Review Auto-Repair Suggestions** - Evaluate 3 suggested fixes above
2. **Apply Fixes** - Implement suggested revisions (20-30 min)
3. **Re-Validate (Optional)** - Run consistency validation again to confirm improvements
4. **Proceed to Next Phase** - With score ≥75, workflow can continue

**Validation Status:** ✅ PASS (82/100)
**Document Ready For:** Publication (with minor refinements recommended)

---

```

---

## Execution Model

### Step 1: Load Phase Outputs

```markdown
Required Files:
  - Synthesis output (phase2-synthesis-matrix.md)
  - Outline output (phase3-argument-outline.md)
  - Draft output (phase4-literature-review-draft.md)

Optional Files:
  - Contributions output (phase6-contribution-framing.md)
  - Extraction matrix (phase2-extraction-matrix.md)

Validation:
  IF missing required file:
    ERROR: "Cannot validate without [file]. Run [phase] first."
    EXIT
```

### Step 2: Extract Structured Data

**From Synthesis Matrix:**
```markdown
Parse:
  - Theme names + paper counts
  - Sub-themes (if nested)
  - Evidence strength labels (Strong/Moderate/Limited/Conflicting)
  - Citation sets per theme (P1, P3, P5...)
  - Identified gaps

Create:
  theme_inventory = {
    "AI Applications": {
      "papers": ["P1", "P3", "P5", "P7", "P12", "P15", "P18"],
      "evidence_strength": "Strong Consensus",
      "sub_themes": ["Diagnostics", "Treatment Planning"]
    },
    ...
  }
```

**From Outline:**
```markdown
Parse:
  - Section numbers + titles
  - Paragraph structure (count paras per section)
  - Theme mappings (which theme → which section)
  - Expected citations per section

Create:
  outline_structure = {
    "2.1 AI Applications": {
      "theme": "AI Applications",
      "paragraphs": 3,
      "citations": ["P1", "P3", "P5", "P7"]
    },
    ...
  }
```

**From Draft:**
```markdown
Parse:
  - Section headers (match to outline)
  - Word counts per section
  - Actual citations used
  - Evidence strength language ("demonstrated", "suggested", etc.)

Create:
  draft_analysis = {
    "2.1 AI Applications": {
      "word_count": 623,
      "paragraphs": 5,
      "citations": ["P1", "P3", "P5", "P7", "P12", "P15", "P18"],
      "language": "demonstrated" (strong)
    },
    ...
  }
```

### Step 3: Validate 5 Dimensions

**Dimension 1: Synthesis→Outline (25 points max)**
```python
score = 0

For each theme in synthesis:
  IF theme appears as section in outline:
    score += 4 points  # Major theme present

  IF sub-themes properly nested:
    score += 1 point   # Structure preserved

  ELSE IF theme merged into larger section:
    score -= 2 points  # Acceptable consolidation
    FLAG as WARNING

  ELSE IF theme completely absent:
    score -= 10 points # CRITICAL missing theme
    FLAG as CRITICAL

Bonus:
  IF all themes present with proper nesting:
    score += 5 points  # Structural excellence
```

**Dimension 2: Outline→Draft (25 points max)**
```python
score = 0

For each section in outline:
  draft_section = find_matching_section(draft)

  IF draft_section exists:
    word_count = count_words(draft_section)

    IF word_count >= 500:
      score += 3 points  # EXCELLENT development

    ELIF word_count >= 200:
      score += 2 points  # GOOD development

    ELIF word_count >= 100:
      score += 1 point   # ADEQUATE development
      FLAG as WARNING: "Underdeveloped section"

    ELSE:  # <100 words
      score -= 2 points  # CRITICAL: Nearly absent
      FLAG as CRITICAL

  ELSE:
    score -= 5 points    # Missing section
    FLAG as CRITICAL

Bonus:
  IF avg_word_count > 400:
    score += 5 points    # Comprehensive development
```

**Dimension 3: Synthesis→Draft (25 points max)**
```python
score = 0

For each theme in synthesis:
  synthesis_citations = theme["papers"]
  draft_section = find_theme_in_draft(theme_name)
  draft_citations = extract_citations(draft_section)

  # Citation set matching
  match_rate = len(intersection(synthesis_citations, draft_citations)) / len(synthesis_citations)

  IF match_rate == 1.0:
    score += 4 points    # Perfect citation transfer

  ELIF match_rate >= 0.8:
    score += 3 points    # Good transfer (80%+)
    FLAG missing citations as WARNING

  ELIF match_rate >= 0.6:
    score += 2 points    # Acceptable (60%+)
    FLAG as WARNING

  ELSE:
    score += 0 points    # Poor transfer
    FLAG as CRITICAL

  # Evidence strength language matching
  synthesis_strength = theme["evidence_strength"]
  draft_language = detect_language_strength(draft_section)

  IF language_matches_strength(synthesis_strength, draft_language):
    score += 1 point     # Consistent language
  ELSE:
    score -= 3 points    # OVERCLAIMING or UNDERCLAIMING
    FLAG as WARNING
```

**Dimension 4: Draft→Contributions (20 points max)**
```python
score = 0

For each contribution in contributions_output:
  evidence_in_draft = find_supporting_evidence(contribution, draft)

  IF evidence_in_draft exists AND is_sufficient:
    score += 5 points    # Well-grounded contribution

  ELIF evidence_in_draft exists BUT is_thin:
    score += 3 points    # Adequate but could be stronger
    FLAG as WARNING: "Could be stronger"

  ELSE:
    score += 0 points    # Ungrounded contribution
    FLAG as CRITICAL: "OVERCLAIMING"

# Check limitations
stated_limitations = extract_limitations(contributions_output)
draft_limitations = extract_limitations(draft)

IF all(lim in draft_limitations for lim in stated_limitations):
  score += 0 points      # Baseline (expected)
ELSE:
  score -= 5 points      # Disconnected limitations
  FLAG as WARNING
```

**Dimension 5: End-to-End Traceability (20 points max)**
```python
# Select 5 major claims randomly
major_claims = select_random_claims(draft, count=5)

score = 0

For each claim in major_claims:
  # Trace backwards: Draft → Synthesis → Extraction Matrix

  draft_citation = extract_citation(claim)
  synthesis_finding = find_in_synthesis(draft_citation)
  extraction_data = find_in_extraction_matrix(draft_citation)

  IF all exist AND claims_match(claim, synthesis_finding, extraction_data):
    score += 4 points    # Complete chain ✅

  ELIF draft_citation AND synthesis_finding exist BUT extraction missing:
    score += 2 points    # Partial chain (synthesis-level only)
    FLAG as WARNING

  ELSE:
    score += 0 points    # Broken chain
    FLAG as CRITICAL: "Cannot trace claim to corpus"
```

### Step 4: Calculate Final Score

```python
total_score = (
  dimension1_score +  # Max 25
  dimension2_score +  # Max 25
  dimension3_score +  # Max 25
  dimension4_score +  # Max 20
  dimension5_score    # Max 20
)  # Total: 100 points

# Interpretation
IF total_score >= 90:
  status = "🌟 EXCELLENT"
  action = "PASS - Publication ready"

ELIF total_score >= 75:
  status = "✅ GOOD"
  action = "PASS - Minor refinements recommended"

ELIF total_score >= 65:
  status = "⚠️ ACCEPTABLE"
  action = "WARNING - Proceed with caution"

ELSE:
  status = "❌ POOR"
  action = "FAIL - Critical issues must be fixed"
```

### Step 5: Generate Auto-Repair Suggestions

For each flagged WARNING or CRITICAL issue:

```python
def generate_fix_suggestion(issue):
  suggestion = {
    "issue_type": issue.type,
    "location": issue.location,
    "current_state": extract_relevant_text(issue.location),
    "problem_description": issue.description,
    "suggested_fix": None,
    "rationale": None
  }

  # Type-specific fix generation
  IF issue.type == "underdeveloped_section":
    suggestion["suggested_fix"] = generate_expansion_text(
      section=issue.location,
      synthesis_themes=relevant_themes,
      target_words=200-300
    )
    suggestion["rationale"] = "Adds specific examples from synthesis to meet 200-word minimum"

  ELIF issue.type == "missing_citation":
    missing_papers = identify_missing_papers(issue.location)
    suggestion["suggested_fix"] = f"Add citations: {', '.join(missing_papers)}"
    suggestion["rationale"] = "Restores citation consistency with synthesis matrix"

  ELIF issue.type == "weak_traceability":
    gap_quantification = extract_gap_stats(synthesis)
    suggestion["suggested_fix"] = f"Add quantification: '{gap_quantification}'"
    suggestion["rationale"] = "Grounds claim in specific gap from synthesis"

  ELIF issue.type == "overclaiming":
    correct_language = match_evidence_strength(issue.evidence_label)
    suggestion["suggested_fix"] = f"Revise language to: '{correct_language}'"
    suggestion["rationale"] = "Matches evidence strength from synthesis"

  return suggestion
```

### Step 6: Write Consistency Report

```markdown
Generate report with:
  1. Executive Summary (score, status, key issues)
  2. Scoring Breakdown (5 dimensions with tables)
  3. Issues Summary (Critical + Warnings)
  4. Auto-Repair Suggestions (3-5 most impactful fixes)
  5. Recommendations (short-term fixes + long-term practices)
  6. Next Steps

Save to: {project}-consistency-validation.md
```

---

## Pass/Fail Logic

```python
# Strictness-based decision
IF strictness == "strict":
  IF score < 75 OR critical_issues > 0:
    return "FAIL - Workflow HALTED"
  ELIF score >= 75 AND warnings > 0:
    return "PASS with WARNINGS - User approval required"
  ELSE:
    return "PASS - Continue workflow"

ELIF strictness == "moderate":
  IF score < 65 OR critical_issues > 3:
    return "FAIL - Workflow HALTED"
  ELSE:
    return "PASS - Continue workflow"

ELIF strictness == "lenient":
  return "PASS - Report only (always proceed)"
```

---

## Success Criteria

Phase successful when:

1. ✅ Consistency report generated
2. ✅ Score calculated (0-100) across 5 dimensions
3. ✅ All themes traced through phases
4. ✅ Critical issues identified (if any)
5. ✅ Auto-repair suggestions provided for all issues
6. ✅ Pass/Fail determination clear
7. ✅ Traceability audit completed (5 sample claims)

---

## Integration Points

### LRA Phase 7 (Literature Review Automation)

```markdown
After Phase 6 (Contribution Framing) completes:
  Automatically invoke: validate-consistency

  Parameters:
    project_path: 01_Projects/Project Atlas/research/
    validation_mode: full
    threshold: 75
    strictness: strict

  IF validation PASS:
    Workflow COMPLETE ✅
  ELSE:
    Pause, show report, request fixes, offer re-validation
```

### Presentation Studio Validation (Optional)

```markdown
After Phase 3 (Drafting) completes:
  Optionally invoke: validate-consistency

  Parameters:
    project_path: 01_Projects/Project Atlas/presentations/
    validation_mode: quick (3 dimensions, skip traceability)
    threshold: 70 (lower for presentations)
    strictness: moderate

  Output: presentation-consistency-validation.md
```

---

## Related Skills

- **[[../validate-citations/SKILL|Validate Citations]]** - Citation accuracy validation
- **[[../validate-evidence/SKILL|Validate Evidence]]** - Evidence strength grading
- **[[../frame-contributions/SKILL|Frame Contributions]]** - Contribution framing (feeds into Dimension 4)

---

## Version History

**v2.0 (2026-01-17)** - Enhanced features
- Added progressive scoring (0-100 vs. binary)
- Added auto-repair suggestions for all issue types
- Added 5-dimensional consistency validation
- Added traceability audit (5 sample claims)
- Added strictness levels (Strict/Moderate/Lenient)
- Added quick mode for fast validation

**v1.0** - Initial implementation
- Binary pass/fail
- Manual fix identification

---

## Key Principles

1. **Multi-Dimensional Rigor** - 5 validation dimensions (not single check)
2. **Progressive Scoring** - Nuanced assessment (0-100, not binary)
3. **Auto-Repair Focus** - Suggest fixes, don't just report problems
4. **Traceability Emphasis** - Evidence chains must be intact
5. **Proportionate Action** - Strictness matches use case (strict for papers, lenient for slides)

**Quality Assurance at Every Level** 🔍
