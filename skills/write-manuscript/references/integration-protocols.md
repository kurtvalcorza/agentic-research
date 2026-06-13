# Integration Protocols

How write-manuscript integrates with other skills in the research workflow.

---

## Integration with Literature Review Automation (LRA)

### Handoff from LRA Phase 3

**Context:**
LRA (recursive-lit-review skill) processes large numbers of papers and produces:
- `argument-outline.md` - Structured argument from literature
- `synthesis-notes.md` - Consolidated findings

**Handoff Protocol:**

1. **Receive LRA Outputs**
   - `argument-outline.md` (from LRA Phase 3)
   - `synthesis-notes.md` (from LRA Phase 2)

2. **Critical Review (Bridge Protocol)**
   - Read LRA outputs
   - **Challenge:** "LRA identified [Gap X]. Do you agree this is the real gap, or is it missing something?"
   - User must adjudicate LRA's interpretation

3. **Proceed with Adjudicated Position**
   - Use LRA outputs as input to Phase 1
   - User's adjudication overrides LRA's framing
   - Write Manuscript builds on user's position, not LRA's output

### Why the Bridge Protocol Matters

**LRA outputs should NOT be accepted uncritically:**
- LRA synthesizes what papers say
- Write Manuscript helps you decide what YOU say
- User must own the intellectual position

**Critical Questions:**
- Does LRA's identified gap match your understanding?
- Is LRA's proposed contribution aligned with your research?
- Are there tensions LRA smoothed over that need surfacing?

### File Dependencies

**Input from LRA:**
- `argument-outline.md` → Used in Phase 2 (outline scaffolding)
- `synthesis-notes.md` → Used in Phase 1 (source understanding)

**Output from Write Manuscript:**
- `manuscript-draft.md` → Can feed back to LRA for gap validation

---

## Integration with Recursive Lit Review (RLM)

### Handoff from RLM

**Context:**
RLM processes 50-500+ papers and produces:
- `meta-themes.md` - Cross-cutting themes across literature

**Handoff Protocol:**

1. **Receive RLM Output**
   - `meta-themes.md` (thematic synthesis)

2. **Structure Themes into Argument**
   - Themes are descriptive (what literature says)
   - Manuscript is argumentative (what YOU claim)
   - Transform themes into Known → Gap → Contribution structure

3. **Critical Transformation**
   - **Meta-themes ≠ Your argument**
   - Themes become background/literature review
   - Your contribution positions itself relative to themes

### Example Transformation

**RLM Meta-theme:**
> "Papers converge on three approaches to AI governance: regulation-first, innovation-first, and hybrid models."

**Your Argument (from Write Manuscript):**
> "While literature identifies three governance approaches, existing frameworks fail to account for [Gap X]. This work proposes [Contribution Y], a fourth approach that addresses [Gap X]."

### File Dependencies

**Input from RLM:**
- `meta-themes.md` → Used in Phase 2 (background section)

**Output from Write Manuscript:**
- `manuscript-draft.md` → Positions contribution relative to meta-themes

---

## Integration with Validate Manuscript

### Auto-Handoff at Phase 5

**Context:**
After Phase 4 quality gates pass, write-manuscript automatically offers validation.

**Handoff Protocol:**

1. **Pre-Population**
   - `manuscript-draft.md` (from Phase 3)
   - `synthesis-notes.md` (from LRA or manual input)
   - `manuscript-outline.md` (from Phase 2)

2. **Validation Invocation**
   - Invoke validate-manuscript skill
   - Pass pre-populated files
   - Begin 4-skill validation sequence

3. **Validation Execution**
   Validate Manuscript runs:
   - Citation validation
   - Evidence checking
   - Contribution validation
   - Consistency verification

4. **Results Handoff**
   - `validation-report.md` (consolidated score)
   - `validation/*.md` (detailed sub-reports)
   - Overall status: PASS / NEEDS ATTENTION / FAIL

### Integration Benefits

**Seamless Workflow:**
- No manual file referencing
- Pre-populated context
- Consistent validation every time
- Clear pass/fail before submission

**Quality Assurance:**
- Catches issues missed in Phase 4 quality gates
- Provides quantitative scoring
- Identifies specific problems with line references
- Suggests remediation

### Post-Validation Actions

**If PASS:**
- Manuscript ready for submission
- Export to final format (DOCX, PDF)

**If NEEDS ATTENTION:**
- Review validation-report.md
- Address flagged issues
- Re-run validation

**If FAIL:**
- Critical issues must be resolved
- Do not proceed to submission
- Address issues and re-validate

### File Dependencies

**Input to Validate Manuscript:**
- `manuscript-draft.md`
- `synthesis-notes.md`
- `manuscript-outline.md`

**Output from Validate Manuscript:**
- `validation-report.md` (consolidated)
- `validation/citation-validation.md`
- `validation/evidence-validation.md`
- `validation/contribution-validation.md`
- `validation/consistency-validation.md`

---

## Integration with Tools for Thought

### Conceptual Integration

**Write Manuscript IS Tools for Thought applied to academic writing:**

**Shared Principles:**
- Provocation mode
- Productive resistance
- Cognitive enhancement (not replacement)
- User intellectual ownership

**Shared Patterns:**
- Challenge before assist
- Surface assumptions
- Present alternatives
- Force adjudication

### When to Use Each

**Use Tools for Thought:**
- General writing (non-academic)
- Exploratory writing
- Content creation (blog posts, articles)
- Communications writing

**Use Write Manuscript:**
- Academic papers
- Research synthesis
- Citation-heavy work
- Requires validation

**Both skills share:** Anti-ghostwriting philosophy

---

## Cross-Skill Workflow Example

**Full Research-to-Publication Pipeline:**

```
1. Recursive Lit Review (RLM)
   → Processes 200 papers
   → Outputs: meta-themes.md

2. Literature Review Automation (LRA)
   → Refines themes into argument
   → Outputs: argument-outline.md, synthesis-notes.md

3. Write Manuscript (This Skill)
   → Transforms argument into manuscript
   → Outputs: manuscript-draft.md, manuscript-outline.md

4. Validate Manuscript (Auto-invoked)
   → Validates citation, evidence, contribution, consistency
   → Outputs: validation-report.md (PASS/FAIL)

5. Export to Submission Format
   → DOCX, PDF, LaTeX (external tools)
```

**Total Time:**
- RLM: 2-4 hours (automated)
- LRA: 1-2 hours
- Write Manuscript: 45 min (Full Mode) or 15-20 min (Express Mode)
- Validate Manuscript: 5 min
- **Total: 4-7 hours** (vs weeks manually)

---

## File Flow Diagram

```
[RLM] → meta-themes.md
          ↓
[LRA] → argument-outline.md + synthesis-notes.md
          ↓
[Write Manuscript] → manuscript-outline.md (Phase 2)
                    → manuscript-draft.md (Phase 3)
                    → citation-check.md (Phase 4)
          ↓
[Validate Manuscript] → validation-report.md (Phase 5)
                       → validation/*.md
```

---

## Version History

### v1.1 - 2026-01-18
- Auto-handoff to Validate Manuscript at Phase 5
- Seamless pre-population of validation inputs
- Consolidated validation reporting
