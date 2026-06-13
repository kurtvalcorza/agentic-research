---
session_id: write-manuscript-slide-deck-[YYYY-MM-DD-HH-MM]
target_folder: [path/to/research/folder]
source_count: [number]
lra_integration: [true|false]
last_updated: [ISO timestamp]
status: [synthesis-complete|interrogation-complete|draft-complete]
target_audience: [academic|executive|technical]
---

# Write Manuscript Slide Deck Staging Document

**Purpose:** This file serves as a checkpoint for Write Manuscript Slide Deck's synthesis process. It captures key arguments, contradictions, gaps, and the SCIPAB framework seed before generating slides.

**Status legend:**
- `synthesis-complete` - Phase 1 done, ready for Phase 2 (Interrogation)
- `interrogation-complete` - Phase 2 done, ready for Phase 3 (Drafting)
- `draft-complete` - Phase 3 done, ready for Phase 4 (Export)

---

## Source Inventory

**Total sources:** [number]

**Breakdown:**
- PDFs: [number] files
- Markdown: [number] files
- Text files: [number] files
- AI summaries: [number] files
- Review Literature outputs: [if applicable]

**Files:**
1. [filename1.pdf] - [brief description, e.g., "Research paper on AI bias"]
2. [filename2.md] - [brief description, e.g., "Meeting notes from stakeholder interview"]
3. [filename3.txt] - [brief description]
4. [... continue for all sources ...]

**Notes:**
- [Any files skipped? Why? e.g., "paper5.pdf - extraction failed (encrypted)"]
- [Any files particularly valuable? e.g., "synthesis-matrix.md (Review Literature output) - primary source"]

---

## Key Arguments (Grounded Truths)

**Instructions:** List the core arguments extracted from sources. Each argument should be:
1. Specific (not vague)
2. Grounded in sources (cite files)
3. Relevant to the presentation topic

**Format:** `[Argument statement] → Sources: [file1, file2, ...]`

### Theme 1: [Theme Name]

1. [Argument 1] → Sources: [file1.pdf, file2.md]
2. [Argument 2] → Sources: [file3.md]
3. [Argument 3] → Sources: [file1.pdf, file4.txt]

**Evidence strength:** [High|Medium|Low]
**Relevance to presentation:** [Core|Supporting|Background]

---

### Theme 2: [Theme Name]

1. [Argument 1] → Sources: [...]
2. [Argument 2] → Sources: [...]
3. [... continue ...]

**Evidence strength:** [High|Medium|Low]
**Relevance to presentation:** [Core|Supporting|Background]

---

### Theme 3: [Theme Name]

[Continue pattern...]

---

**Summary of arguments:**
- Total arguments extracted: [number]
- Themes identified: [number]
- Most strongly supported argument: [brief statement]
- Weakest argument (needs more evidence): [brief statement]

---

## Contradictions Found

**Instructions:** Document any conflicting claims across sources. These are valuable for:
1. Showing intellectual honesty ("Caveats" slide)
2. Identifying areas needing clarification in Phase 2
3. Framing the "Complication" in SCIPAB

**Format:** `[Source A] claims [X], but [Source B] claims [Y]. Possible reasons: [...]`

### Contradiction 1: [Topic]

**Claim A:** [file1.pdf] states [specific claim]
**Claim B:** [file2.md] states [contradictory claim]

**Possible explanations:**
- Different methodologies (A used quantitative, B used qualitative)
- Different timeframes (A is 2020 data, B is 2024 data)
- Different contexts (A studied US, B studied EU)

**Resolution for deck:**
- [ ] Acknowledge both perspectives (show nuance)
- [ ] Choose A as authoritative (justify why)
- [ ] Choose B as authoritative (justify why)
- [ ] Frame contradiction as unresolved (call for more research)

---

### Contradiction 2: [Topic]

[Continue pattern...]

---

**Summary of contradictions:**
- Total contradictions found: [number]
- Most significant contradiction: [brief description]
- Strategy: [How will we handle contradictions in the deck?]

---

## Gaps to Fill (Questions for User)

**Instructions:** These are questions that MUST be answered before drafting slides. Phase 2 (Interrogation) will address these.

### Presentation Context

- [ ] **Target audience:** [Academic researchers? Policymakers? Technical developers? Business executives?]
  - **Why it matters:** Determines template selection, jargon level, evidence depth

- [ ] **Venue/event:** [Conference name? Internal meeting? Public webinar?]
  - **Why it matters:** Affects tone (formal vs. casual), slide count (20 min vs. 60 min)

- [ ] **Presentation goal:** [Persuade? Inform? Propose action? Educate?]
  - **Why it matters:** Determines SCIPAB emphasis (persuasive) vs. traditional structure (informative)

---

### SCIPAB Framing (for Phase 2)

- [ ] **Implication (stakes):** What SPECIFICALLY happens if we don't act?
  - **Current placeholder:** [generic statement, e.g., "We'll fall behind"]
  - **Needs:** Concrete, audience-specific consequence (e.g., "$6M spent on duplicated data work over 5 years")

- [ ] **Action (first step):** What's the concrete, achievable action?
  - **Current placeholder:** [vague goal, e.g., "Adopt the solution"]
  - **Needs:** Specific action with owner, timeline, budget (e.g., "Launch a 6-month pilot with 3 member universities by Q2 2026")

- [ ] **Which theme should lead?** [List themes from "Key Arguments" section]
  - **Option A:** [Theme 1]
  - **Option B:** [Theme 2]
  - **Option C:** [Theme 3]
  - **User must choose:** [Which narrative anchors the deck?]

---

### Content Gaps (Missing Information)

- [ ] [Question 1, e.g., "What's the budget for the proposed solution?"]
  - **Impact if unanswered:** [Can't populate "Action" slide with budget details]
  - **Source to find answer:** [Suggested file or person to ask]

- [ ] [Question 2, e.g., "Who are the key stakeholders?"]
  - **Impact if unanswered:** [Can't tailor "Benefit" slide to audience concerns]

- [ ] [... add more as needed ...]

---

## SCIPAB Seed (Initial Draft)

**Instructions:** This is the rough framework for the presentation. Phase 1 populates what's inferrable from sources. Phase 2 (Interrogation) refines with user input.

### Situation (Where are we?)

**Current state (from sources):**
[1-2 paragraphs describing the baseline reality. Neutral, factual, uncontroversial.]

**Example:**
"Researchers across the consortium currently store and manage their datasets independently (genomics, climate, survey data). The standard practice is for each university to maintain its own data store, re-collecting or re-downloading datasets that peer institutions already hold. As of 2025, 8 universities run separate silos, with a total annual storage and duplication cost of $1.2M."

**Sources:** [list files that support this situation description]

**Confidence:** [High|Medium|Low]

---

### Complication (What's broken?)

**Problem/tension (from sources):**
[1-2 paragraphs identifying what's inefficient, risky, or unsustainable.]

**Example:**
"This fragmented approach creates four critical issues:
1. Budget inefficiency: $1.2M/year with no economies of scale
2. Wasted effort: Teams re-collect and re-store datasets peers already hold (zero reuse)
3. No shared infrastructure: Each silo uses its own formats and access rules (no interoperability)
4. Reproducibility risk: Datasets are unversioned and hard to cite, so results are hard to reproduce"

**Sources:** [list files]

**Visual cues for slide:** [Red/dark theme, words like "fragmented," "bleeding," "vulnerable"]

**Confidence:** [High|Medium|Low]

---

### Implication (What happens if we don't act?)

**Stakes (NEEDS USER INPUT in Phase 2):**

**Current placeholder (from sources):**
[Generic or partially-formed consequence]

**Example of weak placeholder:**
"If we don't act, the consortium will fall behind in research."

**What Phase 2 will clarify:**
- **Specific consequence:** [e.g., "$6M spent on duplicated data work over 5 years, persistent reproducibility gaps, no shared datasets"]
- **Audience relevance:** [Why does THIS audience care? Budget? Research velocity? Reproducibility?]
- **Timeframe:** [When does this consequence materialize? 5 years? 10 years?]

**Action item for Phase 2:** User must answer: "What SPECIFICALLY happens if we don't act?"

---

### Position (What should we believe?)

**Core thesis (from sources):**
[1-sentence statement of the solution/approach]

**Example:**
"A federated open-data platform provides shared, reusable research data infrastructure for the university consortium."

**Supporting claims (from sources):**
1. [Claim 1, e.g., "67% cost reduction vs. duplicated storage and re-collection"] → Sources: [file1, file2]
2. [Claim 2, e.g., "Reuse and collaboration (8 universities sharing one catalog)"] → Sources: [file3]
3. [Claim 3, e.g., "Reproducibility (datasets versioned and citable)"] → Sources: [file4]

**Evidence quality:**
- Claim 1: [High|Medium|Low] confidence
- Claim 2: [High|Medium|Low] confidence
- Claim 3: [High|Medium|Low] confidence

**Gaps:**
- [Any claim lacking strong evidence? Note here.]

---

### Action (What's the first step?)

**Concrete action (NEEDS USER INPUT in Phase 2):**

**Current placeholder (from sources):**
[Vague goal or outcome]

**Example of weak placeholder:**
"We should adopt the open-data platform."

**What Phase 2 will clarify:**
- **Specific action:** [e.g., "Launch a 6-month pilot with 3 member universities"]
- **Owner:** [Who executes? e.g., "Platform engineering lead"]
- **Timeline:** [When? e.g., "Q2 2026 (April-Sept)"]
- **Budget:** [Cost? e.g., "$0.5M"]
- **Success criteria:** [How to measure? e.g., "50% cost reduction, 3 universities onboarded"]

**Action item for Phase 2:** User must answer: "What's the immediate, achievable action?"

---

### Benefit (What do we gain?)

**Positive outcome (from sources):**
[1-2 paragraphs describing the future state if the Position is adopted and Action is taken.]

**Example:**
"By 2028, the consortium has a shared open-science repository:
- $0.8M/year savings (reallocated to research, not duplicated storage)
- 200 datasets shared and citable across member institutions
- 8 universities using the platform (standardized, interoperable data infrastructure)
- Sector leadership: the consortium becomes a reference model for open-science data sharing

**Identity shift:** Research community as collaborator and sharer, not isolated silos."

**Sources:** [list files]

**Aspirational language:** [Use words like "leadership," "capability," "reproducibility," "collaboration"]

**Confidence:** [High|Medium|Low]

---

## Presentation Outline (Preliminary)

**Instructions:** Based on SCIPAB seed, here's the rough slide structure. Phase 3 will finalize.

**Estimated slide count:** [10-20, depending on depth]

1. **Title** (1 slide)
   - [Presentation title]
   - [Subtitle, if any]

2. **Situation** ([1-3] slides)
   - Current state baseline
   - Context/background

3. **Complication** ([1-2] slides)
   - The problem/tension
   - Evidence of inefficiency/risk

4. **Implication** (1 slide)
   - Stakes (what happens if we don't act)
   - Bold/urgent visual theme

5. **Position** ([3-5] slides)
   - Core thesis
   - Supporting claims (evidence-backed)
   - Proof points (case studies, benchmarks)

6. **Action** ([1-2] slides)
   - Concrete first step
   - Timeline, budget, owner

7. **Benefit** (1 slide)
   - Positive future state
   - Bright/uplifting visual theme

8. **Caveats** ([0-1] slide)
   - Limitations, contradictions (if unresolved)
   - Shows intellectual honesty

9. **References** ([0-1] slide)
   - Citations (especially for academic template)

10. **Backup slides** ([0-5] slides)
    - Deep dives for Q&A

**Total:** [Estimated total] slides

**Target presentation time:** [20 min? 40 min? 60 min?]
**Suggested pace:** [1-2 min per slide]

---

## Notes for Phase 2 (Interrogation)

**Instructions:** Phase 2 will challenge weak reasoning. Expect questions like:

1. **Implication challenge:**
   - "Your Implication is generic. What SPECIFICALLY happens? To whom? When?"

2. **Action challenge:**
   - "Your Action is vague. What's the FIRST STEP? Who does it? By when? What's required?"

3. **Theme prioritization:**
   - "You have 3 themes. Which ONE anchors the deck? Multi-theme talks dilute the message."

4. **Contradiction resolution:**
   - "[Source A] says X, [Source B] says Y. Which is authoritative? Or do we present both?"

**Be prepared to:**
- Defend your strategic choices
- Clarify audience priorities (What does THIS audience care about?)
- Provide concrete details (numbers, names, dates)

---

## Metadata & Tracking

**Session information:**
- **Started:** [ISO timestamp]
- **Last updated:** [ISO timestamp]
- **Total synthesis time:** [estimated duration]
- **Phase 1 duration:** [time taken for synthesis]
- **Phase 2 duration:** [time taken for interrogation, once complete]

**File versioning:**
- **STAGING.md version:** 1.0
- **If updated:** Increment version (1.1, 1.2, etc.) and note changes in commit message or at bottom of file

**Collaboration notes:**
- [If this is a team project, note who contributed what]
- [If external feedback was incorporated, cite source]

---

## Changelog (Optional)

**Version 1.0** (2026-01-14)
- Initial synthesis from [X] sources
- [Y] themes identified
- [Z] contradictions documented
- SCIPAB seed drafted (Implication & Action TBD)

**Version 1.1** (2026-01-15)
- Phase 2 complete: Implication refined, Action specified
- Theme prioritization: [Theme X] selected as anchor
- Ready for Phase 3 (Drafting)

---

## Related Documentation

- **[[../SKILL.md]]** - Write Manuscript Slide Deck technical implementation
- **[[../README.md]]** - User guide
- **[[../references/scipab-framework.md]]** - SCIPAB framework deep dive
- **[[../references/Review Literature-integration.md]]** - Review Literature integration guide (if PDFs processed)



