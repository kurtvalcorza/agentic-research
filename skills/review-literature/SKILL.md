---
name: review-literature
description: "Automate literature review from PDF corpus screening through manuscript structuring with optional quick mode for small corpora. Use when running a full literature review pipeline, screening a PDF corpus, or structuring a review manuscript from research papers."
---







# Skill: Review Literature

## Dependencies

### Required Skills
- **[[../enhance-writing/SKILL|Enhance Writing]]** - Required for Phases 4-7 (human-led synthesis and writing)
- **[[../enhance-writing/references/academic-writing|Academic Writing Protocol]]** - Specific protocol for literature review writing

### Required Tools
- `file-read` - Read PDF files and Markdown corpus candidates
- `file-write` - Generate phase outputs (screening reports, synthesis notes, etc.)
- `file-search` - Find corpus files in candidate/approved directories
- `content-search` - Search within documents for themes and citations
- `command-exec` - File operations (move approved PDFs, create directories)
- `sub-agent` - Spawn phase-specific agents (screener, extractor, structurer, etc.)

### Phase Dependencies
**See:** [[references/review-literature-dependency-matrix|Review Literature Dependency Matrix]] for complete phase dependency graph

**Quick Reference:**
- **Phase 0** (optional): No dependencies
- **Phase 1**: Requires screening criteria + corpus candidates
- **Phase 2**: Requires Phase 1 completion + approved corpus
- **Phase 3**: Requires Phase 2 completion + synthesis notes
- **Phase 4**: Requires Phase 3 completion + handoff to Enhance Writing
- **Phase 5**: Requires Phase 4 completion + draft manuscript
- **Phase 6**: Requires Phase 5 completion + validated draft
- **Phase 7**: Requires Phase 6 completion + contribution framing

### Input Files
**Before Phase 1:**
- `settings/research-question.md` (required)
- `settings/screening-criteria.md` (required, or generate via Phase 0)
- `corpus/candidates/*.pdf` or `*.md` (required, 20-100 files recommended)

### Output Directories
**Auto-created if missing:**
- `outputs/` - Phase output files (reports, notes, outlines)
- `corpus/approved/` - Approved papers after Phase 1 screening

### Related Workflows
- **[[../orchestrate-research/SKILL|Orchestrate Research]]** - Run the multi-phase pipeline with validation gates.
- **[[../review-literature/references/ORCHESTRATOR-DECISION-TREE|Orchestrator Decision Tree]]** - Choose between review-literature and adjacent workflows.

**Critical Note:** Phases 1-3 are automated. Phases 4-7 require human intellectual engagement via Enhance Writing.

***

## Purpose
Automate literature discovery, screening, and extraction (Phases 1-3), then hand off to human-led synthesis using Enhance Writing methodology (Phases 4-7) for publication-ready academic reviews. Optional Phase 0 provides interactive guidance for generating screening criteria.

## Domain
research

## Use Cases
- Use case 1: Academic literature reviews for research papers, theses, or dissertations
- Use case 2: Systematic reviews for Example Research Institute project proposals (Project Atlas, Project Beacon, Project Skye)
- Use case 3: Technical reports requiring comprehensive literature synthesis
- Use case 4: Grant proposals needing evidence-based background sections

## Inputs Required

### Required
- **Research Question:** One-sentence research question defining the review scope (see `assets/research-question-template.md`)
- **Screening Criteria:** Inclusion/exclusion criteria for corpus selection (see `assets/screening-criteria-template.md`)
- **Corpus Files:** Research papers in PDF or Markdown format placed in `corpus/candidates/` directory
  - **PDFs:** Academic papers, published articles
  - **Markdown:** Markdown notes, web clippings, curated summaries with frontmatter metadata

### Optional
- **Execution Context:** JSON configuration for advanced orchestrator settings (see `assets/execution-context-template.json`)
- **Project Name:** Specify project-specific workspace (default: `general`)

## Expected Outputs

### Phase 1-3 Outputs (Automated)
- **Phase 1 Output:** `screening-report_project.md` - Approved/rejected papers with justifications
- **Phase 2 Output:** `synthesis-notes_project.md` - Extracted themes, claims, gaps, contradictions
- **Phase 3 Output:** `argument-outline_project.md` - Structured outline (Known → Gap → Contribution)

### Phase 4-7 Outputs (Human-Led/Hybrid)
- **Phase 4 Output:** `handoff-document_project.md` - Transition protocol to Enhance Writing
- **Phase 5 Output:** `citation-validation_project.md` - Citation accuracy verification
- **Phase 6 Output:** `contribution-framing_project.md` - Positioning options for your contribution
- **Phase 7 Output:** `consistency-report_project.md` - Final quality assurance check

## Workflow

### RLM Execution Model (Phases 1-2)
Use a Python REPL as the paper store. Do not paste full PDF text into the prompt.
- Initialize `corpus` as a list of dicts: `{id, path, title, abstract, text}`.
- Use programmatic peeking (title/abstract only) for Phase 1 decisions.
- Use recursive sub-calls for Phase 2 extraction; store results in buffers.
- Only bring summaries/buffers into the main context at checkpoints.
- Helper template: `scripts/rlm_corpus_loader.py`.

### OPTIONAL PHASE 0: Interactive Criteria Generation

**Phase 0: Criteria Generator (Agent: Criteria Generator) - TRULY OPTIONAL**
   - Interactive Q&A dialogue (8 questions)
   - Guides user through defining screening criteria
   - Generates draft criteria for approval
   - **Use if:** Unfamiliar with literature review methodology or need guidance
   - **Skip if:** Already have well-defined screening criteria
   - **Default behavior:** If Phase 0 skipped, uses standard academic screening criteria:
     ```markdown
     ## Default Screening Criteria
     ### Inclusion
     - Peer-reviewed publications
     - Published within last 10 years (adjust based on field)
     - Directly addresses research question
     - Empirical or theoretical contribution

     ### Exclusion
     - Opinion pieces without data
     - Duplicate publications
     - Non-English (unless specified otherwise)
     - Outside domain scope
     ```
   - **Outputs:** `settings/screening-criteria.md` and `settings/research-question.md`
   - **Pro Tip:** Most users can skip Phase 0 and provide criteria directly. Only use Phase 0 if you're unsure how to structure criteria.

### AUTOMATED PHASES (1-3): Discovery & Extraction

**1. Phase 1: Corpus Screening (Agent: Screener)**
   - RLM loop over `corpus` abstracts only (no full text in prompt)
   - Evaluates against screening criteria via sub-calls
   - Assigns relevance scores (0-10)
   - Produces screening report with INCLUDE/EXCLUDE/UNCERTAIN decisions
   - **CHECKPOINT 1**: User approves final corpus

**2. Phase 2: Extraction & Synthesis (Agent: Extractor)**
   - RLM loop over `screened_corpus` with per-paper sub-calls
   - Buffers per-paper extractions (`extraction_buffer`)
   - Aggregates themes from buffer (chunked if needed)
   - Identifies cross-paper themes
   - Maps claims and evidence
   - Surfaces contradictions and gaps
   - Produces synthesis notes organized by theme

**3. Phase 3: Argument Structuring (Agent: Structurer)**
   - Builds logical outline: Known → Unknown → Contribution
   - Maps consensus areas ("Known")
   - Identifies research gaps ("Unknown")
   - Proposes contribution framing ("Your Work")
   - **CHECKPOINT 2**: User approves outline structure

### HANDOFF POINT: Phase 3 → Phase 4

**Critical Transition:** Automation hands off to human-led synthesis.

You receive:
- Approved corpus (Phase 1)
- Synthesis notes (Phase 2) - use as **reading lenses**, not summaries
- Argument outline (Phase 3) - use as **scaffold**, not script

**Before writing, engage with:**
- [[../enhance-writing/references/academic-writing|Enhance Writing Academic Writing Protocol]]
- [[references/handoff-guide|Phase 3→4 Handoff Guide]]

### HUMAN-LED PHASES (4-7): Synthesis & Writing

**4. Phase 4: Drafting (User + Provocation Mode)**
   - User writes literature review sections
   - Agent provides provocations via a critical review perspective, not autocomplete
   - Challenge AI's outline - don't accept uncritically
   - Read papers yourself, don't rely solely on AI synthesis
   - Expected result: Draft sections with YOUR intellectual ownership

**5. Phase 5: Citation Validation (Agent: Validator)**
   - Automated verification of all citations
   - Checks claims match cited sources
   - Flags fabricated or misattributed claims
   - Identifies missing citations
   - Expected result: Citation accuracy report with fixes needed

**6. Phase 6: Contribution Framing (Agent: Framer + User)**
   - AI generates framing options (supportive, challenging, extending)
   - Analyzes positioning trade-offs
   - **CHECKPOINT 3**: User chooses framing approach
   - Expected result: Clear contribution positioning

**7. Phase 7: Consistency Validation (Agent: Consistency)**
   - Cross-checks introduction ↔ conclusion
   - Validates claims ↔ evidence alignment
   - Checks argument logical flow
   - **CHECKPOINT 4**: Final review before completion
   - Expected result: Consistency score (target: ≥75%)

## Usage & Strategic Context

This skill is primarily used for academic reviews, grant proposals, and systematic reviews for Example Research Institute projects.

For detailed usage scenarios, edge case handling, and the "Why Hybrid?" philosophy of literature review, see:
- **[[references/review_details|Detailed Examples, Limits & Philosophy]]**
- **[[references/workflow-phases|Phase-by-Phase Deep Dive]]**
- **[[references/handoff-guide|Phase 3→4 Transition Protocol]]**

---




## Internal Metadata
- **color**: green
- **tags**: ["#skill/research", "#status/active", "#project/literature-review", "review-literature"]
- **domain**: research
- **status**: active
- **version**: 1.2
- **created**: 2026-01-11
- **updated**: 2026-01-18
- **capabilities**: [file-read, file-write, file-search, content-search, command-exec, sub-agent]