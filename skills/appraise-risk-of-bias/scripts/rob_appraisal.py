#!/usr/bin/env python3
"""
rob_appraisal.py — check a risk-of-bias appraisal record and generate the per-study
table and traffic-light summary from it. Standard library only.

WHAT THIS CHECKS
  That each study was appraised with the instrument its design calls for, that every
  domain that instrument defines is present with a value that instrument defines,
  that the declared overall judgment is not more favourable than the study's worst
  domain, and that a human confirmation is recorded.

WHAT THIS CANNOT CHECK
  Whether a human actually made the judgment. It establishes that a confirmation
  record is PRESENT — a name and a date in the file. It cannot establish who wrote
  them, or that they read the paper. No identity mechanism is introduced here, and
  a passing result must not be read as one.

  It also cannot check that a domain judgment is correct: appraisal is where LLM
  accuracy is weakest (~0.62 versus ~0.95 for extraction), which is exactly why the
  human gate exists rather than being automated away.

INPUT — a JSON record (file arg or stdin):
{
  "schema_version": "1.0",
  "studies": [{
    "id": "R1", "design": "rct", "instrument": "rob2",
    "result_assessed": "diagnostic accuracy at 12 months",
    "domains": {"randomization": "low", ...},
    "evidence": {"randomization": "p.4: 'computer-generated sequence'"},
    "overall": "some_concerns",
    "confirmed_by": "K. Valcorza", "confirmed_at": "2026-07-26"
  }]
}

USAGE
  python rob_appraisal.py risk-of-bias.json --strict

EXIT CODES
  0 clean, or violations found without --strict
  1 method violation under --strict
  2 malformed input — no artifact is emitted
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMA_VERSIONS = {"1.0"}

STUDY_KEYS = {"id", "design", "instrument", "result_assessed", "domains", "evidence",
              "overall", "overall_justification", "confirmed_by", "confirmed_at"}

# design -> instrument. RoB 2 and ROBINS-I assess a specific RESULT, not a study as
# a whole, which is why 'result_assessed' is part of the record.
DESIGN_INSTRUMENT = {
    "rct": "rob2",
    "nrsi": "robins_i",
    "observational": "nos",
    "dta": "quadas2",
}

# Severity ranks drive the "overall not better than the worst domain" check.
# Higher is worse. None means "not orderable" and is excluded from the worst-domain
# comparison — see NO_INFORMATION handling below.
SEVERITY = {
    "rob2": {"low": 0, "some_concerns": 1, "high": 2},
    "robins_i": {"low": 0, "moderate": 1, "serious": 2, "critical": 3, "no_information": None},
    "quadas2": {"low": 0, "unclear": 1, "high": 2},
    "nos": {"low": 0, "moderate": 1, "high": 2},
}

DOMAINS = {
    "rob2": ("randomization", "deviations", "missing_data", "measurement", "selection_of_result"),
    "robins_i": ("confounding", "participant_selection", "intervention_classification",
                 "deviations", "missing_data", "outcome_measurement", "selection_of_result"),
    "nos": ("selection", "comparability", "outcome_or_exposure"),
    "quadas2": ("patient_selection", "index_test", "reference_standard", "flow_and_timing"),
}

# Newcastle-Ottawa is a star system, not a vocabulary: each block has a maximum.
NOS_MAX = {"selection": 4, "comparability": 2, "outcome_or_exposure": 3}
# Bands are CONVENTIONAL, not definitional — hence overall_justification may override.
NOS_BANDS = ((7, "low"), (4, "moderate"), (0, "high"))

# QUADAS-2 rates applicability as well as risk of bias, for the first three domains.
QUADAS_APPLICABILITY = ("patient_selection", "index_test", "reference_standard")

MARKS = {"low": "🟢", "some_concerns": "🟡", "moderate": "🟡", "unclear": "🟡",
         "serious": "🔴", "critical": "🔴", "high": "🔴", "no_information": "⚪"}


class InputError(ValueError):
    """The record cannot be read. Fails closed: exit 2, no artifact emitted."""


def _obj(v, name: str) -> dict:
    if not isinstance(v, dict):
        raise InputError(f"{name}: expected an object, got {type(v).__name__}")
    return v


def _str(v, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise InputError(f"{name}: expected a non-empty string, got {v!r}")
    return v


def _no_unknown_keys(d: dict, allowed, ctx: str) -> None:
    unknown = sorted(set(d) - set(allowed))
    if unknown:
        raise InputError(f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
                         f"(expected one of: {', '.join(sorted(allowed))})")


def _stars(v, ctx: str, maximum: int) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise InputError(f"{ctx}: expected an integer star count, got {v!r}")
    if v < 0 or v > maximum:
        raise InputError(f"{ctx}: star count must be between 0 and {maximum}, got {v}")
    return v


def parse(raw: dict) -> list[dict]:
    _obj(raw, "record")
    _no_unknown_keys(raw, {"schema_version", "studies"}, "record")

    version = raw.get("schema_version")
    if version not in SCHEMA_VERSIONS:
        raise InputError(f"record: unrecognised or missing schema_version {version!r} "
                         f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})")

    studies = raw.get("studies")
    if not isinstance(studies, list):
        raise InputError("record: 'studies' must be a list")
    if not studies:
        raise InputError("record: 'studies' is empty — there is nothing to appraise")

    seen: set[str] = set()
    return [_parse_study(s, i, seen) for i, s in enumerate(studies)]


def _parse_study(s, i: int, seen: set) -> dict:
    ctx = f"studies[{i}]"
    _obj(s, ctx)
    _no_unknown_keys(s, STUDY_KEYS, ctx)

    sid = _str(s.get("id"), f"{ctx}.id")
    if sid in seen:
        raise InputError(f"{ctx}.id: duplicate study id {sid!r} — every reference to it "
                         f"would be ambiguous")
    seen.add(sid)
    ctx = f"study {sid}"

    design = s.get("design")
    if design not in DESIGN_INSTRUMENT:
        raise InputError(f"{ctx}.design: must be one of "
                         f"{', '.join(sorted(DESIGN_INSTRUMENT))}, got {design!r}")
    instrument = s.get("instrument")
    if instrument not in DOMAINS:
        raise InputError(f"{ctx}.instrument: must be one of "
                         f"{', '.join(sorted(DOMAINS))}, got {instrument!r}")

    domains_raw = _obj(s.get("domains", {}), f"{ctx}.domains")
    overall = s.get("overall")

    # When the instrument does not match the design, validating domains and the
    # overall value against the DECLARED instrument produces a technically-true but
    # useless complaint ("unrecognised key 'randomization' for quadas2"). The root
    # cause is the instrument, so defer to check(), which reports the mismatch as a
    # violation with a message that names the fix.
    if instrument != DESIGN_INSTRUMENT[design]:
        return {"id": sid, "design": design, "instrument": instrument,
                "result_assessed": s.get("result_assessed", ""),
                "domains": dict(domains_raw), "evidence": s.get("evidence", {}) or {},
                "overall": overall, "overall_justification": s.get("overall_justification"),
                "confirmed_by": str(s.get("confirmed_by", "")).strip(),
                "confirmed_at": str(s.get("confirmed_at", "")).strip(),
                "instrument_mismatch": True}

    # Unknown domain -> malformed (exit 2). Missing domain -> violation (exit 1).
    _no_unknown_keys(domains_raw, DOMAINS[instrument], f"{ctx}.domains")
    domains = {}
    for name, value in domains_raw.items():
        domains[name] = _parse_domain(instrument, name, value, f"{ctx}.domains.{name}")

    if overall not in SEVERITY[instrument]:
        raise InputError(f"{ctx}.overall: must be one of "
                         f"{', '.join(SEVERITY[instrument])} for {instrument}, got {overall!r}")

    return {"id": sid, "design": design, "instrument": instrument,
            "result_assessed": s.get("result_assessed", ""),
            "domains": domains, "evidence": s.get("evidence", {}) or {},
            "overall": overall, "overall_justification": s.get("overall_justification"),
            "confirmed_by": str(s.get("confirmed_by", "")).strip(),
            "confirmed_at": str(s.get("confirmed_at", "")).strip()}


def _parse_domain(instrument: str, name: str, value, ctx: str):
    if instrument == "nos":
        return _stars(value, ctx, NOS_MAX[name])
    if instrument == "quadas2":
        d = _obj(value, ctx)
        allowed = {"risk_of_bias"} | ({"applicability"} if name in QUADAS_APPLICABILITY else set())
        _no_unknown_keys(d, allowed, ctx)
        rob = d.get("risk_of_bias")
        if rob not in SEVERITY["quadas2"]:
            raise InputError(f"{ctx}.risk_of_bias: must be one of "
                             f"{', '.join(SEVERITY['quadas2'])}, got {rob!r}")
        app = d.get("applicability")
        if name in QUADAS_APPLICABILITY and app is not None and app not in SEVERITY["quadas2"]:
            raise InputError(f"{ctx}.applicability: must be one of "
                             f"{', '.join(SEVERITY['quadas2'])}, got {app!r}")
        return {"risk_of_bias": rob, "applicability": app}
    if value not in SEVERITY[instrument]:
        raise InputError(f"{ctx}: must be one of {', '.join(SEVERITY[instrument])} "
                         f"for {instrument}, got {value!r}")
    return value


def _domain_severity(instrument: str, value):
    """Severity rank of a domain value, or None when not orderable."""
    if instrument == "nos":
        return None  # stars are summed, not ranked per domain
    if instrument == "quadas2":
        return SEVERITY["quadas2"][value["risk_of_bias"]]
    return SEVERITY[instrument][value]


def nos_total(domains: dict) -> int:
    return sum(domains.get(d, 0) for d in DOMAINS["nos"])


def nos_band(total: int) -> str:
    for threshold, band in NOS_BANDS:
        if total >= threshold:
            return band
    return "high"


def check(studies: list[dict]) -> tuple[list[str], int]:
    """Return (violations, count of studies awaiting human confirmation)."""
    errs: list[str] = []
    unconfirmed = 0

    for s in studies:
        sid, inst = s["id"], s["instrument"]

        # Rule 1 — the instrument must match the design.
        expected = DESIGN_INSTRUMENT[s["design"]]
        if inst != expected:
            errs.append(f"study {sid}: design '{s['design']}' calls for {expected}, "
                        f"but {inst} was applied")
            continue  # domain checks below would be against the wrong instrument

        # Rule 2 — every domain the instrument defines must be present.
        missing = [d for d in DOMAINS[inst] if d not in s["domains"]]
        if missing:
            errs.append(f"study {sid}: {inst} requires domain(s) {', '.join(missing)}, "
                        f"which are absent")
            continue

        # Rule 3/5 — the overall judgment against the domains beneath it.
        if inst == "nos":
            total = nos_total(s["domains"])
            band = nos_band(total)
            if s["overall"] != band and not s["overall_justification"]:
                errs.append(
                    f"study {sid}: Newcastle-Ottawa total is {total}/9, which bands as "
                    f"'{band}', but overall is '{s['overall']}'. The bands are conventional — "
                    f"record an overall_justification to override")
        else:
            ranks = {d: _domain_severity(inst, v) for d, v in s["domains"].items()}
            ordered = {d: r for d, r in ranks.items() if r is not None}
            no_info = [d for d, r in ranks.items() if r is None]

            if ordered:
                worst_domain = max(ordered, key=lambda d: ordered[d])
                worst = ordered[worst_domain]
                if SEVERITY[inst][s["overall"]] is not None \
                        and SEVERITY[inst][s["overall"]] < worst \
                        and not s["overall_justification"]:
                    worst_value = s["domains"][worst_domain]
                    if inst == "quadas2":
                        worst_value = worst_value["risk_of_bias"]
                    errs.append(
                        f"study {sid}: overall '{s['overall']}' is more favourable than its "
                        f"worst domain ({worst_domain} = '{worst_value}') — record an "
                        f"overall_justification if this is intended")

            # 'No information' is not a clean bill of health. Concluding low risk while
            # a domain is unreported is a judgment the record must justify.
            if no_info and s["overall"] == "low" and not s["overall_justification"]:
                errs.append(
                    f"study {sid}: overall 'low' while domain(s) {', '.join(no_info)} report "
                    f"no information — absence of evidence is not evidence of low risk; "
                    f"record an overall_justification if this is intended")

        # Rule 6 — the human gate. Presence only; see the module docstring.
        if not (s["confirmed_by"] and s["confirmed_at"]):
            unconfirmed += 1
            errs.append(f"study {sid}: no human confirmation recorded "
                        f"(confirmed_by and confirmed_at are both required)")

    return errs, unconfirmed


# --- generation --------------------------------------------------------------

def _mark(instrument: str, name: str, value) -> str:
    """Symbol AND text, never colour alone — the artifact must survive print,
    screen readers, and colour-blind readers."""
    if instrument == "nos":
        return f"{value}/{NOS_MAX[name]}"
    if instrument == "quadas2":
        v = value["risk_of_bias"]
    else:
        v = value
    return f"{MARKS.get(v, '·')} {v.replace('_', ' ')}"


def per_study_table(studies: list[dict]) -> str:
    lines = ["## Appraisal by study", "",
             "| Study | Design | Instrument | Result assessed | Overall | Confirmed |",
             "|:--|:--|:--|:--|:--|:--|"]
    for s in studies:
        confirmed = f"{s['confirmed_by']} ({s['confirmed_at']})" if s["confirmed_by"] \
            and s["confirmed_at"] else "⚠️ **not confirmed**"
        raw_overall = s["overall"] if isinstance(s["overall"], str) else "—"
        overall = f"{MARKS.get(raw_overall, '·')} {raw_overall.replace('_', ' ')}"
        if s.get("instrument_mismatch"):
            overall += " ⚠️ instrument mismatch"
        elif s["instrument"] == "nos":
            overall += f" ({nos_total(s['domains'])}/9)"
        lines.append(f"| {s['id']} | {s['design']} | {s['instrument']} | "
                     f"{s['result_assessed']} | {overall} | {confirmed} |")
    return "\n".join(lines)


def traffic_light(studies: list[dict]) -> str:
    lines = ["## Traffic-light summary", "",
             "*Each cell carries a symbol and its label; colour is never the only encoding.*", ""]
    by_instrument: dict[str, list[dict]] = {}
    for s in studies:
        by_instrument.setdefault(s["instrument"], []).append(s)

    for inst, group in by_instrument.items():
        cols = DOMAINS[inst]
        lines.append(f"**{inst}**")
        lines.append("")
        lines.append("| Study | " + " | ".join(c.replace("_", " ") for c in cols) + " | Overall |")
        lines.append("|:--|" + "|".join([":--"] * len(cols)) + "|:--|")
        for s in group:
            if s.get("instrument_mismatch"):
                lines.append(f"| {s['id']} | " + " | ".join(["— not appraised"] * len(cols)) +
                             " | ⚠️ instrument mismatch |")
                continue
            cells = [_mark(inst, c, s["domains"][c]) if c in s["domains"] else "— absent"
                     for c in cols]
            overall = f"{MARKS.get(s['overall'], '·')} {s['overall'].replace('_', ' ')}"
            lines.append(f"| {s['id']} | " + " | ".join(cells) + f" | {overall} |")
        lines.append("")

        if inst == "quadas2":
            lines.append("| Study | " + " | ".join(
                f"{c.replace('_', ' ')} (applicability)" for c in QUADAS_APPLICABILITY) + " |")
            lines.append("|:--|" + "|".join([":--"] * len(QUADAS_APPLICABILITY)) + "|")
            for s in group:
                cells = []
                for c in QUADAS_APPLICABILITY:
                    app = s["domains"].get(c, {}).get("applicability")
                    cells.append(f"{MARKS.get(app, '·')} {app}" if app else "— not rated")
                lines.append(f"| {s['id']} | " + " | ".join(cells) + " |")
            lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check a risk-of-bias appraisal record and generate its summary tables.")
    ap.add_argument("infile", nargs="?")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if the record violates a rule")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    source = args.infile or "stdin"
    try:
        raw = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()
    except OSError as e:
        sys.stderr.write(f"rob_appraisal: cannot read {source} ({e})\n")
        return 2

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"rob_appraisal: input is not valid JSON ({e})\n")
        return 2

    try:
        studies = parse(data)
        errs, unconfirmed = check(studies)
    except InputError as e:
        sys.stderr.write(f"rob_appraisal: {e}\n")
        return 2

    print(f"# Risk of bias — {len(studies)} stud{'y' if len(studies) == 1 else 'ies'}\n")
    print(per_study_table(studies))
    print()
    print(traffic_light(studies))
    print("\n## Check\n")
    if errs:
        print(f"⚠️ **{len(errs)} issue(s)** — fix before this appraisal feeds certainty grading:")
        for e in errs:
            print(f"- {e}")
    else:
        print("✅ Every study uses the instrument its design calls for, carries every domain "
              "that instrument defines, and has a recorded confirmation.")
    print(f"\n**H_rob: {unconfirmed}** stud{'y' if unconfirmed == 1 else 'ies'} awaiting human "
          f"confirmation.")
    print("\n> This check establishes that a confirmation record is present. It cannot establish "
          "that a human made the judgment, or who that person was.")
    print(f"\n---\n\n*Generated by `rob_appraisal.py` from `{source}`.*")
    return 1 if (errs and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
