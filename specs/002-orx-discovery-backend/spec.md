# Feature Specification: orx Discovery Backend for acquire-corpus

**Feature Branch**: `claude/openresearch-agentic-research-diff-fq5xyi`

**Feature Directory**: `specs/002-orx-discovery-backend`

**Created**: 2026-09-09

**Last Revised**: 2026-09-10 — reviewer rounds 1 and 2 addressed

**Status**: Draft — ready for independent re-review

**Input**: Add OpenResearch's `orx discover` as optional, detect-and-degrade discovery enrichment for `acquire-corpus`. The existing keyless OpenAlex/CrossRef path remains the only guaranteed path. Enrichment may add alphaXiv full-text keyword retrieval, semantic retrieval, OpenAlex discovery, and bioRxiv discovery, but it must not weaken portability, reproducibility disclosure, fail-closed behavior, or downstream study-count integrity.

> **Correction to the original premise.** `orx discover` does not require a local daemon or login.
> Current upstream literature discovery invokes public literature endpoints directly. Availability is
> therefore modeled as executable presence plus bounded discovery invocations, not background-service
> health.

## Review corrections incorporated

### Reviewer round 1

Five findings against the original draft are resolved:

| # | Finding | Resolution |
|:--|:--------|:-----------|
| 1 | Availability assumed a local daemon | `orx discover` is modeled as a public-endpoint CLI call with bounded timeout and keyless fallback. |
| 2 | Gate input could not be JSONL + Markdown under the shared contract | `corpus/acquisition-record.json` is the one closed-schema source of truth; `corpus/search-log.md` is generated from it. |
| 3 | Unknown upstream fields conflicted with Principle IV | Unknown top-level `LitHit` keys fail closed: the enriched response is unsupported and the affected query falls back keyless. |
| 4 | `LitHit` did not supply the assumed corpus shape | The mapping below distinguishes directly supplied fields from bibliographic metadata that must be completed before safe admission. |
| 5 | `verify-sources` limitation was overstated | DOI-less records cannot be resolved directly by DOI, but title/author/year reverse lookup remains available when sufficient metadata exists. |

### Reviewer round 2

Three further findings at `10b8f964` are resolved in this revision:

| # | Finding | Resolution |
|:--|:--------|:-----------|
| 1 | Mandatory record-level provenance conflicted with unchanged keyless output | Existing keyless candidate records remain schema/content-compatible with pre-feature output. Keyless provenance is recorded in the canonical acquisition record and existing per-source raw artifacts; only enriched records carry the new enriched-record provenance fields. |
| 2 | `authors: []` violated fail-closed semantics and exposed title-only false merges | No empty/default author list is synthesized. An enriched hit must be completed to the dedupe-safe bibliographic minimum before admission; otherwise it is preserved in `corpus/enrichment-unresolved.jsonl` and excluded from `candidates.jsonl`. |
| 3 | Per-invocation timeout allowed cumulative stalls | A per-sub-source circuit breaker and run-level enrichment failure budget prevent repeated failed calls from accumulating unbounded delay. |

The safety rule for sparse enrichment is now explicit: **recall evidence may be preserved without being
fed into an unsafe deduplication path**. A hit that cannot be completed to the bibliographic fields
required for guarded deduplication is not discarded silently; it is retained as unresolved evidence,
counted, logged, and handed off for manual or later resolution, but it does not enter the automatic
candidate/dedupe path.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Wider discovery when OpenResearch is usable (Priority: P1)

A reviewer running `acquire-corpus` on a machine with `orx` installed can receive candidate works
that metadata-only keyword discovery may miss: alphaXiv full-text matches, semantic matches, and
bioRxiv/OpenAlex results. Enriched hits are normalized, bibliographically completed when necessary,
and admitted only when they can safely enter the existing downstream deduplication contract.

**Independent Test**: Use a question with a known full-text-only exemplar. Confirm that enrichment
finds the exemplar, then confirm that an enriched hit enters `candidates.jsonl` only after satisfying
the safe-admission rule in FR-031; otherwise it appears in `enrichment-unresolved.jsonl`.

**Acceptance Scenarios**:

1. **Given** a supported enriched response and sufficient bibliographic metadata, **When** acquisition
   runs, **Then** the enriched work is admitted with enriched-source provenance and downstream-safe
   bibliographic fields.
2. **Given** an enriched work duplicates a keyless work, **When** candidates are assembled, **Then**
   both are retained for `dedupe-records`; acquisition does not perform cross-source deduplication.
3. **Given** an enriched hit cannot be completed safely, **When** acquisition finishes, **Then** the
   hit is preserved in `corpus/enrichment-unresolved.jsonl`, counted in the acquisition record, and
   excluded from the automatic candidate/dedupe path.

---

### User Story 2 — Identical keyless behavior when OpenResearch is absent or unusable (Priority: P1)

A reviewer with no `orx` installed gets the existing keyless acquisition behavior. Candidate records
are not rewritten merely to attach new provenance fields. No warning, prompt, installation advice,
changed exit code, or meaningful delay is introduced.

**Independent Test**: Run acquisition with `orx` absent and compare `candidates.jsonl` plus exit code
to the pre-feature run for the same query.

**Acceptance Scenarios**:

1. **Given** OpenResearch is absent, **When** acquisition runs, **Then** keyless candidate records and
   exit semantics remain compatible with the pre-feature output contract.
2. **Given** OpenResearch is absent, **When** acquisition runs, **Then** no output stream emits an
   OpenResearch warning, error, prompt, or installation suggestion.
3. **Given** OpenResearch is present but one enriched sub-source fails, **When** acquisition runs,
   **Then** the query falls back keyless and the circuit breaker prevents repeated failed attempts to
   that sub-source during the same run.
4. **Given** OpenResearch is usable, **When** the reviewer requests keyless-only acquisition, **Then**
   no enriched command is invoked.

---

### User Story 3 — Search documentation discloses reproducibility and losses (Priority: P2)

A reader can determine which backend answered each query, which enriched hits were admitted, which
were unresolved, whether OpenResearch is required to reproduce the search, and whether any
normalization or metadata-completion loss occurred. One structured acquisition record is the source
of truth and the human-readable search log is generated from it.

**Independent Test**: Run enriched and keyless acquisitions, inspect `acquisition-record.json`,
regenerate `search-log.md`, and run the disclosure gate against both.

**Acceptance Scenarios**:

1. Every query entry records backend/sub-source, submitted query, date, outcome, returned count,
   normalization drops, unresolved-enrichment count, and OpenResearch version when used.
2. Successful enrichment requires an explicit non-keyless reproducibility disclosure naming the
   affected queries and backend version(s).
3. A keyless-only run carries no OpenResearch reproducibility caveat.
4. `search-log.md` is generated from `acquisition-record.json`; it is never independently authored.
5. An enriched acquisition record missing required disclosure fails the disclosure gate under
   `--strict` as a method violation.
6. A valid keyless acquisition record passes the disclosure gate.

---

### User Story 4 — The skill remains portable (Priority: P3)

Someone copies `skills/acquire-corpus/` into another project with no OpenResearch installation and no
access to sibling repository code. Keyless acquisition still works.

**Independent Test**: Copy the skill directory outside the repository, remove `orx` from `PATH`, and
run acquisition to completion.

**Acceptance Scenarios**:

1. The copied skill completes keyless acquisition and produces candidates, an acquisition record,
   and a generated search log.
2. No import resolves to a sibling skill, shared repository library, or path outside the copied skill.

## Edge Cases

- **Binary present, public endpoint unavailable.** The failed enriched sub-source opens its circuit
  for the remainder of the run; acquisition proceeds keyless.
- **Discovery invocation hangs.** The process is terminated at the per-invocation deadline and its
  sub-source circuit opens.
- **Repeated failures across sub-sources.** The run-level enrichment failure budget stops further
  enrichment attempts once exhausted; remaining queries are keyless.
- **Malformed transport.** Non-JSON, truncated JSON, a non-collection top-level value, or an empty
  stream is an enrichment failure. A valid empty collection is a genuine zero-result response.
- **Unknown upstream record key.** The enriched response fails closed under FR-007 and falls back
  keyless.
- **Required discovery field missing.** The record is non-normalizable, counted, and not emitted.
- **Authors unavailable.** No `authors: []` placeholder is synthesized. Metadata completion is
  attempted; failure sends the hit to `enrichment-unresolved.jsonl`.
- **Year unavailable.** No null/empty year is used to bypass the dedupe guard. The hit must be
  completed or remain unresolved.
- **DOI unavailable but author/year metadata is verified.** The record may still be admitted under
  FR-016 because guarded fuzzy deduplication remains available and the alternative source identifier
  is preserved.
- **All enriched hits remain unresolved.** The keyless candidate set remains valid; unresolved hits
  are reported separately and do not masquerade as admitted candidates.
- **Disclosure absent from an otherwise valid enriched acquisition record.** Exit `1` under
  `--strict`.
- **Acquisition record malformed, wrong-schema, or carrying unknown keys.** Exit `2`.
- **Version changes during a project.** Version is recorded per enriched query rather than once per
  run.
- **Enrichment dominates identification counts.** Admitted, unresolved, and normalization-dropped
  counts remain separately auditable.

## Requirements *(mandatory)*

### Functional Requirements

**Availability, degradation, and bounded failure**

- **FR-001**: The skill MUST NOT assume or probe a local OpenResearch daemon. Executable presence is
  the local prerequisite; usability is determined by bounded `orx discover` invocations.
- **FR-002**: Each enriched invocation MUST terminate within five seconds on timeout/unreachability
  and MUST NOT block acquisition indefinitely.
- **FR-003**: Absence or failure of enrichment MUST NOT emit an OpenResearch warning/error, prompt the
  user, suggest installation, alter keyless exit semantics, or prevent keyless completion.
- **FR-004**: A failed enriched query MUST fall back to the keyless path and be recorded as
  `failed-and-fell-back`, not as a legitimate zero-result query.
- **FR-005**: The reviewer MUST be able to force keyless-only acquisition even when OpenResearch is
  usable.
- **FR-033**: A timeout, network failure, command-surface failure, or unsupported-schema failure MUST
  open a circuit for the affected enriched sub-source for the remainder of the run. No automatic
  retry is permitted after the circuit opens. The cumulative failure-wait budget across all enriched
  sub-sources MUST NOT exceed fifteen seconds per run; after the budget is exhausted, all remaining
  enrichment attempts are skipped and queries continue keyless.

**Record handling and safe admission**

- **FR-006**: The adapter MUST normalize supported `LitHit` results using the explicit mapping below.
  It MUST NOT fabricate bibliographic values merely to resemble an OpenAlex record.
- **FR-007**: Every enriched response MUST be validated against the supported top-level `LitHit`
  keys. If any record contains an unrecognized top-level key, the response is unsupported: no record
  from that response is emitted, the sub-source circuit opens, and the query falls back keyless.
- **FR-008**: Within a supported shape, a record missing a required discovery field (`source`, `id`,
  or usable `title`) MUST be dropped with a counted reason. A non-empty response yielding zero
  normalizable records MUST fall back keyless.
- **FR-009**: Existing keyless candidate records MUST remain schema/content-compatible with the
  pre-feature candidate contract and MUST NOT be rewritten solely to add `source`/`sub_source`
  fields. Keyless backend provenance MUST instead be recorded per query in
  `corpus/acquisition-record.json` and remain auditable through existing per-source raw artifacts.
  Every **enriched** admitted candidate MUST carry `source: "orx"`, `sub_source`, and `source_id`.
- **FR-010**: Enriched raw responses and normalized enriched records MUST be written to source-
  specific raw artifacts so returned/admitted/unresolved counts can be reconciled.
- **FR-011**: `acquire-corpus` MUST NOT deduplicate across keyless/enriched backends.
- **FR-012**: If an enriched source applies opaque ranking, truncation, or internal selection, the
  acquisition record MUST disclose it and MUST NOT label it as the review's deduplication step.
- **FR-031**: Before an enriched hit may enter `candidates.jsonl`, it MUST satisfy the downstream
  dedupe-safe bibliographic minimum: usable `title`, a non-empty verified `authors` list, and a
  verified `year`. A DOI is preferred but not mandatory; when absent, a stable `source_id` MUST be
  retained. Metadata completion MAY use the skill's existing keyless bibliographic sources, but a
  field not actually resolved MUST remain missing and MUST NOT be defaulted to an empty/zero value.
- **FR-032**: An enriched hit that cannot satisfy FR-031 MUST NOT enter `candidates.jsonl`. It MUST be
  preserved in `corpus/enrichment-unresolved.jsonl` with source identifier, title, available
  discovery metadata, and a machine-readable reason for non-admission. Its count MUST be reported in
  the acquisition record and generated search log.

#### Normalized enriched discovery mapping

Current upstream `LitHit` serialization is the external discovery contract understood by this
feature. Unknown top-level keys invoke FR-007 until deliberately reviewed and added.

| OpenResearch field | Normalized field | Rule |
|:--|:--|:--|
| `source` | `source`, `sub_source` | `source` is `orx`; preserve upstream source (`alphaxiv`, `openalex`, `biorxiv`) as `sub_source`. Required. |
| `id` | `source_id` | Preserve verbatim. Required. |
| `id` | `doi` | Populate only when syntactically a DOI; otherwise DOI remains unresolved unless metadata completion finds one. |
| `title` | `title` | Required non-empty string. |
| *(not supplied by discovery)* | `authors` | **Do not synthesize or emit an empty placeholder.** Resolve through metadata completion before admission; otherwise FR-032 applies. |
| `publicationDate` | `year` | May supply the year when valid; otherwise metadata completion must resolve it before admission. |
| `abstract` | `abstract` | Preserve when supplied. |
| `citations` | `cited_by_count` | Preserve integer count when supplied. |
| `votes` | `orx_votes` | Preserve source-specific metadata when supplied. |
| `snippets` | `orx_snippets` | Preserve source-specific match evidence when supplied. |
| *(derived after completion)* | `identifier_less` | `true` only when the admitted record has no DOI; `false` otherwise. |

The adapter MUST NOT invent authors, venue, publication type, retraction status, references, DOI, or
year. Missing metadata is a resolution problem, not a value to encode as empty merely to satisfy a
shape check.

**Search record, generated log, and provenance**

- **FR-028**: Acquisition MUST emit `corpus/acquisition-record.json` as the canonical structured
  account of the search. It MUST be one closed-schema JSON object with required schema version.
- **FR-013**: The acquisition record MUST capture per query: backend/sub-source, submitted query,
  date, outcome, returned count, normalization-drop counts/reasons, admitted enriched count,
  unresolved-enrichment count/reasons, circuit-breaker state, and OpenResearch version when used.
- **FR-014**: The record MUST distinguish `answered`, `empty`, `failed-and-fell-back`, and
  `skipped-circuit-open` outcomes.
- **FR-015**: When any query was answered successfully by enrichment, the acquisition record MUST
  state that the search is not fully reproducible without OpenResearch, naming affected queries and
  backend version(s).
- **FR-029**: `corpus/search-log.md` MUST be generated from the acquisition record and MUST NOT be a
  separately hand-maintained source of truth.
- **FR-021**: Successful enriched acquisition MUST be stamped as AI-assisted provenance with backend,
  sub-source, and OpenResearch version.

**Downstream compatibility**

- **FR-016**: A DOI-less enriched record MAY be admitted only after FR-031 is satisfied. It MUST
  retain `source_id`, `authors`, and `year` so downstream fuzzy deduplication keeps its collision
  guards. DOI-less records that cannot satisfy FR-031 remain unresolved under FR-032.
- **FR-022**: The acquisition record and generated log MUST report counts of admitted DOI-less
  enriched records and unresolved records missing authors/year. The handoff MUST state that admitted
  DOI-less records lack exact DOI matching but retain the author/year guards; unresolved sparse hits
  are intentionally withheld from automatic deduplication to prevent title-only false merges.
- **FR-023**: Documentation MUST state that DOI-less admitted records cannot be resolved directly by
  DOI but may use title/author/year reverse lookup. Unresolved records are not represented as
  verified candidates and require manual or later bibliographic resolution.
- **FR-030**: This feature MUST NOT modify `dedupe-records` or `verify-sources`. Safe admission in
  `acquire-corpus` is the compatibility boundary for this feature.

**Enforcement posture**

- **FR-017**: A runnable disclosure check MUST consume the canonical acquisition record and verify
  that successful enrichment carries the FR-015 disclosure.
- **FR-024**: The disclosure check MUST follow the shared gate contract: one JSON object from path or
  stdin; `--strict`; exit `0` clean/non-strict, `1` method violation under strict, `2` malformed;
  unknown keys/wrong schema/non-object/invalid JSON are malformed; `--json` changes only output
  format using the shared envelope.
- **FR-025**: A valid keyless acquisition record MUST pass without complaint.
- **FR-026**: The check MUST state what it cannot verify, including truthfulness of provenance,
  backend version, source attribution, candidate-file counts, and correctness of metadata resolution.
- **FR-027**: The disclosure gate MUST NOT be represented as making `acquire-corpus` PRISMA-S
  compliant. PRISMA-S remains guidance/alignment only.

**Constitutional constraints**

- **FR-018**: No dependency may be required to import or run the skill's scripts. OpenResearch is an
  external optional executable.
- **FR-019**: The skill MUST remain functional when copied out alone with no OpenResearch present.
- **FR-020**: The skill MUST state what OpenResearch cannot verify: at minimum opaque ranking,
  uncharacterized recall against the review question, and unquantified source coverage.

### Key Entities

- **Keyless candidate record**: Existing pre-feature candidate schema; not rewritten solely for new
  provenance.
- **Enriched admitted record**: An `orx` discovery hit that satisfies FR-031 and carries enriched
  provenance plus downstream-safe bibliographic fields.
- **Unresolved enriched hit**: Discovery evidence preserved in `enrichment-unresolved.jsonl` because
  it cannot safely enter the automatic dedupe path.
- **Acquisition record**: Closed-schema source of truth for query provenance, outcomes, counts,
  unresolved evidence, circuit state, and reproducibility disclosure.
- **Search log**: Human-readable artifact generated from the acquisition record.
- **Circuit breaker**: Per-sub-source run state that prevents repeated failed enrichment calls.
- **Disclosure verdict**: Gate result concerning enrichment disclosure only, not search quality.

## Success Criteria *(mandatory)*

- **SC-001**: With OpenResearch absent, keyless candidate output and exit code remain compatible with
  pre-feature behavior for 100% of tested queries.
- **SC-002**: With OpenResearch absent, acquisition adds no more than one second wall-clock time.
- **SC-003**: A failed enriched sub-source incurs at most one five-second failure wait in a run; total
  failure waiting across all enriched sub-sources never exceeds fifteen seconds.
- **SC-004**: 100% of admitted enriched candidates carry `source`, `sub_source`, `source_id`, usable
  title, non-empty verified authors, and verified year. Existing keyless candidates are not required
  to gain new record-level provenance fields.
- **SC-005**: A reader can determine from the generated log which queries require OpenResearch to
  reproduce.
- **SC-006**: Malformed transport, timeout, unknown top-level keys, or unsupported enriched output
  never aborts acquisition and cannot trigger repeated calls after its sub-source circuit opens.
- **SC-007**: The copied-out skill completes keyless acquisition without OpenResearch.
- **SC-008**: For a known full-text-only exemplar, the enriched run records at least one discovery
  absent from keyless-only search, either as safely admitted or explicitly unresolved evidence.
- **SC-009**: Every normalization drop and unresolved enriched hit is represented by count and reason
  in the acquisition record.
- **SC-010**: No admitted enriched record uses an empty/default author list or missing year to satisfy
  the downstream minimum.
- **SC-011**: The disclosure gate fails a well-formed enriched acquisition missing disclosure and
  passes it after disclosure is added.
- **SC-012**: The disclosure gate passes 100% of valid keyless acquisition records.
- **SC-013**: Regenerating `search-log.md` from the same acquisition record produces identical
  documentation.
- **SC-014**: A constructed same-title/different-study case with an unresolved author-less hit cannot
  be falsely merged by `dedupe-records` because the unresolved hit never enters `candidates.jsonl`.

## Assumptions

- **Enrichment is on by default when usable.** FR-005 provides a keyless-only opt-out.
- **Discovery needs no daemon, account, or key.** Current literature discovery uses public endpoints.
- **The backend is an external program.** No OpenResearch library is imported.
- **The reviewed `LitHit` shape is version-sensitive.** Additive/breaking upstream changes are
  possible and fail closed until reviewed.
- **Keyless candidate compatibility is intentional.** New per-query provenance belongs in the
  acquisition record; the feature does not rewrite historical keyless records merely for symmetry.
- **Metadata sparsity is not fabricated away.** Missing author/year data triggers completion or the
  unresolved path; empty placeholders are forbidden for safe-admission fields.
- **Recall evidence can exist outside the automatic candidate set.** `enrichment-unresolved.jsonl`
  preserves discovered evidence that is methodologically unsafe to deduplicate automatically.
- **No downstream remediation is hidden here.** `dedupe-records` and `verify-sources` remain unchanged;
  this feature protects them by enforcing a safe admission boundary.
- **The acquisition record is the source of truth.** The Markdown search log is generated from it.
- **The disclosure gate does not upgrade standards claims.** It enforces enrichment disclosure only;
  PRISMA-S remains guidance rather than machine-verified compliance.
