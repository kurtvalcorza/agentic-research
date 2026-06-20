# verify-review

**Drives a research review to a verifiably-finished end-state.** A bounded, audited, self-correcting loop over the suite's validation skills — it clears every *mechanical* defect, then cleanly hands off to the *human* gates.

## Why this exists

The validation skills (`verify-sources`, `validate-citations`, `validate-consistency`, `prisma-flow`, `validate-evidence`) normally run **once**. But the defects they catch — fabricated citations, screening disagreements, PRISMA arithmetic that doesn't reconcile, a sub-threshold consistency score, ungraded evidence — need *re-checking after a repair*. A single pass surfaces them; it doesn't close them.

`verify-review` turns that single pass into a loop: compute a mechanical **"units remaining"** scalar, fix the highest-leverage defect, re-check, repeat — until a **success predicate** holds, or until only a human can move the number.

## The one idea that makes it safe

It is adapted from a general autonomous code-improvement engine, but **inverted**: where that pattern loops to *avoid* humans, this loop runs to *cleanly hand off* to them. Risk-of-bias appraisal, numeric verification, and screening adjudication are documented LLM weak points — they stay **human gates**, never auto-resolved. The loop clears everything mechanical so the human only looks where it matters.

## What it does

1. **Classifies** the review type and resolves which units are in scope (systematic gets all; narrative gets the universal floor — citation integrity + consistency).
2. **Derives a success predicate** and confirms it once upfront.
3. **Loops**: recompute units → route one repair at the dominant defect → re-check → record the cycle.
4. **Stops** at `VERIFIED`, `BLOCKED_ON_HUMAN`, `PLATEAU` (3 flat cycles), or `CEILING` (25), with a soft methodology advisory at cycle 10.
5. **Hands off** to the human gates with the provisional machine judgment for each item.

Citation integrity is weighted ×3 — fabricated citations dominate routing because they are the headline risk.

## Runnable backend

`scripts/review_units.py` (stdlib only) computes the weighted scalar and the loop verdict from a `units.json`, exiting non-zero unless `VERIFIED` — so it gates a pipeline the same way `prisma_flow.py --strict` does.

```
python scripts/review_units.py units.json
```

See `references/loop-protocol.md` for the schemas, the state machine, and a worked example. Full design rationale: [`docs/verification-loop-spec.md`](../../docs/verification-loop-spec.md).

## The floor-guard

A metric-driven loop will "cheat" by deleting what it can't verify. So: removing a citation/study/theme to lower a unit is a **no-op** unless backed by a logged exclusion reason; an `UNVERIFIED (manual)` citation moves to the human gate rather than counting as cleared; regressions are reverted.

## When to run it

- To verify a manuscript/review to a finished state before submission.
- As the validation phase of `orchestrate-research`.
- Standalone: "verify this review", "drive this draft to clean."

## What it does NOT do

It orchestrates — it never re-implements a check or makes a human-gated judgment. It cannot drive human-gate units to zero (it stops and hands off). `VERIFIED` means every mechanical defect is cleared and every human gate confirmed — not that the argument is correct.

## Related

`verify-sources` · `validate-citations` · `validate-consistency` · `prisma-flow` · `validate-evidence` · `appraise-risk-of-bias` · `orchestrate-research` · `.agent/steering/ai-research-provenance.md`
