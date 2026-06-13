# Draft Section

Specialist agent for drafting manuscript sections in the research synthesis pipeline.

## What This Does

Writes individual manuscript sections using structured evidence from the extraction matrix. Works as Phase 3 specialist in the `synthesize-research` workflow.

## When to Use

Typically invoked automatically by `synthesize-research`, but can be used standalone when:

- You have a completed extraction matrix and synthesis
- You need to draft specific sections iteratively
- You want to regenerate sections with different emphasis
- You're building manuscripts outside the full pipeline

## What You Need

**Required Inputs**:
- **phase2-matrix.md**: Extraction matrix with structured evidence and citations
- **phase2-synthesis.md**: Thematic synthesis with cross-cutting insights
- **sections.md**: List of target sections to draft

## What You Get

- **phase3-draft.md**: Iteratively built manuscript with properly cited sections

## How It Works

For each section in `sections.md`:

1. Reads extraction matrix and synthesis
2. Identifies relevant evidence for the section
3. Drafts content in academic tone
4. **Citation Rule**: Only uses citations present in the extraction matrix
5. Appends section to `phase3-draft.md`

## Key Features

- **Citation Integrity**: Strict adherence to matrix citations—no fabricated references
- **Academic Tone**: Formal, evidence-based writing style
- **Iterative Drafting**: Builds manuscript section by section
- **Synthesis Integration**: Incorporates thematic insights from Phase 2
- **Append Mode**: Preserves existing sections, adds new ones

## Citation Policy

This specialist NEVER invents citations. Every reference must exist in the extraction matrix. If evidence is insufficient, the section will note gaps rather than fabricate sources.
