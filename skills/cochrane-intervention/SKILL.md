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

- a prespecified intervention-review protocol, planned comparisons, outcomes/time points, effect measures, synthesis rules, missing-results-bias plan, GRADE plan, team roles/expertise, conflicts, stakeholders, and amendments;
- documented CENTRAL and MEDLINE/PubMed searches, plus Embase when recorded as available; each source carries its own interface, strategy, controlled vocabulary, free text, coverage, filters/limits, and last-search date;
- a conforming acquisition manifest whenever a pre-collected/imported corpus is used;
- explicit **record/report/study separation** through study records linking one or more report IDs to one study ID;
- two **distinct human** full-text eligibility decisions and reconciliation, with an explicit exclusion reason for excluded reports;
- two **distinct human** outcome extractions and reconciliation using result-level fields for comparison, outcome, time point, analysis population, effect measure, source location, and value;
- two **distinct human** risk-of-bias judgments and reconciliation for every extracted study/result pair;
- intervention routing: randomized trials → **RoB 2**; non-randomized studies of interventions → **ROBINS-I**. Newcastle–Ottawa does not satisfy this profile;
- a prespecified synthesis decision that may choose meta-analysis or a justified non-meta-analytic synthesis;
- a first-class synthesis-level missing-results-bias assessment for every result and an explicit linkage into GRADE.

AI/agent passes may assist every stage, but **do not count as either required human reviewer**.

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
  "grade_linkage": {"missing_results_bias_feeds_grade": true}
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
