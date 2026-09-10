# Specification Quality Checklist: orx Discovery Backend for acquire-corpus

**Purpose**: Validate specification completeness and quality before proceeding to planning  
**Created**: 2026-09-09  
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No unresolved implementation choice blocks planning
- [x] Focused on user value, methodological safety, and repository contracts
- [x] All mandatory sections completed
- [x] Review corrections are reflected normatively rather than only in prose notes

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Acceptance scenarios cover enriched, keyless, degraded, and unresolved paths
- [x] Edge cases include schema drift, sparse metadata, timeouts, circuit opening, and unresolved enrichment
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions are explicit
- [x] Downstream compatibility conditions are explicit

## Feature Readiness

- [x] Keyless behavior remains the guaranteed baseline
- [x] Enrichment cannot inject dedupe-unsafe sparse records into `candidates.jsonl`
- [x] Acquisition provenance has one structured source of truth
- [x] Disclosure enforcement uses the repository's shared gate contract

## Notes

- Items marked incomplete require spec updates before `/speckit-plan`.
- **All 16 checklist items pass. Reviewer rounds 1 and 2 are resolved in the current spec.**
- Current size: **33 functional requirements, 14 success criteria, 14 edge cases.**
- The PR should remain draft until an independent reviewer verifies these resolutions.

## Maintainer decisions resolved on 2026-09-10

- **Optional enrichment stays optional.** OpenResearch is an external executable; no daemon, login,
  package import, or authenticated dependency is required for the guaranteed path.
- **Unknown upstream shapes fail closed.** Unknown top-level `LitHit` keys invalidate that enriched
  response and open the affected sub-source circuit for the run.
- **Identifier-less does not mean metadata-less.** A DOI-less enriched record may still be admitted,
  but only after it has a usable title, non-empty verified authors, and verified year. Sparse hits
  that cannot satisfy that minimum are preserved in `corpus/enrichment-unresolved.jsonl` and kept
  out of automatic deduplication.
- **The disclosure gate reads one object.** `corpus/acquisition-record.json` is canonical;
  `corpus/search-log.md` is generated from it.

## Review round 1 — findings at `faeb664`

All five findings were upheld and remediated:

- **P1 — stale daemon availability model: RESOLVED.** Availability is executable presence plus
  bounded public discovery calls with keyless fallback.
- **P1 — gate input mismatch: RESOLVED.** One closed-schema acquisition record is the gate input and
  source of truth; the Markdown search log is generated.
- **P1 — FR-007 vs Principle IV: RESOLVED.** Unknown upstream record keys are rejected, never ignored.
- **P1 — unsupported corpus-shape assumption: RESOLVED.** The spec now has a normative discovery
  mapping and distinguishes direct discovery fields from metadata that must be resolved before
  admission.
- **P2 — `verify-sources` limitation overstated: RESOLVED.** DOI-less records cannot resolve directly
  by DOI, but title/author/year reverse lookup remains available when metadata supports it.

## Review round 2 — findings at `10b8f964`

All three findings were upheld and remediated:

- **P1 — keyless provenance vs unchanged output: RESOLVED.** Existing keyless candidate records are
  not rewritten to add new provenance keys. Keyless provenance lives per query in
  `acquisition-record.json` and remains auditable through existing per-source raw artifacts. New
  record-level provenance fields apply to admitted enriched records.
- **P1 — empty authors / false-merge risk: RESOLVED.** The adapter may not synthesize `authors: []`
  or use a missing year merely to satisfy downstream shape. FR-031 requires title + non-empty
  verified authors + verified year before enriched admission; FR-032 preserves unresolved hits
  outside `candidates.jsonl`. This prevents the known title-only fuzzy false-merge path without
  modifying `dedupe-records`.
- **P2 — cumulative timeout risk: RESOLVED.** FR-033 adds a per-sub-source circuit breaker, no retry
  after a hard failure, and a fifteen-second total enrichment failure-wait budget per run.

## Validation notes

- **Artifact discipline**: `acquisition-record.json` is the canonical closed-schema artifact;
  `search-log.md` is generated from it.
- **Fail-closed discipline**: unknown upstream shapes fail closed; missing safe-admission metadata is
  never defaulted to empty/zero; unresolved evidence is preserved separately.
- **Dedupe safety**: sparse enriched evidence cannot reach automatic fuzzy dedupe until its author
  and year guards are actually available.
- **Keyless compatibility**: keyless candidate records retain the pre-feature contract; new
  provenance does not force schema churn on the guaranteed path.
- **Bounded degradation**: one hard failure opens the affected sub-source circuit, and cumulative
  failure waiting is capped per run.
- **Standards honesty**: the disclosure gate enforces enrichment disclosure only and does not make
  `acquire-corpus` PRISMA-S compliant.
