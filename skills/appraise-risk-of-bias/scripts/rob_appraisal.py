#!/usr/bin/env python3
"""
rob_appraisal.py — check a risk-of-bias appraisal record and generate the
per-appraisal table and traffic-light summary from it. Standard library only.

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
import math
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


def _opt_str(v, name: str) -> str:
    """A text field that may be absent, but must be a STRING when present.

    Never coerce with str(): str({}) is "{}" — truthy and non-empty — which would
    let a malformed JSON object satisfy a check that only tests for emptiness. That
    is how a confirmation gate silently passes on garbage.
    """
    if v is None:
        return ""
    if not isinstance(v, str):
        raise InputError(f"{name}: expected a string, got {type(v).__name__} {v!r}")
    return v.strip()


def _no_unknown_keys(d: dict, allowed, ctx: str) -> None:
    unknown = sorted(set(d) - set(allowed))
    if unknown:
        raise InputError(f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
                         f"(expected one of: {', '.join(sorted(allowed))})")


def _parse_evidence(v, ctx: str, allowed=None) -> dict:
    """Evidence is optional, but if supplied it must be what the schema says.

    `s.get("evidence", {}) or {}` accepted anything: a string, a list and an int
    all passed through, while explicit null was silently converted to {}. Those
    records exited 0 under --strict, then went on to back a confirmed_rob
    certainty rating. Absent is fine; wrong is not — the same fail-closed rule
    the leaf text fields already follow.

    `allowed` is the instrument's domain keys, or None on the instrument-mismatch
    path where the declared instrument is the wrong yardstick to measure against.
    """
    if not isinstance(v, dict):
        raise InputError(f"{ctx}: expected an object mapping domain keys to quoted "
                         f"supporting text, got {type(v).__name__} {v!r}")
    if allowed is not None:
        _no_unknown_keys(v, allowed, ctx)
    for name, text in v.items():
        if not isinstance(text, str) or not text.strip():
            raise InputError(f"{ctx}.{name}: expected a non-empty string quoting the "
                             f"supporting text, got {type(text).__name__} {text!r}")
    return dict(v)


def _stars(v, ctx: str, maximum: int) -> int:
    """Star count. Accepts an integral float (JSON has one number type, so 3.0 is 3),
    matching the shared coercion contract used by the other checks."""
    if isinstance(v, bool):
        raise InputError(f"{ctx}: expected an integer star count, got boolean {v!r}")
    if isinstance(v, float):
        if not math.isfinite(v) or not v.is_integer():
            raise InputError(f"{ctx}: star count must be a whole number, got {v!r}")
        v = int(v)
    if not isinstance(v, int):
        raise InputError(f"{ctx}: expected an integer star count, got {v!r}")
    if v < 0 or v > maximum:
        raise InputError(f"{ctx}: star count must be between 0 and {maximum}, got {v}")
    return v


def parse(raw: dict) -> list[dict]:
    _obj(raw, "record")
    _no_unknown_keys(raw, {"schema_version", "studies"}, "record")

    version = raw.get("schema_version")
    # isinstance FIRST: an unhashable value raises TypeError on set membership.
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(f"record: unrecognised or missing schema_version {version!r} "
                         f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})")

    studies = raw.get("studies")
    if not isinstance(studies, list):
        raise InputError("record: 'studies' must be a list")
    if not studies:
        raise InputError("record: 'studies' is empty — there is nothing to appraise")

    seen: set = set()
    parsed = [_parse_study(s, i, seen) for i, s in enumerate(studies)]

    # A study is one study: its design is a property of the study, not of the result
    # being appraised, so it cannot differ between that study's own appraisals even
    # though its risk-of-bias judgment legitimately can.
    designs: dict = {}
    for st in parsed:
        prior = designs.setdefault(st["id"], st["design"])
        if prior != st["design"]:
            raise InputError(
                f"study {st['id']}: appraised as both {prior!r} and {st['design']!r} — "
                f"a study has one design; only its risk-of-bias judgment varies by "
                f"result")
    return parsed


def _parse_study(s, i: int, seen: set) -> dict:
    ctx = f"studies[{i}]"
    _obj(s, ctx)
    _no_unknown_keys(s, STUDY_KEYS, ctx)

    sid = _str(s.get("id"), f"{ctx}.id")

    # RoB 2 and ROBINS-I appraise a SPECIFIC RESULT, not a study as a whole, so a
    # study contributing to two outcomes carries two appraisals with two judgments.
    # Identity is therefore (study, result), not study alone: keying on the study id
    # made the correct representation inexpressible, because the second appraisal
    # was rejected as a duplicate.
    result_assessed = _str(s.get("result_assessed"), f"{ctx}.result_assessed")
    key = (sid, result_assessed)
    if key in seen:
        raise InputError(f"{ctx}: study {sid!r} is appraised twice for result "
                         f"{result_assessed!r} — a duplicate appraisal is ambiguous. "
                         f"Two appraisals of one study must name different results.")
    seen.add(key)
    ctx = f"study {sid} ({result_assessed})"

    design = s.get("design")
    if not isinstance(design, str) or design not in DESIGN_INSTRUMENT:
        raise InputError(f"{ctx}.design: must be one of "
                         f"{', '.join(sorted(DESIGN_INSTRUMENT))}, got {design!r}")
    instrument = s.get("instrument")
    if not isinstance(instrument, str) or instrument not in DOMAINS:
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
        # Leaf types are still validated even though the vocabulary cannot be: a
        # domain value must be a string, a number, or an object whatever the
        # instrument. Without this, malformed values reach the generator and crash
        # it AFTER the first table has been printed.
        for name, value in domains_raw.items():
            if not isinstance(value, (str, int, float, dict)) or isinstance(value, bool):
                raise InputError(f"{ctx}.domains.{name}: expected a string, number or "
                                 f"object, got {type(value).__name__} {value!r}")
        # `overall` is required whatever the instrument. Deferring the VOCABULARY
        # check is right (we cannot know which vocabulary applies), but presence is
        # instrument-independent, and omitting it produced an artifact with an em
        # dash rather than exit 2.
        _str(overall, f"{ctx}.overall")
        return {"id": sid, "design": design, "instrument": instrument,
                "result_assessed": result_assessed,
                "domains": dict(domains_raw),
                "evidence": _parse_evidence(s.get("evidence", {}), f"{ctx}.evidence"),
                "overall": overall,
                "overall_justification": _opt_str(s.get("overall_justification"),
                                                  f"{ctx}.overall_justification"),
                "confirmed_by": _opt_str(s.get("confirmed_by"), f"{ctx}.confirmed_by"),
                "confirmed_at": _opt_str(s.get("confirmed_at"), f"{ctx}.confirmed_at"),
                "instrument_mismatch": True}

    # Unknown domain -> malformed (exit 2). Missing domain -> violation (exit 1).
    _no_unknown_keys(domains_raw, DOMAINS[instrument], f"{ctx}.domains")
    domains = {}
    for name, value in domains_raw.items():
        domains[name] = _parse_domain(instrument, name, value, f"{ctx}.domains.{name}")

    if not isinstance(overall, str) or overall not in SEVERITY[instrument]:
        raise InputError(f"{ctx}.overall: must be one of "
                         f"{', '.join(SEVERITY[instrument])} for {instrument}, got {overall!r}")

    return {"id": sid, "design": design, "instrument": instrument,
            "result_assessed": result_assessed,
            "domains": domains,
            "evidence": _parse_evidence(s.get("evidence", {}), f"{ctx}.evidence",
                                        DOMAINS[instrument]),
            "overall": overall,
            "overall_justification": _opt_str(s.get("overall_justification"),
                                              f"{ctx}.overall_justification"),
            "confirmed_by": _opt_str(s.get("confirmed_by"), f"{ctx}.confirmed_by"),
            "confirmed_at": _opt_str(s.get("confirmed_at"), f"{ctx}.confirmed_at")}


def _parse_domain(instrument: str, name: str, value, ctx: str):
    if instrument == "nos":
        return _stars(value, ctx, NOS_MAX[name])
    if instrument == "quadas2":
        d = _obj(value, ctx)
        allowed = {"risk_of_bias"} | ({"applicability"} if name in QUADAS_APPLICABILITY else set())
        _no_unknown_keys(d, allowed, ctx)
        rob = d.get("risk_of_bias")
        if not isinstance(rob, str) or rob not in SEVERITY["quadas2"]:
            raise InputError(f"{ctx}.risk_of_bias: must be one of "
                             f"{', '.join(SEVERITY['quadas2'])}, got {rob!r}")
        # QUADAS-2's first three domains carry an applicability judgment as well as
        # a risk-of-bias one. Treating it as optional meant a record omitting all
        # three still reported a clean, complete appraisal — an incomplete appraisal
        # presented as a finished one.
        app = d.get("applicability")
        if name in QUADAS_APPLICABILITY and (
                not isinstance(app, str) or app not in SEVERITY["quadas2"]):
            raise InputError(f"{ctx}.applicability: must be one of "
                             f"{', '.join(SEVERITY['quadas2'])}, got {app!r}")
        return {"risk_of_bias": rob, "applicability": app}
    if not isinstance(value, str) or value not in SEVERITY[instrument]:
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
    """Return (violations, count of APPRAISALS awaiting human confirmation).

    Appraisals, not studies: identity is (study, result), and each is confirmed
    separately because a human signs off on a judgment about one result.
    """
    errs: list[str] = []
    unconfirmed = 0

    for s in studies:
        sid, inst = s["id"], s["instrument"]
        # Identify the APPRAISAL, not the study. When one study is appraised for two
        # results and only one judgment is at fault, "study R1" cannot tell the
        # reviewer which of the two to go and fix.
        who = f"study {sid} (result: {s['result_assessed']!r})"

        # Rule 6 — the human gate, checked FIRST and for every study.
        # It is independent of which instrument was applied: a study with the wrong
        # instrument that also lacks confirmation is still awaiting a human, and
        # must not vanish from H_rob because an earlier check short-circuited.
        if not (s["confirmed_by"] and s["confirmed_at"]):
            unconfirmed += 1
            errs.append(f"{who}: no human confirmation recorded "
                        f"(confirmed_by and confirmed_at are both required)")

        # Rule 1 — the instrument must match the design.
        expected = DESIGN_INSTRUMENT[s["design"]]
        if inst != expected:
            errs.append(f"{who}: design '{s['design']}' calls for {expected}, "
                        f"but {inst} was applied")
            continue  # domain checks below would be against the wrong instrument

        # Rule 2 — every domain the instrument defines must be present.
        missing = [d for d in DOMAINS[inst] if d not in s["domains"]]
        if missing:
            errs.append(f"{who}: {inst} requires domain(s) {', '.join(missing)}, "
                        f"which are absent")
            continue

        # Rule 3/5 — the overall judgment against the domains beneath it.
        if inst == "nos":
            total = nos_total(s["domains"])
            band = nos_band(total)
            if s["overall"] != band and not s["overall_justification"]:
                errs.append(
                    f"{who}: Newcastle-Ottawa total is {total}/9, which bands as "
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
                        f"{who}: overall '{s['overall']}' is more favourable than its "
                        f"worst domain ({worst_domain} = '{worst_value}') — record an "
                        f"overall_justification if this is intended")

            # 'No information' is not a clean bill of health. Concluding low risk while
            # a domain is unreported is a judgment the record must justify.
            if no_info and s["overall"] == "low" and not s["overall_justification"]:
                errs.append(
                    f"{who}: overall 'low' while domain(s) {', '.join(no_info)} report "
                    f"no information — absence of evidence is not evidence of low risk; "
                    f"record an overall_justification if this is intended")

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


def _markdown_cell(value: object) -> str:
    """Render caller-controlled text without creating extra table cells or rows."""
    return (str(value).replace("\r\n", "\n").replace("\r", "\n")
            .replace("|", "&#124;").replace("\n", "<br>"))


def per_study_table(studies: list[dict]) -> str:
    lines = ["## Appraisal by study", "",
             "| Study | Design | Instrument | Result assessed | Overall | Confirmed |",
             "|:--|:--|:--|:--|:--|:--|"]
    for s in studies:
        confirmed = (
            f"{_markdown_cell(s['confirmed_by'])} ({_markdown_cell(s['confirmed_at'])})"
            if s["confirmed_by"] and s["confirmed_at"] else "⚠️ **not confirmed**"
        )
        raw_overall = s["overall"] if isinstance(s["overall"], str) else "—"
        overall = f"{MARKS.get(raw_overall, '·')} {raw_overall.replace('_', ' ')}"
        if s.get("instrument_mismatch"):
            overall += " ⚠️ instrument mismatch"
        elif s["instrument"] == "nos":
            overall += f" ({nos_total(s['domains'])}/9)"
        lines.append(f"| {_markdown_cell(s['id'])} | {s['design']} | {s['instrument']} | "
                     f"{_markdown_cell(s['result_assessed'])} | {overall} | {confirmed} |")
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
        # The result is a column, not a decoration: identity is (study, result), so a
        # study appraised for two results renders two rows that are otherwise identical.
        lines.append("| Study | Result assessed | " +
                     " | ".join(c.replace("_", " ") for c in cols) + " | Overall |")
        lines.append("|:--|:--|" + "|".join([":--"] * len(cols)) + "|:--|")
        for s in group:
            head = (f"| {_markdown_cell(s['id'])} | "
                    f"{_markdown_cell(s['result_assessed'])} | ")
            if s.get("instrument_mismatch"):
                lines.append(head + " | ".join(["— not appraised"] * len(cols)) +
                             " | ⚠️ instrument mismatch |")
                continue
            cells = [_mark(inst, c, s["domains"][c]) if c in s["domains"] else "— absent"
                     for c in cols]
            overall = f"{MARKS.get(s['overall'], '·')} {s['overall'].replace('_', ' ')}"
            lines.append(head + " | ".join(cells) + f" | {overall} |")
        lines.append("")

        if inst == "quadas2":
            lines.append("| Study | Result assessed | " + " | ".join(
                f"{c.replace('_', ' ')} (applicability)" for c in QUADAS_APPLICABILITY) + " |")
            lines.append("|:--|:--|" + "|".join([":--"] * len(QUADAS_APPLICABILITY)) + "|")
            for s in group:
                head = (f"| {_markdown_cell(s['id'])} | "
                        f"{_markdown_cell(s['result_assessed'])} | ")
                if s.get("instrument_mismatch"):
                    # Its domains were never validated against quadas2, so they may
                    # not be objects at all. Rendering them would crash mid-artifact.
                    lines.append(head + " | ".join(
                        ["— not appraised"] * len(QUADAS_APPLICABILITY)) + " |")
                    continue
                cells = []
                for c in QUADAS_APPLICABILITY:
                    entry = s["domains"].get(c)
                    app = entry.get("applicability") if isinstance(entry, dict) else None
                    cells.append(f"{MARKS.get(app, '·')} {app}" if app else "— not rated")
                lines.append(head + " | ".join(cells) + " |")
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
        if args.infile:
            with open(args.infile, encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
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

    # Since identity is (study, result), len(studies) counts APPRAISALS, not studies.
    # Reporting it as a study count inflates the manuscript-facing figure whenever a
    # study contributes to more than one result.
    n_appraisals = len(studies)
    n_studies = len({s["id"] for s in studies})
    head = f"# Risk of bias — {n_appraisals} appraisal{'' if n_appraisals == 1 else 's'}"
    head += f" of {n_studies} stud{'y' if n_studies == 1 else 'ies'}"
    print(head + "\n")
    print(per_study_table(studies))
    print()
    print(traffic_light(studies))
    print("\n## Check\n")
    if errs:
        print(f"⚠️ **{len(errs)} issue(s)** — fix before this appraisal feeds certainty grading:")
        for e in errs:
            print(f"- {e}")
    else:
        print("✅ Every appraisal uses the instrument its design calls for, carries every domain "
              "that instrument defines, and has a recorded confirmation.")
    # H_rob has always counted appraisals — each is confirmed separately, since a
    # human signs off on a judgment about one result, not on a study wholesale.
    print(f"\n**H_rob: {unconfirmed}** appraisal{'' if unconfirmed == 1 else 's'} awaiting human "
          f"confirmation.")
    print("\n> This check establishes that a confirmation record is present. It cannot establish "
          "that a human made the judgment, or who that person was.")
    print(f"\n---\n\n*Generated by `rob_appraisal.py` from `{source}`.*")
    return 1 if (errs and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
