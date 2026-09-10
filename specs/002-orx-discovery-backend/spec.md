# Feature Specification: orx Discovery Backend for acquire-corpus

**Feature Branch**: `claude/openresearch-agentic-research-diff-fq5xyi`

**Feature Directory**: `specs/002-orx-discovery-backend`

**Created**: 2026-09-09

**Status**: Draft

**Input**: User description: "Add OpenResearch's `orx discover` as an optional, detect-and-degrade discovery backend for the acquire-corpus skill. Keyless OpenAlex/CrossRef remains the default and only guaranteed path; orx is enrichment only (alphaXiv full-text search, embedding/semantic search, bioRxiv preprints) used when the `orx` binary is present and its daemon is reachable. Must normalize orx's structured JSON discovery results into the existing corpus JSONL schema with defensive parsing (orx is pre-1.0, schema undocumented and unstable). Must never block, error, or prompt when orx is absent. Must record the backend used per query in the PRISMA-S search log, because an orx-augmented search is not reproducible by a reader without orx — omitting that makes the search log misleading. Constitutional constraints: Principle II (keyless stdlib baseline, orx is optional enrichment like the scite MCP), Principle III (acquire-corpus must still run when copied out alone, with no orx present), Principle I (state what the backend cannot verify), Principle VII (provenance stamping of which backend answered)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Wider discovery when OpenResearch is installed (Priority: P1)

A reviewer building a corpus on a machine where OpenResearch is installed and running gets
candidate records that the keyless backends structurally cannot return: full-text matches inside
paper bodies, semantically similar work that shares no keywords with the query, and biology
preprints. These arrive merged into the same candidate set, in the same record shape, and flow
into `dedupe-records` unchanged.

**Why this priority**: This is the entire value of the feature. Keyword search over titles,
abstracts and indexed metadata misses papers whose relevant content sits in the body text, and
misses papers that use different vocabulary for the same construct. Recall is the property a
systematic search is judged on, and this is the only slice that improves it.

**Independent Test**: On a machine with OpenResearch running, run the acquisition step for a
question with known full-text-only exemplars, and confirm those exemplars appear in the candidate
set and are absent from a keyless-only run of the same query.

**Acceptance Scenarios**:

1. **Given** OpenResearch is installed and reachable, **When** the reviewer runs the acquisition
   step, **Then** candidate records from the enriched sources appear in the candidate set in the
   same record shape as keyless records, each tagged with the source that produced it.
2. **Given** OpenResearch is installed and reachable, **When** the enriched search returns records
   already found by the keyless search, **Then** both copies are retained and handed to
   `dedupe-records`, because record-level deduplication is that skill's auditable step and not this
   one's.
3. **Given** OpenResearch becomes unreachable partway through a multi-query acquisition, **When**
   the remaining queries run, **Then** those queries complete against the keyless backends and the
   run finishes successfully with the partial enrichment recorded.

---

### User Story 2 - Identical behaviour when OpenResearch is absent (Priority: P2)

A reviewer on a machine with no OpenResearch — the overwhelming majority of users, and the only
configuration the repository guarantees — runs the same acquisition step and gets today's keyless
result. No error, no prompt, no instruction to install anything, no meaningful delay, and no
mention of a backend they do not have.

**Why this priority**: Principle II makes the keyless path non-negotiable. A feature that produces
a warning, a stall, or a degraded exit code on the default configuration has broken the
repository's central promise ("point your agent at `skills/` and it works") in exchange for an
enhancement most users cannot use.

**Independent Test**: Run the acquisition step in an environment where the OpenResearch binary is
absent from the executable search path, and diff the resulting candidate set and exit code against
the pre-feature behaviour for the same query.

**Acceptance Scenarios**:

1. **Given** OpenResearch is not installed, **When** the reviewer runs the acquisition step,
   **Then** the candidate set is identical to the pre-feature keyless result and the exit code is
   unchanged.
2. **Given** OpenResearch is not installed, **When** the acquisition step runs, **Then** no output
   stream carries an error, a warning, or a suggestion to install OpenResearch.
3. **Given** the OpenResearch binary is present but its service is not running, **When** the
   acquisition step runs, **Then** the run proceeds keyless without stalling on a connection
   attempt.
4. **Given** OpenResearch is installed and reachable, **When** the reviewer explicitly requests a
   keyless-only search, **Then** the enriched backend is not consulted and the search log records
   the search as keyless.

---

### User Story 3 - A search log that discloses what a reader cannot reproduce (Priority: P2)

A reader, peer reviewer, or journal editor examining the finished review's search documentation can
determine, for every query, which backend answered it and whether they could reproduce that query
themselves. Where enriched sources contributed, the log says so plainly and states what the reader
would need in order to repeat the search.

**Why this priority**: PRISMA-S exists so a search can be repeated. An enriched search is not
repeatable by a reader without OpenResearch, and a log that presents enriched and keyless results
as one undifferentiated search is misleading in exactly the way the repository claims to prevent.
Same priority as User Story 2 because both are the conditions under which User Story 1 is
publishable at all.

**Independent Test**: Run acquisitions in both configurations, then read the two search logs and
confirm each states its backends per query and that only the enriched log carries the
reproducibility caveat.

**Acceptance Scenarios**:

1. **Given** an acquisition ran with enrichment, **When** the search log is written, **Then** each
   query entry names the backend and sub-source that answered it, the date it ran, and the record
   count it returned.
2. **Given** any query in a run was answered by an enriched source, **When** the search log is
   written, **Then** the log carries an explicit statement that the search is not fully
   reproducible without OpenResearch, naming the affected queries.
3. **Given** an acquisition ran keyless, **When** the search log is written, **Then** no
   reproducibility caveat appears, because none applies.
4. **Given** an acquisition ran with enrichment, **When** the search log is written, **Then** the
   version of OpenResearch that answered the queries is recorded, because its result behaviour is
   not stable across versions.
5. **Given** a candidate set containing enriched records and a search log carrying no disclosure,
   **When** the disclosure check runs under enforcement, **Then** it reports the omission and exits
   as a method violation.
6. **Given** the same candidate set once the disclosure is added, **When** the check runs again,
   **Then** it passes.
7. **Given** a keyless candidate set, **When** the check runs under enforcement, **Then** it passes,
   because no disclosure is owed.

---

### User Story 4 - The skill still works when copied out on its own (Priority: P3)

Someone copies the `acquire-corpus` directory alone into an unrelated project, on a machine with no
OpenResearch and no access to this repository, and it runs.

**Why this priority**: Principle III, and the documented install path. Lower priority only because
it is a property to preserve rather than a capability to add — but a violation is a defect that
makes the skill fail at the moment of use.

**Independent Test**: Copy the skill directory to a location outside the repository, remove
OpenResearch from the executable search path, and run an acquisition to completion.

**Acceptance Scenarios**:

1. **Given** the skill directory copied out alone with no OpenResearch present, **When** an
   acquisition runs, **Then** it completes and produces a candidate set and a search log.
2. **Given** the skill directory copied out alone, **When** its scripts are imported, **Then** no
   import resolves to a sibling skill, a shared library, or any path outside the skill directory.

---

### Edge Cases

- **Service absent but binary present.** The executable exists on the search path while the
  background service is not running. Detection must resolve this as unavailable within a bounded
  time rather than waiting on a connection.
- **Detection or query hangs.** The backend accepts the invocation and never returns. The run must
  abandon the attempt at a bounded deadline and continue keyless rather than hanging the
  acquisition.
- **Output is not the expected shape.** The backend emits non-JSON, truncated JSON, a JSON value
  that is not a collection of records, or an empty stream. Each must be treated as a failed query
  that degrades to keyless, never as a crash and never as a legitimate zero-result search.
- **Unrecognised fields appear.** A newer version emits fields this feature has never seen.
  Unknown fields must be ignored rather than rejected. This is the one place the repository's
  fail-closed posture is deliberately inverted, and the inversion is justified in Assumptions.
- **Expected fields disappear.** A newer version stops emitting a field the normalisation depends
  on. Records that cannot be normalised must be dropped with a counted, logged reason, and the
  drop count must reach the search log — silently discarding candidates would corrupt the
  identification count that feeds the PRISMA flow.
- **Records carry no DOI.** Preprint and full-text sources routinely return records with no DOI.
  They are admitted and tagged (FR-016), which means `dedupe-records` sees records it can match only
  on title and `verify-sources` sees records it cannot resolve. The count must be disclosed at
  acquisition (FR-022) so the cost is known before it is paid.
- **Every record in a corpus is identifier-less.** A legitimate outcome for a preprint-heavy
  question. The corpus is still valid and must pass acquisition, but the disclosure of FR-022 makes
  the situation visible rather than presenting it as an ordinary corpus.
- **Enriched records present, no search log at all.** The disclosure check must treat this as a
  method violation — the disclosure is owed and absent — not as malformed input.
- **A disclosure that names no queries.** A log carrying the caveat as boilerplate without
  identifying which queries it applies to does not satisfy FR-015 and must fail the check.
- **A genuine zero-result query.** The backend runs correctly and matches nothing. This must be
  distinguishable in the log from a query that failed and fell back, because the two mean opposite
  things about the search.
- **Version changes mid-project.** A reviewer upgrades OpenResearch between the first and last
  query of one review. The log must show which version answered which query.
- **Enrichment returns overwhelmingly more records than the keyless search.** Identification counts
  feeding the PRISMA flow must remain per-source and auditable rather than collapsing into one
  total that hides the imbalance.

## Requirements *(mandatory)*

### Functional Requirements

**Availability and degradation**

- **FR-001**: The skill MUST determine whether the enriched backend is usable before relying on it,
  treating "usable" as both the executable being present and its service answering.
- **FR-002**: Availability determination MUST complete within a bounded time and MUST NOT block the
  acquisition indefinitely.
- **FR-003**: When the enriched backend is unavailable, the skill MUST proceed with the keyless
  backends and MUST NOT emit an error, emit a warning, prompt the user, alter its exit code, or
  suggest installing anything.
- **FR-004**: A failure occurring after a successful availability check — a query that errors,
  hangs, or returns unusable output — MUST be handled as unavailability for that query and MUST NOT
  abort the acquisition.
- **FR-005**: The reviewer MUST be able to force a keyless-only acquisition on a machine where the
  enriched backend is available and reachable.

**Record handling**

- **FR-006**: Records obtained from the enriched backend MUST be normalised into the corpus record
  shape already produced by the keyless backend, so downstream skills consume one schema.
- **FR-007**: Normalisation MUST tolerate unrecognised fields in the backend's output by ignoring
  them, and MUST NOT fail a record or a run on their presence.
- **FR-008**: A record that cannot be normalised MUST be dropped rather than emitted partially, and
  every drop MUST be counted and attributed to a reason.
- **FR-009**: Every record in the candidate set MUST identify the source that produced it, for both
  enriched and keyless records.
- **FR-010**: Enriched records MUST be written to their own per-source raw output, preserving the
  existing convention that per-source counts remain separately auditable.
- **FR-011**: The skill MUST NOT deduplicate across backends. Cross-source duplicates are
  `dedupe-records`' auditable step and its removed-count feeds the PRISMA flow.
- **FR-012**: Where the enriched backend performs its own internal ranking or deduplication before
  returning results, the skill MUST NOT treat that as the review's deduplication step, and MUST
  disclose in the search log that an opaque upstream selection occurred.

**Search log and provenance**

- **FR-013**: The search log MUST record, per query: the backend and sub-source that answered it,
  the exact query as submitted, the date it ran, the record count returned, and any records
  dropped in normalisation.
- **FR-014**: The search log MUST distinguish a query that legitimately returned no records from a
  query that failed and fell back to the keyless backend.
- **FR-015**: When any query in a run was answered by an enriched source, the search log MUST carry
  an explicit statement that the search is not fully reproducible without OpenResearch, naming the
  affected queries and recording the backend version that answered them.

**Downstream compatibility**

- **FR-016**: Records lacking a DOI MUST be admitted to the candidate set, tagged as
  identifier-less, and MUST carry whatever alternative identifier the source did provide. Recall is
  the property this feature exists to improve, and excluding these records would discard most of the
  preprint and full-text coverage that motivates it.
- **FR-022**: The number of identifier-less records admitted MUST be recorded in the search log and
  reported at handoff, so the next skill in the pipeline receives a known quantity rather than
  discovers it. An identification count that hides how much of the corpus cannot be resolved is the
  kind of unaudited number this repository exists to prevent.
- **FR-023**: The skill MUST state, where it documents its outputs, what admitting these records
  costs downstream: `dedupe-records` can match them only by title similarity, and `verify-sources`
  cannot resolve them at all. A reviewer MUST be able to learn this at acquisition time rather than
  at the gate that stalls on it.

**Enforcement posture**

- **FR-017**: A runnable check MUST verify that a candidate set containing enriched records is
  accompanied by a search log carrying the disclosure required by FR-015. A corpus whose enrichment
  is undisclosed MUST fail that check.
- **FR-024**: The check MUST conform to the repository's shared gate contract: the record is read
  from a path argument or from standard input; `--strict` selects enforcement; exit `0` means clean
  or non-strict, exit `1` a method violation under `--strict`, exit `2` malformed input. A corpus
  that is merely undisclosed is a method violation, never a malformed input.
- **FR-025**: The check MUST pass a keyless corpus without complaint. No disclosure is owed when no
  enriched source contributed, and a check that demanded one would make the keyless path harder than
  the enriched one.
- **FR-026**: The check MUST document what it cannot verify — at minimum that the disclosure is
  truthful, that the recorded backend version is the version that actually answered, and that
  records attributed to a source genuinely came from it. The check reads what the run wrote about
  itself; it does not re-execute the search.
- **FR-027**: This check MUST NOT be represented as making the skill PRISMA-S compliant. It enforces
  enrichment disclosure and nothing else. The skill's PRISMA-S posture remains guidance, and the
  standards table MUST continue to say so.

**Constitutional constraints**

- **FR-018**: The feature MUST NOT introduce any dependency required to import or run the skill's
  scripts. The enriched backend is consulted as an external program, never imported.
- **FR-019**: The skill MUST remain functional when its directory is copied out of this repository
  on its own, with no enriched backend present.
- **FR-020**: The skill MUST state what the enriched backend cannot verify — at minimum that its
  relevance ranking is opaque, that its recall against the review's question is uncharacterised,
  and that the coverage of its underlying sources is unquantified.
- **FR-021**: Use of the enriched backend MUST be stamped as an AI-assisted acquisition step per
  the repository's provenance convention, including which backend answered.

### Key Entities

- **Corpus record**: One candidate work. Already defined by the keyless backend; this feature adds
  no field to it beyond the source attribution of FR-009 and changes no existing field's meaning.
- **Search log entry**: One query as executed — its text, backend, sub-source, date, returned
  count, dropped count, and outcome (answered, empty, or failed-and-fell-back).
- **Backend availability verdict**: The outcome of FR-001, held for the run: available and at which
  version, or unavailable. It is a fact about the environment, not a user setting.
- **Reproducibility caveat**: The statement required by FR-015, attached to the search log when and
  only when an enriched source contributed to the corpus.
- **Disclosure verdict**: The outcome of the check required by FR-017 — clean, a method violation
  naming what is missing, or malformed input. It is a statement about what the run recorded about
  itself, never about whether the search was good.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a machine without OpenResearch, the candidate set and exit code for a given query
  are identical to the pre-feature result, for 100% of queries tested.
- **SC-002**: On a machine without OpenResearch, the acquisition adds no more than one second of
  wall-clock time versus the pre-feature run.
- **SC-003**: On a machine where the binary is present but its service is not running, the
  acquisition still completes, adding no more than five seconds versus a keyless run.
- **SC-004**: 100% of records in a merged candidate set are attributable to a named source.
- **SC-005**: A reader of a search log can determine, for every query, whether they can reproduce
  it without OpenResearch — verified by having a reader unfamiliar with the run answer that
  question correctly for every query in a sample log.
- **SC-006**: No malformed, truncated, empty, or unexpected backend output aborts an acquisition,
  across the full set of malformation cases enumerated in Edge Cases.
- **SC-007**: The skill directory copied out alone, with no OpenResearch present, completes an
  acquisition and produces both a candidate set and a search log.
- **SC-008**: For a question with known full-text-only exemplars, the enriched run returns
  exemplars the keyless run does not, demonstrating the recall gain that motivates the feature.
- **SC-009**: Every record dropped during normalisation is reflected in a count in the search log,
  so identification totals reconcile with what the backend actually returned.
- **SC-010**: The disclosure check fails an enriched corpus whose log carries no disclosure, and
  passes that same corpus once the disclosure is added — demonstrating it detects the condition it
  claims to, rather than always passing.
- **SC-011**: The disclosure check passes 100% of keyless corpora, so the guaranteed path is never
  made harder than the enriched one.
- **SC-012**: The count of admitted identifier-less records appears in the search log for 100% of
  runs that admit any, so the proportion of the corpus that downstream gates cannot resolve is
  known before those gates run.

## Assumptions

- **Enrichment is on by default when available.** This follows the scite precedent in
  `verify-sources`: present means used, and the report stamps which backend answered. FR-005
  provides the opt-out for a reviewer who wants a search any reader can repeat.
- **The backend is consulted as an external program.** No language binding, no library, no
  long-lived connection managed by this skill. This is what keeps FR-018 satisfiable.
- **Its discovery output is machine-readable.** The upstream skill documentation states that the
  discovery command emits a structured JSON result carrying source, identifier, title, abstract and
  publication date, with full-text snippets on some sources. No output schema is published and no
  live binary was available while writing this specification, so the exact field names are treated
  as unknown and the normalisation is specified defensively rather than against a fixed schema.
  Confirming the real shape against a running binary belongs in `/speckit-plan`.
- **Unknown fields are ignored rather than rejected.** This inverts the repository's fail-closed
  default, and the inversion is deliberate and bounded. Fail-closed protects artifacts a reviewer
  authors, where an unknown key is a typo that would otherwise read as an omission. This input is
  not authored by the reviewer; it is emitted by a pre-1.0 external program whose additive changes
  carry no methodological meaning. Rejecting it on an unknown field would convert a routine upstream
  release into a broken acquisition. The fail-closed posture is preserved where it matters: a record
  that cannot be normalised is dropped and counted (FR-008), never emitted partially, and never
  silently (FR-013, SC-009).
- **The upstream interface is unstable.** OpenResearch is pre-1.0 and shipping quickly. Its command
  surface and output shape are not a stable contract, which is why FR-004 treats any post-detection
  failure as degradation and why FR-015 records the version that answered.
- **The keyless backends remain primary.** This feature adds a source; it does not reorder,
  reweight, or replace the existing ones, and it does not change the record shape they produce.
- **Scope is discovery only.** Reading paper full text through the enriched backend, its experiment
  and run-orchestration capabilities, and any use of it to execute agent sessions are out of scope
  for this feature.
- **Identifier-less records are admitted with a known, deferred cost.** FR-016 resolves in favour of
  recall. The consequence is real and is accepted rather than hidden: `dedupe-records` will match
  these records on title similarity alone, which is its weaker path, and `verify-sources` cannot
  resolve them at all, so a review that cites one will need another route to verification. This
  feature's obligation is to make the quantity visible before those gates run (FR-022, FR-023), not
  to solve it.
- **No change to downstream skills is in scope.** Teaching `dedupe-records` or `verify-sources` to
  handle identifier-less records is separate work with its own specification. This feature must not
  quietly widen to include it.
- **The disclosure check is a new gate and inherits the workflow rules that apply to gates.** Under
  the repository's development workflow every script that can fail a review run has a test module,
  and gates share one exit-code contract. Both bind here (FR-024).
- **The disclosure check does not upgrade the skill's standards claim.** `acquire-corpus` gains its
  first runnable gate, but that gate enforces enrichment disclosure, not PRISMA-S. Presenting the
  skill as PRISMA-S enforced on the strength of it would be precisely the unbacked claim Principle I
  calls a defect (FR-027).
