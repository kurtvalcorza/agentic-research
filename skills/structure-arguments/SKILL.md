---
name: structure-arguments
description: "Convert synthesis into a defensible outline and draft theme-driven literature review prose grounded in evidence. Use when building an argument outline from synthesis data, drafting literature review sections, or structuring themes into prose."
---








# Argument Structure + Drafting Agent

## Overview
This skill covers two phases:
- **Phase 3:** Convert synthesis matrix into a draft-ready outline with evidence labels.
- **Phase 4:** Draft theme-driven literature review prose grounded in synthesis evidence.

> **Narrative synthesis → report per SWiM:** The output is a *non-meta-analytic* narrative synthesis, so report it per the SWiM (Synthesis Without Meta-analysis) guideline — see the SWiM elements in `[[../extract-synthesis/SKILL|Extract Synthesis]]` (grouping, standardized metric/effect-direction, synthesis method, presentation, structured findings summary, synthesis limitations).

## Dependencies

- **[[../extract-synthesis/SKILL|Extract Synthesis]]** - Provides the synthesis matrix.
- **Tools**: `file-read`, `file-write`.

---

## Phase 3: Argument Structure (Outline)

### Output
- `outputs/phase3-argument-outline.md`

### Steps
1.  Read `phase2-synthesis-matrix.md`.
2.  Organize themes into a logical outline.
3.  **Label Evidence**: Every point must have citations attached.
4.  **Flow Check**: Ensure specific logic flows (General -> Specific -> Gap).

### Structure Rules
- Introduction first.
- Themes ordered by evidence strength.
- Gaps section must lead to "Future Directions".

---

## Phase 4: Drafting

### Output
- `outputs/phase4-literature-review-draft.md`

### Core Principle
**Write by theme, not by paper.** Every claim must trace to the synthesis matrix.

### Evidence Strength Language
- **Strong consensus:** "Research clearly shows..."
- **Mixed views:** "Much research suggests..."
- **Emerging:** "Preliminary evidence indicates..."
- **Limited:** "One study suggests..."

### Steps
1.  Read the Outline and the Matrix.
2.  Draft paragraphs covering all sub-points.
3.  **Strict Citation**: `[Author2023]` for every claim.

> **Gate before submission:** Any draft produced here must pass `[[../verify-sources/SKILL|verify-sources]]` (external citation verification: real DOI, author/year match, no retractions, claim-vs-source fidelity) and ship with an `ai-disclosure.md` per `.agent/steering/ai-research-provenance.md` before submission.


## Internal Metadata
- **tags**: ["#skill/research", "#status/active"]
- **domain**: research
- **status**: active
- **version**: 1.1
- **created**: 2026-01-26
- **updated**: 2026-01-26