---
tags: [research, decision-tree, orchestrators]
created: 2026-01-12
status: active
---

# Research Orchestrator Decision Tree

**Purpose:** Help users choose the right research synthesis workflow based on input type and goals.

---

## Quick Decision

**Answer these two questions:**

### 1. What's your input format?

- **PDFs** (research papers, academic articles) → **Review Literature**
- **Markdown files** (AI-generated research from other tools) → **Deep Research Synthesis**
- **Both** → **Review Literature**, then bridge to **Deep Research Synthesis**

### 2. What's your output goal?

- **Literature review section** (for thesis, paper, proposal) → **Review Literature**
- **Academic manuscript** (standalone paper) → **Deep Research Synthesis**
- **Both** → Use **Review Literature** (more comprehensive)

---

## Detailed Decision Matrix

| Your Situation | Recommended Orchestrator | Reasoning |
|----------------|-------------------------|-----------|
| **Starting from scratch with 20-100 PDFs** | Review Literature | Handles corpus screening, extraction, and synthesis end-to-end |
| **Already have AI research summaries (from other tools)** | Deep Research Synthesis | Optimized for reconciling multiple AI perspectives |
| **Need quick literature review (5-20 papers)** | Review Literature (Quick Mode) | 3-phase simplified workflow |
| **Need publication-ready manuscript with citations** | Deep Research Synthesis | Includes 2 quality gates (citation validation, consistency) |
| **First time doing literature review** | Review Literature | Includes Phase 0 interactive guidance |
| **Expert researcher, need automation only** | Deep Research Synthesis | Skips teaching, focuses on synthesis |
| **Mixed inputs (PDFs + AI summaries)** | Review Literature → Deep Research Synthesis | Use Review Literature for PDFs, export to DRS for final synthesis |

---

## Workflow Comparison

### Review Literature

**Location:** `.agent/skills/review-literature/SKILL.md`

**Input:** PDF corpus + screening criteria
**Output:** Literature review sections (Introduction, Background, Methods, Findings, Gaps, Contribution)
**Phases:** 8 (0-7, with Phase 0 optional)
**Complexity:** High (but can use Quick Mode for 3-phase simplified version)
**Best for:** Academic researchers, thesis/dissertation work, comprehensive reviews

**Key Features:**
- ✅ Phase 0: Interactive criteria generation (optional)
- ✅ Corpus screening with inclusion/exclusion criteria
- ✅ Automatic extraction and thematic synthesis
- ✅ Human-led drafting with Enhance Writing provocation
- ✅ Contribution framing, citation validation, consistency checking
- ✅ Supports mixed formats (PDFs + Markdown)

**Workflow Phases:**
```
Phase 0: Interactive Criteria Generation (optional)
Phase 1: Corpus Screening → approved corpus
Phase 2: Extraction & Synthesis → synthesis notes
Phase 3: Argument Structuring → outline
Phase 4: Drafting (Human + Enhance Writing) → draft sections
Phase 6: Contribution Framing → positioned contribution
Phase 5: Citation Validation → validated citations
Phase 7: Consistency Validation → final review
```

**Checkpoints:** 4 (Phases 1, 3, 6, 7)
**Duration:** 30-90 minutes (depends on corpus size)

---

### Research Writer (Deep Research Synthesis)

**Location:** `.agent/skills/write-manuscript/SKILL.md`

**Input:** Multiple Markdown files (AI-generated research documents)
**Output:** Academic manuscript with quality validation
**Phases:** 6 (with 2 quality gates)
**Complexity:** High (but more streamlined than Review Literature)
**Best for:** Synthesizing multiple AI research outputs, manuscript generation

**Key Features:**
- ✅ Handles multiple AI-generated documents
- ✅ Theme consolidation across sources
- ✅ Citation tracking and preservation
- ✅ 2 mandatory quality gates (Phase 4: citations, Phase 6: consistency)
- ✅ State persistence and resumability
- ✅ Explicit dependency validation

**Workflow Phases:**
```
Phase 1: Input Processing → synthesis-matrix_project.md, source-mapping_project.md
Phase 2: Argument Structuring → manuscript-outline_project.md
Phase 3: Literature Drafting → manuscript-draft_project.md
Phase 4: Quality Validation (Gate 1) → quality-validation-report_project.md
Phase 5: Contribution Framing → contributions-section_project.md
Phase 6: Consistency Validation (Gate 2) → manuscript-final_project.md
```

**Checkpoints:** 4 (Phases 1, 2, 4, 6)
**Duration:** 20-45 minutes (depends on document count and size)

---

## When to Use Both (Bridged Workflow)

### Scenario: PDFs + AI Summaries

**Step 1:** Run **Review Literature** on PDF corpus
- Produces: `synthesis-notes_project.md`, `argument-outline_project.md`, drafted sections

**Step 2:** Export Review Literature outputs as Markdown files

**Step 3:** Run **Research Writer** on combined corpus:
- Input: Review Literature synthesis notes + AI-generated summaries + manually written sections
- Output: Unified manuscript

**Bridging Guide:**
1. Complete Review Literature through Phase 7
2. Export key outputs:
   - `outputs/synthesis-notes_project.md` (from Phase 2)
   - `outputs/manuscript-draft_project.md` (from Phase 4)
3. Place these files alongside AI-generated research docs
4. Run Research Writer orchestrator
5. DRS Phase 1 will consolidate all sources into unified synthesis-matrix

**When to use this approach:**
- Large PDF corpus (50+ papers) + multiple AI research assistants used
- Need comprehensive literature review + original contribution
- Building on existing literature review for new manuscript

---

## Phase Alignment Between Orchestrators

Both orchestrators share similar phases in the middle:

| Review Literature | Research Writer | Purpose |
|------------------------------|------------------------|---------|
| Phase 2: Extraction & Synthesis | Phase 1: Input Processing | Extract themes, claims, evidence |
| Phase 3: Argument Structuring | Phase 2: Argument Structuring | Build outline (Known → Gap → Contribution) |
| Phase 4: Drafting | Phase 3: Literature Drafting | Generate academic prose |
| Phase 5: Citation Validation | Phase 4: Quality Validation | Verify citations and evidence grounding |
| Phase 6: Contribution Framing | Phase 5: Contribution Framing | Position your work |
| Phase 7: Consistency Validation | Phase 6: Consistency Validation | Final coherence check |

**Key Difference:** Review Literature Phases 0-1 handle corpus screening (PDFs), DRS assumes pre-processed inputs (Markdown)

---

## Choosing Based on Experience Level

### First-Time Literature Review
→ **Review Literature** with Phase 0 (Interactive Criteria Generation)
- Provides guided setup
- Teaches best practices
- Comprehensive workflow with teaching moments

### Experienced Researcher
→ **Research Writer** (if inputs are ready) OR **Review Literature (Quick Mode)**
- Skip teaching phases
- Automation-focused
- Faster turnaround

---

## Invocation Examples

### Review Literature

**Full Mode (8 phases):**
```markdown
I need a comprehensive literature review for my thesis on AI tutoring systems.

I have 45 PDFs in the corpus/candidates/ folder.
I want to use the full Review Literature workflow with Phase 0 guidance.

Topic: AI-powered tutoring systems in K-12 mathematics education
```

**Quick Mode (3 phases):**
```markdown
I need a quick literature review for a grant proposal.

I have 12 PDFs already screened and placed in corpus/approved/.
Skip Phase 0 and 1 (corpus screening).

Just run:
- Phase 2: Extraction & Synthesis
- Phase 3: Argument Structuring
- Phase 4: Drafting (with Enhance Writing)
```

---

### Research Writer (Deep Research Synthesis)

**Standard Invocation:**
```markdown
I have 3 AI-generated research documents on AIaaS for national SMEs:
- research/AIaaS-Deep-Dive.md (ChatGPT output)
- research/Comprehensive-Review.md
- research/democratizing-intelligence.md

Synthesize these into a single academic manuscript using Research Writer orchestrator.
```

**With State Resume:**
```markdown
Continue my Research Writer workflow from yesterday.
The execution log shows I completed Phases 1-3, and Phase 4 (Quality Validation) is pending.

Resume from Phase 4.
```

---

## Quick Reference Card

| Question | Answer | Tool |
|----------|--------|------|
| Do I have PDFs to screen? | Yes | Review Literature |
| Do I have AI summaries? | Yes | Research Writer |
| Do I have both? | Yes | Review Literature → Bridge → DRS |
| Is this my first literature review? | Yes | Review Literature with Phase 0 |
| Do I need a quick review (<15 papers)? | Yes | Review Literature Quick Mode |
| Do I need publication-ready manuscript? | Yes | Research Writer |
| Do I need to resume interrupted work? | Yes | Either (both support resumability) |

---

## Next Steps After Choosing

### If you chose Review Literature:
1. Read `.agent/skills/review-literature/SKILL.md`
2. Prepare your corpus (place PDFs in `corpus/candidates/`)
3. Optional: Run Phase 0 for interactive criteria generation
4. Invoke the orchestrator with your research question

### If you chose Research Writer:
1. Read `.agent/skills/write-manuscript/SKILL.md`
2. Organize your AI-generated research docs (Markdown format)
3. Place files in appropriate directory (e.g., `research/`, `deep-research/`)
4. Invoke the orchestrator with document paths

### If you need both:
1. Start with Review Literature (Phases 1-7)
2. Export outputs (synthesis notes, draft sections)
3. Combine with AI-generated summaries
4. Run Research Writer for final manuscript

---

**Last Updated:** 2026-01-14
**Related:**
- [[../../review-literature/SKILL]]
- [[../../write-manuscript/SKILL]]
- [[../../enhance-writing/SKILL]]





