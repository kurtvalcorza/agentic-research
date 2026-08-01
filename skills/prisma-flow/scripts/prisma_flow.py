#!/usr/bin/env python3
"""
prisma_flow.py — assemble a PRISMA 2020 flow diagram from REAL run counts and
check that the numbers reconcile. Standard library only.

This renders the PRISMA 2020 flow as a Mermaid diagram (GitHub/Markdown
renderable) and FAILS if the arithmetic does not reconcile end to end. The
counts come from the pipeline: acquire-corpus (identification), dedupe-records
(duplicates removed), and screen-literature (screened / excluded / included).

WHAT THIS CANNOT CHECK
  Whether the counts are TRUE. Reconciliation proves the numbers are mutually
  consistent, not that they describe what actually happened: a run that screened
  400 records and recorded 380 reconciles perfectly and is still wrong. The counts
  must come from the stages that own them — acquire-corpus, dedupe-records,
  screen-literature — and never be adjusted to make this script pass. Adjusting a
  count to satisfy the arithmetic converts a detectable error into an undetectable
  one.

TWO-ARM MODEL (PRISMA 2020)
  PRISMA 2020 ships two flow-diagram templates and this script renders whichever
  the counts describe:
    * Template 1 — databases & registers ONLY (a single identification column).
    * Template 2 — databases & registers PLUS a parallel "other methods" arm
      (citation searching, websites, organisations) that runs its own
      sought -> assessed -> excluded chain and merges at "Studies included".
  The two arms are reconciled INDEPENDENTLY and then merged — "other methods"
  records are NOT pooled into the database title/abstract screening box, because
  citation-searched / website / organisation reports enter at the report level,
  not at title/abstract screening. Registers belong to the databases/registers
  (left) arm, not "other methods".

INPUT — a JSON counts object (file arg or stdin). Other-methods fields are
optional; omit them (or leave them zero) for a Template-1 databases-only flow.
The record must name both ends of the flow: at least one identified_* key and at
least one studies_included_* key. Everything between them is optional, and an
omitted stage simply goes unchecked:
{
  "schema_version": "1.0",
  "identified_databases": {"OpenAlex": 412, "CrossRef": 88},
  "identified_registers": {"PROSPERO": 0},
  "identified_other": {"citation searching": 23, "websites": 0, "organisations": 0},
  "duplicates_removed": 96,
  "removed_other_reasons": 0,
  "records_screened": 404,
  "records_excluded_title_abstract": 328,
  "reports_sought": 76,
  "reports_not_retrieved": 4,
  "reports_assessed": 72,
  "reports_excluded": {"wrong population": 18, "not empirical": 9, "wrong outcome": 7},
  "studies_included_databases": 38,
  "other_reports_sought": 23,
  "other_reports_not_retrieved": 1,
  "other_reports_assessed": 22,
  "other_reports_excluded": {"wrong outcome": 4},
  "studies_included_other": 18,
  "studies_included_total": 56
}

USAGE
  python prisma_flow.py counts.json            # mermaid + reconciliation
  echo '{...}' | python prisma_flow.py --strict   # exit 1 if reconciliation fails

EXIT CODES
  0 reconciles (or non-strict);  1 does not reconcile under --strict;
  2 malformed input — no artifact is emitted. That covers: not valid JSON; not an
    object; a MISSING or unrecognised schema_version; an UNRECOGNISED KEY (a
    misspelled count is not an absent one); a count that is not a whole,
    non-negative JSON number (booleans, quoted numbers such as "3", fractions and
    non-finite values all fail closed); a BREAKDOWN KEY that is not an object
    (the three identified_* and the two *reports_excluded map a source or reason
    to its own count, so a bare number is malformed, not a total); and a record
    naming NO identification count or NO inclusion count, where `null` and `{}`
    do not count as naming one.

  A reconciling record reports how many of the eight stages were actually
  checked. One that checks none of them says so rather than printing ✅ — an
  empty error list means nothing failed, which is not the claim that everything
  held.

  The version, unknown-key, breakdown-shape and both-ends rules are all
  deliberate BREAKING changes to a shipped script — contracts/cli-contract.md
  binds this check as much as the three added alongside it. Existing records need
  "schema_version": "1.0" added and both ends of the flow named. See
  specs/001-standards-enforcement-parity/contracts/prisma-flow.md (D-020, and
  rules 7-9 for issues #9 and #10).
"""
from __future__ import annotations
import argparse, json, math, sys


SCHEMA_VERSIONS = {"1.0"}

# The closed record schema. contracts/cli-contract.md binds ALL FOUR checks —
# "a check that deviates is non-conforming regardless of whether its own rules are
# correct" — and this one, the oldest, enforced neither the version nor the key
# set. A misspelled count key therefore dropped silently out of the record while
# the remaining arithmetic reconciled and the diagram printed an authoritative ✅,
# which is the precise fail-open the unknown-key rule exists to prevent.
#
# Closing the key set was not enough on its own: it said WHICH keys may appear
# and never what may appear UNDER them. The five breakdown keys below are read
# with `.items()`, so a truthy non-mapping — `identified_databases: 500`, the
# obvious thing to write — reached `.items()` unguarded and died with an
# AttributeError traceback at exit 1, where the contract promises a structured
# error at exit 2. Fifteen shapes did that. The scalar keys were never affected,
# because _int() already rejects every wrong type.
BREAKDOWN_KEYS = {
    "identified_databases", "identified_registers", "identified_other",
    "reports_excluded", "other_reports_excluded",
}

COUNT_KEYS = {
    "duplicates_removed", "removed_other_reasons",
    "records_screened", "records_excluded_title_abstract",
    "reports_sought", "reports_not_retrieved", "reports_assessed",
    "studies_included_databases",
    "other_reports_sought", "other_reports_not_retrieved", "other_reports_assessed",
    "studies_included_other", "studies_included_total",
}

RECORD_KEYS = {"schema_version"} | BREAKDOWN_KEYS | COUNT_KEYS

# A flow diagram describes a path from records identified to studies included.
# A record naming neither end of it is not an under-specified diagram, it is not
# a diagram at all — and the arithmetic could not say so, because zero edges
# checked reconciles as readily as zero edges broken.
IDENTIFICATION_KEYS = {"identified_databases", "identified_registers", "identified_other"}
INCLUSION_KEYS = {"studies_included_databases", "studies_included_other",
                  "studies_included_total"}


class CountError(ValueError):
    """A count value is not a non-negative integer."""


def validate_record(c) -> None:
    """Apply the shared closed-schema rules before any count is read.

    Raises CountError, which main() already reports as exit 2 with no artifact.
    """
    if not isinstance(c, dict):
        raise CountError("record: expected an object of counts")
    version = c.get("schema_version")
    # isinstance first: an unhashable value raises TypeError on set membership,
    # which would surface as a traceback and exit 1 instead of the documented 2.
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise CountError(f"record: unrecognised or missing schema_version {version!r} "
                         f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})")
    unknown = sorted(set(c) - RECORD_KEYS)
    if unknown:
        raise CountError(
            f"record: unrecognised key(s) {', '.join(repr(k) for k in unknown)}. "
            f"A misspelled count is not an absent one: read past, it drops out of "
            f"the record while the remaining arithmetic still reconciles")

    # Value SHAPE, not just key membership. Without this, a breakdown key given a
    # plain number reached `.items()` and raised AttributeError — a traceback at
    # exit 1 where the contract promises a structured error at exit 2. Checked
    # here, where CountError already means "exit 2, no artifact", rather than
    # scattered through the readers.
    for key in sorted(BREAKDOWN_KEYS & set(c)):
        value = c[key]
        if value is None:          # explicit null reads as absent, as elsewhere
            continue
        if not isinstance(value, dict):
            raise CountError(
                f"{key}: expected an object mapping each source to its count "
                f"(e.g. {{\"PubMed\": 320}}), got {type(value).__name__} {value!r}. "
                f"A single total cannot be attributed, and this key is the "
                f"attribution")

    # A record naming neither end of the flow cannot be reconciled, only
    # rubber-stamped: with nothing supplied, no edge is checked, and "no edge was
    # checked" printed as "counts reconcile end to end" over a diagram whose every
    # node read n=0. Absent counts must be reported as missing, never defaulted to
    # zero (constitution, fail closed).
    # Supplied means "carries a count", not "the key is present". This gate has
    # now been walked around twice by things that are present and say nothing:
    #
    #   "identified_databases": null   — null reads as absent for the breakdown
    #                                    keys and studies_included_total, so every
    #                                    reader downstream saw an empty record
    #   "identified_databases": {}     — an empty breakdown names no source and
    #                                    sums to 0
    #
    # Both satisfied a presence test and then produced the all-zero diagram
    # certifying itself, which is the exact output this gate exists to stop. The
    # constitution names the second case directly: an empty collection must
    # report failure, not vacuous success.
    #
    # Note null is NOT uniformly "absent" in this file — the 13 scalar count keys
    # reject it outright via _int(), which is a different and stricter answer. It
    # reads as absent for the five breakdown keys and studies_included_total, and
    # that is the set this gate ranges over.
    supplied = {k for k, v in c.items() if v is not None and v != {}}
    for label, required in (("identification", IDENTIFICATION_KEYS),
                            ("inclusion", INCLUSION_KEYS)):
        if not required & supplied:
            raise CountError(
                f"record: no {label} count supplied. A PRISMA flow runs from "
                f"records identified to studies included, so it needs at least one "
                f"of {', '.join(sorted(required))}. Every count defaulting to zero "
                f"reconciles trivially, which certifies nothing")


def _int(v, name: str) -> int:
    """Coerce a count to int, rejecting anything that is not a JSON number.

    Fails closed rather than coercing (constitution Principle IV). In particular a
    QUOTED count such as "3" is malformed input, not a number to parse: in a
    hand-authored record it is far more likely to be a mistake than an intention,
    and silently accepting it is the class of quiet reconciliation the principle
    forbids. This matches review_units.py, so both gates share one definition of
    malformed input.
    """
    # bool is an int subclass, so it must be rejected before the int check —
    # otherwise `true` would silently count as 1.
    if isinstance(v, bool):
        raise CountError(f"{name}: expected an integer count, got boolean {v!r}")
    if isinstance(v, int):
        iv = v
    elif isinstance(v, float):
        if not math.isfinite(v):
            raise CountError(f"{name}: count must be a finite number, got {v!r}")
        if not v.is_integer():
            raise CountError(f"{name}: count must be a whole number, got {v!r}")
        iv = int(v)
    else:
        raise CountError(f"{name}: count must be a JSON number, got {v!r}")
    if iv < 0:
        raise CountError(f"{name}: count must be non-negative, got {iv}")
    return iv


def _as_mapping(d, name: str) -> dict:
    """Absent/null → {}; a non-mapping is malformed input, never a traceback.

    validate_record() has already rejected a non-mapping, so this is the backstop
    for a caller that arrives without passing the gate. It has to live in ONE
    place: `(d or {}).items()` appears at four sites, `or {}` covers None but
    passes a truthy non-mapping straight through to .items(), and guarding only
    _sum() protected the site reached LAST — main() builds the diagram before it
    reconciles, so mermaid() and _src_label() would raise AttributeError first
    and the backstop would never fire.
    """
    if d is None:
        return {}
    if not isinstance(d, dict):
        raise CountError(f"{name}: expected an object of source counts, "
                         f"got {type(d).__name__} {d!r}")
    return d


def _sum(d, name: str) -> int:
    return sum(_int(v, f"{name}.{k}") for k, v in _as_mapping(d, name).items())


def _has_other(c: dict) -> bool:
    """True if the counts describe an 'other methods' arm (Template 2)."""
    if _sum(c.get("identified_other"), "identified_other") > 0:
        return True
    keys = ("other_reports_sought", "other_reports_not_retrieved",
            "other_reports_assessed", "studies_included_other")
    if any(_int(c.get(k, 0), k) > 0 for k in keys):
        return True
    return _sum(c.get("other_reports_excluded"), "other_reports_excluded") > 0


def reconcile(c: dict, checked: list | None = None) -> list[str]:
    """Return a list of reconciliation errors (empty = clean).

    An edge is checked when BOTH of its counts were SUPPLIED, not when both are
    truthy. Truthiness could not tell an omitted count from one explicitly recorded
    as `0`, so a record stating 500 identified, 96 removed and `records_screened: 0`
    disabled three edges at once and reconciled clean under --strict — the same
    fail-open the closed schema was added to prevent, reached through a correctly
    spelled key instead of a misspelled one. Presence is only decidable now that
    the key set is closed; before that, an unknown key was indistinguishable from
    an absent one.

    Pass a list as ``checked`` to learn WHICH edges were evaluated. An empty error
    list means "nothing failed", which is not the same claim as "everything held":
    a record naming only two ends checks no edge at all and returned the same []
    as a fully reconciling one, so the caller printed "counts reconcile end to end"
    over a flow it had not examined. Reporting that honestly needs the count, and
    the count has to come from the gates themselves — deriving it separately would
    be a second copy of this function's presence rules, free to drift from them.

    The parameter is optional so the fourteen existing callers keep working
    unchanged; only main() asks.
    """
    errs = []
    have = c.__contains__

    def gate(name: str, ok: bool) -> bool:
        """Record an edge as evaluated when its counts were supplied."""
        if ok and checked is not None:
            checked.append(name)
        return ok

    # --- Databases & registers arm (left column) ---
    id_dbreg = _sum(c.get("identified_databases"), "identified_databases") \
        + _sum(c.get("identified_registers"), "identified_registers")
    removed = _int(c.get("duplicates_removed", 0), "duplicates_removed") \
        + _int(c.get("removed_other_reasons", 0), "removed_other_reasons")
    screened = _int(c.get("records_screened", 0), "records_screened")
    if gate("identification", have("records_screened") and bool(id_dbreg)) \
            and (id_dbreg - removed) != screened:
        errs.append(f"databases/registers identification: identified {id_dbreg} - removed {removed} = "
                    f"{id_dbreg - removed}, but records_screened = {screened}")
    ex_ta = _int(c.get("records_excluded_title_abstract", 0), "records_excluded_title_abstract")
    sought = _int(c.get("reports_sought", 0), "reports_sought")
    if gate("screening", have("records_screened") and have("reports_sought")) \
            and (screened - ex_ta) != sought:
        errs.append(f"screening: screened {screened} - excluded(t/a) {ex_ta} = {screened - ex_ta}, "
                    f"but reports_sought = {sought}")
    not_ret = _int(c.get("reports_not_retrieved", 0), "reports_not_retrieved")
    assessed = _int(c.get("reports_assessed", 0), "reports_assessed")
    if gate("retrieval", have("reports_sought") and have("reports_assessed")) \
            and (sought - not_ret) != assessed:
        errs.append(f"retrieval: sought {sought} - not_retrieved {not_ret} = {sought - not_ret}, "
                    f"but reports_assessed = {assessed}")
    ex_ft = _sum(c.get("reports_excluded"), "reports_excluded")
    inc_db = _int(c.get("studies_included_databases", 0), "studies_included_databases")
    if gate("eligibility", have("reports_assessed") and have("studies_included_databases")) \
            and (assessed - ex_ft) != inc_db:
        errs.append(f"eligibility (databases/registers): assessed {assessed} - excluded(full-text) {ex_ft} = "
                    f"{assessed - ex_ft}, but studies_included_databases = {inc_db}")

    # --- Other-methods arm (right column), only if present ---
    inc_other = _int(c.get("studies_included_other", 0), "studies_included_other")
    if _has_other(c):
        id_other = _sum(c.get("identified_other"), "identified_other")
        o_sought = _int(c.get("other_reports_sought", 0), "other_reports_sought")
        if gate("other identification", have("other_reports_sought") and bool(id_other)) \
                and id_other != o_sought:
            errs.append(f"other methods identification: identified {id_other} reports, "
                        f"but other_reports_sought = {o_sought} (every identified report should be sought)")
        o_not_ret = _int(c.get("other_reports_not_retrieved", 0), "other_reports_not_retrieved")
        o_assessed = _int(c.get("other_reports_assessed", 0), "other_reports_assessed")
        if gate("other retrieval", have("other_reports_sought") and have("other_reports_assessed")) \
                and (o_sought - o_not_ret) != o_assessed:
            errs.append(f"other methods retrieval: sought {o_sought} - not_retrieved {o_not_ret} = "
                        f"{o_sought - o_not_ret}, but other_reports_assessed = {o_assessed}")
        o_ex_ft = _sum(c.get("other_reports_excluded"), "other_reports_excluded")
        if gate("other eligibility", have("other_reports_assessed") and have("studies_included_other")) \
                and (o_assessed - o_ex_ft) != inc_other:
            errs.append(f"other methods eligibility: assessed {o_assessed} - excluded {o_ex_ft} = "
                        f"{o_assessed - o_ex_ft}, but studies_included_other = {inc_other}")

    # --- Merge: total included = databases arm + other arm ---
    # The merge edge obeys the same both-counts-supplied rule as every other one.
    # It used to fire on the grand total alone, comparing it against arm totals
    # that default to zero rather than being presence-gated — so a record naming
    # only `studies_included_total: 0` reported "1 of 8 stages checked: merge"
    # having compared 0 + 0 against 0. That is the defaulting-to-zero pattern the
    # rest of this check exists to refuse, and instrumenting it only gave it a
    # "checked" label it had not earned.
    total = c.get("studies_included_total")
    arms = have("studies_included_databases") or have("studies_included_other")
    if gate("merge", total is not None and arms):
        total = _int(total, "studies_included_total")
        if (inc_db + inc_other) != total:
            errs.append(f"merge: studies_included_databases {inc_db} + studies_included_other {inc_other} = "
                        f"{inc_db + inc_other}, but studies_included_total = {total}")
    return errs


def _mermaid_label(value: object) -> str:
    """Render caller-controlled text inside a quoted mermaid node label.

    The counts in this diagram were rigorously validated and the LABELS were not:
    database names and exclusion reasons are caller-supplied dictionary KEYS, and
    they went into `NODE["..."]` untouched. A reason containing a double quote
    closed the string early, so the rest of it was parsed as diagram source —

        EXFT["Reports excluded:<br/>wrong population"] --> EVIL[injected node: 20"]

    which puts a fabricated node and edge into the PRISMA diagram, the headline
    figure of the review. A quote becomes an entity; newlines become the line break
    the label already uses.
    """
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    return text.replace('"', "&quot;").replace("\n", "<br/>")


def _src_label(d, name: str) -> str:
    return ", ".join(f"{_mermaid_label(k)} n={_int(v, f'{name}.{k}')}"
                     for k, v in _as_mapping(d, name).items())


def mermaid(c: dict) -> str:
    has_other = _has_other(c)
    id_db = _sum(c.get("identified_databases"), "identified_databases")
    id_reg = _sum(c.get("identified_registers"), "identified_registers")
    id_dbreg = id_db + id_reg
    dbreg_src = ", ".join(s for s in (_src_label(c.get("identified_databases"), "identified_databases"),
                                      _src_label(c.get("identified_registers"), "identified_registers")) if s)
    dup = _int(c.get("duplicates_removed", 0), "duplicates_removed")
    rem_oth = _int(c.get("removed_other_reasons", 0), "removed_other_reasons")
    ex_ta = _int(c.get("records_excluded_title_abstract", 0), "records_excluded_title_abstract")
    not_ret = _int(c.get("reports_not_retrieved", 0), "reports_not_retrieved")
    ex_ft = _as_mapping(c.get("reports_excluded"), "reports_excluded")
    ex_ft_lines = "<br/>".join(f"{_mermaid_label(k)}: {_int(v, f'reports_excluded.{k}')}"
                              for k, v in ex_ft.items()) or "n=0"
    inc_db = _int(c.get("studies_included_databases", 0), "studies_included_databases")
    inc_other = _int(c.get("studies_included_other", 0), "studies_included_other")
    total = c.get("studies_included_total")
    total = _int(total, "studies_included_total") if total is not None else inc_db + inc_other

    L = ["```mermaid", "flowchart TB",
         '  subgraph DBREG["Identification via databases & registers"]',
         f'    ID["Records identified: n={id_dbreg}<br/>{dbreg_src}"]',
         f'    DUP["Records removed before screening:<br/>duplicates n={dup}, other n={rem_oth}"]',
         f'    SCR["Records screened: n={_int(c.get("records_screened",0),"records_screened")}"]',
         f'    EXTA["Records excluded (title/abstract): n={ex_ta}"]',
         f'    SOU["Reports sought for retrieval: n={_int(c.get("reports_sought",0),"reports_sought")}"]',
         f'    NR["Reports not retrieved: n={not_ret}"]',
         f'    ASS["Reports assessed for eligibility: n={_int(c.get("reports_assessed",0),"reports_assessed")}"]',
         f'    EXFT["Reports excluded:<br/>{ex_ft_lines}"]',
         f'    INCDB["Studies included (databases/registers): n={inc_db}"]',
         "  end"]
    if has_other:
        id_other = _sum(c.get("identified_other"), "identified_other")
        oth_src = _src_label(c.get("identified_other"), "identified_other")
        o_not_ret = _int(c.get("other_reports_not_retrieved", 0), "other_reports_not_retrieved")
        o_ex_ft = _as_mapping(c.get("other_reports_excluded"), "other_reports_excluded")
        o_ex_ft_lines = "<br/>".join(f"{_mermaid_label(k)}: {_int(v, f'other_reports_excluded.{k}')}"
                                    for k, v in o_ex_ft.items()) or "n=0"
        L += ['  subgraph OTHER["Identification via other methods"]',
              f'    IDO["Records identified: n={id_other}<br/>{oth_src}"]',
              f'    OSOU["Reports sought for retrieval: n={_int(c.get("other_reports_sought",0),"other_reports_sought")}"]',
              f'    ONR["Reports not retrieved: n={o_not_ret}"]',
              f'    OASS["Reports assessed for eligibility: n={_int(c.get("other_reports_assessed",0),"other_reports_assessed")}"]',
              f'    OEXFT["Reports excluded:<br/>{o_ex_ft_lines}"]',
              f'    INCO["Studies included (other methods): n={inc_other}"]',
              "  end"]
    L += [f'  INC["Studies included in review: n={total}"]',
          "  ID --> DUP", "  ID --> SCR", "  SCR --> EXTA", "  SCR --> SOU",
          "  SOU --> NR", "  SOU --> ASS", "  ASS --> EXFT", "  ASS --> INCDB",
          "  INCDB --> INC"]
    if has_other:
        L += ["  IDO --> OSOU", "  OSOU --> ONR", "  OSOU --> OASS",
              "  OASS --> OEXFT", "  OASS --> INCO", "  INCO --> INC"]
    L.append("```")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble + reconcile a PRISMA 2020 flow diagram from real counts.")
    ap.add_argument("infile", nargs="?")
    ap.add_argument("--strict", action="store_true", help="exit 1 if the counts do not reconcile")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    # The read was unguarded: a missing file or one that is not valid UTF-8 raised
    # through main() as a traceback and exit 1, while every sibling check reports
    # unreadable input as exit 2. UnicodeDecodeError is a ValueError, not an
    # OSError, so both have to be named.
    try:
        if args.infile:
            with open(args.infile, encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write(f"prisma_flow: cannot read {args.infile or 'stdin'} ({e})\n")
        return 2
    try:
        c = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"prisma_flow: input is not valid JSON ({e})\n")
        return 2
    if not isinstance(c, dict):
        sys.stderr.write("prisma_flow: input must be a JSON object of counts\n")
        return 2

    try:
        validate_record(c)
    except CountError as e:
        sys.stderr.write(f"prisma_flow: {e}\n")
        return 2

    try:
        diagram = mermaid(c)
        checked: list[str] = []
        errs = reconcile(c, checked)
    except CountError as e:
        sys.stderr.write(f"prisma_flow: {e}\n")
        return 2

    print("# PRISMA 2020 Flow Diagram\n")
    print(diagram)
    print("\n## Reconciliation\n")
    if errs:
        print("⚠️ **Counts do NOT reconcile** — fix before reporting:")
        for e in errs:
            print(f"- {e}")
    elif not checked:
        # No error is not the same claim as no problem. A record naming only two
        # ends supplies no edge with both of its counts, so nothing is compared
        # and the error list is empty for want of any check — which used to print
        # as "counts reconcile end to end" over a flow that had never been
        # examined. Issue #9 asked for this message to be a function of how many
        # edges were actually checked, and this is that.
        print("⚠️ **Nothing was reconciled** — no stage had both of its counts "
              "supplied, so no arithmetic was checked. This diagram reports the "
              "counts given; it does not attest to them.")
    else:
        print(f"✅ Counts reconcile end to end ({len(checked)} of 8 stages checked: "
              f"{', '.join(checked)}).")
    # An unreconciled record is incomplete, not contradictory — the same
    # distinction the presence gates draw — so --strict still fails only on a
    # real contradiction. What changed is that silence no longer reads as a tick.
    return 1 if (errs and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
