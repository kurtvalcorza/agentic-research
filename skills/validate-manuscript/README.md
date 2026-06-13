# Validate Manuscript

**Comprehensive quality assurance suite for research manuscripts.**

## What It Does

Runs three validation checks in sequence (citations → evidence → consistency), then produces a consolidated validation report with an overall quality score. Acts as a quality gate before manuscript submission.

## When to Use

- Final quality check before submitting manuscripts
- Ensuring citations are properly formatted and complete
- Verifying evidence strength claims match actual support
- Catching consistency issues across document sections
- Need systematic validation instead of manual review

## Quick Start

**Trigger:** "Validate my manuscript" or point to a manuscript file for quality check

The skill will run all three validators and generate a comprehensive report.

## Key Features

- **Multi-layer validation:**
  1. **Citations (internal)** - `validate-citations`: in-text citations vs. extraction matrix (consistency, format, completeness). Cannot tell if a source is real or retracted.
  2. **Source verification (external)** - `verify-sources`: runs **alongside** citations, resolving each citation against the external bibliographic record (scite MCP / CrossRef / OpenAlex) — DOI existence, author/year match, retraction/correction/concern, and claim-vs-source fidelity. Emits per-citation VERIFIED/RETRACTED/UNVERIFIED/FLAGGED/MISMATCH and a PASS/FAIL gate.
  3. **Evidence** - Strength claims vs. actual support (strong/moderate/weak/absent)
  4. **Consistency** - Cross-references, terminology, argument flow

- **Hard gate on sources:** A `verify-sources` FAIL (any RETRACTED or UNVERIFIED citation) is a HARD fail of the manuscript gate — it cannot be silently passed. Any override must be logged as a `human_override` per the ai-research-provenance steering doc.
- **AI disclosure:** Each run emits `ai-disclosure.md` per the ai-research-provenance steering doc (PRISMA-trAIce 2025 aligned; ICMJE/COPE).

- **Time savings:** 75% reduction (20 minutes → 5 minutes)
- **Consolidated reporting:** Single `validation-report.md` with overall score
- **Actionable feedback:** Specific line numbers and fix recommendations
- **Batch execution:** Runs all checks automatically

## Output Format

Validation report includes:
- Overall quality score
- Pass/fail status for each validator
- Detailed findings with line references
- Prioritized recommendations
- Quick-fix vs. structural issues

## Related Skills

- **write-manuscript** - Creates manuscripts with anti-ghostwriting controls
- **validate-evidence** - Standalone evidence strength checker
- **validate-citations** - Standalone INTERNAL citation validator (draft vs. extraction matrix)
- **verify-sources** - Standalone EXTERNAL citation verifier (real? retracted? faithful?) — complements validate-citations; run both
- **synthesize-research** - Generates research syntheses for validation

## Related Steering

- **.agent/steering/ai-research-provenance.md** - Per-decision provenance stamping + mandatory `ai-disclosure.md` artifact; `human_override` logging for gate overrides
