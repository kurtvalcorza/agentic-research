## Execution Model

> **Input conventions (both supported):** The filenames in this guide follow the `review-literature` 8-phase pipeline — `phase2-extraction-matrix.md` / `phase2-synthesis-matrix.md` (source matrices) and `phase4-literature-review-draft.md` (draft). The `synthesize-research` 4-phase pipeline feeds the same artifacts under shorter names — `phase2-matrix.md` (matrix) and `phase3-draft.md` (draft). Both are valid inputs: detect which pipeline produced the corpus and match the files that actually exist rather than assuming one naming scheme. See the Inputs table in `SKILL.md` for the side-by-side mapping.

### Step 1: Extract Citations from Document

```markdown
1. Read target document
2. Detect citation format (APA, IEEE, Chicago, Vancouver)
3. Extract all citations using format-specific regex:

   APA: (Author, Year) or (Author et al., Year)
   IEEE: [1], [2-5], [1,3,7]
   Chicago: (Author Year) or footnote markers
   Vancouver: (1), (1-3), (1,3,5)

4. Create citation inventory:
   - Citation text: "Research shows X (Smith, 2024)"
   - Author-Year/Number: Smith, 2024 OR [12]
   - Claim: "Research shows X"
   - Location: [section name, paragraph number, line number]
   - Format: APA parenthetical
```

### Step 2: Load Source Corpus

```markdown
IF source_type == "extraction-matrix":
    Read {corpus-dir}/outputs/phase2-extraction-matrix.md
    Parse into:
    - Paper ID → Author-Year → Findings → Evidence Strength

ELSE IF source_type == "corpus":
    Glob {corpus-dir}/corpus/approved/*.pdf
    For each PDF:
        - Extract metadata (author, year, title)
        - Extract key findings (abstract, conclusion)

ELSE IF source_type == "synthesis":
    Read {corpus-dir}/outputs/phase2-synthesis-matrix.md
    Parse themes + citations
```

### Step 3: Validate Each Citation

For each citation extracted from document:

#### A) Existence Check
```markdown
Is this citation in source corpus?

YES → Proceed to B
NO  → FABRICATED CITATION (CRITICAL)
      - Score: -40 points
      - Severity: CRITICAL
      - Action: HALT workflow (if strictness == strict)
```

#### B) Claim Alignment Check
```markdown
Does draft claim match what source actually found?

Scoring:
- Perfect match or reasonable paraphrase: +3 points
- Different finding than paper: MISATTRIBUTION (WARNING, -10 points)
- Overstated beyond paper's findings: OVERCLAIM (WARNING, -15 points)
- Understated (paper found more): OK (conservative, +2 points)

Evidence Strength Check:
IF source evidence == "Strong Consensus":
    Draft language should be confident ("Research shows", "Studies demonstrate")
    IF draft uses weak language: Suggest stronger phrasing

IF source evidence == "Limited" OR "Conflicting":
    Draft language should be cautious ("Some studies suggest", "Limited evidence indicates")
    IF draft uses confident language: OVERCLAIM (WARNING, -15 points)
```

#### C) Format Validation
```markdown
Is citation formatted correctly for target format?

APA Checks:
- Parentheses present: (Author, Year)
- Et al. used for 3+ authors: (Smith et al., 2024)
- Page numbers for direct quotes: (Smith, 2024, p. 15)
- Multiple citations alphabetized: (Brown, 2023; Smith, 2024)

IEEE Checks:
- Square brackets: [1]
- Sequential numbering: [1], [2], [3] (not [1], [3], [2])
- Range formatting: [1-5] (not [1,2,3,4,5])

Chicago Checks:
- Parenthetical: (Author Year) OR Footnote: ^1
- Consistency within document

Vancouver Checks:
- Parentheses with number: (1)
- Sequential numbering
```

### Step 4: Calculate Validation Score

```markdown
Total Points: 100

Dimension 1: Citation Accuracy (40 points max)
- All citations exist in corpus: +40
- Each fabricated citation: -40 (CRITICAL)
- Each misattribution: -10

Dimension 2: Evidence Strength (30 points max)
- Strong consensus claims properly cited: +30
- Each weak evidence overclaim: -15
- Each unsupported claim: -20

Dimension 3: Format Consistency (30 points max)
- All citations correctly formatted: +30
- Each format inconsistency: -3
- Each missing required element (page #, et al., etc.): -5

Final Score: Sum / 100

Interpretation:
- 90-100: 🌟 EXCELLENT - Publication-ready
- 75-89:  ✅ PASS - Minor fixes recommended
- 60-74:  ⚠️ WARNING - Proceed with caution
- 0-59:   ❌ FAIL - Critical issues, cannot proceed
```

### Step 5: Generate Auto-Repair Suggestions

For each warning/error, provide:

```markdown
**Suggested Fix Template:**

Issue: [Brief description]
Location: [Section, paragraph, line]
Current Text: "[Exact quote from draft]"
Problem: [What's wrong]
Suggested Fix: "[Corrected version]"
Rationale: [Why this fix]

Example:

Issue: Overclaim detected
Location: Section 3, paragraph 2, line 14
Current Text: "AI diagnostics are 25% more accurate (Smith et al., 2024)"
Problem: Smith et al. report 12-18% improvement, not 25%
Suggested Fix: "AI diagnostics show 12-18% accuracy improvements in controlled settings (Smith et al., 2024)"
Rationale: Matches source evidence strength, adds context qualifier
```

### Step 6: Write Validation Report

```markdown
Generate {document-name}-citation-validation.md with:

1. Executive Summary (Pass/Fail, score, key issues)
2. Scoring Breakdown (3 dimensions)
3. Critical Issues section (if any)
4. Warnings section (with suggested fixes)
5. Recommendations (citation balance, format suggestions)
6. Full Citation Audit table
7. Next Steps
```

---

## Pass/Fail Logic

```markdown
PASS (Score ≥75) IF:
- Zero fabricated citations
- Zero high-severity misattributions
- Format inconsistencies <10

WARNING (Score 60-74) IF:
- Minor format issues present
- Some potential overclaims
- User acknowledges and proceeds

FAIL (Score <60) IF:
- Any fabricated citations found
- High-severity misattributions (>3)
- Cannot proceed without fixes

Actions by Strictness Level:

STRICT (default):
  FAIL → HALT workflow, require fixes, re-validate
  WARN → User approval required to proceed
  PASS → Continue workflow

MODERATE:
  FAIL → HALT only for fabricated citations
  WARN → Report but allow proceed
  PASS → Continue workflow

LENIENT:
  All → Report issues, always allow proceed
```

---

## Success Criteria

Phase successful when:

1. ✅ Validation report generated
2. ✅ Score calculated (0-100)
3. ✅ All citations checked against source
4. ✅ Fabricated citations identified (if any)
5. ✅ Auto-repair suggestions provided
6. ✅ Pass/Fail determination clear
7. ✅ Next steps documented

---

## Usage Examples

### Example 1: Validate LRA Phase 4 Draft

```bash
# Input
document_path: "01_Projects/Project Atlas/research/outputs/phase4-literature-review-draft.md"
source_type: "extraction-matrix"
citation_format: "apa"
strictness: "strict"

# Agent Executes
1. Reads phase4-literature-review-draft.md
2. Extracts 45 APA citations
3. Reads phase2-extraction-matrix.md
4. Validates each citation
5. Detects 2 format issues, 1 overclaim
6. Score: 87/100 ✅ PASS
7. Generates: phase4-literature-review-draft-citation-validation.md

# Output
"✅ PASS (87/100) - 2 minor fixes recommended. Document ready for Phase 6."
```

### Example 2: Validate Press Release

```bash
# Input
document_path: "01_Projects/Admin/PressReleases/atlas-launch.md"
source_type: "synthesis"
citation_format: "apa"
strictness: "moderate"

# Agent Executes
1. Reads atlas-launch.md
2. Extracts 8 citations
3. Reads synthesis notes from Project Atlas background
4. Validates claims against synthesis
5. Detects 1 fabricated citation (CRITICAL)
6. Score: 45/100 ❌ FAIL
7. Generates: atlas-launch-citation-validation.md

# Output
"❌ FAIL (45/100) - 1 fabricated citation detected. Remove (Johnson, 2025) - not in corpus."
```

### Example 3: Validate Technical Presentation

```bash
# Input
document_path: "01_Projects/Project Atlas/presentations/executive-briefing.md"
source_type: "synthesis"
citation_format: "apa"
strictness: "lenient"

# Agent Executes
1. Reads executive-briefing.md (Marp slides)
2. Extracts 12 citations from slides
3. Validates against Project Atlas synthesis
4. All citations valid, minor format variations
5. Score: 92/100 🌟 EXCELLENT
6. Generates: executive-briefing-citation-validation.md

# Output
"🌟 EXCELLENT (92/100) - Presentation citations are publication-ready."
```

---

## Advanced Features

### Multi-Format Citation Detection

Agent auto-detects citation format from document:

```markdown
Heuristics:
- Scan first 50 citations
- Count format patterns:
  - Parenthetical (Author, Year): APA or Chicago
  - Numeric [1]: IEEE
  - Numeric (1): Vancouver
  - Footnote markers: Chicago

- Majority format wins
- Report if mixed formats detected
```

### Citation Balance Analysis

Agent analyzes citation distribution

```markdown
For each unique source:
  Count citations
  Calculate percentage of total

IF any source >30% of total:
  FLAG: "Over-reliance on single paper"
  SUGGEST: "Consider citing additional sources for Themes X, Y"

IF any theme has <3 citations:
  FLAG: "Thin evidence for Theme Z"
  SUGGEST: "Add supporting citations OR acknowledge limitation"
```

### Evidence Strength Matching

Agent validates claim language matches evidence strength

```markdown
Evidence Strength Labels (from extraction matrix):
- Strong Consensus (5+ papers, agreement)
- Moderate Evidence (3-4 papers, mostly agree)
- Limited Evidence (1-2 papers)
- Conflicting Evidence (papers disagree)
- No Evidence (gap identified)

Language Matching:
Strong Consensus → "Research demonstrates", "Studies show", "Evidence indicates"
Moderate Evidence → "Research suggests", "Studies indicate", "Some evidence shows"
Limited Evidence → "Preliminary research suggests", "Limited studies indicate"
Conflicting → "Mixed evidence suggests", "Studies show conflicting results"

Overclaiming Detection:
IF draft uses "demonstrates" BUT evidence == "Limited":
  FLAG: OVERCLAIM (-15 points)
  SUGGEST: Downgrade language to "suggests"
```

---

## Error Handling

### Missing Source Corpus

```markdown
IF source_type == "extraction-matrix" AND file not found:
  ERROR: "Cannot validate without extraction matrix"
  SUGGEST: "Run LRA Phase 2 first OR specify source_type='corpus'"
  EXIT
```

### Ambiguous Citations

```markdown
IF citation format unclear (e.g., "Smith 2024" without parentheses):
  WARN: "Ambiguous citation format at Section X"
  ASSUME: Default to APA
  FLAG: Recommend adding parentheses
```

### Large Documents

```markdown
IF document >10,000 lines OR >500 citations:
  WARN: "Large document detected, validation may take 10-15 minutes"
  OFFER: "Run validation in background? (yes/no)"
  IF yes: Run as background task, notify on completion
```

---

## Integration Points

### Phase 5 of LRA (Literature Review Automation)

```markdown
After Phase 4 (Drafting) completes:
  Automatically invoke: validate-citations

  Parameters:
    document_path: outputs/phase4-literature-review-draft.md
    source_type: extraction-matrix
    citation_format: apa
    strictness: strict

  IF validation PASS:
    Proceed to Phase 6
  ELSE:
    Pause workflow, show validation report, request fixes
```

### Presentation Studio (Research Deck) Phase 3.5 (NEW)

```markdown
After Phase 3 (Drafting slides) completes:
  Optionally invoke: validate-citations

  Parameters:
    document_path: presentation.md
    source_type: synthesis
    citation_format: apa
    strictness: moderate (slides less strict than papers)

  Output: presentation-citation-validation.md
```

---

## Related Skills

- **[[../validate-consistency/SKILL|Validate Consistency]]** - Cross-phase consistency validation
- **[[../validate-evidence/SKILL|Validate Evidence]]** - Evidence strength grading (GRADE, Oxford CEBM)
- **[[../frame-contributions/SKILL|Frame Contributions]]** - Contribution framing with provocation

---

## Version History

**v2.0 (2026-01-17)** - Enhanced features
- Added multi-format support (APA, IEEE, Chicago, Vancouver)
- Added auto-repair suggestions
- Added evidence strength matching
- Added citation balance analysis
- Added progressive scoring (0-100)

**v1.0** - Initial implementation
- Author-year matching
- Binary pass/fail
- Manual repair

---

## Key Principles

1. **Zero Tolerance for Fabrication** - Any fabricated citation = CRITICAL
2. **Evidence-Claim Alignment** - Claims must match source evidence strength
3. **Format Consistency** - Citations follow academic standards
4. **Helpful Suggestions** - Auto-repair suggestions for all issues
5. **Progressive Scoring** - Nuanced quality assessment (not binary)

**Academic Integrity First** 🎓