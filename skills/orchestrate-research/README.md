# Orchestrate Research

Master orchestrator for literature review workflows with zero configuration required.

## What It Does

Automatically detects your corpus size, selects the appropriate review methodology (Standard review via the review-literature skill for <50 papers, Recursive LRA for 50+ papers), configures output paths, and integrates validation. You provide the corpus, the skill handles everything else.

## When to Use

- Starting a literature review with any number of papers
- Need automatic routing between review methodologies based on corpus size
- Want integrated validation without manual configuration
- Prefer zero-config workflows over manual setup

## Quick Start

**Trigger**: "Review this corpus" or "Orchestrate research for [topic]"

Simply point to your corpus directory or provide paper files. The skill will:
1. Count papers and auto-select methodology
2. Configure output paths automatically
3. Execute the appropriate LRA workflow
4. Run post-review validation
5. Deliver synthesis-ready results

## Three-Layer Intelligence Stack

- **Layer 1**: Corpus analysis and methodology selection
- **Layer 2**: Workflow execution (Standard or Recursive LRA)
- **Layer 3**: Automated validation and quality assurance

## Related Skills

- `synthesize-research` - Generate manuscripts from review outputs
- `validate-evidence` - Deep validation of research claims
- `write-note` - Capture individual research insights
