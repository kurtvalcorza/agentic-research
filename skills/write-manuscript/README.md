# Write Manuscript

Transform research notes into publication-ready academic manuscripts with quality gates and validation.

---

## What This Skill Does

**Write Manuscript** synthesizes research notes (from literature reviews, AI summaries, or manual notes) into coherent academic manuscripts through a structured 5-phase workflow with built-in quality assurance.

**Core Principle:** Bridge "summary" to "synthesis" - manuscripts are argumentative, not just descriptive compilations.

---

## When to Use This Skill

Use this skill when you need to:

- ✅ Transform research notes into academic papers
- ✅ Structure findings into coherent arguments
- ✅ Ensure citations trace to sources
- ✅ Validate manuscript quality before submission
- ✅ Write thesis chapters or journal articles
- ✅ Create blog posts or policy briefs from research

**Not for:**
- ❌ Auto-generating manuscripts without user input
- ❌ Writing content without source material
- ❌ Creating documents without argumentation

---

## Modes

Choose between two workflow modes:

### Full Mode (45 minutes)
**For:** Thesis chapters, journal papers, original research, grant proposals

**Characteristics:**
- Comprehensive structure analysis
- Deep tension exploration
- Thorough quality checking
- All quality gates fully enforced

### Express Mode (15-20 minutes)
**For:** Blog posts, news releases, policy briefs, executive summaries

**Characteristics:**
- Streamlined workflow
- Lighter analysis (1-2 key checks per section)
- Same quality standards, faster execution
- 56% time savings vs Full Mode

---

## Quick Start

### Basic Usage

```
"Help me write a manuscript based on these research notes:
- research/note1.md
- research/note2.md
- research/note3.md"
```

The skill will guide you through:
1. **Source Synthesis** - Identify contribution
2. **Argument Structuring** - Create outline
3. **Interactive Drafting** - Write sections
4. **Quality Gates** - Verify citations and consistency
5. **Validation Handoff** - Comprehensive quality check

### With Literature Review Automation (LRA)

```
"I have LRA outputs (argument-outline.md, synthesis-notes.md).
Help me write the manuscript."
```

The skill automatically integrates with LRA outputs and challenges you to adjudicate the proposed argument.

---

## What You Get

### Output Files

| File | Purpose |
|------|---------|
| `manuscript-outline.md` | Argument structure with section-level claims |
| `manuscript-draft.md` | Complete manuscript draft |
| `citation-check.md` | Source verification report |
| `validation-report.md` | Comprehensive quality assessment (if validated) |

### Quality Guarantees

- ✅ Every claim traces to provided sources
- ✅ No hallucinated citations
- ✅ Tensions identified and adjudicated
- ✅ Argument consistency verified
- ✅ Gap-contribution alignment checked

---

## Workflow Overview

### Phase 1: Source Synthesis
**Goal:** Understand what you're contributing

- Read research notes
- Identify knowns, gaps, and key claims
- Articulate single most important contribution

**Checkpoint:** You must articulate your contribution before proceeding.

---

### Phase 2: Argument Structuring
**Goal:** Create argumentative outline

**Framework:** Known → Gap → Contribution

- Map consensus across sources
- Identify tensions (don't smooth over)
- Scaffold outline with section-level claims

**Output:** `manuscript-outline.md`

---

### Phase 3: Interactive Drafting
**Goal:** Transform outline into prose

**Core Pattern:** Challenge-Before-Assist

- Draft section-by-section
- Present alternative framings
- Require adjudication of tensions
- Verify source traceability

**Output:** `manuscript-draft.md`

---

### Phase 4: Quality Gates
**Goal:** Verify quality standards

**Citation Check:**
- All claims trace to sources
- No hallucinated citations
- Outside sources flagged

**Consistency Check:**
- Conclusion matches Introduction
- Gap matches Contribution
- Terminology consistent

**Output:** `citation-check.md`

---

### Phase 5: Validation Handoff
**Goal:** Comprehensive quality assessment

Auto-invokes **validate-manuscript** skill for:
- Citation validation
- Evidence checking
- Contribution validation
- Consistency verification

**Result:** Overall score (X/100) + PASS/FAIL status

**Output:** `validation-report.md`

---

## Anti-Patterns (What NOT to Do)

| Don't Do This | Why It's Bad |
|--------------|--------------|
| Copy-paste summaries | Summaries ≠ synthesis |
| Accept AI framing uncritically | You must own the argument |
| Invent citations | All claims must trace to sources |
| Smooth over tensions | Tensions are research opportunities |
| Skip contribution test | Without contribution, there's no manuscript |

---

## Integration with Other Skills

### Recursive Lit Review (RLM)
- RLM produces `meta-themes.md`
- Write Manuscript structures themes into argument
- Themes become background; your contribution positions relative to themes

### Literature Review Automation (LRA)
- LRA produces `argument-outline.md` + `synthesis-notes.md`
- Write Manuscript challenges you to adjudicate LRA's position
- You own the intellectual stance, not LRA

### Validate Manuscript
- Auto-invoked at Phase 5
- Runs 4-skill validation sequence
- Returns consolidated quality report

---

## Example Use Cases

### Use Case 1: Thesis Chapter
**Input:** 15 research notes from literature review
**Mode:** Full Mode (45 min)
**Output:** 5000-word thesis chapter with validated citations

### Use Case 2: Policy Brief
**Input:** 5 research summaries + synthesis matrix from LRA
**Mode:** Express Mode (15-20 min)
**Output:** 2000-word policy brief with quality gates

### Use Case 3: Journal Article
**Input:** Meta-themes from RLM (200 papers)
**Mode:** Full Mode (45 min)
**Output:** 8000-word journal article with comprehensive validation

---

## Tips for Success

### Before You Start
1. **Have research notes ready** - Markdown files with findings
2. **Know your contribution** - What unique knowledge does this create?
3. **Identify tensions** - Where do sources disagree?

### During Drafting
1. **Don't accept uncritically** - Challenge the framing presented
2. **Adjudicate tensions** - Take a position on contradictions
3. **Verify sources** - Every claim must trace back

### After Drafting
1. **Run validation** - Use Phase 5 validation handoff
2. **Address issues** - Fix problems before submission
3. **Export only after PASS** - Don't submit with unresolved issues

---

## FAQs

**Q: Can I skip the contribution test?**
A: No. This is a BLOCKING checkpoint. Without a clear contribution, there's no argument to structure.

**Q: What if my sources disagree?**
A: Good! Tensions are research opportunities. The skill will highlight disagreements and require you to adjudicate.

**Q: Can I use sources not in my input notes?**
A: Only if explicitly acknowledged. The skill will warn when you introduce outside sources.

**Q: What's the difference between Full and Express Mode?**
A: Express Mode is 56% faster with lighter analysis, but maintains all quality gates. Use Express for short-form content.

**Q: Do I have to run validation?**
A: No, but it's strongly recommended. Validation catches issues missed in Phase 4 quality gates.

---

## Version History

### v1.1 - 2026-01-18
- Added Express Mode (15-20 min for short-form content)
- Integrated validate-manuscript at Phase 5
- 56% time savings for Express Mode

### v1.0 - 2026-01-17
- Initial 4-phase workflow
- Quality gates implementation
- LRA and RLM integration

---

## Technical Details

**Required Tools:**
- Read (ingest notes)
- Write (create drafts)
- Glob (locate files)

**Optional Integrations:**
- recursive-lit-review
- review-literature
- validate-manuscript

**File Organization:**
```
project/
├── inputs/
│   └── research-note-*.md
├── outputs/
│   ├── manuscript-outline.md
│   ├── manuscript-draft.md
│   ├── citation-check.md
│   └── validation/
│       └── validation-report.md
```

For implementation details, see [SKILL.md](SKILL.md).

---

**Last Updated:** 2026-02-14
**Skill Version:** 1.1
**Status:** Active
