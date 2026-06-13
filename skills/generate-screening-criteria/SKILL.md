---
name: generate-screening-criteria
description: "Interview the user and generate screening-criteria.md for Phase 1. Use when setting up a new literature review, defining inclusion/exclusion criteria, or preparing screening parameters before corpus screening."
---








# Criteria Generator Agent

## Overview
This agent acts as a **Research Design Interviewer**. It helps the user define clear parameters for their literature review before the screening begins.

**Goal**: Convert user's vague intent into a rigorous `screening-criteria.md` file.

**Output**: `{WorkDir}/settings/screening-criteria.md`

> **Upstream note — derive criteria from the protocol, don't invent them.** In a pre-specified review, the eligibility criteria are decided *before* this skill runs, by `design-review-protocol` (which sets the review type — systematic / scoping / rapid / umbrella / narrative — and frames the question with PICO / PEO / SPIDER / PCC). This skill's job is then to **operationalize** that protocol's eligibility into binary `screening-criteria.md` rules — not to re-derive scope from scratch.
> - **If a `protocol.md` exists** (look in `{WorkDir}/` or the review's protocol location), read its **Eligibility criteria** and translate each include/exclude rule into a binary screening rule. The interview becomes a *confirmation/refinement* pass, not a from-scratch design. Do not silently widen, narrow, or contradict the protocol's eligibility; if a clarification changes scope, treat it as a protocol amendment (flag it for the protocol's change log).
> - **If no `protocol.md` exists**, this skill can still build criteria interactively (the default below). For any review intended to be **registrable, reproducible, or publishable**, recommend running `design-review-protocol` first so the criteria have a pre-specified, auditable source.

## Dependencies

### Required Skills
- None.

### Required Capabilities
- `file-read` - Capture user context and constraints.
- `file-write` - Generate the screening criteria file.

### Phase Dependencies
**See:** `design-review-protocol` (recommended upstream). For a pre-specified review, this skill operationalizes the protocol's eligibility rather than designing scope ad hoc.

### Input Files
**MUST exist before execution:**
- None (criteria are generated from the interview).

**Use if present (pre-specified review):**
- `protocol.md` (from `design-review-protocol`) — its **Eligibility criteria** are the authoritative source to operationalize into `screening-criteria.md`.

### Output Directories
**Auto-created if missing:**
- `{WorkDir}/settings/` - Screening criteria location.

### Related Workflows
- **[[../design-review-protocol/SKILL|Design Review Protocol]]** - Recommended upstream. Sets review type + framed question and pre-specifies the eligibility this skill operationalizes.
- **[[../screen-literature/SKILL|Screen Literature]]** - Runs Phase 1 screening.
- **[[../orchestrate-research/SKILL|Orchestrate Research]]** - Full multi-phase pipeline.

## Interaction Model

### Step 0: Check for a pre-specified protocol
Before interviewing, check whether a `protocol.md` (from `design-review-protocol`) exists for this review.
- **If it exists**: read its **Eligibility criteria** and use Steps 1–2 below as a *confirmation/refinement* pass — translate each protocol include/exclude rule into a binary screening rule, rather than re-deriving scope. Any change that alters scope is a protocol amendment; flag it for the protocol's change log instead of silently overriding it.
- **If it does not exist**: proceed with the full interview below. For a registrable/publishable review, recommend running `design-review-protocol` first.

### Step 1: Context Gathering (The Interview)
Ask the following questions (group them logically, don't overwhelm):

**Round 1: The Core**
1.  **Research Topic**: What is the specific research question or topic?
2.  **Objective**: Are you looking for a broad overview, specific empirical evidence, or a theoretical framework?

**Round 2: The Scope**
3.  **Timeframe**: What is the date range (e.g., last 5 years, 2010-Present)? Why?
4.  **Geography**: Is this specific to a country (e.g., a target country), a region (ASEAN), or global?
5.  **Language**: English only? Any others?

**Round 3: The Filter**
6.  **Inclusion Specs**: What *must* a paper have to be included? (e.g., "Must include empirical data", "Must discuss policy")
7.  **Exclusion Specs**: What specific things do you want to ignore? (e.g., "Exclude non-peer-reviewed", "Exclude technical engineering papers", "Exclude opinion pieces")

### Step 2: Draft Generation
Once you have the answers, generate the content for `screening-criteria.md` following the standard template format.

**Template Structure to Fill:**
- Research Context (Topic, Type, Scope)
- Inclusion Criteria (The "Must Haves")
- Exclusion Criteria (The "Must Nots")
- Edge Cases (How to handle uncertainty)

### Step 3: File Writing
Write the file to: `{WorkDir}/settings/screening-criteria.md`

### Step 4: Confirmation
Present a summary of the generated criteria to the user and ask if they are ready to proceed to **Phase 1: Literature Screening**.

## Example Dialogue
> **Agent**: "Let's set up your screening criteria. First, what is your main research question?"
> **User**: "I want to know about sustainable agriculture in Vietnam."
> **Agent**: "Got it. What's the ideal timeframe for this research? And are we focusing strictly on Vietnam or the Mekong Delta region?" ...

## Success Criteria
- [ ] User feels understood.
- [ ] `screening-criteria.md` is created/updated.
- [ ] Criteria are binary/operational (an AI can say YES or NO to them).



## Internal Metadata
- **color**: teal
- **tags**: ["#skill/research", "#status/active"]
- **capabilities**: [file-read, file-write, command-exec]
- **domain**: research
- **status**: active
- **version**: 1.0
- **created**: 2026-01-17
- **updated**: 2026-01-17
- **input**: Working Directory