# Implementation Plan: Standards Enforcement Parity

**Branch**: `001-standards-enforcement-parity` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-standards-enforcement-parity/spec.md`

## Summary

Three new command-line checks — certainty grading, risk-of-bias appraisal, and reporting
completeness — join the existing flow-diagram check, all sharing one input convention, one
outcome contract, and one fail-closed posture. Each consumes a versioned JSON record and
generates the manuscript artifact from it rather than checking a hand-written one. The
verification loop's backend is extended so its certainty, traceability, and reporting units are
computed from those checks instead of asserted by hand. Guidance that instructs practices the
GRADE framework does not define is corrected first, because a check built around it would make
the errors authoritative. Every script that can fail a review run — the six that exist and the
three that are new — gets first-time automated coverage, run in CI on every push and pull
request.

Technical approach: sibling scripts, one per owning skill, mirroring `prisma_flow.py` exactly.
No shared library, because a skill directory must stay copyable on its own. Cross-artifact
traceability is achieved by passing the appraisal record's path as a command-line argument, never
by importing across skills.

## Technical Context

**Language/Version**: Python 3.11+ (CI matrix: 3.11, 3.12; local development on 3.12.10)

**Primary Dependencies**: None. Standard library only, including for tests — required by
constitution Principle II.

**Storage**: JSON documents on disk, authored per review run; generated Markdown artifacts
alongside them. No database.

**Testing**: `unittest` (stdlib) with `unittest.mock` for network isolation. Discovery via
`python -m unittest discover -s tests -v`.

**Target Platform**: Cross-platform CLI (Windows, macOS, Linux). Primary development environment
is Windows, so path handling and text encoding must not assume POSIX; the existing scripts already
call `sys.stdout.reconfigure(encoding="utf-8")` defensively and new scripts follow suit.

**Project Type**: Skills library — a collection of self-contained skill directories, each
optionally shipping a standalone CLI script. Not an application; there is no service, no
persistent process, and no build step.

**Performance Goals**: Not a driver. A review comprises tens to low hundreds of studies and at
most a few dozen results. Each check should complete in well under one second for a record of 500
studies; no optimisation work is planned or warranted.

**Constraints**: No third-party dependency may be introduced, including for testing. No script may
import from another skill. No test may perform a network request. All four checks must share one
exit-code contract.

**Scale/Scope**: 27 reporting items (20 for the scoping variant), 4 appraisal instruments spanning
5–7 domains each, 5 certainty downgrade domains plus 3 upgrade reasons, 11 test modules, 8 guidance
files to correct.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against constitution v1.0.0.

| Principle | Verdict | Evidence |
|:--|:--|:--|
| **I. Standards enforced, not described** | **PASS** | The feature exists to satisfy this principle. FR-035 additionally removes the repository's one unbacked claim, and FR-036 lists the omitted check. |
| **II. Keyless, stdlib-only baseline** | **PASS** | No runtime or test dependency added. `unittest` chosen over `pytest` specifically to honour this (see research.md D-003). |
| **III. Skills self-contained and portable** | **PASS** | Each check lives in its owning skill. Cross-artifact traceability uses a CLI path argument (FR-019), not an import. The only shared code is `tests/_load.py`, which never ships with a skill. |
| **IV. Fail closed** | **PASS** | FR-027 (outcome contract), FR-028 (unknown keys rejected), FR-029 (empty collections fail), FR-044 (absent/unknown version rejected), FR-024 (absent applicable unit is missing, not zero). |
| **V. Humans where LLMs are weak** | **PASS** | FR-014 requires confirmation per study; FR-026 forbids the loop from auto-satisfying it; FR-009 refuses an estimation basis for systematic and umbrella reviews. |
| **VI. Only mechanically decidable claims** | **PASS** | FR-030 requires every check to document its limits. FR-015 states the confirmation check establishes presence, not authenticity. No check asserts a judgment is correct. |
| **VII. AI provenance recorded** | **PASS** | Generated artifacts carry a provenance line identifying the generating check and record, consistent with `steering/ai-research-provenance.md`. No change to the provenance convention itself. |

**Result: no violations.** The Complexity Tracking section is therefore empty and has been removed.

One deliberate cost is accepted rather than justified as a violation: the input-coercion and
verdict-formatting helpers are duplicated across four scripts instead of shared. This is the direct
consequence of Principle III and is treated as intended design, not debt. Cross-script consistency
of those helpers is enforced by test rather than by shared code (see research.md D-002).

## Project Structure

### Documentation (this feature)

```text
specs/001-standards-enforcement-parity/
├── plan.md              # This file
├── research.md          # Phase 0 output — decisions with rationale and rejected alternatives
├── data-model.md        # Phase 1 output — entities, fields, validation rules
├── quickstart.md        # Phase 1 output — runnable validation scenarios
├── contracts/           # Phase 1 output — record and CLI contracts
│   ├── cli-contract.md
│   ├── grade-profile.md
│   ├── risk-of-bias.md
│   ├── prisma-checklist.md
│   └── review-units.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (already passing 16/16)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
skills/
├── validate-evidence/
│   ├── SKILL.md                      # MODIFIED — output contract, script usage, decidability limit
│   ├── scripts/
│   │   └── grade_profile.py          # NEW — certainty grading check + profile/SoF generator
│   └── references/
│       ├── DETAILS.md                # MODIFIED — remove aggregate certainty, per-paper grading,
│       │                             #   any-RCT starting rule; repair self-referential link
│       └── grade-framework.md        # MODIFIED — imprecision reconciled to CI/OIS primary
├── appraise-risk-of-bias/
│   ├── SKILL.md                      # MODIFIED — output contract, script usage, presence-not-
│   │                                 #   authenticity statement
│   ├── scripts/
│   │   └── rob_appraisal.py          # NEW — appraisal check + traffic-light generator
│   └── references/
│       └── instruments.md            # MODIFIED — add machine-readable domain keys and vocabularies
├── prisma-flow/
│   ├── SKILL.md                      # MODIFIED — document the checklist check alongside the flow
│   └── scripts/
│       ├── prisma_flow.py            # CHANGED — quoted counts (D-019), closed schema (D-020)
│       └── prisma_checklist.py       # NEW — reporting completeness check + checklist generator
└── verify-review/
    ├── SKILL.md                      # MODIFIED — new units in both tables
    └── scripts/
        └── review_units.py           # MODIFIED — U_grade redefined; U_rob_trace, U_checklist added;
                                      #   H_rob computed

tests/                                # NEW — stdlib unittest, discovered from repo root
├── _load.py                          # Shared loader (importlib) — the ONLY shared test code
├── fixtures/                         # JSON records, one defect per fixture; *.valid.json pass
├── test_prisma_flow.py               # NEW coverage for existing script
├── test_kappa.py                     # NEW coverage for existing script
├── test_dedupe_records.py            # NEW coverage for existing script
├── test_review_units.py              # NEW coverage for existing script
├── test_resolve_citation.py          # NEW coverage for existing script (network mocked)
├── test_search_openalex.py           # NEW coverage for existing script (network mocked)
├── test_grade_profile.py             # NEW
├── test_rob_appraisal.py             # NEW
├── test_prisma_checklist.py          # NEW
├── test_coercion_conformance.py      # NEW — the four checks agree on malformed input
└── test_no_dependencies.py           # NEW — asserts stdlib-only imports (Principle II)

.github/workflows/
└── tests.yml                         # NEW — unittest discovery on push and pull request

README.md                             # MODIFIED — runnable-checks table completed; checklist claim
                                      #   made true rather than aspirational
SKILLS-REGISTRY.md                    # MODIFIED — register the new scripts
CLAUDE.md                             # NEW — agent context file with SPECKIT markers
```

**Structure Decision**: The repository is a skills library, not an application, so the template's
`src/` + `tests/` single-project layout does not apply and has been replaced by the real tree
above. Each check lives under `scripts/` inside the skill that owns the methodology it enforces —
certainty grading under `validate-evidence`, appraisal under `appraise-risk-of-bias`, reporting
completeness under `prisma-flow` alongside the existing flow check. This keeps every skill
directory independently copyable, satisfying Principle III.

Tests are the one exception to co-location: they live in a single `tests/` tree at the repository
root rather than inside each skill. Skills are distributed to users; their tests are not. A single
tree also permits one discovery command and one CI job, and confines the shared `_load.py` helper
to code that never ships.

## Phase Sequencing

Implementation proceeds in three independently reviewable phases, matching the spec's stated
assumption:

1. **Guidance correctness** (FR-031 to FR-034). Must come first: a check written against the
   current guidance would encode the aggregate-certainty and per-paper-grading errors into
   executable form, which is harder to reverse than prose.
2. **The three checks** (FR-001 to FR-022, FR-042 to FR-044), each with its tests, in priority
   order — certainty, then appraisal and traceability, then reporting completeness.
3. **Loop integration, backfilled coverage, and CI** (FR-023 to FR-026, FR-035 to FR-041).

Phase 3 carries the known risk that first-time coverage of `kappa.py` and `review_units.py` may
surface pre-existing defects. Each such finding is raised individually rather than folded into this
feature's diff, per the spec's edge-case rule.

## Constitution Check — post-design re-evaluation

Re-run after Phase 1. **Still no violations**, with two items recorded during design that a
reviewer should see rather than have to rediscover.

**1. A pre-existing divergence was found, and resolving it changes shipped behaviour.**
`prisma_flow.py` accepts a quoted count such as `"3"` and coerces it; `review_units.py` rejects
non-numbers outright, commenting that a wrong type must fail closed. The shared contract cannot be
real while both stand. Principle IV settles the direction — the strict behaviour wins, and
`prisma_flow.py` changes (research.md D-019). This is a behavioural change to working code, so it
is tracked as its own task and called out in the pull request rather than absorbed silently.

**2. The scoping-review checklist variant is a live Principle I risk.**
The repository's standards table claims PRISMA-ScR support. This feature adds a `prisma_scr`
variant whose item table must be transcribed from the published checklist — and an item table
reconstructed from memory would make every completeness verdict wrong while looking authoritative,
which is a worse failure than having no check. Two outcomes satisfy Principle I and one does not:

- Transcribe the variant's items from the source and implement it. **Preferred.**
- Ship without the variant and add an explicit non-enforcement note to the standards table.
- Ship an approximated item table. **Forbidden** — it manufactures exactly the false confidence
  Principle I exists to prevent.

The plan takes the first option and allocates a transcription task with a cross-check against the
source; if that transcription cannot be completed, the second option is the fallback, never the
third.

Both items are design outputs rather than gate failures, so the Complexity Tracking table remains
empty and the gate passes.
