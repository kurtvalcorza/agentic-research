# verify-sources

**External-truth citation verification for AI-assisted research.** Resolves every citation in a draft against real bibliographic databases — confirming each source exists, hasn't been retracted, and is faithfully represented.

## Why this exists

AI-assisted writing fabricates or distorts citations at alarming rates (studies report 14% to >90% depending on model and task). The vault's `validate-citations` skill checks whether a citation in your draft matches your own extraction matrix — but a fabricated source can be *consistently* fabricated across both. This skill closes that hole by checking against the outside world.

It is the most important guardrail in the research pipeline: **a single retracted or hallucinated citation can invalidate an entire review.**

## What it does

For every citation in a draft, it checks three layers:

1. **Existence** — does the DOI/title resolve to a real publication with matching authors, year, and title?
2. **Integrity** — has it been retracted, corrected, or flagged with an editorial concern?
3. **Fidelity** — does the draft's claim faithfully represent what the source actually says?

It emits a per-citation report (`VERIFIED` / `RETRACTED` / `UNVERIFIED` / `FLAGGED` / `MISMATCH`) and a pass/fail gate.

## How it connects to services

Backend-agnostic, in preference order:
- **scite MCP** (preferred) — one call returns metadata, retraction notices, and Smart Citation tallies.
- **CrossRef API** (free) — DOI resolution + retraction flags.
- **OpenAlex API** (free) — metadata + `is_retracted`, plus title→DOI reverse lookup.
- **Manual web check** (last resort) — flagged for human confirmation, never auto-passed.

See `references/verification-protocol.md` for field mappings and a worked example.

## When to run it

- Before submitting or sharing any cited research output.
- As a gate inside `validate-manuscript` and the research orchestrators.
- Any time an LLM produced prose with references.

## What it does NOT do

It verifies citations against external records only. Internal draft↔matrix consistency is `validate-citations`; evidence grading is `validate-evidence`; cross-phase traceability is `validate-consistency`. `validate-manuscript` runs them together. A PASS means the citations are real and current — not that the argument is correct.

## Related

`validate-citations` · `validate-manuscript` · `orchestrate-research` · `synthesize-research` · `.agent/steering/ai-research-provenance.md`
