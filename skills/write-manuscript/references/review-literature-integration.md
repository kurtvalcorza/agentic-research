# Review Literature Integration

## Overview

**Write Manuscript Slide Deck** can integrate with **Review Literature** skill when processing PDF-heavy research folders. This document explains when and how to bridge between the two skills.

**Key insight:** Review Literature specializes in deep synthesis of academic PDFs, while Write Manuscript Slide Deck specializes in strategic presentation framing. Used together, they create research decks with strong evidence foundations.

---

## When to Use Review Literature Before Write Manuscript Slide Deck

### Trigger Conditions

**Phase 0 Detection (automatic):**
```python
# Write Manuscript Slide Deck checks folder composition
if pdf_count > 5 and (pdf_count / total_files) > 0.5:
    recommend_lra = True
    prompt_user("This folder is PDF-heavy (>5 PDFs). Consider running Review Literature first for better synthesis.")
```

**User scenarios:**
1. **Research presentation** (thesis defense, conference talk)
   - Input: 10-20 academic PDFs
   - Need: Deep literature synthesis, citation tracking

2. **Systematic review** (meta-analysis, scoping review)
   - Input: 30+ PDFs
   - Need: Thematic extraction, contradiction detection

3. **Policy proposal** (evidence-based recommendations)
   - Input: 15+ policy papers, research reports
   - Need: Argument structuring, evidence grading

---

## Workflow Comparison

### Option A: Write Manuscript Slide Deck Direct (PDF-light)

**Best for:** <5 PDFs, Markdown-heavy folders, AI summaries

**Workflow:**
```
User Folder (3 PDFs, 5 MD files)
    ↓
Write Manuscript Slide Deck Phase 1 (Synthesis)
    → Extracts text from PDFs (basic)
    → Reads Markdown (full depth)
    → Creates STAGING.md
    ↓
Phase 2-4 (Interrogation → Drafting → Export)
    ↓
presentation.pdf
```

**Limitations:**
- PDF text extraction is basic (no citation parsing)
- No deep thematic analysis across papers
- Risk of missing nuanced arguments

---

### Option B: Review Literature → Write Manuscript Slide Deck (PDF-heavy)

**Best for:** >5 PDFs, deep research synthesis needed

**Workflow:**
```
User Folder (15 PDFs, 3 MD files)
    ↓
Review Literature
    → Phase 1: Corpus Screening
    → Phase 2: Extraction & Synthesis
    → Phase 3: Argument Structuring
    → Outputs: synthesis-matrix_project.md, thematic-clusters_project.md
    ↓
Write Manuscript Slide Deck ingests Review Literature outputs
    → Phase 1: Reads synthesis-matrix_project.md (structured themes)
    → Phase 2: Interrogation (SCIPAB framing)
    → Phase 3-4: Drafting → Export
    ↓
presentation.pdf (evidence-backed, citation-rich)
```

**Advantages:**
- Deep PDF synthesis (citation extraction, author analysis)
- Thematic clustering (identifies patterns across papers)
- Contradiction detection (flags conflicting findings)
- Higher-quality STAGING.md (stronger arguments)

---

## Decision Tree

```
Start: User requests deck from research folder
    ↓
Q1: How many PDFs?
    ├─ <5 PDFs → Write Manuscript Slide Deck Direct
    └─ >5 PDFs → Continue to Q2

Q2: What's the presentation type?
    ├─ Quick overview (30 min prep) → Write Manuscript Slide Deck Direct (accept lower depth)
    └─ Academic/research (90 min prep) → Review Literature → Write Manuscript Slide Deck

Q3: Are citations critical?
    ├─ No (internal briefing) → Write Manuscript Slide Deck Direct
    └─ Yes (conference, thesis) → Review Literature → Write Manuscript Slide Deck

Q4: Do you need thematic analysis?
    ├─ No (single-paper focus) → Write Manuscript Slide Deck Direct
    └─ Yes (multi-paper synthesis) → Review Literature → Write Manuscript Slide Deck
```

**Quick heuristic:**
- Academic presentation + >5 PDFs → **Use Review Literature first**
- Executive briefing + mixed sources → **Write Manuscript Slide Deck direct**

---

## Technical Integration

### Review Literature Output Structure

**Files produced by Review Literature:**
```
research-folder/
├── papers/                   # Original PDFs (unchanged)
│   ├── paper1.pdf
│   ├── paper2.pdf
│   └── ...
├── synthesis-matrix_project.md       # Main output (themes, arguments, citations)
├── thematic-clusters_project.md      # Grouped by research themes
├── screening-results_project.md      # Inclusion/exclusion decisions
└── bibliography.bib          # BibTeX citations (optional)
```

**Key file for Write Manuscript Slide Deck:** `synthesis-matrix_project.md`

---

### synthesis-matrix_project.md Format

**Example structure:**
```yaml
---
corpus_size: 15
screening_date: 2026-01-14
themes_identified: 6
---

## Theme 1: AI Bias in Hiring Systems

**Core argument:** AI hiring tools replicate human biases present in training data.

**Key papers:**
1. **[Dastin, 2018]** - Amazon's hiring AI favored male candidates (gender bias)
2. **[Buolamwini & Gebru, 2018]** - Facial recognition has higher error rates for darker skin (racial bias)
3. **[Obermeyer et al., 2019]** - Healthcare AI underestimates Black patients' needs (outcome bias)

**Contradictions:**
- [Cowgill & Tucker, 2020] argue AI can *reduce* bias if trained on de-biased data (methodological debate)

**Gaps:**
- Limited research on bias in non-Western contexts
- No longitudinal studies (>5 years)

---

## Theme 2: Explainability vs. Performance Trade-off

[Similar structure...]
```

---

### Write Manuscript Slide Deck Ingestion

**Phase 1 (Synthesis):**
```python
# Pseudo-code for Write Manuscript Slide Deck's Review Literature integration

def ingest_lra_outputs(folder_path):
    lra_synthesis = read_file(folder_path / "synthesis-matrix_project.md")

    if lra_synthesis exists:
        # Extract pre-structured themes
        themes = parse_themes(lra_synthesis)
        arguments = extract_arguments(lra_synthesis)
        contradictions = extract_contradictions(lra_synthesis)

        # Populate STAGING.md with high-quality data
        staging = {
            "source_inventory": ["synthesis-matrix_project.md (Review Literature output)"] + original_files,
            "key_arguments": arguments,  # Already grounded in citations
            "contradictions_found": contradictions,
            "scipab_seed": {
                "situation": infer_from_themes(themes),
                "complication": identify_primary_gap(lra_synthesis),
                # Implication & Action still need user input (Phase 2)
            }
        }
    else:
        # Fallback: Direct PDF ingestion (basic extraction)
        staging = synthesize_directly(folder_path)
```

**Key benefit:** Review Literature's `synthesis-matrix_project.md` provides structured, citation-backed arguments that Write Manuscript Slide Deck can directly map to SCIPAB elements.

---

## Example Workflow

### Scenario: AI Ethics Conference Presentation

**Input Folder:**
```
01_Projects/Research/AI-Ethics/
├── papers/                   # 18 PDFs (academic papers)
├── meeting-notes.md          # 1 MD file
└── research-questions.md     # 1 MD file
```

---

### Step 1: Invoke Review Literature

**User command (to agent):**
```
User: "I need a literature review for my AI ethics conference talk. Folder: @01_Projects/Research/AI-Ethics/"

Agent: "Detected 18 PDFs in this folder. For a high-quality synthesis, I recommend:

         Option A: Run Review Literature first (Quick Mode: 25 min)
                   → Structured themes, citations, contradictions
                   → Then feed to Write Manuscript Slide Deck for presentation framing

         Option B: Write Manuscript Slide Deck direct (15 min, lower depth)
                   → Basic PDF extraction, faster but less rigorous

         Which approach? [A/B]"

User: "Option A"
```

---

### Step 2: Review Literature Execution

**Review Literature workflow (simplified):**
1. **Phase 1: Corpus Screening**
   - Reads all 18 PDFs
   - Extracts metadata (authors, year, journal)
   - Applies inclusion criteria (relevance to AI ethics)
   - Output: `screening-results_project.md` (15 included, 3 excluded)

2. **Phase 2: Extraction & Synthesis**
   - Extracts key arguments from 15 papers
   - Clusters by theme (bias, transparency, accountability, etc.)
   - Identifies contradictions (e.g., EU vs. US regulatory approaches)
   - Output: `synthesis-matrix_project.md` (6 themes, 42 arguments)

3. **Phase 3: Argument Structuring**
   - Creates narrative arc (Which theme leads?)
   - Suggests citation order (chronological vs. thematic)
   - Output: `thematic-clusters_project.md` (ready for writing)

**Review Literature completion:**
```
Agent: "Review Literature complete! Generated:
         - synthesis-matrix_project.md (6 themes, 42 arguments)
         - thematic-clusters_project.md (narrative structure)
         - screening-results_project.md (15 included papers)

         Ready to invoke Write Manuscript Slide Deck for presentation framing?"

User: "Yes"
```

---

### Step 3: Write Manuscript Slide Deck Ingestion

**Write Manuscript Slide Deck Phase 0:**
```
Agent: "Scanning folder...
         - Found 18 PDFs (original papers)
         - Found synthesis-matrix_project.md (Review Literature output detected!)
         - Found 2 MD files (meeting-notes, research-questions)

         Ingesting Review Literature synthesis for higher-quality STAGING.md..."
```

**Write Manuscript Slide Deck Phase 1:**
```yaml
# STAGING.md (generated with Review Literature integration)

---
session_id: write-manuscript-slide-deck-2026-01-14-18-42
target_folder: 01_Projects/Research/AI-Ethics/
source_count: 21 (18 PDFs + 3 MD files)
lra_integration: true
last_updated: 2026-01-14T18:42:00Z
status: synthesis-complete
---

## Source Inventory
- **synthesis-matrix_project.md** (Review Literature output: 6 themes, 15 papers)
- meeting-notes.md
- research-questions.md
- papers/*.pdf (18 files - see synthesis-matrix_project.md for details)

## Key Arguments (from Review Literature)

### Theme: AI Bias in Hiring
1. AI hiring tools replicate training data biases → [Dastin, 2018; Buolamwini & Gebru, 2018]
2. Facial recognition has racial bias (higher error for darker skin) → [Buolamwini & Gebru, 2018]
3. Healthcare AI underestimates needs of Black patients → [Obermeyer et al., 2019]

### Theme: Explainability vs. Performance
1. Deep learning models are "black boxes" (high accuracy, low explainability) → [Rudin, 2019]
2. GDPR "right to explanation" conflicts with model complexity → [Wachter et al., 2017]

[... 4 more themes ...]

## Contradictions Found (from Review Literature)
- **Bias reduction debate:** [Cowgill & Tucker, 2020] claim AI can reduce bias if trained on de-biased data, but [Dastin, 2018] shows real-world failures (Amazon case).
- **Explainability necessity:** [Rudin, 2019] argues for inherently interpretable models, but [LeCun, 2020] defends black-box deep learning for high-stakes tasks.

## Gaps to Fill (for Write Manuscript Slide Deck Phase 2)
- [ ] Target audience? (Academic conference → researchers? Policy track → regulators?)
- [ ] Primary action? (Advocate for regulation? Promote technical solution? Call for more research?)
- [ ] Which theme should lead? (Bias? Explainability? Accountability?)

## SCIPAB Seed

**Situation (from Review Literature synthesis):**
AI systems are increasingly deployed in high-stakes domains (hiring, healthcare, criminal justice). Current practice is to optimize for performance (accuracy) without equal emphasis on fairness or transparency.

**Complication (from Review Literature contradictions):**
- Bias: AI replicates/amplifies existing societal biases
- Black-box models: High accuracy but no explanations (GDPR compliance risk)
- Regulatory gap: No unified framework (EU has AI Act, US has voluntary guidelines)

**Implication:** [NEEDS USER INPUT - Phase 2]
**Position:** [TO BE REFINED - Phase 2]
**Action:** [NEEDS USER INPUT - Phase 2]
**Benefit:** [TO BE REFINED - Phase 2]
```

**Checkpoint:**
```
Agent: "Phase 1 complete! I've synthesized 15 papers into 6 themes (42 arguments).

         Key findings:
         - AI bias is well-documented (hiring, facial recognition, healthcare)
         - Explainability vs. performance is a core tension
         - Contradictions exist (can AI reduce bias? are black-box models acceptable?)

         CHECKPOINT: Review STAGING.md. Ready for interrogation (Phase 2)? [Yes/Edit/Abort]"

User: "Yes"
```

---

### Step 4: Write Manuscript Slide Deck Phase 2 (Interrogation)

**Enhance Writing mode:**
```
Agent: "Your synthesis identifies 6 themes. Which ONE should anchor this talk?

         Option A: AI Bias (most papers, emotionally resonant)
         Option B: Explainability (GDPR angle, policy-relevant)
         Option C: Accountability (emerging, less explored)

         Pick one. A multi-theme talk dilutes the message."

User: "Option A - Bias. My audience is policymakers."

Agent: "Good. Now, your Complication is 'AI replicates biases.' That's a known problem.
         What's the SPECIFIC implication for your audience (policymakers)?

         A) Discriminatory AI violates existing anti-discrimination laws (legal risk)
         B) Public trust in govt AI erodes (political risk)
         C) Marginalized groups further disadvantaged (equity risk)

         Which resonates most with your audience?"

User: "Option A - Legal risk. Policymakers care about liability."

Agent: "Perfect. Your Implication: 'If we don't regulate AI bias, governments face
         legal challenges under existing anti-discrimination law.'

         Now, your Action. 'Regulate AI' is vague. What's the FIRST STEP?

         A) Mandate bias audits for govt AI systems (operational)
         B) Draft AI anti-discrimination law (legislative)
         C) Fund research on bias detection tools (R&D)

         Which is achievable in the next 12 months?"

User: "Option A - Bias audits. That's implementable now."

Agent: "Excellent. Updating STAGING.md with your strategic choices..."
```

**Updated STAGING.md (after Phase 2):**
```yaml
## SCIPAB Seed (Finalized)

**Situation:**
AI systems deployed in high-stakes govt domains (hiring, benefits allocation, criminal justice).

**Complication:**
AI replicates biases from training data (documented in hiring [Dastin], facial recognition [Buolamwini & Gebru], healthcare [Obermeyer]).

**Implication:**
If left unregulated, governments face legal liability under existing anti-discrimination laws (Title VII, Equal Protection Clause).

**Position:**
Mandate bias audits for all govt AI systems (inspired by EU AI Act, adapted to US context).

**Action:**
1. Draft executive order requiring bias audits (6-month timeline)
2. Pilot in 3 agencies (EEOC, HHS, DOJ)
3. Release audit framework by Q4 2026

**Benefit:**
- Legal protection (reduce discrimination lawsuits)
- Public trust (transparent AI governance)
- Equity (ensure AI doesn't harm marginalized groups)
```

---

### Step 5: Write Manuscript Slide Deck Phase 3-4 (Drafting & Export)

**Phase 3:**
```
Agent: "Template selection: Academic (for conference).

         Deck structure (18 slides):
         - Title (1 slide)
         - Situation (2 slides: Current AI deployment landscape)
         - Complication (2 slides: Bias evidence from [Dastin], [Buolamwini & Gebru], [Obermeyer])
         - Implication (1 slide: Legal liability, bold red theme)
         - Position (5 slides: Bias audit framework, EU AI Act comparison, pilot design)
         - Action (2 slides: Executive order timeline, 3-agency pilot)
         - Benefit (1 slide: Legal protection + public trust)
         - Caveats (1 slide: Limitations of audits, ongoing research needed)
         - References (1 slide: 15 papers cited)
         - Backup (2 slides: Detailed bias metrics, audit checklist)

         CHECKPOINT: Review presentation.md. Export to PDF? [Yes/Edit/Cancel]"

User: "Yes"
```

**Phase 4:**
```bash
# Agent runs Marp CLI
npx @marp-team/marp-cli@latest presentation.md -o presentation.pdf

# Output
✓ presentation.pdf (18 slides, 3.2 MB)
```

**Final report:**
```
Agent: "Export complete! Generated files in 01_Projects/Research/AI-Ethics/:

         ✓ synthesis-matrix_project.md (Review Literature output - 6 themes, 42 arguments)
         ✓ STAGING.md (Write Manuscript Slide Deck synthesis - 1,247 lines)
         ✓ presentation.md (Marp source - 487 lines, 18 slides)
         ✓ presentation.pdf (Final deck - 3.2 MB)

         Your AI ethics talk is ready! 15 papers synthesized, SCIPAB-framed, citation-rich.

         Next steps:
         - Review presentation.pdf
         - Practice talk (aim for 20 min, 1 min/slide pace)
         - Prepare for Q&A (use synthesis-matrix_project.md for deep-dive answers)"
```

---

## Integration Patterns

### Pattern 1: Review Literature Full → Write Manuscript Slide Deck

**Use case:** Comprehensive research presentation (thesis, dissertation, major conference)

**Timeline:**
- Review Literature Full Mode: 60-90 minutes (8 phases)
- Write Manuscript Slide Deck: 15-20 minutes (Phases 1-4)
- Total: ~2 hours

**Quality:** Highest (deep synthesis, rigorous citations, thematic coherence)

---

### Pattern 2: Review Literature Quick → Write Manuscript Slide Deck

**Use case:** Rapid research briefing (<15 papers, tight deadline)

**Timeline:**
- Review Literature Quick Mode: 15-25 minutes (3 phases)
- Write Manuscript Slide Deck: 15-20 minutes
- Total: ~40 minutes

**Quality:** High (structured themes, good citations, adequate depth)

---

### Pattern 3: Write Manuscript Slide Deck Direct (No Review Literature)

**Use case:** Markdown-heavy folder, <5 PDFs, or AI summaries dominant

**Timeline:**
- Write Manuscript Slide Deck: 20-30 minutes (Phases 0-4)
- Total: ~30 minutes

**Quality:** Medium (basic PDF extraction, good for non-academic contexts)

---

## Bridging Outputs

### Review Literature → Write Manuscript Slide Deck Data Flow

**Review Literature provides:**
- `synthesis-matrix_project.md` → Write Manuscript Slide Deck's "Key Arguments"
- Thematic clusters → SCIPAB "Situation" and "Complication"
- Contradictions → STAGING.md "Contradictions Found"
- Bibliography → Slide deck "References" slide

**Write Manuscript Slide Deck adds:**
- SCIPAB framing (Implication, Action, Benefit)
- Enhance Writing interrogation (strategic clarity)
- Visual design (Marp templates, SCIPAB color coding)
- Export automation (PDF/PPTX/HTML)

---

### File Organization

**Recommended folder structure after Review Literature + Write Manuscript Slide Deck:**
```
research-folder/
├── papers/                   # Original PDFs
│   ├── paper1.pdf
│   └── ...
├── synthesis-matrix_project.md       # Review Literature output (themes, arguments)
├── thematic-clusters_project.md      # Review Literature output (narrative structure)
├── screening-results_project.md      # Review Literature output (inclusion/exclusion)
├── STAGING.md                # Write Manuscript Slide Deck checkpoint (SCIPAB seed)
├── presentation.md           # Write Manuscript Slide Deck output (Marp source)
├── presentation.pdf          # Final deck (exported)
└── notes/                    # Optional: Speaker notes, rehearsal logs
```

---

## Troubleshooting Integration

### Issue 1: Review Literature Outputs Not Detected

**Symptom:** Write Manuscript Slide Deck runs Phase 1 without ingesting `synthesis-matrix_project.md`.

**Cause:** File naming mismatch or missing file.

**Solution:**
```
# Verify Review Literature output exists
ls research-folder/synthesis-matrix_project.md

# If renamed, update Write Manuscript Slide Deck's expected filename:
# (Tell Agent: "The Review Literature output is named lit-review-summary.md instead")
```

---

### Issue 2: STAGING.md Has Weak Arguments

**Symptom:** STAGING.md "Key Arguments" are generic or poorly cited.

**Cause:** Review Literature synthesis was shallow (Quick Mode on complex corpus).

**Solution:**
- Re-run Review Literature in Full Mode (more rigorous)
- Or manually edit `synthesis-matrix_project.md` to strengthen arguments
- Then re-invoke Write Manuscript Slide Deck (it will re-ingest)

---

### Issue 3: SCIPAB Framing Doesn't Fit Research

**Symptom:** Phase 2 interrogation feels forced (research is exploratory, not persuasive).

**Cause:** SCIPAB is designed for persuasive presentations, not descriptive research.

**Solution:**
- Use Write Manuscript Slide Deck's Academic template (less SCIPAB emphasis)
- Or skip SCIPAB framing: Tell the agent "Use traditional structure (Intro, Methods, Results, Discussion)"
- Write Manuscript Slide Deck can adapt (it's not rigidly SCIPAB-only)

---

## Best Practices

### 1. Run Review Literature First If Unsure

**Rule of thumb:** If you're debating "Should I use Review Literature?", the answer is probably yes.

**Reason:** Review Literature's output is reusable (you can use `synthesis-matrix_project.md` for papers, reports, etc.). Write Manuscript Slide Deck's output is presentation-specific.

---

### 2. Don't Re-Run Review Literature Unnecessarily

**Scenario:** You've run Review Literature, generated `synthesis-matrix_project.md`, and now want to create a different presentation (e.g., executive vs. academic).

**Workflow:**
1. Keep `synthesis-matrix_project.md` (don't re-run Review Literature)
2. Invoke Write Manuscript Slide Deck with different template:
   - First deck: Academic template
   - Second deck: Executive template (same sources, different framing)

**Result:** Two decks from one Review Literature run (efficient).

---

### 3. Edit synthesis-matrix_project.md Manually

**Scenario:** Review Literature's synthesis is 90% correct, but one theme is misclassified.

**Workflow:**
1. Open `synthesis-matrix_project.md` in your Markdown editor
2. Edit the "Theme" section (move papers, rephrase argument)
3. Tell Agent: "Re-run Write Manuscript Slide Deck using the updated synthesis-matrix_project.md"

**Result:** Write Manuscript Slide Deck re-ingests, STAGING.md updated.

---

## Related Documentation

- **[[../SKILL.md]]** - Write Manuscript Slide Deck technical implementation
- **[[../README.md]]** - Write Manuscript Slide Deck user guide
- **[[../../review-literature/SKILL.md]]** - Review Literature skill documentation
- **[[../../research/ORCHESTRATOR-DECISION-TREE.md]]** - Research orchestrator selection guide
- **[[scipab-framework.md]]** - SCIPAB strategic storytelling



