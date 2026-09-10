# Feature Specification: orx Discovery Backend for acquire-corpus

**Feature Branch**: `claude/openresearch-agentic-research-diff-fq5xyi`

**Feature Directory**: `specs/002-orx-discovery-backend`

**Created**: 2026-09-09

**Last Revised**: 2026-09-10 — reviewer findings at `faeb664` addressed

**Status**: Draft

**Input**: User description: "Add OpenResearch's `orx discover` as an optional, detect-and-degrade discovery backend for the acquire-corpus skill. Keyless OpenAlex/CrossRef remains the default and only guaranteed path; orx is enrichment only (alphaXiv full-text search, embedding/semantic search, bioRxiv preprints) used when the `orx` binary is present and its daemon is reachable. Must normalize orx's structured JSON discovery results into the existing corpus JSONL schema with defensive parsing (orx is pre-1.0, schema undocumented and unstable). Must never block, error, or prompt when orx is absent. Must record the backend used per query in the PRISMA-S search log, because an orx-augmented search is not reproducible by a reader without orx — omitting that makes the search log misleading. Constitutional constraints: Principle II (keyless stdlib baseline, orx is optional enrichment like the scite MCP), Principle III (acquire-corpus must still run when copied out alone, with no orx present), Principle I (state what the backend cannot verify), Principle VII (provenance stamping of which backend answered)."

> **Correction to the original premise.** `orx discover` does not require a local daemon or login.
> Current upstream literature discovery invokes public alphaXiv/OpenAlex/bioRxiv retrieval paths
> directly. Availability is therefore modeled as executable presence plus a bounded discovery
> invocation, not as background-service health.

## Corrections from review

Five findings were raised against `faeb664`; all five are resolved in this revision.

| # | Finding | Resolution |
|:--|:--------|:-----------|
| 1 | Availability model assumed a local daemon | **Resolved.** FR-001/002, Story 2, edge cases and SC-003 now use bounded discovery invocation; no daemon or login is assumed. |
| 2 | Gate input could not be JSONL + Markdown under the shared contract | **Resolved.** FR-028 makes one closed-schema acquisition record the source of truth; FR-029 generates Markdown from it; FR-024 binds the gate to the existing single-object CLI contract. |
| 3 | FR-007 conflicted with Principle IV | **Resolved conservatively.** Unknown upstream record keys now invalidate that enriched response and the affected query falls back keyless. No constitutional amendment or scoped exception is required. |
| 4 | `orx discover` does not supply the corpus shape FR-006 assumed | **Resolved.** FR-006 plus the mapping below define exactly what is guaranteed, what is derived, what is absent, and the false-merge consequence of missing DOI/author/year guards. |
| 5 | FR-023 overstated `verify-sources` limitations | **Resolved.** DOI-less records cannot be resolved directly by DOI, but title/author/year reverse lookup remains available; missing author/year metadata weakens that path and increases manual review. |

The downstream consequence of finding 4 is methodologically important. `dedupe_records.py` uses
exact DOI first, then fuzzy title with year and first-author guards. Those guards are permissive when
a field is absent: missing year or author makes the corresponding guard vacuously true. An enriched
record lacking DOI, author, and year can therefore be matched on title similarity alone. That can
falsely merge two distinct same-titled works, deflate records-screened, and silently remove a study
from the review. This feature does not change `dedupe-records`; it makes the exposure explicit and
counted before handoff.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Wider discovery when OpenResearch is usable (Priority: P1)

A reviewer building a corpus on a machine where OpenResearch is installed and its public literature
retrieval path is reachable gets candidate records that the keyless backends structurally cannot
return: full-text matches inside paper bodies, semantically similar work that shares no keywords
with the query, and biology preprints. These are normalized into the declared corpus contract,
stamped with provenance, and merged without adding a special downstream ingestion path.

**Why this priority**: This is the feature's value. Keyword search over titles, abstracts and indexed
metadata misses papers whose relevant content sits in the body text and papers that use different
vocabulary for the same construct. Recall is the property this enrichment is intended to improve.

**Independent Test**: On a machine with `orx` installed and a working public literature connection,
run acquisition for a question with known full-text-only exemplars and confirm those exemplars
appear in the enriched candidate set but not in a keyless-only run of the same query.

**Acceptance Scenarios**:

1. **Given** `orx` is installed and the requested discovery command succeeds, **When** acquisition
   runs, **Then** enriched candidates appear in the candidate set with the normalized fields and
   source/sub-source provenance defined below.
2. **Given** enrichment returns records already found by keyless discovery, **When** candidates are
   assembled, **Then** both copies are retained and handed to `dedupe-records`, because cross-source
   deduplication is that skill's auditable step.
3. **Given** an enrichment invocation fails partway through a multi-query acquisition, **When** the
   remaining work proceeds, **Then** the affected query falls back keyless and the run completes
   successfully with partial enrichment recorded.

---

### User Story 2 - Identical behaviour when OpenResearch is absent or unusable (Priority: P2)

A reviewer on a machine with no OpenResearch — the only configuration the repository guarantees —
runs the same acquisition step and gets today's keyless result. No error, no prompt, no instruction
to install anything, no changed exit code, and no meaningful delay are introduced.

**Why this priority**: Principle II makes the keyless path non-negotiable. Optional enrichment may
add recall; it may not make the guaranteed path harder to run.

**Independent Test**: Run acquisition with `orx` absent from the executable search path and diff the
candidate set and exit code against pre-feature behaviour for the same query.

**Acceptance Scenarios**:

1. **Given** OpenResearch is not installed, **When** acquisition runs, **Then** the candidate set and
   exit code are identical to the pre-feature keyless result.
2. **Given** OpenResearch is not installed, **When** acquisition runs, **Then** no output stream
   carries an error, warning, prompt, or installation suggestion concerning OpenResearch.
3. **Given** the binary is present but a discovery invocation fails because of network, upstream,
   command-surface, timeout, or schema problems, **When** acquisition runs, **Then** the affected
   enrichment attempt ends within its bound and the query proceeds keyless.
4. **Given** OpenResearch is usable, **When** the reviewer explicitly requests keyless-only
   acquisition, **Then** no enriched command is invoked and the acquisition record identifies those
   queries as keyless.

---

### User Story 3 - Search documentation discloses what a reader cannot reproduce (Priority: P2)

A reader, peer reviewer, or journal editor can determine, for every query, which backend answered it
and whether they could reproduce that query themselves. One machine-readable acquisition record is
the source of truth. The human-readable PRISMA-S-oriented search log is generated from it. Where
OpenResearch contributed, both artifacts disclose the non-keyless dependency and affected queries.

**Why this priority**: Search reporting exists so the search can be repeated. Presenting enriched and
keyless results as one undifferentiated search would misstate reproducibility.

**Independent Test**: Run enriched and keyless acquisitions, inspect their acquisition records and
generated search logs, and run the disclosure check against both.

**Acceptance Scenarios**:

1. **Given** acquisition ran, **When** `corpus/acquisition-record.json` is written, **Then** each query
   entry names the backend and sub-source, exact submitted query, run date, outcome, returned count,
   normalization drops, sparse-metadata counts, and OpenResearch version when enrichment answered.
2. **Given** at least one enriched query answered, **When** the acquisition record is finalized,
   **Then** it contains an explicit reproducibility disclosure naming the affected queries and
   backend version(s).
3. **Given** acquisition ran keyless, **When** its record is finalized, **Then** no OpenResearch
   reproducibility caveat appears.
4. **Given** a valid acquisition record, **When** search documentation is emitted, **Then**
   `corpus/search-log.md` is generated from that record rather than independently authored.
5. **Given** a syntactically valid acquisition record with successful enriched queries but no
   required disclosure, **When** the disclosure check runs with `--strict`, **Then** it reports a
   method violation and exits `1`.
6. **Given** the same record after the disclosure is added, **When** the check runs again, **Then** it
   passes.
7. **Given** a valid keyless acquisition record, **When** the check runs under enforcement, **Then**
   it passes because no enrichment disclosure is owed.

---

### User Story 4 - The skill remains portable (Priority: P3)

Someone copies the `acquire-corpus` directory into an unrelated project on a machine with no
OpenResearch and no access to this repository, and it still runs.

**Why this priority**: Principle III and the documented install path require each skill to remain
self-contained.

**Independent Test**: Copy the skill directory outside the repository, remove `orx` from the
executable search path, and run acquisition to completion.

**Acceptance Scenarios**:

1. **Given** the skill directory is copied out alone with no OpenResearch present, **When**
   acquisition runs, **Then** it produces candidates, an acquisition record, and a generated search
   log using only the keyless path.
2. **Given** the copied skill is imported/executed, **Then** no import resolves to sibling skills,
   shared repository libraries, or paths outside the skill directory.

---

### Edge Cases

- **Binary present, discovery endpoint unavailable.** The executable exists but a public literature
  endpoint cannot be reached. The enrichment invocation terminates within its deadline and the query
  continues keyless. No daemon state is modeled.
- **Discovery invocation hangs.** The process starts and never returns. The attempt is terminated at
  its bounded deadline and acquisition continues keyless.
- **Output transport is malformed.** Non-JSON, truncated JSON, a non-collection top-level value, or
  an empty stream is an unusable enrichment response and falls back keyless. A valid empty JSON
  collection is different: it is a genuine zero-result response.
- **An upstream record contains an unknown key.** Principle IV governs this structured boundary.
  The enriched response is rejected as unsupported, no record from that response is emitted, and
  the query falls back keyless until the adapter is deliberately updated for the new shape.
- **A required upstream field disappears.** Records that cannot satisfy the normalization contract
  are dropped with counted reasons. If a non-empty enriched response yields zero normalizable
  records, the query falls back keyless rather than being reported as a genuine zero-result search.
- **Records carry no DOI and no authors.** This is expected for some enriched sources. Exact DOI
  matching is unavailable and the first-author dedupe guard becomes vacuously true, increasing false
  merge risk. Missing year can remove the second guard as well.
- **Every enriched record is identifier-less.** The corpus remains admissible for recall purposes,
  but the acquisition record and generated log expose the quantity and downstream burden.
- **Disclosure absent from an otherwise valid enriched acquisition record.** This is a method
  violation (exit `1` under `--strict`), not malformed input.
- **The acquisition record itself is missing, invalid JSON, wrong-schema, or carries an unknown
  record key.** The disclosure gate cannot evaluate it; this is malformed input under the shared
  contract (exit `2`), not a method violation.
- **A disclosure names no affected queries.** Boilerplate without query attribution does not satisfy
  FR-015 and fails the check.
- **A genuine zero-result enriched query.** A valid empty collection is recorded as `empty`, distinct
  from `failed-and-fell-back`.
- **OpenResearch version changes mid-project.** The record shows which version answered each enriched
  query rather than assigning one version to the entire run.
- **Enrichment returns far more records than keyless discovery.** Identification counts remain
  per-source and auditable rather than collapsing into one total.

## Requirements *(mandatory)*

### Functional Requirements

**Availability and degradation**

- **FR-001**: The skill MUST NOT assume or probe a local OpenResearch daemon. Executable presence is
  the local prerequisite; usability is determined per requested enriched query by whether the
  bounded `orx discover` invocation returns a successful, supported structured response.
- **FR-002**: Every enriched discovery invocation MUST complete within a bounded time and MUST NOT
  block acquisition indefinitely.
- **FR-003**: When the enriched backend is absent or unusable, the skill MUST proceed with keyless
  backends and MUST NOT emit an OpenResearch error/warning, prompt the user, alter the acquisition
  exit code, or suggest installing anything.
- **FR-004**: A query that errors, times out, cannot reach its public upstream, or returns unusable
  output MUST be treated as enrichment failure for that query and MUST NOT abort acquisition.
- **FR-005**: The reviewer MUST be able to force keyless-only acquisition even when OpenResearch is
  usable.

**Record handling**

- **FR-006**: The adapter MUST normalize supported OpenResearch discovery results using the explicit
  mapping below. It MUST NOT assume bibliographic fields the upstream discovery result does not
  provide and MUST NOT fabricate values merely to resemble an OpenAlex record.
- **FR-007**: The adapter MUST validate each OpenResearch discovery object against the upstream
  top-level record keys it explicitly supports. If any record in an enriched response contains an
  unrecognized top-level key, the response MUST be treated as an unsupported structured shape: no
  records from that response are emitted, the enriched query is recorded as failed, and the query
  falls back keyless. Unknown upstream fields MUST NOT be silently ignored.
- **FR-008**: Within a supported upstream shape, any record that cannot satisfy the required mapping
  (for example missing a usable title or source identifier) MUST be dropped rather than emitted
  partially, with a counted reason. If a non-empty response yields zero normalizable records, the
  enriched query MUST fall back keyless rather than masquerade as a zero-result search.
- **FR-009**: Every candidate record MUST identify the backend and sub-source that produced it, for
  both enriched and keyless records.
- **FR-010**: Enriched records MUST be written to their own per-source raw output so per-source
  identification counts remain auditable.
- **FR-011**: The skill MUST NOT deduplicate across backends. Cross-source duplicate removal remains
  `dedupe-records`' auditable responsibility.
- **FR-012**: If an enriched sub-source performs opaque ranking or internal selection before
  returning results, the acquisition record MUST disclose that upstream selection and MUST NOT treat
  it as the review's deduplication step.

#### Normalized enriched-record mapping

Current upstream `LitHit` serialization is the external contract the adapter understands. The table
below is normative for this feature. Any new upstream top-level record key invokes FR-007 until it
is deliberately reviewed and added here.

| OpenResearch field | Corpus field | Normalization rule |
|:--|:--|:--|
| `source` | `source`, `sub_source` | Set `source` to `orx`; preserve the upstream source as `sub_source` (for example `alphaxiv`, `openalex`, `biorxiv`). Required. |
| `id` | `source_id` | Preserve the self-routing identifier verbatim. Required. |
| `id` | `doi` | Populate only when the identifier is syntactically a DOI; otherwise set `null`. No title-based DOI synthesis occurs during normalization. |
| `title` | `title` | Required non-empty string; otherwise the record is non-normalizable under FR-008. |
| *(not supplied by current discovery output)* | `authors` | Emit `[]` to satisfy the downstream minimum while explicitly representing unavailable author metadata. This disables the first-author fuzzy-dedupe guard. |
| `publicationDate` | `year` | Parse a valid four-digit publication year; otherwise set `null`. A null year disables the year fuzzy-dedupe guard. |
| `abstract` | `abstract` | Preserve text when supplied; otherwise set `null`. |
| `citations` | `cited_by_count` | Preserve an integer citation count when supplied; otherwise set `null`. |
| `votes` | `orx_votes` | Preserve as declared source-specific metadata when supplied. |
| `snippets` | `orx_snippets` | Preserve as declared source-specific match evidence when supplied. |
| *(derived from `doi`)* | `identifier_less` | `true` when `doi` is null; `false` otherwise. |

The adapter MUST NOT synthesize authors, venue, publication type, retraction status, or reference
lists from absence. Downstream code may preserve the declared extra fields above, but unavailable
metadata must remain distinguishable from a verified negative or zero.

**Search record, generated log, and provenance**

- **FR-028**: Acquisition MUST emit `corpus/acquisition-record.json` as the canonical structured
  account of what the search did. It MUST be one JSON object with a closed schema and required
  schema version, suitable for the repository's shared gate contract.
- **FR-013**: The acquisition record MUST capture per query: backend, sub-source, exact submitted
  query, date, outcome (`answered`, `empty`, or `failed-and-fell-back`), returned count,
  normalization-drop counts/reasons, counts lacking DOI/authors/year, and OpenResearch version when
  enrichment answered.
- **FR-014**: The acquisition record MUST distinguish a legitimate zero-result query from an
  enrichment failure followed by keyless fallback.
- **FR-015**: When any query was answered successfully by an enriched source, the acquisition record
  MUST include an explicit statement that the search is not fully reproducible without OpenResearch,
  naming affected queries and the backend version(s) that answered them.
- **FR-029**: `corpus/search-log.md` MUST be generated from the acquisition record and MUST NOT be
  maintained as a second hand-authored source of truth.
- **FR-021**: Use of enrichment MUST be stamped as an AI-assisted acquisition step under the
  repository's provenance convention, including backend, sub-source, and OpenResearch version.

**Downstream compatibility**

- **FR-016**: Records lacking a DOI MUST be admitted for recall, tagged `identifier_less: true`, and
  retain the alternative `source_id` supplied by OpenResearch.
- **FR-022**: Counts of admitted records lacking DOI, authors, and year MUST be recorded in the
  acquisition record and reported at handoff. The skill MUST disclose that missing DOI removes exact
  matching, missing authors disables the first-author fuzzy-dedupe guard, and missing year disables
  the year guard; when all are absent, title similarity alone may falsely merge distinct works and
  deflate records-screened.
- **FR-023**: The skill MUST state the verification cost accurately: DOI-less records cannot be
  resolved directly by DOI, but `verify-sources` can attempt title/author/year reverse lookup. When
  author or year is unavailable, that lookup is less discriminating and more records may remain
  `UNVERIFIED` pending human review.
- **FR-030**: This feature MUST NOT modify `dedupe-records` or `verify-sources`. Improving their
  behaviour for sparse enriched records is separate work.

**Enforcement posture**

- **FR-017**: A runnable disclosure check MUST consume the canonical acquisition record and verify
  that any record describing successfully enriched queries contains the FR-015 disclosure.
- **FR-024**: The disclosure check MUST conform to the shared CLI gate contract in full: one JSON
  object read from a path or standard input; `--strict` selects enforcement; exit `0` means clean or
  non-strict, exit `1` a method violation under `--strict`, exit `2` malformed input; unknown keys,
  invalid JSON, wrong/missing schema version, or a non-object input are malformed. `--json` changes
  only output format and uses the shared machine-readable envelope. Missing enrichment disclosure in
  an otherwise well-formed record is a method violation, not malformed input.
- **FR-025**: The check MUST pass a valid keyless acquisition record without complaint.
- **FR-026**: The check MUST document what it cannot verify — at minimum that the record is truthful,
  that the recorded OpenResearch version actually answered, that source attribution is true, and
  that declared counts agree with separate candidate files. It does not re-run discovery.
- **FR-027**: The disclosure check MUST NOT be represented as making `acquire-corpus` PRISMA-S
  compliant. It enforces enrichment disclosure only; the skill's PRISMA-S posture remains guidance.

**Constitutional constraints**

- **FR-018**: The feature MUST introduce no dependency required to import or run the skill's scripts.
  OpenResearch is consulted only as an external program.
- **FR-019**: The skill MUST remain functional when copied out of this repository on its own with no
  OpenResearch present.
- **FR-020**: The skill MUST state what OpenResearch cannot verify — at minimum that relevance
  ranking is opaque, recall against the review question is uncharacterized, and coverage of the
  underlying sources is unquantified.

### Key Entities

- **Corpus record**: One candidate work. The downstream minimum is `doi`, `title`, `authors`, and
  `year`; this feature adds explicit `source`, `sub_source`, `source_id`, and `identifier_less`
  provenance/availability fields for enriched records without changing existing field meanings.
- **Acquisition record**: The canonical, closed-schema one-object JSON account of the executed
  search. It contains query provenance, outcomes/counts, normalization losses, sparse-metadata
  counts, backend versions, and the optional reproducibility disclosure.
- **Search log**: The human-readable PRISMA-S-oriented artifact generated from the acquisition record.
  It is never the source of truth.
- **Field mapping**: The normative correspondence between OpenResearch `LitHit` fields and corpus
  fields, including explicit absence behaviour.
- **Backend availability verdict**: A per-query outcome — enrichment answered within the deadline or
  the query fell back. No daemon/service state is represented.
- **Reproducibility disclosure**: The FR-015 statement present when and only when enrichment
  contributed successfully.
- **Disclosure verdict**: Clean, method violation, or malformed input as determined by the disclosure
  gate; it says whether the record disclosed enrichment, not whether the search itself was good.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With OpenResearch absent, candidate output and exit code are identical to pre-feature
  behaviour for 100% of tested queries.
- **SC-002**: With OpenResearch absent, acquisition adds no more than one second wall-clock time
  versus the pre-feature run.
- **SC-003**: With `orx` present but an enrichment invocation unreachable or hung, each failed
  enrichment attempt terminates within five seconds and the affected query continues keyless.
- **SC-004**: 100% of emitted candidates have backend/sub-source attribution; 100% of enriched
  candidates carry `source_id`, and the downstream minimum keys (`doi`, `title`, `authors`, `year`)
  are present with null/empty values only where explicitly allowed by the mapping.
- **SC-005**: A reader unfamiliar with the run can determine from the generated search log, for every
  query in a sample, whether OpenResearch is required to reproduce it.
- **SC-006**: Malformed transport, timeout, unsupported top-level record keys, and other unusable
  enriched responses never abort acquisition; each tested case degrades to the keyless path.
- **SC-007**: The skill copied out alone with no OpenResearch completes acquisition and produces a
  candidate set, acquisition record, and generated search log.
- **SC-008**: For a question with known full-text-only exemplars, enriched discovery returns at least
  one exemplar absent from the keyless-only run.
- **SC-009**: Every normalization drop is represented by count and reason in the acquisition record.
- **SC-010**: The disclosure check fails a well-formed enriched acquisition record missing the
  disclosure and passes the same record after disclosure is added.
- **SC-011**: The disclosure check passes 100% of valid keyless acquisition records.
- **SC-012**: Counts of admitted records lacking DOI, authors, and year appear in 100% of acquisition
  records where those conditions occur, exposing the population at increased false-merge/manual-
  verification risk before downstream processing.
- **SC-013**: Regenerating `search-log.md` from the same acquisition record produces identical
  search documentation; the human-readable log and structured source of truth cannot drift.

## Assumptions

- **Enrichment is on by default when usable.** FR-005 provides a keyless-only opt-out for a reviewer
  who needs a search reproducible without OpenResearch.
- **Discovery needs no daemon, account, or key.** Current upstream literature discovery uses public
  endpoints directly. This feature must not add an unnecessary background-service health model.
- **The backend is an external program.** No OpenResearch library is imported and no long-lived
  connection is managed by this skill.
- **The reviewed upstream discovery shape is version-sensitive.** Current `LitHit` serialization
  contains `source`, `id`, `title`, `abstract`, `publicationDate`, and optional `votes`, `citations`,
  and `snippets`. OpenResearch is pre-1.0, so additive or breaking output changes are possible.
- **Unknown upstream fields fail closed.** This is deliberately less forward-compatible than
  ignoring additive fields, but it satisfies Principle IV without an amendment. Because
  OpenResearch is optional enrichment, schema drift may safely reduce the run to keyless discovery
  until the adapter mapping is reviewed and updated.
- **Metadata sparsity is preserved rather than fabricated.** Current discovery output does not
  guarantee authors, venue, publication type, retraction state, or reference lists. The mapping
  explicitly represents unavailable data and the downstream costs are disclosed.
- **Keyless discovery remains primary.** Enrichment cannot remove or replace a keyless result and
  cannot change the guaranteed path's exit semantics.
- **Scope is discovery only.** `orx paper` full-text reading, OpenResearch experiment/run machinery,
  and agent execution are out of scope.
- **Sparse records are admitted with a known cost.** Recall wins at acquisition, while false-merge
  and manual-verification exposure is measured and disclosed before downstream use.
- **No downstream remediation is hidden in this feature.** `dedupe-records` and `verify-sources`
  remain unchanged under FR-030; follow-up changes require separate work.
- **The acquisition record is the source of truth.** The Markdown log is generated from it, satisfying
  the repository's artifact-generation rule and giving the gate one structured object to consume.
- **The disclosure check inherits repository gate rules.** It requires a test module and the shared
  CLI/exit-code/output contract.
- **The disclosure gate does not upgrade standards claims.** It enforces enrichment disclosure only;
  PRISMA-S remains guidance rather than machine-verified compliance.
