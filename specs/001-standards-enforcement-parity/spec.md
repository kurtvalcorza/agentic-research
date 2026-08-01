# Feature Specification: Standards Enforcement Parity

**Feature Branch**: `001-standards-enforcement-parity`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "Standards enforcement parity — give GRADE, risk-of-bias, and the PRISMA 2020 checklist the same machine-checkable enforcement that the PRISMA flow diagram already has, and fix the methodological errors those gates would otherwise enforce. Tests are explicitly requested."

## Context

The suite claims alignment to PRISMA 2020, Cochrane review conduct, and GRADE. Only one of
those claims is currently enforced: the PRISMA flow diagram is assembled from recorded
counts and refuses to pass when the arithmetic does not reconcile. Certainty grading and
risk-of-bias appraisal are guidance documents that an agent applies by judgment, with no
check that the judgment was complete or even legal under the framework's own rules.

Three consequences follow, and this feature addresses all three:

1. **Unenforced standards.** The verification loop declares a unit for certainty grading
   defined only as "not yet graded", and a human-confirmation gate that is asserted by hand
   rather than computed from any artifact. Neither can fail for the right reason.
2. **Erroneous guidance that a gate would cement.** The certainty-grading reference material
   instructs practices the framework does not define — averaging certainty across results to
   produce a single "overall" rating, rating individual papers rather than a body of
   evidence, and starting the whole body at the highest level whenever any single randomized
   study is present. Two reference files in the same skill contradict each other on how
   imprecision is judged. Building a checker around this guidance would make the errors
   authoritative rather than incidental.
3. **An unbacked public claim.** The project's standards table asserts PRISMA 2020 "flow +
   checklist" while no checklist artifact exists anywhere in the repository, and its table of
   runnable checks omits the very script that decides whether a review is verified.

**Tests are explicitly requested for this feature.** The default task template treats tests
as optional; the project constitution requires that every check capable of failing a review
run has automated coverage. This request satisfies that override.

## Clarifications

### Session 2026-07-26

- Q: How should a study referenced in the certainty record be matched to its entry in the appraisal record? → A: Exact string match on the declared study identifier; a duplicate identifier within one record is malformed input.
  - **Superseded during implementation review.** The answer was right about exact matching and wrong about identity. RoB 2 and ROBINS-I appraise a *result*, so a study contributing to two outcomes carries two appraisals, and keying on the study identifier made the correct representation inexpressible. Matching is on `(study identifier, result assessed)`; only a repeated *pair* is malformed. See FR-042 and [contracts/risk-of-bias.md](contracts/risk-of-bias.md#identity-study-result-not-study).
- Q: Should the record formats carry a schema version? → A: Yes — a version field is required, and a record with no version or an unrecognised version is rejected.
- Q: Should the body-level risk-of-bias judgment be compared against the per-study ratings? → A: Yes — flag a body-level judgment contradicted by the per-study distribution, permitted only when a justification is recorded.
- Q: Which review types must use human-confirmed appraisal rather than the heuristic fallback? → A: Systematic and umbrella require confirmed; rapid may use the heuristic when the shortcut is disclosed; scoping and narrative do not grade certainty.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Certainty grading that cannot be incomplete or illegal (Priority: P1)

A reviewer has finished synthesis and needs to record how certain the evidence is for each
result. Today they follow prose guidance and produce a narrative rating; nothing detects that
they forgot a required domain, that their rating arithmetic does not add up, or that they
applied a move the framework does not permit. They want the same treatment the flow diagram
already gets: record the judgments, run a check, and be told exactly what is wrong before the
review reaches a reader.

**Why this priority**: This is the largest gap and the one with the most consequential failure
mode — a certainty rating is the single claim a reader trusts most, and an incomplete or
illegally-derived rating is indistinguishable from a sound one in prose. It also subsumes the
correctness work, because a check cannot be built around guidance that is itself wrong.

**Independent Test**: Fully testable by recording a set of certainty judgments containing a
known defect (a missing domain, arithmetic that does not add up, an aggregate rating across
results) and confirming each is reported with its specific discrepancy, while a sound set
passes. Delivers value alone: certainty grading becomes verifiable even if nothing else in
this feature ships.

**Acceptance Scenarios**:

1. **Given** a certainty record where one of the five required downgrade domains is absent,
   **When** the check runs, **Then** it reports the missing domain by name and does not treat
   the omission as a judgment of "no concern".
2. **Given** a certainty record whose declared final rating does not equal its starting level
   adjusted by its recorded downgrades and upgrades, **When** the check runs, **Then** it
   reports the exact arithmetic discrepancy.
3. **Given** a certainty record that raises certainty for a reason outside the three the
   framework permits, **When** the check runs, **Then** the record is rejected.
4. **Given** a certainty record attempting to express a single aggregate certainty across
   multiple results, **When** the check runs, **Then** the record is rejected as malformed,
   because the framework defines no such aggregate.
5. **Given** a body of evidence in which randomized studies are a minority, **When** the
   starting level is declared as if the body were predominantly randomized without a stated
   justification, **Then** the check reports the inconsistency.
6. **Given** a sound and complete certainty record, **When** the check runs, **Then** it emits
   the evidence profile and a summary-of-findings table, labelled with whether certainty was
   keyed to protocol outcomes or to synthesis themes.

---

### User Story 2 - Risk-of-bias appraisal that is verifiably complete and human-confirmed (Priority: P2)

A reviewer appraises each included study for risk of bias using the instrument appropriate to
its design, and a human must confirm every rating before it influences certainty. Today the
instruments exist only as prose, so nothing catches an instrument applied to the wrong design,
a missing domain, a value that instrument does not define, or a rating that reached certainty
grading without ever being confirmed by a person.

**Why this priority**: Appraisal is the pipeline's designated human gate and the input that
drives one of the five certainty domains. Without it, the certainty check from Story 1 has to
trust an unverified input. It ranks below Story 1 only because Story 1 delivers value even
while appraisal input remains unverified.

**Independent Test**: Scenarios 1–4 are fully testable alone — record appraisals containing a
design/instrument mismatch, a missing domain, an out-of-vocabulary value, and an unconfirmed
study, and confirm each is reported. That portion delivers value by itself, making appraisal
completeness checkable regardless of what consumes it.

**Dependency, stated rather than implied**: scenarios 5–8 are traceability and coherence, and they
exercise the certainty check from User Story 1. They cannot be tested until that check exists. The
story is therefore independently *valuable* but only partially independently *testable*, and the
two halves should be reviewed as separate increments.

**Acceptance Scenarios**:

1. **Given** a study whose design and chosen instrument do not correspond, **When** the check
   runs, **Then** the mismatch is reported.
2. **Given** an appraisal missing one of its instrument's domains, or carrying a value that
   instrument does not define, **When** the check runs, **Then** the defect is reported with
   the domain named.
3. **Given** an appraisal whose declared overall judgment is more favourable than its worst
   domain without a stated justification, **When** the check runs, **Then** the inconsistency
   is flagged.
4. **Given** studies lacking a recorded human confirmation, **When** the check runs, **Then**
   the count of unconfirmed studies is reported as an outstanding human gate.
5. **Given** a certainty record that claims its risk-of-bias domain rests on confirmed
   appraisals, **When** the referenced studies cannot be resolved to confirmed appraisals,
   **Then** the discrepancy is reported.
6. **Given** a certainty record claiming confirmed appraisals as its basis but supplying no
   appraisal record to check against, **When** the check runs in enforcing mode, **Then** it
   fails rather than accepting the claim on trust.
7. **Given** a body-level risk-of-bias judgment of no concern over studies whose confirmed
   ratings are predominantly high risk, **When** the check runs without a recorded
   justification, **Then** the contradiction is flagged.
8. **Given** a referenced identifier differing from the appraised one only in case or
   surrounding whitespace, **When** the check runs, **Then** it is reported as unresolved rather
   than matched.

---

### User Story 3 - Reporting completeness that can be demonstrated (Priority: P3)

A reviewer preparing a manuscript for submission must show that every required reporting item
has been addressed, and journals ask for this as a completed checklist. Today the project
claims to support this and provides nothing that produces it.

**Why this priority**: It removes a public, verifiable overclaim and produces an artifact
journals actually request. It ranks below Stories 1 and 2 because an absent checklist is a
reporting inconvenience, whereas an unsound certainty rating is a methodological error.

**Independent Test**: Fully testable by recording item-to-location mappings with some items
unaddressed, and confirming the completed checklist is produced with the unaddressed items
listed explicitly. Delivers value alone as a submission artifact.

**Acceptance Scenarios**:

1. **Given** a record mapping each required reporting item to its location in the manuscript,
   **When** the check runs, **Then** a completed checklist is produced.
2. **Given** items that are neither located nor justified as not-applicable, **When** the check
   runs, **Then** those items are listed and the check fails in enforcing mode.
3. **Given** an item marked not-applicable with a stated justification, **When** the check runs,
   **Then** it is accepted and the justification appears in the output.
4. **Given** a scoping review, **When** the check runs, **Then** the check REFUSES with exit 2
   and names PRISMA-ScR as untranscribed, rather than approximating it or falling back to the
   systematic-review set. See the note under FR-022.

---

### User Story 4 - A verification loop that will not declare an unfinished review verified (Priority: P4)

A reviewer runs the verification loop to reach a defensible end state. The loop must not report
a review as verified while its certainty grading is incomplete, its appraisals are unconfirmed,
or its reporting checklist has gaps — and it must not silently skip a check that was never
recorded.

**Why this priority**: This turns three standalone checks into a gate on the review as a whole.
It depends on Stories 1–3 existing, so it follows them.

**Independent Test**: Fully testable by presenting the loop with a review record that omits an
applicable check and confirming it reports the omission rather than passing.

**Acceptance Scenarios**:

1. **Given** a systematic review whose record omits an applicable check, **When** the loop
   evaluates it, **Then** the omission is reported as missing and the review cannot be declared
   verified.
2. **Given** outstanding certainty, traceability, or reporting defects, **When** the loop
   evaluates the review, **Then** it continues rather than declaring verification.
3. **Given** a narrative review to which reporting checklists and appraisal do not apply,
   **When** the loop evaluates it, **Then** those checks are treated as out of scope rather than
   as zero-to-achieve.
4. **Given** appraisals awaiting human confirmation, **When** the loop runs any number of cycles,
   **Then** the human gate is never automatically satisfied.

---

### User Story 5 - Checks that are themselves trustworthy (Priority: P5)

A maintainer changing any check needs confidence that it still behaves correctly, and a
contributor needs that verified automatically rather than by memory.

**Why this priority**: Enforcement is only as credible as the enforcers. It ranks last because
it protects the other stories rather than delivering reviewer-facing capability, but the
feature is not complete without it.

**Independent Test**: Fully testable by running the automated suite against every check and
confirming it passes, and by confirming the suite runs automatically when changes are proposed.

**Acceptance Scenarios**:

1. **Given** any check capable of failing a review run, **When** the suite runs, **Then** that
   check has coverage of both its passing and its failing paths.
2. **Given** a proposed change, **When** it is submitted for review, **Then** the suite runs
   automatically and its result is visible before merge.
3. **Given** a machine with no project dependencies installed, **When** the suite is run,
   **Then** it executes without any installation step.
4. **Given** checks that consult external bibliographic services, **When** the suite runs,
   **Then** no network request is made.

---

### Edge Cases

- **Empty collections.** A certainty record with no results, an appraisal record with no
  studies, or a checklist with no items MUST report failure rather than vacuous success.
- **Unrecognised fields.** A misspelled domain name MUST be rejected outright rather than
  silently read as an absent domain — a typo that reads as an omission is the worst failure
  mode a completeness check can have.
- **Non-integer and boolean counts.** Values that are not whole non-negative numbers MUST be
  rejected rather than coerced.
- **Malformed input versus method violation.** A caller MUST be able to distinguish "the record
  you supplied is unreadable" from "your review is incomplete or wrong", because the two demand
  different responses.
- **Provisional risk-of-bias basis.** A certainty record resting on estimated rather than
  confirmed appraisals MUST be marked provisional in its output, and MUST NOT pass in enforcing
  mode for a review type that requires appraisal.
- **Review types without certainty grading.** Scoping and narrative reviews MUST NOT be required
  to produce certainty records they legitimately do not have.
- **Pre-existing defects surfaced by new coverage.** Writing first-time coverage for existing
  checks may reveal existing faults; each MUST be raised individually rather than folded
  silently into this work.
- **Near-miss study identifiers.** An identifier differing only in case or surrounding
  whitespace MUST be reported as an unresolved reference, never quietly matched.
- **Repeated appraisal identity.** The same `(study identifier, result assessed)` pair appearing
  twice within one appraisal record MUST be rejected, since it makes every reference to it
  ambiguous. A repeated study identifier alone MUST NOT be rejected — that is how a study
  contributing to two results is represented — but the study's declared design MUST agree across
  its appraisals. In a certainty record, the ambiguity is a study identifier repeated within a
  single result, which MUST be rejected.
- **Missing or unrecognised record version.** A record with no declared format version, or one
  the check does not recognise, MUST be rejected as unreadable rather than assumed current.
- **Body-level judgment contradicting its own studies.** A body rated as having no risk-of-bias
  concern while the confirmed ratings beneath it are predominantly high risk MUST be flagged
  unless a justification is recorded.

## Requirements *(mandatory)*

### Functional Requirements

**Certainty grading**

- **FR-001**: The system MUST verify that every result carries all five required downgrade
  domains, and MUST report an absent domain as missing rather than as a judgment of no concern.
- **FR-002**: The system MUST reject any domain judgment outside the permitted set of
  whole-step values; partial steps MUST NOT be representable.
- **FR-003**: The system MUST verify that the declared final certainty equals the starting
  level adjusted by recorded downgrades and upgrades, bounded to the framework's range, and
  MUST report the exact discrepancy on mismatch.
- **FR-004**: The system MUST verify that the declared starting level is consistent with the
  predominant study design in the body of evidence, permitting deviation only when an explicit
  justification is recorded.
- **FR-005**: The system MUST permit certainty to be raised only when the body of evidence is
  non-randomized, the result's declared starting level is below the maximum, and no downgrade has
  been applied. The declared level is a separate bar because a recorded justification may move it
  (FR-004): a body already declared at the maximum can absorb an upgrade into the ceiling, and a
  randomized body declared *below* the maximum must not be raised back up on that account.
- **FR-006**: The system MUST restrict reasons for raising certainty to the three the framework
  defines, so that any other reason is unrepresentable.
- **FR-007**: The system MUST reject any attempt to express a single aggregate certainty across
  multiple results.
- **FR-008**: The system MUST require each certainty record to declare whether certainty is
  keyed to protocol outcomes or to synthesis themes, and MUST label its output accordingly.
- **FR-009**: The system MUST require each certainty record to declare whether its risk-of-bias
  domain rests on confirmed appraisals or on estimation, and MUST mark estimation-based output as
  provisional. In enforcing mode it MUST refuse an estimation basis for **systematic** and
  **umbrella** reviews; it MUST permit an estimation basis for **rapid** reviews only when the
  streamlined method is disclosed in the record. Scoping and narrative reviews do not grade
  certainty, so the requirement does not apply to them.
- **FR-010**: The system MUST produce, from a valid certainty record, both an evidence profile
  and a summary-of-findings presentation suitable for a manuscript.

**Risk-of-bias appraisal**

- **FR-011**: The system MUST verify that the appraisal instrument applied to each study
  corresponds to that study's design.
- **FR-012**: The system MUST verify that every domain defined by the applied instrument is
  present and carries a value that instrument defines.
- **FR-013**: The system MUST flag a declared overall judgment more favourable than the study's
  worst domain unless an explicit justification is recorded.
- **FR-014**: The system MUST require a recorded human confirmation for every study, and MUST
  report the count of appraisals lacking one.
- **FR-015**: The system MUST state plainly, wherever human confirmation is checked, that the
  check establishes the presence of a confirmation record and not its authenticity.
- **FR-016**: The system MUST produce, from a valid appraisal record, a per-study summary and a
  visual per-domain summary suitable for a manuscript.

**Traceability between appraisal and certainty**

- **FR-017**: When a certainty record claims confirmed appraisals as its risk-of-bias basis, the
  system MUST verify that every referenced study resolves to a confirmed appraisal, and MUST
  report those that do not.
- **FR-018**: The system MUST treat a claim of confirmed appraisals unaccompanied by an
  appraisal record as a failure in enforcing mode, rather than accepting the claim on trust.
- **FR-019**: Traceability MUST be established by data supplied to the check at invocation,
  never by one skill depending on the internals of another, so that any skill remains usable in
  isolation.
- **FR-042**: Study identifiers MUST be matched between records by exact comparison, with no
  normalisation of case or surrounding whitespace, so that a near-miss surfaces as an unresolved
  reference rather than being silently reconciled. Uniqueness is required of whatever constitutes
  identity in each record: in an appraisal record that is the pair of study identifier and the
  result assessed, so the same pair appearing twice MUST be rejected as malformed input while the
  same study appraised for two different results MUST be accepted; in a certainty record it is the
  study identifier within a single result. A study identifier alone repeating across an appraisal
  record is therefore not an error, but that study's declared design MUST agree across all of its
  appraisals, since design is a property of the study and only the judgment varies by result.
- **FR-043**: The system MUST flag a body-level risk-of-bias judgment that is contradicted by
  the distribution of confirmed per-study ratings it rests on — for example, no downgrade applied
  to a body in which high-risk studies predominate — and MUST permit it only when an explicit
  justification is recorded, consistent with how a deviating starting level is handled.

**Reporting completeness**

- **FR-020**: The system MUST verify that every required reporting item is either located in the
  manuscript or justified as not applicable, and MUST list those that are neither.
- **FR-021**: The system MUST produce a completed reporting checklist as a submission-ready
  artifact.
- **FR-022**: The system MUST apply the reporting-item set appropriate to the review type,
  including the variant used for scoping reviews.

  > **Deliberately unenforced for scoping reviews, and the check says so.** The PRISMA-ScR item
  > table has not been transcribed, and the three options were: ship an approximation of it,
  > silently fall back to the systematic-review table, or refuse. The first two would produce a
  > completed-looking checklist for items nobody had checked, so the check REFUSES — exit 2, no
  > artifact, naming what is missing. Recorded here because a requirement that reads as built when
  > it is not is exactly the overclaim this specification exists to prevent. See
  > `contracts/prisma-checklist.md` and the README's ⚠️ row.

**Verification loop**

- **FR-023**: The verification loop MUST derive its outstanding-work count for certainty
  grading, appraisal traceability, and reporting completeness from the corresponding checks
  rather than from hand-entered assertions.
- **FR-024**: The verification loop MUST treat an applicable check that is absent from a
  review's record as missing, and MUST NOT declare the review verified.
- **FR-025**: The verification loop MUST resolve which checks apply from the review type, so
  that checks which legitimately do not apply are absent rather than outstanding.
- **FR-026**: The verification loop MUST NEVER automatically satisfy a human confirmation gate.

**Shared behaviour across all checks**

- **FR-027**: All checks MUST share one outcome contract distinguishing a clean result, a method
  violation under enforcement, and unreadable input.
- **FR-028**: All checks MUST reject unrecognised fields rather than ignoring them.
- **FR-029**: All checks MUST report failure on an empty collection rather than passing.
- **FR-030**: Every check MUST document what it cannot verify.
- **FR-044**: Every structured record MUST declare the version of the format it is written in.
  A record carrying no version, or a version the check does not recognise, MUST be rejected as
  malformed input rather than interpreted as the current format, so that a record authored today
  cannot be silently misread by a later version of the check.

**Guidance correctness**

- **FR-031**: Guidance instructing practices the framework does not define — aggregating
  certainty across results, rating individual studies rather than bodies of evidence, and
  deriving the starting level from the presence of a single randomized study — MUST be
  corrected.
- **FR-032**: Where two guidance documents describing the same domain disagree, they MUST be
  reconciled to a single stated rule.
- **FR-033**: Guidance MUST describe structured records as the source of truth and manuscript
  artifacts as generated from them, rather than as parallel documents maintained by hand.
- **FR-034**: Broken internal references in guidance MUST be repaired.

**Public claims**

- **FR-035**: Every standard the project claims MUST be traceable to an enforcing check or carry
  an explicit note that it is not enforced; the reporting-checklist claim MUST become true
  rather than remain aspirational.
- **FR-036**: The project's list of runnable checks MUST include every such check, including the
  one that decides whether a review is verified.

**Verification of the checks themselves**

- **FR-037**: Every check capable of failing a review run MUST have automated coverage of both
  passing and failing paths.
- **FR-038**: Generated manuscript artifacts MUST have their form pinned by automated coverage,
  so that a change to what reviewers see cannot pass unnoticed.
- **FR-039**: Automated coverage MUST run without any installation step and MUST introduce no
  new dependency.
- **FR-040**: Automated coverage of checks that consult external services MUST NOT make network
  requests.
- **FR-041**: The automated suite MUST run whenever a change is proposed, with its result
  visible before the change is accepted.

### Key Entities

- **Certainty record**: The recorded judgments behind one review's certainty assessment — per
  result: the study identifiers, the predominant design of the body, the declared starting
  level, the five domain judgments with their bases, any raising reasons, and the declared final
  certainty. Declares whether certainty is keyed to outcomes or themes.
- **Appraisal record**: Per included study — its design, the instrument applied, each of that
  instrument's domain judgments, the supporting evidence located in the paper, the declared
  overall judgment, and who confirmed it and when.
- **Reporting record**: Per required reporting item — where it is addressed in the manuscript,
  or the justification for it not applying.
- **Review record**: The outstanding-work counts and human gates for one review, resolved
  against the checks applicable to its review type, from which a verification verdict is
  derived.
- **Generated artifacts**: The evidence profile, summary of findings, per-study and per-domain
  appraisal summaries, and completed reporting checklist — all derived from the records above
  rather than authored independently.

**Identity and versioning rules applying to all records above:**

- Every record declares the version of the format it is written in; an absent or unrecognised
  version makes the record unreadable.
- A study carries a declared identifier, a local label chosen by the reviewer rather than a
  bibliographic one. The identifier alone is **not** the identity of an appraisal: one paper may
  yield several separately appraised results, so an appraisal is identified by the pair of study
  identifier and the result it assesses, and that pair is what must be unique within a record and
  what is matched across records by exact comparison. A study's design, by contrast, belongs to
  the study and must agree across all of its appraisals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every standard the project claims is either backed by a runnable check or carries
  an explicit non-enforcement note — zero unbacked claims remain.
- **SC-002**: A certainty assessment missing any required domain is rejected in 100% of cases;
  silent acceptance of an incomplete assessment is impossible.
- **SC-003**: Aggregate certainty across results cannot be expressed at all, rather than being
  discouraged by guidance.
- **SC-004**: A reviewer can produce a submission-ready reporting checklist from recorded data in
  one step, with every unaddressed item named.
- **SC-005**: A reviewer can produce a summary-of-findings presentation from the same data used
  to check certainty, without re-entering it.
- **SC-006**: 100% of checks capable of failing a review run have automated coverage of both
  passing and failing paths, and that coverage runs on every proposed change.
- **SC-007**: The entire suite of checks and their coverage runs on a machine with nothing
  installed beyond a standard language runtime.
- **SC-008**: A review of a type requiring a given check cannot be reported as verified when that
  check is absent from its record.
- **SC-009**: Every check states what it cannot verify, so that a passing result is never read as
  a broader guarantee than it is.
- **SC-010**: Guidance contains no instruction that contradicts the framework it describes, and
  no two guidance documents give conflicting rules for the same judgment.

## Assumptions

- **Structured records are expressed as JSON**, matching the format the existing flow-diagram
  check already consumes, so reviewers encounter one input convention rather than several.
- **Manuscript artifacts are generated from those records**, not maintained alongside them.
  Guidance describing hand-authored artifacts is updated accordingly.
- **Certainty keyed to themes is retained** as an explicitly labelled adaptation for narrative
  synthesis, rather than removed. Removing it would invalidate the vocabulary used across the
  existing synthesis skills for no methodological gain, provided the adaptation is disclosed.
- **Quantitative pooling remains out of scope.** Synthesis follows a narrative standard, so the
  inconsistency and imprecision domains are judged qualitatively, and checks verify that a
  judgment was recorded and is legal — never that it was numerically derived.
- **Human confirmation is verified by presence, not authenticity.** No cryptographic or identity
  mechanism is introduced; the check confirms a record exists, and the limitation is stated
  wherever it applies.
- **Existing checks may prove faulty** once covered for the first time. Repairing them is in
  scope because they gate review outcomes, but each repair is surfaced individually.
- **Delivery is by feature branch and pull request**, with adversarial review before merge, per
  the project's development workflow.
- **Implementation is phased** — guidance correctness first, then the checks, then loop
  integration and automated coverage — so each phase is independently reviewable.
