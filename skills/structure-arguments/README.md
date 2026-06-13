# Structure Arguments

**Transforms synthesis matrices into theme-driven literature review drafts.**

## What It Does

Two-phase workflow: (1) Converts synthesis matrix into draft-ready outline with evidence strength labels, (2) Drafts literature review prose organized by themes, not papers. Writes with calibrated evidence language (strong/moderate/weak).

## When to Use

- Converting synthesis matrices into literature review drafts
- Need theme-driven (not paper-by-paper) literature organization
- Ensuring evidence strength language matches actual support
- Building arguments from clustered research findings
- Part of systematic research synthesis pipeline

## Quick Start

**Trigger:** Provide a synthesis matrix (table with papers × themes) and request argument structuring

The skill will outline themes, then draft cohesive narrative sections.

## Key Features

- **Theme-first organization:** Writes by conceptual themes, not chronologically by paper
- **Evidence strength calibration:**
  - Strong: Multiple converging sources, robust methodology
  - Moderate: Some support with limitations
  - Weak: Preliminary or conflicting evidence
- **Outline generation:** Converts matrix into hierarchical argument structure
- **Prose drafting:** Transforms outline into coherent literature review sections
- **Citation integration:** Maintains traceability to source papers

## Workflow

1. **Phase 1:** Synthesis matrix → Structured outline with evidence labels
2. **Phase 2:** Outline → Theme-driven prose with calibrated language

## Reporting & Submission Notes

- **Narrative synthesis → SWiM:** Output is a non-meta-analytic narrative synthesis; report it per the SWiM (Synthesis Without Meta-analysis) guideline. See the SWiM elements in **extract-synthesis**.
- **Gate before submission:** Any draft must pass **verify-sources** (external citation verification) and ship with an `ai-disclosure.md` per `.agent/steering/ai-research-provenance.md`.

## Related Skills

- **synthesize-research** - Generates synthesis matrices from literature
- **validate-evidence** - Verifies evidence strength claims
- **write-manuscript** - Full manuscript generation including lit reviews
- **validate-manuscript** - Quality assurance for final drafts
