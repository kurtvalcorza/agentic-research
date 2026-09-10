# Specification Quality Checklist: orx Discovery Backend for acquire-corpus

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-09
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`.
- **All 16 items pass. Reviewer round 1 findings are resolved without an outstanding governance
  exception. The specification is ready for re-review and, if accepted, `/speckit-plan`.**

### Maintainer decisions resolved on 2026-09-10

- **FR-016 — identifier-less records are admitted for recall.** They retain the source identifier,
  are counted, and their downstream risk is disclosed rather than hidden.
- **FR-017 — enrichment disclosure is enforced by a runnable gate.** The gate reads one structured
  acquisition record, not a corpus JSONL plus a Markdown file.
- **FR-007 — Principle IV is applied conservatively.** Unknown upstream top-level record keys are
  not ignored. The enriched response is rejected as unsupported and the affected query falls back
  keyless. No constitutional amendment or scoped exemption is required for this feature.

### Review round 1 — findings at `faeb664`

All five findings were upheld and remediated against primary repository/upstream evidence.

- **P1 — availability model was stale. RESOLVED.** `orx discover` does not depend on a local daemon
  or login. FR-001/002 now model executable presence plus a bounded discovery invocation; Story 2,
  edge cases, and SC-003 use public-upstream failure rather than daemon failure.
- **P1 — gate input contract mismatch. RESOLVED.** FR-028 defines
  `corpus/acquisition-record.json` as the closed-schema one-object source of truth. FR-029 generates
  `corpus/search-log.md` from it. FR-024 binds the disclosure check to the existing one-JSON-object
  CLI contract, including `--strict`, `--json`, and exit codes 0/1/2.
- **P1 — FR-007 vs Principle IV. RESOLVED.** Unknown upstream record keys now invalidate the
  enriched response and trigger keyless fallback. Schema drift reduces optional enrichment rather
  than being silently accepted.
- **P1 — corpus-shape assumption. RESOLVED.** The spec now contains a normative field mapping for
  current OpenResearch `LitHit` output. Missing DOI/authors/year are represented explicitly rather
  than fabricated. The specification documents the serious downstream effect: `dedupe_records.py`
  treats absent author/year guards as vacuously true, so sparse records can fall back to title-only
  fuzzy matching and be falsely merged, deflating records-screened. FR-022 requires the exposed
  population to be counted before handoff.
- **P2 — `verify-sources` limitation was overstated. RESOLVED.** FR-023 now states that DOI-less
  records cannot be resolved directly by DOI, while existing title/author/year reverse lookup
  remains available. Missing author/year metadata makes that fallback less discriminating and can
  increase `UNVERIFIED`/manual-review outcomes.

Net after reviewer remediation: **30 functional requirements, 13 success criteria.**

### Validation notes

- **Artifact/source-of-truth discipline**: the acquisition record is structured and closed-schema;
  the human-readable search log is generated from it, satisfying the repository's artifact-
  generation rule.
- **Fail-closed discipline**: both the external structured boundary (FR-007) and the produced
  acquisition record/gate boundary (FR-024/FR-028) reject unknown shapes rather than silently
  accepting them.
- **Portability**: OpenResearch remains an external optional executable. No import-time or runtime
  dependency is added to the guaranteed keyless path.
- **Standards honesty**: the new disclosure gate does not convert `acquire-corpus` into a PRISMA-S
  compliance checker; PRISMA-S remains guidance as required by FR-027.
