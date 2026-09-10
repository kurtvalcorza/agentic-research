# Feature Specification: orx Discovery Backend for acquire-corpus

**Feature Branch**: `claude/openresearch-agentic-research-diff-fq5xyi`

**Feature Directory**: `specs/002-orx-discovery-backend`

**Created**: 2026-09-09

**Last Revised**: 2026-09-10 — reviewer findings at `faeb664` addressed

**Status**: Draft

**Input**: User description: "Add OpenResearch's `orx discover` as an optional, detect-and-degrade discovery backend for the acquire-corpus skill. Keyless OpenAlex/CrossRef remains the default and only guaranteed path; orx is enrichment only (alphaXiv full-text search, embedding/semantic search, bioRxiv preprints) used when the `orx` binary is present and its daemon is reachable. Must normalize orx's structured JSON discovery results into the existing corpus JSONL schema with defensive parsing (orx is pre-1.0, schema undocumented and unstable). Must never block, error, or prompt when orx is absent. Must record the backend used per query in the PRISMA-S search log, because an orx-augmented search is not reproducible by a reader without orx — omitting that makes the search log misleading. Constitutional constraints: Principle II (keyless stdlib baseline, orx is optional enrichment like the scite MCP), Principle III (acquire-corpus must still run when copied out alone, with no orx present), Principle I (state what the backend cannot verify), Principle VII (provenance stamping of which backend answered)."

> **Note on the original input.** The description above specified availability as the binary being
> present *and its daemon reachable*. That premise was wrong and has been corrected throughout:
> `orx discover` requires no local daemon and no login. See **Corrections from review**.

## Corrections from review

Five findings were raised against `faeb664` and all five are upheld. Two required correcting facts
this specification had asserted, and two required correcting facts stated in the review itself.

| # | Finding | Disposition |
|:--|:--------|:------------|
| 1 | Availability model assumed a local daemon | **Upheld.** Upstream documents "No login is required" and "exactly one public endpoint request" per discovery call. FR-001, FR-002, Story 2, SC-003 and the edge cases are rewritten; the service-down latency criterion is removed. |
| 2 | Gate input cannot be JSONL + Markdown under the shared contract | **Upheld.** Resolved as the reviewer proposed and as the constitution's artifact-generation rule already requires: a structured acquisition record is the source of truth, the Markdown log is generated from it, and the gate reads one JSON object. FR-013, FR-015, FR-024 and new FR-028 carry this. |
| 3 | FR-007 conflicts with Principle IV | **Upheld.** Deferring it to the Constitution Check did not resolve it. FR-007 is rewritten in a conforming form. A constitutional clarification remains available and is recorded as an open maintainer decision below rather than assumed. |
| 4 | orx does not supply the corpus shape FR-006 assumed | **Upheld, and understated.** See below. |
| 5 | FR-023 overstates the `verify-sources` limitation | **Upheld, and the reviewer's correction is itself incomplete.** See below. |

**On finding 4.** Upstream guarantees five fields — source, self-routing id, title, abstract,
publication date — with votes and snippets on some sources and citation counts on others. Authors,
DOI, venue and type are **not** guaranteed. `dedupe_records.py` documents its minimum as `doi`,
`title`, `year`, `authors`. The consequence is sharper than a weakened guard. In
`dedupe_records.py`, the year and first-author-surname guards are written as
`author_ok = (not sn or not csn) or sn == csn` and the equivalent for year: when the field is
absent the guard evaluates **vacuously true** rather than failing. The guards therefore **degrade
open, not closed**. An author-less, DOI-less record is matched on title similarity alone, with both
collision guards disabled — precisely the same-title-different-paper collision the surname guard
exists to prevent. The risk is a **false merge**, which *deflates* records-screened and can silently
drop a distinct study from the review. This is a corruption of a PRISMA number, and it is the most
serious consequence of admitting these records under FR-016.

**On finding 5.** The reviewer is right that `verify-sources` is not helpless: `resolve_citation.py`
exposes `--title`, `--author`, `--year` and a `reverse_lookup` path. The correction needs one more
step, because reverse lookup is weakened by the *same* missing field as dedup: the candidate filter
is `(not author or author.lower() in wa)`, so with no author to supply, matching falls back to title
plus a ±1-year window, and the function's own failure note is "title found candidates but none
matched author/year — review manually". So these records are resolvable *in principle*, at a higher
manual-review rate, and are not simply unverifiable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Wider discovery when OpenResearch is installed (Priority: P1)

A reviewer building a corpus on a machine where OpenResearch is installed gets candidate records
that the keyless backends structurally cannot return: full-text matches inside paper bodies,
semantically similar work that shares no keywords with the query, and biology preprints. These
arrive merged into the same candidate set, normalised as far as the source data allows, and flow
into `dedupe-records` with their known gaps declared.

**Why this priority**: This is the entire value of the feature. Keyword search over titles,
abstracts and indexed metadata misses papers whose relevant content sits in the body text, and
misses papers that use different vocabulary for the same construct. Recall is the property a
systematic search is judged on, and this is the only slice that improves it.

**Independent Test**: On a machine with OpenResearch installed, run the acquisition step for a
question with known full-text-only exemplars, and confirm those exemplars appear in the candidate
set and are absent from a keyless-only run of the same query.

**Acceptance Scenarios**:

1. **Given** OpenResearch is available, **When** the reviewer runs the acquisition step, **Then**
   candidate records from the enriched sources appear in the candidate set, each tagged with the
   source and sub-source that produced it and with any field the source did not supply marked as
   absent rather than empty.
2. **Given** OpenResearch is available, **When** the enriched search returns records already found
   by the keyless search, **Then** both copies are retained and handed to `dedupe-records`, because
   record-level deduplication is that skill's auditable step and not this one's.
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
3. **Given** the binary is present but its discovery call fails — no network, an upstream error, a
   changed endpoint — **When** the acquisition step runs, **Then** the run proceeds keyless within
   the bounded deadline of FR-002 rather than retrying or stalling.
4. **Given** OpenResearch is available, **When** the reviewer explicitly requests a keyless-only
   search, **Then** the enriched backend is not consulted and the search log records the search as
   keyless.

---

### User Story 3 - A search log that discloses what a reader cannot reproduce (Priority: P2)

A reader, peer reviewer, or journal editor examining the finished review's search documentation can
determine, for every query, which backend answered it and whether they could reproduce that query
themselves. Where enriched sources contributed, the log says so plainly and states what the reader
would need in order to repeat the search. A runnable check enforces that the disclosure is present.

**Why this priority**: PRISMA-S exists so a search can be repeated. An enriched search is not
repeatable by a reader without OpenResearch, and a log that presents enriched and keyless results
as one undifferentiated search is misleading in exactly the way the repository claims to prevent.
Same priority as User Story 2 because both are the conditions under which User Story 1 is
publishable at all.

**Independent Test**: Run acquisitions in both configurations, then read the two generated search
logs and confirm each states its backends per query and that only the enriched log carries the
reproducibility caveat; then run the disclosure check against both.

**Acceptance Scenarios**:

1. **Given** an acquisition ran, **When** the structured acquisition record is written, **Then**
   each query entry names the backend and sub-source that answered it, the query as submitted, the
   date it ran, the record count returned, and the records dropped in normalisation.
2. **Given** any query in a run was answered by an enriched source, **When** the acquisition record
   is written, **Then** it carries an explicit statement that the search is not fully reproducible
   without OpenResearch, naming the affected queries and the backend version that answered them.
3. **Given** an acquisition ran keyless, **When** the acquisition record is written, **Then** no
   reproducibility caveat appears, because none applies.
4. **Given** an acquisition record exists, **When** the human-readable search log is produced,
   **Then** it is generated from that record rather than authored alongside it.
5. **Given** an acquisition record containing enriched queries and carrying no disclosure, **When**
   the disclosure check runs under enforcement, **Then** it reports the omission and exits as a
   method violation.
6. **Given** the same record once the disclosure is added, **When** the check runs again, **Then**
   it passes.
7. **Given** a keyless acquisition record, **When** the check runs under enforcement, **Then** it
   passes, because no disclosure is owed.

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
   acquisition runs, **Then** it completes and produces a candidate set, an acquisition record, and
   a generated search log.
2. **Given** the skill directory copied out alone, **When** its scripts are imported, **Then** no
   import resolves to a sibling skill, a shared library, or any path outside the skill directory.

---

### Edge Cases

- **Binary present, discovery call fails.** No network, an upstream outage, a moved endpoint, or a
  changed command surface. Detection must resolve this as unavailable within a bounded time and the
  run must continue keyless.
- **Detection or query hangs.** The call is accepted and never returns. The run must abandon it at a
  bounded deadline and continue keyless rather than hanging the acquisition.
- **Output is not the expected shape.** Non-JSON, truncated JSON, a JSON value that is not a
  collection of records, or an empty stream. Each is a failed query that degrades to keyless, never
  a crash and never a legitimate zero-result search.
- **A record carries fields the mapping does not recognise.** Handled per FR-007.
- **Expected fields disappear.** A newer version stops emitting a field the mapping depends on.
  Records that cannot be normalised are dropped with a counted reason reaching the acquisition
  record — silently discarding candidates would corrupt the identification count feeding the
  PRISMA flow.
- **Records carry no DOI and no authors.** The common case for these sources, not an exception.
  Both of `dedupe_records.py`'s collision guards degrade *open* when the fields are absent, so such
  records are matched on title similarity alone and can be falsely merged with a distinct
  same-titled paper. See FR-022 and FR-023.
- **Every record in a corpus is identifier-less.** A legitimate outcome for a preprint-heavy
  question. The corpus is valid and must pass acquisition, but the disclosure of FR-022 makes the
  situation visible rather than presenting it as an ordinary corpus.
- **A genuine zero-result query.** The backend runs correctly and matches nothing. This must be
  distinguishable in the record from a query that failed and fell back, because the two mean
  opposite things about the search.
- **Version changes mid-project.** A reviewer upgrades OpenResearch between the first and last query
  of one review. The record must show which version answered which query.
- **Enriched records present, no acquisition record at all.** A method violation for the disclosure
  check — the disclosure is owed and absent — not malformed input.
- **A disclosure that names no queries.** Boilerplate carrying the caveat without identifying which
  queries it applies to does not satisfy FR-015 and must fail the check.
- **Enrichment returns far more records than the keyless search.** Identification counts feeding the
  PRISMA flow must remain per-source and auditable rather than collapsing into one total that hides
  the imbalance.

## Requirements *(mandatory)*

### Functional Requirements

**Availability and degradation**

- **FR-001**: The skill MUST determine whether the enriched backend is usable before relying on it.
  Usable means the executable is present **and a discovery call completes successfully**. There is
  no local service to probe and no authentication step: upstream documents discovery as requiring no
  login and issuing one public endpoint request.
- **FR-002**: Availability determination MUST complete within a bounded time and MUST NOT block the
  acquisition indefinitely.
- **FR-003**: When the enriched backend is unavailable, the skill MUST proceed with the keyless
  backends and MUST NOT emit an error, emit a warning, prompt the user, alter its exit code, or
  suggest installing anything.
- **FR-004**: A failure occurring after a successful availability check — a query that errors,
  hangs, or returns unusable output — MUST be handled as unavailability for that query and MUST NOT
  abort the acquisition.
- **FR-005**: The reviewer MUST be able to force a keyless-only acquisition on a machine where the
  enriched backend is available.

**Record handling**

- **FR-006**: The skill MUST define an explicit field-by-field mapping from a discovery result to
  the corpus record shape, and MUST NOT assume fields the source does not guarantee. Upstream
  guarantees only **source, self-routing id, title, abstract, publication date**, with votes and
  snippets on some sources and citation counts on others. **Authors, DOI, venue and type are not
  guaranteed.** The mapping MUST state, per corpus field, its source field and its behaviour when
  that field is absent.
- **FR-007**: Normalisation MUST read only the fields named in the FR-006 mapping and MUST NOT
  reject a discovery payload for carrying fields outside it. A payload field the mapping does not
  name contributes nothing to the corpus record and cannot change any verdict. This is data
  ingestion from a third-party endpoint, not the reading of a reviewer-authored artifact, and no
  gate verdict is derived from the payload. Principle IV continues to govern every artifact this
  feature *produces*: the acquisition record of FR-028 is closed-schema and rejects unknown keys.
  *(See "Open maintainer decision" — a constitutional clarification would settle the scope question
  this requirement currently answers by argument.)*
- **FR-008**: A record that cannot be normalised — one missing a field the mapping marks as required
  — MUST be dropped rather than emitted partially, and every drop MUST be counted and attributed to
  a reason.
- **FR-009**: Every record in the candidate set MUST identify the source and sub-source that
  produced it, for both enriched and keyless records.
- **FR-010**: Enriched records MUST be written to their own per-source raw output, preserving the
  existing convention that per-source counts remain separately auditable.
- **FR-011**: The skill MUST NOT deduplicate across backends. Cross-source duplicates are
  `dedupe-records`' auditable step and its removed-count feeds the PRISMA flow.
- **FR-012**: Where the enriched backend performs its own internal ranking or deduplication before
  returning results, the skill MUST NOT treat that as the review's deduplication step, and MUST
  disclose in the acquisition record that an opaque upstream selection occurred.

**Search record, generated log, and provenance**

- **FR-028**: The acquisition MUST emit a **structured acquisition record** as the source of truth
  for what the search did. It MUST be a single JSON object with a closed schema and a required
  schema version, matching the form the repository's gates already consume.
- **FR-013**: The acquisition record MUST capture, per query: the backend and sub-source that
  answered it, the query as submitted, the date it ran, the record count returned, the records
  dropped in normalisation with reasons, and the count of admitted records lacking a DOI or authors.
- **FR-014**: The acquisition record MUST distinguish a query that legitimately returned no records
  from a query that failed and fell back to the keyless backend.
- **FR-015**: When any query in a run was answered by an enriched source, the acquisition record
  MUST carry an explicit statement that the search is not fully reproducible without OpenResearch,
  naming the affected queries and recording the backend version that answered them.
- **FR-029**: The human-readable PRISMA-S search log MUST be **generated** from the acquisition
  record, never authored alongside it, per the repository's artifact-generation rule. Hand-
  maintaining both invites the two to disagree.
- **FR-021**: Use of the enriched backend MUST be stamped as an AI-assisted acquisition step per
  the repository's provenance convention, including which backend answered.

**Downstream compatibility**

- **FR-016**: Records lacking a DOI MUST be admitted to the candidate set, tagged as
  identifier-less, and MUST carry whatever alternative identifier the source did provide. Recall is
  the property this feature exists to improve, and excluding these records would discard most of the
  preprint and full-text coverage that motivates it.
- **FR-022**: The counts of admitted records lacking a DOI and lacking authors MUST be recorded in
  the acquisition record and reported at handoff. The skill MUST disclose the specific downstream
  consequence: in `dedupe_records.py` the year and first-author-surname guards evaluate vacuously
  true when those fields are absent, so such records are matched on **title similarity alone** and
  may be **falsely merged** with a distinct same-titled paper. A false merge deflates
  records-screened and can drop a study from the review. An identification count that hides how much
  of the corpus is exposed to this is the kind of unaudited number this repository exists to
  prevent.
- **FR-023**: The skill MUST state, where it documents its outputs, what admitting these records
  costs downstream, accurately and without overstatement: they cannot be resolved **directly by
  DOI**; `verify-sources` can still reverse-look-up by title, author and year, but that path is
  weakened by the same missing author field and returns its "review manually" outcome more often, so
  a higher proportion of these records will remain **UNVERIFIED** pending human checking.
- **FR-030**: The skill MUST NOT modify `dedupe-records` or `verify-sources`. Their behaviour with
  identifier-less records is disclosed here and addressed, if at all, by separate work.

**Enforcement posture**

- **FR-017**: A runnable check MUST verify that an acquisition record describing enriched queries
  carries the disclosure required by FR-015. A record whose enrichment is undisclosed MUST fail.
- **FR-024**: The check MUST conform to the repository's shared gate contract: **one JSON object**
  read from a path argument or from standard input; `--strict` selects enforcement; exit `0` clean
  or non-strict, exit `1` a method violation under `--strict`, exit `2` malformed input including an
  unknown key or a missing schema version. An undisclosed acquisition is a method violation, never
  malformed input.
- **FR-025**: The check MUST pass a keyless acquisition record without complaint. No disclosure is
  owed when no enriched source contributed, and a check that demanded one would make the keyless
  path harder than the enriched one.
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
  relevance ranking is opaque, that its recall against the review's question is uncharacterised, and
  that the coverage of its underlying sources is unquantified.

### Key Entities

- **Corpus record**: One candidate work. Already defined by the keyless backend. This feature adds
  the source attribution of FR-009 and the identifier-less tag of FR-016, and changes no existing
  field's meaning.
- **Acquisition record**: The structured, closed-schema account of what the search did (FR-028) —
  the source of truth from which the search log is generated and the input the disclosure check
  reads.
- **Search log**: The human-readable PRISMA-S-oriented document, generated from the acquisition
  record (FR-029). Never the source of truth.
- **Field mapping**: The declared correspondence between discovery result fields and corpus record
  fields, including absence behaviour per field (FR-006).
- **Backend availability verdict**: The outcome of FR-001, held for the run — available and at which
  version, or unavailable. A fact about the environment, not a user setting.
- **Reproducibility caveat**: The statement required by FR-015, present when and only when an
  enriched source contributed.
- **Disclosure verdict**: The outcome of FR-017 — clean, a method violation naming what is missing,
  or malformed input. A statement about what the run recorded about itself, never about whether the
  search was good.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a machine without OpenResearch, the candidate set and exit code for a given query
  are identical to the pre-feature result, for 100% of queries tested.
- **SC-002**: On a machine without OpenResearch, the acquisition adds no more than one second of
  wall-clock time versus the pre-feature run.
- **SC-003**: On a machine where the binary is present but the discovery call fails, the acquisition
  still completes within the bounded deadline of FR-002 and produces a keyless result.
- **SC-004**: 100% of records in a merged candidate set are attributable to a named source and
  sub-source.
- **SC-005**: A reader of a generated search log can determine, for every query, whether they can
  reproduce it without OpenResearch — verified by having a reader unfamiliar with the run answer
  that question correctly for every query in a sample log.
- **SC-006**: No malformed, truncated, empty, or unexpected backend output aborts an acquisition,
  across the full set of malformation cases enumerated in Edge Cases.
- **SC-007**: The skill directory copied out alone, with no OpenResearch present, completes an
  acquisition and produces a candidate set, an acquisition record, and a generated search log.
- **SC-008**: For a question with known full-text-only exemplars, the enriched run returns exemplars
  the keyless run does not, demonstrating the recall gain that motivates the feature.
- **SC-009**: Every record dropped during normalisation is reflected in a count in the acquisition
  record, so identification totals reconcile with what the backend actually returned.
- **SC-010**: The disclosure check fails an enriched acquisition record carrying no disclosure, and
  passes that same record once the disclosure is added — demonstrating it detects the condition it
  claims to, rather than always passing.
- **SC-011**: The disclosure check passes 100% of keyless acquisition records.
- **SC-012**: The counts of admitted records lacking a DOI and lacking authors appear in the
  acquisition record for 100% of runs that admit any, so the proportion of the corpus exposed to
  false-merge risk is known before `dedupe-records` runs.
- **SC-013**: The generated search log and the acquisition record never disagree, verified by
  regenerating the log from the record and comparing.

## Assumptions

- **Enrichment is on by default when available.** This follows the scite precedent in
  `verify-sources`: present means used, and the report stamps which backend answered. FR-005
  provides the opt-out for a reviewer who wants a search any reader can repeat.
- **Discovery needs no daemon, no account, and no key.** Upstream documents "No login is required"
  and one public endpoint request per discovery call. This is materially better for Principle II
  than the original premise: enrichment adds no authentication dependency, only an executable.
- **The backend is consulted as an external program.** No language binding, no library, no
  long-lived connection managed by this skill. This is what keeps FR-018 satisfiable.
- **Only five discovery fields are guaranteed.** Source, id, title, abstract, publication date. The
  mapping is specified against that guarantee rather than against a hoped-for richer shape.
  Confirming the exact field names and per-sub-source variation against a running binary belongs in
  `/speckit-plan`; no live binary was available while writing this specification.
- **The upstream interface is unstable.** OpenResearch is pre-1.0 and shipping quickly. Its command
  surface and output shape are not a stable contract, which is why FR-004 treats any post-detection
  failure as degradation and why FR-015 records the version that answered.
- **The keyless backends remain primary.** This feature adds a source; it does not reorder,
  reweight, or replace the existing ones, and it does not change the record shape they produce.
- **Identifier-less records are admitted with a known, disclosed cost.** FR-016 resolves in favour
  of recall. The consequence is accepted, not hidden, and its most serious form is the false-merge
  risk of FR-022 rather than a mere inconvenience.
- **No change to downstream skills is in scope** (FR-030). Teaching `dedupe-records` to fail closed
  on absent guard fields, or `verify-sources` to handle identifier-less records, is separate work.
  Note that `dedupe_records.py`'s guards degrading open is a pre-existing property of that skill,
  surfaced by this feature rather than introduced by it.
- **The disclosure check is a new gate and inherits the workflow rules that apply to gates.** Every
  script that can fail a review run has a test module, and gates share one exit-code contract. Both
  bind here (FR-024).
- **The disclosure check does not upgrade the skill's standards claim.** `acquire-corpus` gains its
  first runnable gate, but that gate enforces enrichment disclosure, not PRISMA-S (FR-027).

## Open maintainer decision

**Does Principle IV govern the ingestion of third-party API payloads, or only the reading of
artifacts a reviewer authors?**

FR-007 currently answers this by argument: it reads a declared field mapping, ignores the rest of
the payload, derives no verdict from it, and keeps every artifact the feature *produces* closed and
fail-closed. That is conforming under the reading that Principle IV governs verdict-producing gates
over authored artifacts — the reading its own rationale supports ("a gate that passes on absence of
evidence inverts its own purpose"), and the context in which it cites `review_units.py`.

Under the strictest literal reading — "Unknown keys MUST be rejected, never ignored", unqualified —
FR-007 does not conform, and the alternative is to reject any payload carrying an unrecognised
field, count it, and degrade that query to keyless. That conforms without an amendment but makes
enrichment brittle: any additive upstream release silently reduces enrichment to nothing until the
mapping is updated, disclosed but useless.

Settling this by amendment is a **PATCH-level clarification** if the maintainer agrees the scoped
reading is the existing meaning, or **MINOR** if it is judged to extend it. Principle IV is not
marked NON-NEGOTIABLE, so neither route requires the recorded-approval bar that Principles II and V
carry. This is a governance decision, not an implementation one, and is left to the maintainer
rather than assumed here.
