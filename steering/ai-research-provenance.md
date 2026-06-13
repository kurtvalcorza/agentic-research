---
description: "Defines how AI/LLM involvement in research pipelines is recorded and disclosed — per-decision provenance stamping (model, version, prompt, human override) and the ai-disclosure.md artifact, aligned with PRISMA-trAIce (2025) and ICMJE/COPE AI-disclosure norms. Read before running any research-suite skill that screens, extracts, appraises, drafts, or validates."
source-section: "AI Research Provenance"
---

# AI Research Provenance & Disclosure Convention

## Purpose

When AI agents perform substantive steps of a literature review or research synthesis — screening, extraction, appraisal, drafting, citation handling — the output is only trustworthy and reproducible if **how the AI was used is recorded**. Model behaviour changes across versions; a review run on one model/prompt may not replicate on another. Reporting standards now require this: **PRISMA-trAIce (2025)** is a 14-item checklist for AI-in-systematic-reviews, and ICMJE/COPE require disclosing substantive AI assistance (and never listing AI as an author).

This convention applies to every research-suite skill (`orchestrate-research`, `screen-literature`, `extract-synthesis`, `validate-*`, `write-manuscript`, `verify-sources`, etc.). It is **not** a literature standard this pipeline invented — it operationalizes external requirements for an AI-assisted pipeline.

## Two requirements

### 1. Per-decision provenance stamping

Every automated **include/exclude**, **extraction**, **appraisal grade**, and **citation verification** decision must be attributable. Record, in the run's state/log (e.g. `execution-log.json`, `manifest.json`, or the phase report):

```yaml
decision:
  stage: screening            # screening | extraction | appraisal | drafting | verification
  item: "Smith2024.pdf"       # the record/claim acted on
  outcome: "INCLUDE"          # the decision
  model: "claude-fable-5"     # the model that made it
  model_version: "2026-06"    # version/date — model behaviour is version-specific
  prompt_id: "screen-v1"      # which prompt/criteria version drove it
  human_override: null        # or: {by: "user", from: "EXCLUDE", to: "INCLUDE", reason: "..."}
  timestamp: "2026-06-13"
```

Agents need not write this for every trivial step by hand — pipeline skills should log it as part of their state. The minimum bar: **for any include/exclude, extraction, grade, or verification a human could later question, the model + prompt version that produced it is recoverable.**

### 2. The `ai-disclosure.md` artifact

Every completed review/synthesis run emits an `ai-disclosure.md` (in the run's output workspace), so the human author can paste it into a methods/acknowledgements section. It follows PRISMA-trAIce. Template:

```markdown
# AI-Assistance Disclosure

**Review/Output:** <title>
**Date:** <YYYY-MM-DD>

## Tasks performed with AI assistance
| Stage | AI-assisted? | Model + version | Human role |
|:------|:-------------|:----------------|:-----------|
| Search strategy design | … | … | … |
| Screening (title/abstract) | yes | claude-fable-5 (2026-06) | adjudicated conflicts + all exclusions |
| Full-text screening | … | … | … |
| Data extraction | yes | … | verified all numeric fields |
| Risk-of-bias appraisal | assistive only | … | human made final judgments |
| Synthesis / drafting | … | … | … |
| Citation verification | yes | scite MCP + claude-fable-5 | reviewed all flags |

## Prompts / criteria
- Screening criteria: <link to settings/screening-criteria.md, version>
- Key prompt versions: <ids>

## Human oversight
- Checkpoints where a human approved/overrode: <list>
- Decisions overridden: <count + summary>

## Validation
- External citation verification: <verify-sources gate result + date>
- Limitations of the AI assistance: <e.g. appraisal is model-assisted, not a substitute for expert judgment>

## Statement
AI tools were used as described above. AI is not an author. All substantive
judgments were reviewed by the human author(s), who take responsibility for
the final content.
```

## Disclosure threshold (per ICMJE/COPE)

- **Routine language polishing** (grammar, flow) — generally does not require disclosure, but check the target venue.
- **Substantive assistance** (screening, extraction, appraisal, synthesis, drafting, citation handling) — **must** be disclosed. This research pipeline is substantive by definition, so `ai-disclosure.md` is mandatory for any output intended for submission or external sharing.
- **Never** list an AI tool as an author. The human author is accountable.

## Gate-override logging

When a human chooses to proceed past a failed quality gate (e.g. a `verify-sources` FAIL, a `validate-consistency` score < 75), that override is a provenance event: log it under `human_override` with the reason. Silent override defeats the audit trail.

## Relationship to other conventions

- Complements `two-output-rule.md` (passive enrichment) and `bi-temporal-tracking.md` (fact provenance) — this one is *decision* provenance for AI-run research.
- The `verify-sources` skill is the technical gate; this steering file is the recording/disclosure convention around it.
