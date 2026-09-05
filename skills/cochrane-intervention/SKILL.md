---
name: cochrane-intervention
description: Validate the strict cochrane_intervention systematic-review profile against machine-checkable MECIR-oriented conduct controls. Use when a review explicitly opts into Cochrane-style intervention-review requirements; do not apply these gates to generic systematic reviews.
---

# Cochrane intervention-review profile

## Purpose

`cochrane_intervention` is an **opt-in profile** under `review_type: systematic`. It hardens the generic research pipeline around intervention-review conduct requirements derived from the *Cochrane Handbook for Systematic Reviews of Interventions* and MECIR expectations.

The profile is deliberately separate from generic `systematic`: ordinary systematic reviews remain backward compatible and may use different methodological standards.

## What is enforced

The runnable checker `scripts/cochrane_profile.py` validates a closed JSON contract for:

- a prespecified intervention-review protocol, planned comparisons, outcomes/time points, effect measures, synthesis rules, missing-results-bias plan, GRADE plan, conflicts, stakeholders, and amendments;
- a **team roster whose expertise is drawn from a closed vocabulary** (`methodologist`, `statistician`, `topic_expert`, `information_specialist`, `consumer_representative`), and the profile requires at least one `methodologist`, one `statistician`, and one `topic_expert` across the roster — free-text expertise strings that merely mention a keyword are rejected at parse time;
- documented CENTRAL and MEDLINE/PubMed searches, plus Embase when recorded as available; each source carries its own interface, strategy, controlled vocabulary, free text, coverage, filters/limits, and last-search date. Source-name matching is normalised (a parenthetical interface qualifier, e.g. `MEDLINE (Ovid)`, does not defeat matching);
- a **structured acquisition-manifest reference** — `{reference, digest, captured_by}` — whenever a pre-collected/imported corpus is used, with `captured_by` bound to a declared `protocol.team` member;
- explicit **record/report/study separation** through study records linking one or more report IDs to one study ID;
- two **distinct human** full-text eligibility decisions and reconciliation, with an explicit exclusion reason for excluded reports;
- two **distinct human** outcome extractions of **structured, typed result-level effect data** — `binary` (per-arm `n`/`events`), `continuous` (per-arm `n`/`mean`/`sd`), or `precomputed_effect` (`estimate`/`ci_lower`/`ci_upper`, optional `se`/`variance`) — for comparison, outcome, time point, analysis population, effect measure, and source location. Null/empty/absent effect payloads are rejected at parse time, not just "present";
- two **distinct human** risk-of-bias judgments and reconciliation for every extracted study/result pair;
- **decision-maker binding and independence metadata**: every eligibility/extraction/RoB decision-maker id must be a declared `protocol.team` member, each decision carries its own `recorded_at` timestamp and a per-actor `independence_attestation`, and the two attestations in a pair may not be identical boilerplate. This closes the gap where two arbitrary id strings (e.g. `alice`/`alice2`, with `alice2` on no team) could satisfy the independence gate;
- **reconciliation cannot silently overturn a unanimous pair**: whenever two independent reviewers/extractors/assessors agree and the reconciled decision/value/judgment differs from that agreement, a non-empty reconciliation note is required, exactly as it already was for disagreement;
- intervention routing: randomized trials → **RoB 2**; non-randomized studies of interventions → **ROBINS-I**. Newcastle–Ottawa does not satisfy this profile;
- a prespecified synthesis decision that may choose meta-analysis or a justified non-meta-analytic synthesis;
- a first-class synthesis-level missing-results-bias assessment for every result, and a **falsifiable GRADE linkage**: `grade_linkage.linked_results` must name, by `result_id`, the exact GRADE outcome/certainty-domain each missing-results-bias record informs. A record with an unlinked missing-results-bias result, or a linkage pointing at a non-existent result, fails.

AI/agent passes may assist every stage, but **do not count as either required human reviewer**. `recorded_at` and `independence_attestation` are **self-declared, machine-checked for shape and non-duplication only** — this profile cannot authenticate that a named human actually performed, or was first to perform, the recorded action. A clean result surfaces the count of these self-declared independence pairs rather than treating them as verified.

## Minimal record shape

```json
{
  "schema_version": "1.0",
  "review_type": "systematic",
  "profile": "cochrane_intervention",
  "protocol": {"...": "see contract below"},
  "search": {"...": "source-specific acquisition evidence"},
  "studies": [],
  "screening": [],
  "extractions": [],
  "risk_of_bias": [],
  "synthesis": {"...": "prespecified method decision"},
  "missing_results_bias": [],
  "grade_linkage": {"linked_results": [{"result_id": "O1", "grade_outcome": "...", "certainty_domain": "..."}]}
}
```

The complete executable schema is intentionally defined by the parser in `scripts/cochrane_profile.py`; unknown fields and malformed types fail closed rather than being silently ignored.

## Run

```bash
python skills/cochrane-intervention/scripts/cochrane_profile.py review-profile.json --strict
python skills/cochrane-intervention/scripts/cochrane_profile.py review-profile.json --strict --json
```

Exit codes: `0` clean (or non-strict), `1` profile violation in strict mode, `2` malformed/unreadable input.

## Verification semantics

A clean result means:

> The declared `cochrane_intervention` record satisfies the machine-checkable and human-actor invariants implemented by this profile.

It does **not** mean:

> This is an official Cochrane Review, the judgments are substantively correct, the named people/authorship history were independently authenticated, or Cochrane editorial/publication requirements have been certified.

Accordingly, repository-level wording remains **Cochrane-aligned**. `cochrane_intervention` is a **MECIR-oriented profile verification**, not institutional certification.

## Relationship to other skills

- `design-review-protocol` supplies the protocol material.
- `acquire-corpus` / external database adapters supply the source-specific search record.
- `dedupe-records` operates on records; this profile adds report→study linkage after deduplication.
- `screen-literature` may provide agent QA, but the final eligibility gate here requires two humans.
- `extract-synthesis` may assist extraction, but the profile requires two human outcome extractions.
- `appraise-risk-of-bias` supplies RoB 2 / ROBINS-I evidence; this profile adds duplicate-human conduct requirements.
- `validate-evidence` consumes RoB and missing-results-bias evidence for GRADE.
- `prisma-flow` remains the reporting flow; Cochrane conduct and PRISMA reporting are separate concerns.

## Boundary

The checker cannot determine whether an expert judgment is *correct*. Its job is to make required conduct records explicit, traceable, and fail-closed so that a two-agent simulation cannot silently masquerade as the two-person review process required by this profile.

## Activation status — not yet wired into `verify-review`

`cochrane_intervention` is, today, a **standalone conduct validator**, not an activated review-verification profile. Concretely:

- No pipeline skill reads a `review_type`/`profile` pair and dispatches into this checker automatically; it must be invoked directly against a record.
- The shared `verify-review` unit vocabulary (`review_units.py`) does not yet register a `U_cochrane` unit, so this checker's JSON envelope (`units.U_cochrane`) is not currently consumable by that layer, and `SKILLS-REGISTRY.md` does not list this skill in its decision trees or skill/script index.
- No test in this repository enforces agreement between this skill and the shared `verify-review` registry.

This is a **known, intentional integration gap**, not a hidden one: registering `U_cochrane` and wiring activation belongs to the shared `verify-review` layer (tracked separately), not to this standalone skill, per the "never import across skills" rule — this skill must keep running correctly when copied out on its own. Until that registration lands, a clean run of this checker means the declared record satisfies the `cochrane_intervention` contract; it does **not** mean the surrounding review pipeline enforced or required that contract.
