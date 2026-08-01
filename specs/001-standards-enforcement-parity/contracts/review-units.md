# Contract: Review Units Record (`units.json`) — extension

Consumed by the existing `skills/verify-review/scripts/review_units.py`. This feature **extends**
an established contract; everything not listed here is unchanged.

## Existing configuration (unchanged)

```python
DEFAULT_WEIGHTS = {
    "U_cite_external": 3, "U_cite_internal": 1, "U_screen": 1,
    "U_extract": 1, "U_prisma": 1, "U_grade": 1, "U_consistency": 1,
}
GATE_KEYS      = ("H_rob", "H_screen_adj", "H_cite_manual", "H_numeric")
UNIVERSAL_FLOOR = ("U_cite_external", "U_cite_internal", "U_consistency")
CONSISTENCY_GATE = 75 ; PLATEAU_K = 3 ; CEILING = 25
```

## Additions

```python
DEFAULT_WEIGHTS["U_rob_trace"] = 1
DEFAULT_WEIGHTS["U_checklist"] = 1
```

`U_grade` keeps its weight of 1 and its key. Only its **definition** changes: from the undocumented
"themes not yet graded" to "results failing the certainty check under `--strict`" (FR-023).
`H_rob` keeps its key and its position in `GATE_KEYS`; only its **source** changes, from asserted
to computed by the appraisal check (FR-014). A matching but unconfirmed appraisal belongs
exclusively to `H_rob`; it is not also counted as `U_rob_trace`.

`UNIVERSAL_FLOOR` is **not** extended. The floor is the set every review type must satisfy however
light; certainty, traceability, and reporting completeness are review-type dependent and belong in
the in-scope set instead.

## Unit definitions

| Unit | Weight | Produced by | Counts |
|:--|:--:|:--|:--|
| `U_grade` | 1 | certainty check | Results violating any certainty rule |
| `U_rob_trace` | 1 | certainty check with `--rob` | References not resolving at the named `(study, result)` target; matching but unconfirmed appraisals are excluded |
| `U_checklist` | 1 | checklist check | Rows neither located nor justified |
| `H_rob` | gate | appraisal check | **Appraisals** lacking confirmation, keyed `(study, result)` — one study appraised for two results counts twice |

## In-scope resolution by review type

Passed as `units_in_scope`, resolved once at classification and frozen for the run.

| Unit | systematic | umbrella | rapid | scoping | narrative |
|:--|:--:|:--:|:--:|:--:|:--:|
| `U_grade` | ✅ | ✅ | ✅ | ⬜ | ⬜ |
| `U_rob_trace` | ✅ | ✅ | ⬜ | ⬜ | ⬜ |
| `U_checklist` | ✅ | ✅ | ✅ | ⬜ | ⬜ |
| `H_rob` | ✅ | ✅ | ⬜ | ⬜ | ⬜ |

`U_rob_trace` and `H_rob` are out of scope for rapid reviews because the heuristic basis is
permitted there (research.md D-009); a rapid review still grades certainty, so `U_grade` applies.
The PRISMA-ScR checklist checker is deliberately unimplemented, so scoping reviews keep
`U_checklist` out of scope rather than treating an unavailable check as zero. They also do not
grade certainty.

## Fail-closed behaviour (existing, extended to the new units)

The backend already refuses `VERIFIED` when a declared in-scope unit is absent from the map. The
new units inherit this without new machinery: a systematic review whose `units.json` omits
`U_checklist` lists it under `missing_units` and cannot be reported verified (FR-024).

Inapplicable units are **absent**, not zero-to-achieve (FR-025). The existing distinction between
"missing" and "out of scope" is what makes this correct, and it is not modified.

## Derived counts — the `checks` block (issue #4)

Optional top-level object. Each entry names **which check** and **which record**; the backend runs
it with `--strict --json` (see [cli-contract.md](./cli-contract.md)) and takes the counts it
reports.

A fragment, deliberately not in a `json` fence: every fenced `json` block in this directory is
executed by `tests/test_contract_examples.py` as a complete record, and a fragment dressed as one
would fail for being incomplete rather than for being wrong.

```
"checks": {
  "prisma_flow":      {"record": "counts.json"},
  "prisma_checklist": {"record": "checklist.json"},
  "rob_appraisal":    {"record": "appraisal.json"},
  "grade_profile":    {"record": "certainty.json", "rob_record": "appraisal.json"}
}
```

| Entry | Derives | Notes |
|:--|:--|:--|
| `prisma_flow` | `U_prisma` | |
| `prisma_checklist` | `U_checklist` | |
| `grade_profile` | `U_grade`, `U_rob_trace` | `U_rob_trace` **only** when `rob_record` is supplied |
| `rob_appraisal` | `H_rob` | Produces no unit — the gate is not auto-reducible work |

**Keyed by check, not by unit — a departure from the decision recorded on issue #4.** That comment
specified `{"U_prisma": {"check": "prisma_flow", "record": …}}`. Two things make keying by check
better, and neither was visible when the decision was written: the certainty check produces **two**
units, so a unit-keyed block would name it twice and run it twice against the same record; and the
sketch's `"U_rob"` is not a key that exists — `H_rob` is a gate and `U_rob_trace` a unit, and they
are produced by different checks. Everything the decision was actually protecting is unchanged: the
name is still a key into a fixed table, and no part of the record reaches the argv.

### Precedence, and the two new verdict fields

**The frozen scope binds every count, derived or reported.** A unit that is *not* in
`units_in_scope` does not enter the verdict — scope is resolved once at classification and neither a
check nor a stale entry in `units` widens it. The universal floor is always allowed, since it is
required whether or not it appears in the declared list. A rapid review may hand `rob_record` to the certainty check to validate a
voluntarily-used `confirmed_rob` basis, and `U_rob_trace` would otherwise block a review the table
above explicitly freezes that unit out of. The drop is named in `ignored_inputs`, never silent.

**Gates are not scope-filtered, and the asymmetry is deliberate.** A pending signature is
outstanding work whatever the scope says; the record's own `gates` object has always contributed
every `H_*` key regardless, and filtering the derived value while keeping the reported one would let
scope hide the one count Principle V says a loop may never auto-zero.

A derived count **overrides** a reported one. A disagreement is named in `ignored_inputs`, on the
same reasoning as the `U_consistency` row below: the verdict is correct either way, and a
contradiction the check resolves quietly is still a contradiction. An *agreeing* value is not
reported — nothing was dropped, and flagging it would make the field noise in the ordinary case.

| Field | Contains | Effect |
|:--|:--|:--|
| `underived_units` | In-scope units a check could have derived, where no entry named its record | Verdict held at `CONTINUE` |
| `underived_gates` | The same, for a human gate | Verdict held at `CONTINUE` |
| `gates_evaluated` | The gate map the verdict actually used, after any derived value overrode a reported one | Recorded in the manifest |
| `unattributed_issues` | Work a check reported that no unit and no gate counts | Verdict held at `CONTINUE` |

**Supplying `rob_record` requires the `rob_appraisal` entry.** The certainty check *reads* an
appraisal and reports the pending signatures it finds as diagnostics — but books them to no unit (a
signature is not auto-reducible) and to no gate (`rob_appraisal` owns `H_rob`), so they vanish from
its envelope. Without this rule a rapid review could declare only `grade_profile` with an unsigned
appraisal and reach `VERIFIED` while that subprocess exited 1 for an outstanding human gate. The
rule is **structural, not scope-based**, which is what lets it reach the review types the scope
proxy below cannot.

It must be the **same** appraisal, not merely some appraisal: `grade_profile.rob_record` and
`rob_appraisal.record` must resolve to the same file. Requiring only that the entry exist left the
two checks free to read different records — the certainty check reading one with a pending
signature, the appraisal check reading a clean one and reporting `H_rob: 0`.

**Why this rule is total** where the two before it were partial. A pending signature lives in an
appraisal *file* and reaches the verdict only through `H_rob`, which only `rob_appraisal` derives
and only from its own `record`. So the property needed is: every appraisal file the block names is
read by `rob_appraisal`. A file can be named by `rob_appraisal.record` — read by definition — or by
a secondary record key, and `grade_profile.rob_record` is the **only** secondary record key in the
table. Forcing it equal closes the set with nothing left over. The enumeration is pinned by
`test_every_appraisal_route_is_read_by_the_gate_owner`, so a fifth check adding a record key cannot
reopen it silently.

**A gate reads its scope from the unit it moves with.** `H_rob` cannot appear in `units_in_scope` —
that list is validated against the unit weights — so requiring only units left the gate
self-reported on the rigorous path: a record could declare systematic scope, omit the
`rob_appraisal` entry, and reach `VERIFIED` with a signature still pending. That is this issue's own
failure mode surviving for the one count Principle V says a loop may never auto-zero. `H_rob` is
therefore required whenever **`U_rob_trace`** is in scope: the two are in scope for exactly the same
review types in every row of the table above, because both come from the appraisal record, and a
review that must trace appraisals must also have them signed.

Both are tested **before** the done-states and ahead of the human gate. Neither is a repair stall
and neither is a human's to clear — the agent adds the entry, or fixes the record the check
rejected — so reaching `BLOCKED_ON_HUMAN` on either would park an unestablished verdict on a
person.

### Requiring it (FR-024's reasoning, applied one level up)

**When `units_in_scope` is declared, a unit a check can derive may not be self-reported.** Without
that rule the block is optional and anyone wanting the old behaviour simply omits it. It bites
only where a check exists: `U_cite_external`, `U_cite_internal`, `U_screen` and `U_extract` have no
runnable check and stay reported, which the skill documentation states rather than leaving a reader
to infer from a shorter list. Declaring no scope stays lenient — the same choice `gates` already
makes.

This is a **breaking change** for a scope-declaring record: one that reached `VERIFIED` on
hand-written zeros now reports `CONTINUE` and names the units it must derive.

### Security

`units.json` is untrusted input. The check name is a key into a fixed table in `review_units.py` —
never a path, never a basename to be matched — and the argv is built there: `--strict --json` are
fixed, `--rob` is added for the certainty check, and the only caller-supplied values are record
paths, which a check opens for reading and never executes. An unknown name, an unknown entry key,
or a `rob_record` on a check that does not take one is malformed input (exit 2).

Record paths must resolve **inside** `--records-root`, which defaults to the directory holding
`units.json`. Resolution is `realpath`-first, so a symlink or a `..` cannot walk out of it.

Two more expressive designs were considered and rejected: a per-script flag allowlist (a second
allowlist to maintain, for a need that does not exist), and free-form `args` behind a basename
allowlist (which hands the argv of a script in the repository to whoever writes the record).

`--records-root` and `--skills-root` come from the **argv**, which is the operator's. Someone who
can pass flags to this script can already run anything on the machine, so constraining them would
buy nothing.

### The audit trail records what the verdict used

`--manifest` rebuilt its `gates` field from the record's own object, so a verdict that overrode a
reported `H_rob: 0` with a derived `1` appended a row claiming `0` — the audit trail contradicting
the verdict it was recording, which is the one thing an audit trail may not do. It now writes
`gates_evaluated`.

### Failure is never zero

A declared check that does not produce a verdict is an error (exit 2, no verdict written): exit 2
from the check, a crash, a timeout, output that is not valid JSON, an envelope version this backend
does not know, a script identifying as a different check, or one reporting a different set of units
from the one the entry planned. A malformed record is a record nothing evaluated, and booking it as
zero outstanding work would make the most broken input in the system indistinguishable from the
cleanest.

### What it does not achieve

Running the checks makes the counts derived rather than asserted. It does **not** make them
unforgeable — a caller can still point `record` at a doctored file. The loop verifies that the
checks were run and what they reported, not that the underlying review is true. That framing
survives this change rather than being deleted by it.

## Reported-but-unused input

`U_consistency` is derived **only** from a `consistency` object carrying a numeric score. A value
written into `units` is dropped, so a caller cannot hand-write `"U_consistency": 0` and clear the
universal floor without a real score.

The input is a closed schema. Unknown top-level fields are rejected, and the optional
`consistency` object accepts exactly `score` and `critical_breaks`; misspellings cannot fall
through to an optional-field default.

Dropping it is correct; dropping it silently was not. The verdict carries an `ignored_inputs`
array — empty in the normal case — naming what was received, why it was not used, and the remedy.
It is populated **whenever the direct key is present**, in both situations:

| Supplied | Verdict effect | Reported |
|:--|:--|:--|
| Direct key only, no usable `consistency` object | Unit is missing; cannot reach `VERIFIED` | "supply the object" — read alongside `missing_units`, which names the same unit, the pair means "supplied, but not in a form that counts" rather than "forgotten" |
| **Both**, disagreeing | Derived value wins, which may be `VERIFIED` | "the derived value is authoritative; remove the direct key" — the record must not be able to state two different things without saying so |

The second row is the one that matters most and the easiest to omit: the verdict is correct, so
nothing looks wrong. A contradiction the check silently resolves is still a contradiction the
reader is entitled to see.

## Example

A complete record captured **mid-review**, with units still outstanding — two ungraded results,
one unresolved risk-of-bias reference, four unaddressed checklist rows. The verdict is therefore
not `VERIFIED` and the exit code is 1. That is the fail-closed behaviour above, shown working
rather than described. `tests/test_contract_examples.py` runs this record and asserts the whole
diagnostic — `missing_units` empty, `by_unit` exact — not merely the exit code.

Note that `U_consistency` is **not** listed in `units`. It is derived solely from the
`consistency` object, so that a caller cannot write `"U_consistency": 0` and satisfy the
universal floor without a real score. A value supplied under `units` is ignored and the unit is
then reported missing; the check says so explicitly rather than dropping it silently.

```json
{
  "schema_version": "1.0",
  "review_type": "systematic",
  "units_in_scope": ["U_cite_external", "U_cite_internal", "U_consistency",
                     "U_screen", "U_extract", "U_prisma",
                     "U_grade", "U_rob_trace", "U_checklist"],
  "units": {
    "U_cite_external": 0, "U_cite_internal": 0,
    "U_screen": 0, "U_extract": 0, "U_prisma": 0,
    "U_grade": 2, "U_rob_trace": 1, "U_checklist": 4
  },
  "consistency": {"score": 82, "critical_breaks": 0},
  "gates": {"H_rob": 3, "H_screen_adj": 0, "H_cite_manual": 0, "H_numeric": 0},
  "cycle": 4
}
```

Verdict: **CONTINUE** — seven units outstanding across three checks, and three appraisals awaiting
human confirmation. `H_rob` is never auto-satisfied by further cycles (FR-026).

The record declares scope and carries **no `checks` block**, so the verdict also reports
`underived_units: ["U_checklist", "U_grade", "U_prisma", "U_rob_trace"]` — the record's counts for
those four are asserted, not derived. That is deliberate here and not an oversight: this example is
executed by `tests/test_contract_examples.py` from a scratch directory, and a `checks` block would
have to name four artifact files a self-contained example cannot ship. **A real scope-declaring
record must carry one**, and its absence is what holds this verdict at `CONTINUE` even once the
seven units reach zero.
