<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0 (2026-07-26)
Rationale: MINOR — Principle II materially expanded, no principle removed or redefined.

  Writing the first automated check of Principle II (tests/test_no_dependencies.py)
  surfaced skills/review-literature/scripts/rlm_corpus_loader.py importing pypdf /
  PyPDF2. Inspection showed the imports are lazy (inside the function), guarded by
  try/except with an actionable message, and that the loader's Markdown path works
  without them.

  Principle II as ratified would have banned PDF reading outright. That was not the
  intent: the requirement is that nothing is needed to GET STARTED and no core path is
  blocked, not that no optional library may ever be touched. Principle II now carves
  out optional capability dependencies under four conditions (lazy, guarded, non-
  blocking, disclosed), and forbids without exception any dependency required to
  import or run a script.

  This was found by enforcement, not by review — which is the point of the principle.

Templates requiring updates for 1.1.0:
  ✅ tests/test_no_dependencies.py — enforces the refined rule: module-level imports
     must be stdlib; third-party imports permitted only when lazy AND guarded
  ✅ README.md — rlm_corpus_loader.py added to the script table with its optional
     dependency disclosed, satisfying condition 4

---
PREVIOUS: Version change: (none) → 1.0.0
Rationale: Initial ratification. The repository operated on these rules implicitly
(README "Design principles", the human gate in appraise-risk-of-bias, the fail-closed
posture of review_units.py); this codifies them as governing principles.

Modified principles: none (initial adoption)

Added sections:
  - Core Principles I–VII
  - Standards Alignment & Scope Boundaries
  - Development Workflow & Quality Gates
  - Governance

Removed sections: none

Template count deviation: the constitution template ships 5 principle slots; this
constitution defines 7, per explicit user instruction.

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check gate is generic
     ("[Gates determined based on constitution file]"); no edit required
  ✅ .specify/templates/spec-template.md — no constitution-mandated sections added
  ⚠ .specify/templates/tasks-template.md — two generic-boilerplate tensions, left
     unedited to avoid drift from the upstream-managed template, and handled per
     feature instead:
       - "Tests are OPTIONAL - only include them if explicitly requested" conflicts
         with the workflow rule that every gate script MUST have a test module.
         Every spec under this constitution MUST therefore request tests explicitly.
       - Scaffold task "Initialize [language] project with [framework] dependencies"
         conflicts with Principle II. Setup tasks MUST NOT add dependencies.
  ✅ README.md — REMEDIATED 2026-07-26, ahead of the feature that will close the
     underlying gaps. The runnable-backends table now lists review_units.py, and the
     standards table gained an explicit "Enforced?" column separating a runnable gate
     from documented guidance; GRADE, the risk-of-bias instruments, dual extraction,
     SWiM and the reporting checklist are marked ⚠️ guidance rather than implied as
     enforced. Principle I is satisfied by the honest label; upgrading those rows to
     enforced is the work of 001-standards-enforcement-parity.

Follow-up TODOs: none deferred.
-->

# agentic-research Constitution

## Core Principles

### I. Standards Are Enforced, Not Described

Every methodological standard this repository claims to support MUST be backed by either
a machine-checkable gate or a prominent, specific honesty note stating that it is not
enforced. A claim in the README, a skill description, or a standards table with no
artifact behind it is a **defect**, not documentation.

Enforcement means: a runnable script that consumes a declared artifact, reports the exact
discrepancy when the artifact violates the standard's own rules, and exits non-zero under
`--strict`. Prose that instructs an agent to "assess rigorously" is not enforcement.

*Rationale: the repository's entire value proposition over an unaided LLM is that its
claims are checkable. An unbacked claim is worse than an absent one, because it transfers
false confidence to a reviewer who will not go looking.*

### II. Keyless, Standard-Library Baseline (NON-NEGOTIABLE)

Every runnable backend MUST work with only the Python standard library and free,
unauthenticated APIs (OpenAlex, CrossRef). Paid or authenticated services (e.g. the scite
MCP) are optional enrichment: skills MUST detect their absence and degrade gracefully,
and MUST NEVER block on them.

This extends to development tooling. Test suites MUST use `unittest` from the standard
library. No dependency may be introduced for tests, linting, or formatting.

**Optional capability dependencies.** A capability genuinely impossible with the standard
library — PDF text extraction being the only current case — MAY use a third-party library,
subject to all four of:

1. The import is **lazy** (inside the function that needs it), never at module level, so
   importing the script never requires the package.
2. The import is **guarded**, failing with an actionable message naming what to install.
3. The skill's **other paths still work** without it. A loader reading both Markdown and
   PDF must still read Markdown.
4. The dependency is **disclosed** in the README's script table.

A dependency required to import or run a script at all is forbidden, with no exception.

*Rationale: "point your agent at `skills/` and it works" is the adoption path. A single
`pip install` in the critical path breaks the promise for the reviewer who is not a
Python developer, which is most of the intended audience. But an absolute prohibition would
ban PDF reading outright, which serves nobody — the real requirement is that nothing is
needed to get started and no core path is blocked.*

### III. Skills Are Self-Contained and Portable

A skill directory MUST remain functional when copied out of this repository on its own.
Scripts MUST NOT import from sibling skills, from a shared library, or from any path
outside their own skill directory.

When one gate needs data produced by another skill, that data MUST be passed as a **file
path on the command line**, never as an import. Reading a path supplied by the caller
preserves portability; importing a sibling does not.

Shared test infrastructure is exempt only because it lives entirely under `tests/` and is
never shipped with a skill.

*Rationale: INSTALL.md tells users to wire `skills/` into their agent, and skills are
routinely copied individually. A cross-skill import turns a working copy into a
`ModuleNotFoundError` at the moment of use.*

### IV. Fail Closed

Malformed, empty, or partial input MUST NEVER yield a passing verdict.

- Missing required fields MUST be reported as missing, never defaulted to zero or empty.
- Unknown keys MUST be rejected, never ignored — a typo that reads as an omission is the
  worst failure mode a completeness checker can have.
- An empty collection (no outcomes, no studies, no checklist items) MUST report failure,
  not vacuous success.
- Input malformation and method violation MUST be distinguishable by exit code, so a
  caller can tell "you gave me garbage" from "your review is wrong".

*Rationale: a gate that passes on absence of evidence inverts its own purpose. This rule
already governs `review_units.py`, which refuses `VERIFIED` on a citation-less units map;
it is generalized here to every gate.*

### V. Humans Where LLMs Are Weak (NON-NEGOTIABLE)

Where the published evidence shows LLM performance is inadequate for a task, this
repository MUST require human confirmation rather than automate it.

This applies at minimum to **risk-of-bias appraisal** (reported LLM accuracy ~0.62 versus
~0.95 for extraction) and to **numeric verification** of effect sizes, sample sizes, and
confidence intervals. For these steps: the agent extracts evidence and MAY propose a
rating, which MUST be marked PROVISIONAL. An appraisal carrying unconfirmed machine
ratings is **not a completed appraisal** and MUST NOT feed downstream certainty grading.

Human gates MUST be tracked separately from automated units and MUST NEVER be
auto-zeroed by any loop, retry, or convergence mechanism.

*Rationale: automating the pipeline's weakest link is precisely how an LLM-assisted review
produces confident, wrong output. The gate is deliberate, and removing it silently would
be a regression in rigor, not an improvement in throughput.*

### VI. Gates Assert Only What Is Mechanically Decidable

A gate MUST verify completeness, internal consistency, and legality under a framework's
own rules. A gate MUST NOT claim that a human judgment was correct.

Every gate MUST document, in its skill, what it cannot check. Examples that MUST be
stated rather than implied:

- PRISMA counts reconciling arithmetically does not make the counts true.
- The presence of a `confirmed_by` field is not proof that a human confirmed anything.
- A legal GRADE downgrade arithmetic does not mean "serious inconsistency" was the right
  call.
- A `verify-sources` PASS means citations are real and not misrepresented — not that the
  argument is sound.

*Rationale: overclaiming what a gate proves is the same failure as an unbacked standards
claim, one level deeper. Stating the limit is what makes the passing verdict trustworthy.*

### VII. AI Provenance Is Recorded

Every substantive AI-performed step — screening, extraction, appraisal, drafting, citation
handling, verification — MUST be stamped with the model, the prompt or skill version, and
any human override, per `steering/ai-research-provenance.md`.

Every completed run MUST emit an `ai-disclosure.md` following PRISMA-trAIce, suitable for
pasting into a methods or acknowledgements section. AI MUST NEVER be listed as an author.

*Rationale: model behaviour changes across versions; a review run on one model and prompt
may not replicate on another. Reporting standards now require the disclosure, and
retrofitting it after the fact produces a reconstruction rather than a record.*

## Standards Alignment & Scope Boundaries

The repository aligns to: **PRISMA 2020** (flow and checklist), **PRISMA-S** (search
reporting), **PRISMA-ScR** (scoping), **PRISMA-P** (protocol), **Cochrane/JBI** review
conduct (dual screening, dual extraction, pre-specified protocol), **RoB 2 / ROBINS-I /
Newcastle-Ottawa / QUADAS-2** (risk of bias), **GRADE** (certainty), **SWiM**
(non-meta-analysis synthesis), and **PRISMA-trAIce / ICMJE** (AI disclosure).

Per Principle I, each entry in that list MUST be traceable to an enforcing artifact or
carry an explicit non-enforcement note.

**Explicit scope exclusions**, which MUST be stated plainly rather than left to inference:

- **No meta-analysis.** No pooled effect sizes, no forest plots, no heterogeneity
  computation. Synthesis follows SWiM. Consequently GRADE's inconsistency and imprecision
  domains are assessed qualitatively, and this MUST be disclosed wherever GRADE output is
  produced.
- **Where GRADE is applied to themes rather than protocol outcomes**, the output MUST be
  labelled as a SWiM adaptation, because certainty keyed to themes is not GRADE as
  published by the GRADE Working Group.
- **Certainty MUST NOT be aggregated across outcomes.** GRADE defines no mean, weighted
  average, or overall certainty across a body of outcomes; producing one is a
  methodological error, not a summary convenience.

## Development Workflow & Quality Gates

- **Branch and review.** Substantive changes land on a feature branch and merge via pull
  request. Method-critical logic (any gate, any standards reference file) MUST NOT be
  committed directly to `main`.
- **Adversarial review.** Pull requests touching gates or standards content are reviewed
  by both available review bots; findings are fixed or explicitly recorded as false
  positives before merge.
- **Tests gate merge.** Every script that can fail a review run MUST have a test module.
  CI MUST run the full suite on push and pull request, and MUST pass before merge.
- **Exit-code uniformity.** All gates share one contract: `0` clean or non-strict, `1`
  method violation under `--strict`, `2` malformed input. Divergence requires an
  amendment.
- **Artifact generation over hand-authoring.** Where a gate consumes a structured input,
  that input is the source of truth and the human-readable artifact is **generated** from
  it. Hand-maintaining both invites the two to disagree.

## Governance

This constitution supersedes conflicting practice elsewhere in the repository. Where a
skill's instructions contradict a principle here, the principle governs and the skill is
a defect to be fixed.

**Amendment procedure.** Amendments require: a written rationale, a version bump per the
policy below, an update to the Sync Impact Report at the head of this file, and
propagation to any template, skill, or document the amendment invalidates. An amendment
that weakens Principle II or Principle V — both marked NON-NEGOTIABLE — requires explicit
maintainer approval recorded in the pull request, not merely a passing review.

**Versioning policy.** MAJOR for backward-incompatible governance changes or removal or
redefinition of a principle; MINOR for a new principle or materially expanded guidance;
PATCH for clarifications and wording that do not change meaning.

**Compliance review.** Every pull request MUST verify compliance with the principles it
touches. The `/speckit-plan` Constitution Check gate is the enforcement point for planned
work; reviewers are the enforcement point for unplanned work. Added complexity MUST be
justified against Principle II and Principle III specifically, as those are the two most
commonly eroded by convenience.

**Version**: 1.1.0 | **Ratified**: 2026-07-26 | **Last Amended**: 2026-07-26
