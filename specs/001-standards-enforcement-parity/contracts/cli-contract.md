# Contract: Shared CLI Behaviour

Binding on all four checks — the existing flow check and the three added by this feature. A check
that deviates is non-conforming regardless of whether its own rules are correct.

## Invocation

```
python <check>.py <record.json> [--strict] [--json] [check-specific options]
echo '{...}' | python <check>.py [--strict]
```

The record is read from the path argument, or from standard input when no path is given. This
mirrors `prisma_flow.py` exactly.

## Exit codes

| Code | Meaning | Emitted when |
|:--:|:--|:--|
| `0` | Clean, or issues found without `--strict` | Record is well-formed and either satisfies every rule, or violates rules while `--strict` is absent |
| `1` | Method violation under enforcement | `--strict` given and at least one rule is violated |
| `2` | Malformed input | Not valid JSON; not an object; unknown key; missing or unrecognised `schema_version`; value outside its permitted vocabulary; count that is boolean or non-integral; duplicate identifier; empty primary collection |

Exit `2` is never reachable from a review being *wrong* — only from a record being *unreadable*.
The verification loop depends on this distinction: exit `1` is outstanding work, exit `2` is an
authoring error requiring a human.

## Output

Standard output carries the generated Markdown artifact followed by the verdict section:

```markdown
# <Artifact title>

<generated tables / diagram>

## <Check name>

✅ <clean statement>
```

or

```markdown
## <Check name>

⚠️ **<N> issue(s)** — fix before reporting:
- <exact discrepancy, one per line>
```

Malformed-input diagnostics go to standard error prefixed with the check name, and no artifact is
emitted — a record that cannot be read must not produce a document that looks authoritative.

## Machine-readable output — `--json`

Binding on all four, like `--strict`. It **replaces** the artifact: standard output carries one
JSON object and nothing else, so a consumer parses the whole stream rather than a prefix of it.

Deliberately not in a `json` fence: `tests/test_contract_examples.py` executes every fenced `json`
block in this directory as an input RECORD, and this is a sample of OUTPUT — it could only fail
there for being the wrong kind of thing.

```
{"check": "grade_profile", "schema_version": "1.0", "issues": 5,
 "units": {"U_grade": 2, "U_rob_trace": 1}, "gates": {}, "unattributed": 1,
 "detail": {"failing_results": ["O1", "O4"]}}
```

| Field | Meaning |
|:--|:--|
| `check` | The check's own name. A consumer verifies it, so a script identifying as another one is rejected rather than believed |
| `schema_version` | Version of this **envelope**, not of the input record |
| `issues` | Diagnostics raised — the `N` in `⚠️ **N issue(s)**`. A human number, not a unit count |
| `units` | The unit counts this check DEFINES, by their `review_units.py` names |
| `gates` | The human-gate counts it defines |
| `unattributed` | Issues belonging to no unit and no gate. A consumer that dropped these would read work it cannot count as no work at all |
| `detail` | Optional, advisory. No consumer may depend on it — the counts above are the contract |

Three rules make the number trustworthy rather than merely present:

- **A count is emitted, never re-derived.** `U_grade` is failing results and one result can raise
  four diagnostics; a consumer counting messages books four units of work for one broken result.
  The check owns its unit's definition, so it prints the number rather than leaving it to be
  reconstructed from prose.
- **`--json` does not change the exit code.** It is an output format. A flag that changed the
  verdict as well as the rendering could not be added to an existing invocation safely.
- **Malformed input emits no envelope.** Exit 2 means the record was never evaluated, and an
  envelope of zeros there is the shape a consumer trusts carrying counts nothing produced — the
  single worst output this contract could permit.

`review_units.py` consumes this to derive its counts instead of trusting the ones its own record
asserts; see [review-units.md](./review-units.md).

## Discrepancy message style

Each message states the observed values and the expected relation, so the reader can act without
re-deriving it. Modelled on the existing reconciliation output:

```
eligibility (databases/registers): assessed 72 - excluded(full-text) 34 = 38,
but studies_included_databases = 40
```

Not `"eligibility mismatch"`. A message that names the rule without the numbers forces the reader
back into the record.

## Mandatory documentation

Every check's skill documents what that check **cannot** verify (constitution Principle VI). At
minimum:

| Check | Cannot verify |
|:--|:--|
| Flow diagram | That the counts are true — only that they reconcile |
| Certainty | That a domain judgment was the right call — only that it is present, legal, and arithmetically consistent |
| Appraisal | That a human actually confirmed — only that a confirmation record exists |
| Checklist | That the cited location genuinely addresses the item — only that a location or justification was recorded |

## Shared input coercion

Reimplemented per script (research.md D-001, D-002), identical in behaviour:

- Booleans are rejected as counts, including `True`, which Python would otherwise coerce to `1`.
- Floats are accepted only when integral; `3.0` is `3`, `3.5` is malformed.
- Negative counts are malformed.
- Non-finite values (`NaN`, `Infinity`) are malformed.
- **Numeric strings are rejected.** `"3"` is malformed input, not `3`.

A conformance test asserts all four scripts agree on this table of inputs.

### ⚠️ Pre-existing divergence to resolve

The two existing scripts **already disagree** on the last rule, and this was discovered while
drafting this contract rather than being a consequence of the feature:

| Script | Numeric string `"3"` |
|:--|:--|
| `prisma_flow.py` `_int()` | **Accepted** — falls through to `int(str(v).strip())` |
| `review_units.py` `_as_count()` | **Rejected** — "the contract requires JSON numbers, so a wrong type fails closed" |

The contract above adopts the stricter behaviour, because constitution Principle IV requires that
input be rejected rather than coerced, and because a quoted count in a hand-authored record is
more likely a mistake than an intention.

Adopting it means **changing `prisma_flow.py`'s existing behaviour**, which is a behavioural change
to a working, shipped script. It is low-risk — JSON counts are naturally written unquoted, and the
repository ships no record using quoted counts — but it is a change, not a clarification, and it
must be called out in the pull request rather than folded in silently. This is the first instance
of the spec's "pre-existing defects surfaced by new coverage" rule and is tracked as its own task.
