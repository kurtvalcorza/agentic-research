# Phase 0 Research: Standards Enforcement Parity

No `NEEDS CLARIFICATION` markers survived specification — the design forks were resolved in
conversation and recorded in the spec's Clarifications section. This document records the
decisions, why each was taken, and what was rejected, so a reviewer can audit the reasoning
without reconstructing it.

---

## D-001 — Enforcement architecture: sibling scripts

**Decision**: Each new check is a standalone script inside the skill that owns the methodology it
enforces, structurally mirroring the existing `prisma_flow.py`.

**Rationale**: The repository is consumed by pointing an agent at `skills/`, and individual skill
directories are routinely copied out. A check that lives beside its own guidance stays usable in
that mode. Replicating an already-trusted pattern also means reviewers recognise the shape.

**Alternatives considered**:

- *Shared validation core with thin per-skill CLIs.* Rejected: it directly violates constitution
  Principle III. Copying `validate-evidence/` alone would produce a script that raises
  `ModuleNotFoundError` at the moment of use.
- *One unified `standards_check.py` with subcommands.* Rejected as the primary structure — it
  contradicts "each skill ships its own backend" and rewires working code. Its one genuinely good
  property, a natural home for cross-artifact checks, is preserved by D-005 instead.

---

## D-002 — Accept helper duplication; enforce consistency by test

**Decision**: Input coercion, JSON loading, and verdict formatting are reimplemented in each
script with identical semantics. A test asserts that all four behave the same on the same inputs.

**Rationale**: This is the unavoidable cost of D-001, roughly forty lines. Duplication that is
pinned by a cross-script conformance test cannot silently drift, which is the failure mode that
makes duplication dangerous.

**Alternatives considered**: extracting a shared module (rejected, see D-001); tolerating drift
(rejected — four checks with subtly different notions of "malformed" would be worse than one
inconsistent check).

---

## D-003 — `unittest` rather than `pytest`

**Decision**: Standard-library `unittest`, discovered with `python -m unittest discover -s tests`.

**Rationale**: Constitution Principle II forbids introducing a dependency, and explicitly extends
that to development tooling. A suite requiring `pip install pytest` breaks the "works with nothing
installed" promise that is the repository's adoption path.

**Alternatives considered**: `pytest` (rejected — better ergonomics do not outweigh a mandatory
install); a hand-rolled runner (rejected — reinvents `unittest` with less capability).

---

## D-004 — Structured record is the source; the artifact is generated

**Decision**: Each check consumes a JSON record and emits both the verdict and the human-readable
Markdown artifact. Nothing is authored twice.

**Rationale**: `prisma_flow.py` already works this way, emitting the Mermaid diagram alongside its
reconciliation, so this extends a proven convention. Hand-maintaining a record and a parallel
Markdown table guarantees they eventually disagree, and the disagreement would be invisible.

**Alternatives considered**:

- *Parse the Markdown the skills already emit.* Rejected: table parsing is brittle, and the check
  would fail on formatting drift rather than on real method errors. False alarms erode trust in a
  gate faster than missing checks do.
- *Author both by hand.* Rejected for the divergence reason above.

---

## D-005 — Traceability by command-line path, inside the certainty check

**Decision**: `grade_profile.py` accepts `--rob <path>`; when any domain declares a confirmed
appraisal basis, every referenced study must resolve in that file. Declaring a confirmed basis
without supplying the path fails under `--strict`.

**Rationale**: Placing this in the verification loop instead would mean a standalone run of the
certainty check passes happily on a fabricated basis claim — the check would only bite at the very
end, long after the error was introduced. Reading a caller-supplied path is not an import, so
Principle III is preserved.

**Alternatives considered**: implementing it in `review_units.py` (rejected as above — too late to
be useful); importing the appraisal module (rejected — violates Principle III).

---

## D-006 — Exact study-identifier matching; duplicates rejected

**Decision**: Identifiers match by exact comparison with no case or whitespace normalisation. A
repeated identifier within one record is malformed input.

**Rationale**: Silent reconciliation of near-misses is precisely the behaviour Principle IV
forbids. A reviewer who typed `p1` where the appraisal says `P1` should be told, not
accommodated. A duplicated identifier makes every reference to it ambiguous, so it cannot be
resolved at all.

**Alternatives considered**: case-insensitive trimmed matching (rejected — two genuinely distinct
identifiers could collide); DOI-based matching (rejected — appraisal applies to a specific assessed
result, and one paper may yield several, so a DOI is not a unique key).

---

## D-007 — Record format versioning is mandatory

**Decision**: Every record declares its format version. A missing or unrecognised version is
malformed input, never assumed to be current.

**Rationale**: These records are a public contract that reviewers hand-author, and the repository
sells reproducibility. Defaulting an absent version to "current" would mean that the day the
format changes, every previously authored record is silently misread rather than rejected.

**Alternatives considered**: optional version defaulting to current (rejected for the silent-misread
reason); no versioning (rejected — weakens the reproducibility claim the repository makes).

---

## D-008 — Body-level risk-of-bias judgment is checked against its studies

**Decision**: Flag a body-level judgment contradicted by the distribution of confirmed per-study
ratings — for example no downgrade applied where high-risk studies predominate — permitted only
with a recorded justification.

**Rationale**: The alternative leaves a genuinely decidable error class unchecked: a profile
claiming no risk-of-bias concern over a predominantly high-risk body would pass, and that is
exactly what a methodological reviewer notices first. Handling it as "flag unless justified"
reuses the pattern already chosen for a deviating starting level, so the record format stays
internally consistent rather than growing a second override style.

**Alternatives considered**: presence and confirmation only (rejected — misses the error class);
advisory-only warning (rejected — a warning nothing acts on approximates no check, and it would
make this the sole rule with its own severity tier).

---

## D-009 — Which review types require a confirmed appraisal basis

**Decision**: Systematic and umbrella reviews must use confirmed appraisals. Rapid reviews may use
the heuristic basis when the streamlined method is disclosed in the record. Scoping and narrative
reviews do not grade certainty, so the rule does not apply.

**Rationale**: This mirrors the review-type table already in `design-review-protocol`, which
defines rapid reviews as legitimately streamlined provided shortcuts are stated. Requiring
confirmation everywhere would contradict the repository's own definition of a rapid review.
Umbrella reviews are held to the strict rule because they report certainty inherited from the
reviews they synthesise.

**Alternatives considered**: confirmation required for every certainty-grading review (rejected —
makes rapid reviews impractical and contradicts an existing skill); confirmation required only for
systematic (rejected — lets umbrella reviews rest their inherited certainty on estimation).

---

## D-010 — Certainty may be keyed to outcomes or to themes, declared explicitly

**Decision**: The record declares `synthesis_mode` as either outcome-keyed (true GRADE, per the
protocol's stated outcomes) or theme-keyed (a SWiM adaptation). The generated profile is labelled
accordingly.

**Rationale**: GRADE as published rates certainty per outcome, but this repository's synthesis
skills are built on themes throughout. Forcing outcomes would invalidate the vocabulary across
several skills for no methodological gain, while silently grading themes and calling it GRADE
would be an unlabelled deviation. Declaring the mode makes the adaptation visible to the reader,
which is the actual requirement.

**Alternatives considered**: outcomes only (rejected — large rewrite of unrelated skills); themes
only without labelling (rejected — an undisclosed deviation from the published framework).

---

## D-011 — Test modules load scripts via `importlib`

**Decision**: `tests/_load.py` loads each script by file path using
`importlib.util.spec_from_file_location`.

**Rationale**: Scripts live in directories such as `appraise-risk-of-bias`, which is not a legal
Python module name, and the skill directories deliberately contain no `__init__.py`. Path-based
loading sidesteps both without adding packaging metadata that would only exist to serve tests.

**Alternatives considered**: adding `__init__.py` files and renaming directories (rejected — would
break every documented skill path for the sake of tests); manipulating `sys.path` per test
(rejected — order-dependent and fragile across platforms).

---

## D-012 — Network isolation by patching `urlopen`

**Decision**: Tests for the two network-dependent scripts patch `urllib.request.urlopen` within
the module under test.

**Rationale**: Both scripts funnel every request through a single `_get()` helper, so one patch
point covers each completely. Patching at the `urlopen` level rather than at `_get` means an
unmocked code path raises rather than silently reaching the network, which turns "no network in
tests" from a convention into an enforced property.

**Alternatives considered**: patching `_get` (rejected — a new call path bypassing `_get` would
hit the network unnoticed); recorded HTTP fixtures on disk (rejected — added complexity and a
dependency-shaped abstraction for two simple JSON endpoints).

---

## D-013 — Reporting checklist items are referenced, not reproduced

**Decision**: The checklist record and generated artifact identify items by their official number
and a short topic label (for example, item 7, "Search strategy"), and cite the source publication.
Full official item wording is not reproduced in the repository.

**Rationale**: This keeps the artifact useful — a journal wants to see item numbers mapped to
manuscript locations — while avoiding wholesale reproduction of a third party's published
instrument. The generated checklist links to the source so a reader can consult the authoritative
wording.

**Alternatives considered**: embedding the full item text (rejected — unnecessary reproduction when
numbers plus labels serve the purpose); numbers only without labels (rejected — unusable without
the source open alongside).

---

## D-014 — Imprecision guidance reconciled to a single rule

**Decision**: Judgement rests primarily on the confidence interval relative to the decision
threshold and on optimal information size. Absolute participant and event thresholds are retained
only as an explicitly labelled fallback when interval data is unavailable.

**Rationale**: The two existing reference files contradict each other on exactly this point, one
presenting absolute thresholds as primary indicators and the other as a crude fallback. A check
cannot enforce a rule the guidance states two ways. The fallback framing is the methodologically
correct one and is therefore the survivor.

**Alternatives considered**: absolute thresholds as primary (rejected — methodologically wrong);
removing the fallback entirely (rejected — narrative syntheses frequently lack pooled intervals,
and leaving no guidance would push assessors toward inventing one).

---

## D-015 — Starting level derives from the predominant design

**Decision**: The declared starting level must be consistent with the design that predominates in
the body of evidence; deviation requires a recorded justification.

**Rationale**: The current guidance starts the entire body at the highest level whenever any single
randomized study is present, so one randomized trial among eight cross-sectional studies would
start the body at high certainty. GRADE assesses a body of evidence, so the predominant design is
the correct anchor. Judgement legitimately departs from a mechanical rule, hence the justification
escape hatch rather than a hard constraint.

**Alternatives considered**: preserving the any-randomized rule (rejected — the defect being
fixed); a strict rule with no deviation (rejected — GRADE explicitly permits judgement here).

---

## D-016 — Aggregate certainty is made unrepresentable

**Decision**: A record containing an overall or aggregate certainty key is rejected as malformed
input.

**Rationale**: The existing guidance computes a weighted mean of certainty across themes, which the
framework does not define. Deleting the worked example would remove the instruction but not the
possibility; rejecting the key removes the possibility. This is the difference between guidance
that discourages an error and a format in which the error cannot be expressed.

**Alternatives considered**: deleting the guidance only (rejected — leaves the door open); accepting
the key with a warning (rejected — a warning legitimises the concept).

---

## D-017 — Continuous integration matrix

**Decision**: GitHub Actions runs the suite on push and pull request against Python 3.11 and 3.12.

**Rationale**: The repository already contains a 3.11 bytecode artifact and local development is on
3.12.10, so those two bracket real usage. No install step is needed, making the job a checkout, a
runtime setup, and a discovery command.

**Alternatives considered**: single-version CI (rejected — cheap insurance against version-specific
behaviour); adding 3.13 (deferred — no evidence of use, and the matrix can grow later).

---

## D-018 — One exit-code contract across all four checks

**Decision**: `0` clean or non-enforcing, `1` method violation under `--strict`, `2` malformed
input.

**Rationale**: `prisma_flow.py` already uses exactly this, so three of the four values are already
established convention. Separating malformed input from method violation lets a caller distinguish
"your record is unreadable" from "your review is incomplete", which demand different responses —
and lets the verification loop treat only the latter as outstanding work.

**Alternatives considered**: a single non-zero failure code (rejected — collapses the distinction
the loop depends on); per-check codes (rejected — no caller benefit, and it defeats uniform wiring).

---

## D-019 — Numeric strings are rejected; `prisma_flow.py` is aligned to the stricter rule

**Decision**: A quoted count such as `"3"` is malformed input across all four checks. This changes
`prisma_flow.py`, which currently accepts it.

**Rationale**: The two existing scripts already disagree — `prisma_flow.py` coerces via
`int(str(v).strip())`, while `review_units.py` rejects non-numbers outright with the comment that a
wrong type must fail closed. One of the two has to move for the shared contract to be real.
Principle IV settles the direction: a quoted count in a hand-authored record is far more likely to
be a mistake than an intention, and silent coercion is the behaviour the principle forbids.

**Risk**: this is a behavioural change to shipped, working code, not a clarification. It is low
impact — JSON counts are naturally unquoted and no record in the repository uses quoted counts —
but it is called out in the pull request as its own change rather than absorbed into the new work,
per the spec's rule on pre-existing defects surfaced by new coverage.

**Alternatives considered**: aligning `review_units.py` to the permissive behaviour (rejected —
moves the codebase away from fail-closed to preserve a laxness nothing depends on); documenting
the divergence and leaving both (rejected — the shared contract would then be fiction, and the
conformance test could not exist).

## D-020 — `prisma_flow.py` gets the shared closed schema too

**Decision**: The flow record requires `schema_version` and rejects unknown keys, like the other
three. This is the second behavioural change to `prisma_flow.py` in this feature.

**Rationale**: `cli-contract.md` says it binds all four checks and that "a check that deviates is
non-conforming regardless of whether its own rules are correct", and FR-028 and FR-044 say *all*
checks and *every* structured record. The flow check enforced neither rule, so a record could
carry `"recrods_screenedd": 999`, drop that count silently, reconcile over what remained, and
print an authoritative ✅ over a number nobody had checked — the exact fail-open the unknown-key
rule exists to prevent, in the artifact the README leads with. It was missed because the flow
check was the one check with no contract document, so nothing executed its example and nothing
compared it against the shared rules.

**Risk**: a second behavioural change to shipped, working code, and a larger one than D-019 —
every existing flow record needs `"schema_version": "1.0"` added. Called out in the pull request
as its own change, per the same rule. The repository contains three flow records (a docstring
example and two test modules); all were updated.

**A second, smaller fail-open found while closing the first**: every reconciliation edge was
guarded by truthiness, so a count recorded as `0` was indistinguishable from one omitted. A record
stating 500 identified, 96 removed and `records_screened: 0` disabled three edges and reconciled
clean. Edges are now checked on key PRESENCE, which is only decidable because the key set is
closed — before that, an unknown key and an absent one looked the same.

**Consequence**: `contracts/prisma-flow.md` now exists, so the flow record is covered by
`tests/test_contract_examples.py` like the other three. That is the durable half of this decision
— the divergence survived because the check's schema lived in a docstring that nothing ran.

**Alternatives considered**: leaving the flow check permissive and narrowing the contract's "all
four checks" claim (rejected — the contract would be describing a rule the repository does not
follow, and `tests/test_coercion_conformance.py` exists precisely so shared rules cannot be
aspirational); enforcing unknown keys but not the version (rejected — half a schema is not a
closed one, and FR-044 is not conditional).
