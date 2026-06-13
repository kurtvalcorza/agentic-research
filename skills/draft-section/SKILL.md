---
name: draft-section
description: "Draft manuscript sections iteratively from extracted data and outlines. Use when writing a specific manuscript section (Introduction, Results, Discussion), or iterating on draft prose from synthesis evidence."
---








# Specialist: Section Drafter

## Purpose
Write specific sections of the manuscript based on extracted data and an outline.

## Inputs
- `outputs/phase2-matrix.md`
- `outputs/phase2-synthesis.md`
- `Section Name` (e.g., "Introduction", "Results")

## Outputs
- `outputs/phase3-draft.md` (Appended)

## Workflow

### 1. Preparation
- Read variable inputs.
- Determine section goals (e.g., Intro = Context + Gap; Results = Findings + Evidence).

### 2. Drafting
- Write the section in academic tone.
- **Citation Rule**: ONLY use citations found in `phase2-matrix.md`.
- **Auto-Fix**: If the draft mentions a claim not supported by the matrix, rewrite it to be more tentative.

### 3. Output
- Append to `outputs/phase3-draft.md`.

## Error Handling
- **Missing Data**: If matrix is empty, return "Cannot draft [Section] - No data".


## Internal Metadata
- **capabilities**: [file-read, file-write]
- **domain**: research
- **status**: active
- **version**: 2.0
- **type**: specialist