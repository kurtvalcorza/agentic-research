#!/usr/bin/env python3
"""Validate the ``cochrane_intervention`` review profile. Standard library only.

WHAT THIS CHECKS
  A closed, auditable contract for the intervention-review controls in RFC #22:
  protocol completeness; required search-source evidence; record/report/study
  linkage; two distinct HUMAN full-text eligibility decisions; two distinct HUMAN
  outcome extractions; two distinct HUMAN risk-of-bias assessments; RoB 2 / ROBINS-I
  routing; a prespecified synthesis decision; and synthesis-level missing-results
  bias that explicitly feeds GRADE.

WHAT THIS CANNOT CHECK
  Whether a search strategy is scientifically optimal, whether an eligibility,
  extraction, risk-of-bias, synthesis, or missing-results-bias judgment is correct,
  whether a named human really performed the recorded action, or whether the review
  satisfies Cochrane editorial/institutional requirements. A clean result means the
  declared MECIR-oriented profile contract is complete and internally consistent;
  it is not official Cochrane certification.

EXIT CODES
  0 clean, or violations found without --strict
  1 method/profile violations under --strict
  2 malformed input — no authoritative artifact is emitted
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMA_VERSIONS = {"1.0"}
JSON_ENVELOPE_VERSION = "1.0"
PROFILE = "cochrane_intervention"

ROOT_KEYS = {
    "schema_version", "review_type", "profile", "protocol", "search", "studies",
    "screening", "extractions", "risk_of_bias", "synthesis",
    "missing_results_bias", "grade_linkage",
}
PROTOCOL_KEYS = {
    "question", "planned_comparisons", "eligibility_criteria", "outcomes",
    "time_points", "eligible_designs", "search_update_plan", "effect_measures",
    "rob_tools", "synthesis_decision_rules", "missing_results_bias_plan",
    "grade_plan", "team", "conflicts_of_interest", "stakeholder_involvement",
    "amendment_log",
}
TEAM_KEYS = {"id", "actor_type", "roles", "expertise"}
SEARCH_KEYS = {"sources", "embase", "imported_corpus", "acquisition_manifest"}
SOURCE_KEYS = {
    "name", "interface", "strategy", "controlled_vocabulary", "free_text",
    "last_searched", "coverage", "filters_limits",
}
EMBASE_KEYS = {"available", "searched", "justification"}
STUDY_KEYS = {"study_id", "reports", "primary_report", "design"}
SCREEN_KEYS = {
    "report_id", "reviewer_a", "reviewer_b", "reconciled_decision",
    "reconciliation_note", "exclusion_reason",
}
DECISION_KEYS = {"id", "actor_type", "decision"}
EXTRACTION_KEYS = {
    "result_id", "study_id", "comparison", "outcome", "outcome_definition",
    "time_point", "analysis_population", "effect_measure", "source_location",
    "extractor_a", "extractor_b", "reconciled_value", "reconciliation_note",
}
EXTRACTOR_KEYS = {"id", "actor_type", "value"}
ROB_KEYS = {
    "result_id", "study_id", "design", "instrument", "assessor_a", "assessor_b",
    "reconciled_judgment", "reconciliation_note",
}
ASSESSOR_KEYS = {"id", "actor_type", "judgment"}
SYNTHESIS_KEYS = {"method", "prespecified_decision_rule", "rationale"}
MRB_KEYS = {"result_id", "judgment", "rationale"}
GRADE_LINK_KEYS = {"missing_results_bias_feeds_grade"}

VALID_DESIGNS = {"rct", "nrsi"}
ROB_ROUTE = {"rct": "RoB 2", "nrsi": "ROBINS-I"}
SCREEN_DECISIONS = {"include", "exclude"}
SYNTHESIS_METHODS = {"meta_analysis", "non_meta"}


class InputError(ValueError):
    """Malformed input (exit 2)."""


def _obj(value, ctx: str) -> dict:
    if not isinstance(value, dict):
        raise InputError(f"{ctx}: expected an object, got {type(value).__name__}")
    return value


def _list(value, ctx: str) -> list:
    if not isinstance(value, list):
        raise InputError(f"{ctx}: expected a list, got {type(value).__name__}")
    return value


def _text(value, ctx: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise InputError(f"{ctx}: expected a string, got {type(value).__name__} {value!r}")
    out = value.strip()
    if not allow_empty and not out:
        raise InputError(f"{ctx}: expected non-empty text")
    return out


def _bool(value, ctx: str) -> bool:
    if not isinstance(value, bool):
        raise InputError(f"{ctx}: expected a boolean, got {type(value).__name__} {value!r}")
    return value


def _closed(value: dict, allowed: set[str], ctx: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise InputError(
            f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
            f"(expected one of: {', '.join(sorted(allowed))})"
        )


def _required_text_fields(value: dict, fields: tuple[str, ...], ctx: str) -> None:
    for field in fields:
        if field not in value:
            raise InputError(f"{ctx}: missing required field {field!r}")
        _text(value[field], f"{ctx}.{field}")


def _required_nonempty_list(value: dict, field: str, ctx: str) -> list:
    if field not in value:
        raise InputError(f"{ctx}: missing required field {field!r}")
    rows = _list(value[field], f"{ctx}.{field}")
    if not rows:
        raise InputError(f"{ctx}.{field}: must not be empty")
    return rows


def parse(raw: dict) -> dict:
    _obj(raw, "record")
    _closed(raw, ROOT_KEYS, "record")

    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(
            f"record: unrecognised or missing schema_version {version!r} "
            f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})"
        )
    if raw.get("review_type") != "systematic":
        raise InputError("record.review_type: cochrane_intervention requires 'systematic'")
    if raw.get("profile") != PROFILE:
        raise InputError(f"record.profile: expected {PROFILE!r}, got {raw.get('profile')!r}")

    protocol = _obj(raw.get("protocol"), "record.protocol")
    _closed(protocol, PROTOCOL_KEYS, "record.protocol")
    _required_text_fields(
        protocol,
        (
            "question", "search_update_plan", "synthesis_decision_rules",
            "missing_results_bias_plan", "grade_plan", "stakeholder_involvement",
        ),
        "record.protocol",
    )
    for field in (
        "planned_comparisons", "eligibility_criteria", "outcomes", "time_points",
        "eligible_designs", "effect_measures", "rob_tools", "team",
        "conflicts_of_interest", "amendment_log",
    ):
        rows = _required_nonempty_list(protocol, field, "record.protocol")
        if field != "team":
            for i, item in enumerate(rows):
                _text(item, f"record.protocol.{field}[{i}]")

    for i, member in enumerate(protocol["team"]):
        ctx = f"record.protocol.team[{i}]"
        _obj(member, ctx)
        _closed(member, TEAM_KEYS, ctx)
        _required_text_fields(member, ("id", "actor_type"), ctx)
        if member["actor_type"] != "human":
            raise InputError(f"{ctx}.actor_type: review-team members must be 'human'")
        for field in ("roles", "expertise"):
            vals = _required_nonempty_list(member, field, ctx)
            for j, item in enumerate(vals):
                _text(item, f"{ctx}.{field}[{j}]")

    search = _obj(raw.get("search"), "record.search")
    _closed(search, SEARCH_KEYS, "record.search")
    sources = _required_nonempty_list(search, "sources", "record.search")
    for i, source in enumerate(sources):
        ctx = f"record.search.sources[{i}]"
        _obj(source, ctx)
        _closed(source, SOURCE_KEYS, ctx)
        _required_text_fields(
            source,
            (
                "name", "interface", "strategy", "controlled_vocabulary", "free_text",
                "last_searched", "coverage", "filters_limits",
            ),
            ctx,
        )

    embase = _obj(search.get("embase"), "record.search.embase")
    _closed(embase, EMBASE_KEYS, "record.search.embase")
    if "available" not in embase or "searched" not in embase:
        raise InputError("record.search.embase: 'available' and 'searched' are required")
    _bool(embase["available"], "record.search.embase.available")
    _bool(embase["searched"], "record.search.embase.searched")
    if "justification" in embase:
        _text(embase["justification"], "record.search.embase.justification", allow_empty=True)

    if "imported_corpus" not in search:
        raise InputError("record.search: 'imported_corpus' is required")
    _bool(search["imported_corpus"], "record.search.imported_corpus")
    if "acquisition_manifest" in search:
        _text(search["acquisition_manifest"], "record.search.acquisition_manifest", allow_empty=True)

    studies = _required_nonempty_list(raw, "studies", "record")
    for i, study in enumerate(studies):
        ctx = f"record.studies[{i}]"
        _obj(study, ctx)
        _closed(study, STUDY_KEYS, ctx)
        _required_text_fields(study, ("study_id", "primary_report", "design"), ctx)
        reports = _required_nonempty_list(study, "reports", ctx)
        for j, report in enumerate(reports):
            _text(report, f"{ctx}.reports[{j}]")

    screening = _required_nonempty_list(raw, "screening", "record")
    for i, row in enumerate(screening):
        ctx = f"record.screening[{i}]"
        _obj(row, ctx)
        _closed(row, SCREEN_KEYS, ctx)
        _required_text_fields(row, ("report_id", "reconciled_decision"), ctx)
        if row["reconciled_decision"] not in SCREEN_DECISIONS:
            raise InputError(
                f"{ctx}.reconciled_decision: expected one of {sorted(SCREEN_DECISIONS)!r}"
            )
        for who in ("reviewer_a", "reviewer_b"):
            reviewer = _obj(row.get(who), f"{ctx}.{who}")
            _closed(reviewer, DECISION_KEYS, f"{ctx}.{who}")
            _required_text_fields(reviewer, ("id", "actor_type", "decision"), f"{ctx}.{who}")
            if reviewer["decision"] not in SCREEN_DECISIONS:
                raise InputError(f"{ctx}.{who}.decision: invalid decision {reviewer['decision']!r}")
        for field in ("reconciliation_note", "exclusion_reason"):
            if field in row:
                _text(row[field], f"{ctx}.{field}", allow_empty=True)

    extractions = _required_nonempty_list(raw, "extractions", "record")
    for i, row in enumerate(extractions):
        ctx = f"record.extractions[{i}]"
        _obj(row, ctx)
        _closed(row, EXTRACTION_KEYS, ctx)
        _required_text_fields(
            row,
            (
                "result_id", "study_id", "comparison", "outcome", "outcome_definition",
                "time_point", "analysis_population", "effect_measure", "source_location",
            ),
            ctx,
        )
        if "reconciled_value" not in row:
            raise InputError(f"{ctx}: missing required field 'reconciled_value'")
        for who in ("extractor_a", "extractor_b"):
            extractor = _obj(row.get(who), f"{ctx}.{who}")
            _closed(extractor, EXTRACTOR_KEYS, f"{ctx}.{who}")
            _required_text_fields(extractor, ("id", "actor_type"), f"{ctx}.{who}")
            if "value" not in extractor:
                raise InputError(f"{ctx}.{who}: missing required field 'value'")
        if "reconciliation_note" in row:
            _text(row["reconciliation_note"], f"{ctx}.reconciliation_note", allow_empty=True)

    robs = _required_nonempty_list(raw, "risk_of_bias", "record")
    for i, row in enumerate(robs):
        ctx = f"record.risk_of_bias[{i}]"
        _obj(row, ctx)
        _closed(row, ROB_KEYS, ctx)
        _required_text_fields(
            row, ("result_id", "study_id", "design", "instrument", "reconciled_judgment"), ctx
        )
        for who in ("assessor_a", "assessor_b"):
            assessor = _obj(row.get(who), f"{ctx}.{who}")
            _closed(assessor, ASSESSOR_KEYS, f"{ctx}.{who}")
            _required_text_fields(assessor, ("id", "actor_type", "judgment"), f"{ctx}.{who}")
        if "reconciliation_note" in row:
            _text(row["reconciliation_note"], f"{ctx}.reconciliation_note", allow_empty=True)

    synthesis = _obj(raw.get("synthesis"), "record.synthesis")
    _closed(synthesis, SYNTHESIS_KEYS, "record.synthesis")
    _required_text_fields(
        synthesis, ("method", "prespecified_decision_rule", "rationale"), "record.synthesis"
    )
    if synthesis["method"] not in SYNTHESIS_METHODS:
        raise InputError(
            f"record.synthesis.method: expected one of {sorted(SYNTHESIS_METHODS)!r}"
        )

    mrb = _required_nonempty_list(raw, "missing_results_bias", "record")
    for i, row in enumerate(mrb):
        ctx = f"record.missing_results_bias[{i}]"
        _obj(row, ctx)
        _closed(row, MRB_KEYS, ctx)
        _required_text_fields(row, ("result_id", "judgment", "rationale"), ctx)

    grade = _obj(raw.get("grade_linkage"), "record.grade_linkage")
    _closed(grade, GRADE_LINK_KEYS, "record.grade_linkage")
    if "missing_results_bias_feeds_grade" not in grade:
        raise InputError(
            "record.grade_linkage: 'missing_results_bias_feeds_grade' is required"
        )
    _bool(
        grade["missing_results_bias_feeds_grade"],
        "record.grade_linkage.missing_results_bias_feeds_grade",
    )
    return raw


def _human_pair(a: dict, b: dict, ctx: str, errors: list[str]) -> None:
    if a["actor_type"] != "human" or b["actor_type"] != "human":
        errors.append(f"{ctx}: both independent reviewers must be recorded as human actors")
    if a["id"] == b["id"]:
        errors.append(f"{ctx}: reviewer A and reviewer B must be distinct people")


def check(record: dict) -> list[str]:
    errors: list[str] = []
    protocol = record["protocol"]

    team_ids = [member["id"] for member in protocol["team"]]
    if len(set(team_ids)) < 2:
        errors.append("protocol.team: at least two distinct human review-team members are required")
    expertise = {e.casefold() for member in protocol["team"] for e in member["expertise"]}
    if not any("method" in e or "systematic review" in e for e in expertise):
        errors.append("protocol.team: methodological/systematic-review expertise is not recorded")
    if not any("topic" in e or "clinical" in e or "domain" in e for e in expertise):
        errors.append("protocol.team: topic/domain expertise is not recorded")

    source_names = {s["name"].strip().casefold() for s in record["search"]["sources"]}
    if "central" not in source_names:
        errors.append("search.sources: CENTRAL is required for the cochrane_intervention profile")
    if not ({"medline", "pubmed"} & source_names):
        errors.append("search.sources: MEDLINE/PubMed is required for the cochrane_intervention profile")
    embase = record["search"]["embase"]
    if embase["available"]:
        if not embase["searched"] or "embase" not in source_names:
            errors.append("search.embase: Embase is available but was not documented as searched")
    else:
        if embase["searched"]:
            errors.append("search.embase: cannot be marked searched when available=false")
        if not (embase.get("justification") or "").strip():
            errors.append("search.embase: unavailability requires an explicit justification")
    if record["search"]["imported_corpus"] and not (
        record["search"].get("acquisition_manifest") or ""
    ).strip():
        errors.append(
            "search.acquisition_manifest: imported/pre-collected corpora require a conforming acquisition manifest"
        )

    study_ids: set[str] = set()
    report_to_study: dict[str, str] = {}
    study_design: dict[str, str] = {}
    for study in record["studies"]:
        sid = study["study_id"]
        if sid in study_ids:
            errors.append(f"studies: duplicate study_id {sid!r}")
            continue
        study_ids.add(sid)
        design = study["design"]
        study_design[sid] = design
        if design not in VALID_DESIGNS:
            errors.append(
                f"study {sid}: design {design!r} is outside the intervention profile's rct/nrsi routing contract"
            )
        if study["primary_report"] not in study["reports"]:
            errors.append(f"study {sid}: primary_report must be one of the linked reports")
        if len(study["reports"]) != len(set(study["reports"])):
            errors.append(f"study {sid}: duplicate report id in reports")
        for report in study["reports"]:
            other = report_to_study.get(report)
            if other and other != sid:
                errors.append(f"report {report!r}: linked to more than one study ({other}, {sid})")
            report_to_study[report] = sid

    screening_by_report: dict[str, dict] = {}
    for row in record["screening"]:
        rid = row["report_id"]
        if rid in screening_by_report:
            errors.append(f"screening: duplicate report_id {rid!r}")
            continue
        screening_by_report[rid] = row
        if rid not in report_to_study:
            errors.append(f"screening {rid}: report is not linked to a study")
        _human_pair(row["reviewer_a"], row["reviewer_b"], f"screening {rid}", errors)
        a, b = row["reviewer_a"]["decision"], row["reviewer_b"]["decision"]
        if a != b and not (row.get("reconciliation_note") or "").strip():
            errors.append(f"screening {rid}: disagreement requires a reconciliation note")
        if row["reconciled_decision"] == "exclude" and not (
            row.get("exclusion_reason") or ""
        ).strip():
            errors.append(f"screening {rid}: excluded full text requires an exclusion reason")
    missing_screen = sorted(set(report_to_study) - set(screening_by_report))
    for rid in missing_screen:
        errors.append(f"screening {rid}: no independent full-text eligibility record")

    extraction_keys: set[tuple[str, str]] = set()
    results: set[str] = set()
    for row in record["extractions"]:
        key = (row["study_id"], row["result_id"])
        if key in extraction_keys:
            errors.append(f"extractions: duplicate study/result pair {key!r}")
        extraction_keys.add(key)
        results.add(row["result_id"])
        if row["study_id"] not in study_ids:
            errors.append(f"extraction {row['result_id']}: unknown study {row['study_id']!r}")
        _human_pair(row["extractor_a"], row["extractor_b"], f"extraction {key!r}", errors)
        if row["extractor_a"]["value"] != row["extractor_b"]["value"] and not (
            row.get("reconciliation_note") or ""
        ).strip():
            errors.append(f"extraction {key!r}: differing independent values require reconciliation")

    rob_keys: set[tuple[str, str]] = set()
    for row in record["risk_of_bias"]:
        key = (row["study_id"], row["result_id"])
        if key in rob_keys:
            errors.append(f"risk_of_bias: duplicate study/result pair {key!r}")
        rob_keys.add(key)
        if key not in extraction_keys:
            errors.append(f"risk_of_bias {key!r}: no corresponding extracted result")
        design = row["design"]
        if row["study_id"] in study_design and design != study_design[row["study_id"]]:
            errors.append(f"risk_of_bias {key!r}: design disagrees with study linkage record")
        expected = ROB_ROUTE.get(design)
        if expected is None:
            errors.append(f"risk_of_bias {key!r}: unsupported intervention design {design!r}")
        elif row["instrument"] != expected:
            errors.append(
                f"risk_of_bias {key!r}: {design} must route to {expected}, got {row['instrument']!r}"
            )
        _human_pair(row["assessor_a"], row["assessor_b"], f"risk_of_bias {key!r}", errors)
        if row["assessor_a"]["judgment"] != row["assessor_b"]["judgment"] and not (
            row.get("reconciliation_note") or ""
        ).strip():
            errors.append(f"risk_of_bias {key!r}: differing judgments require reconciliation")
    for key in sorted(extraction_keys - rob_keys):
        errors.append(f"risk_of_bias {key!r}: missing independent duplicate appraisal")

    mrb_by_result: set[str] = set()
    for row in record["missing_results_bias"]:
        rid = row["result_id"]
        if rid in mrb_by_result:
            errors.append(f"missing_results_bias: duplicate result_id {rid!r}")
        mrb_by_result.add(rid)
        if rid not in results:
            errors.append(f"missing_results_bias {rid}: result does not exist in extraction records")
    for rid in sorted(results - mrb_by_result):
        errors.append(f"missing_results_bias {rid}: synthesis-level assessment is required")

    if record["grade_linkage"]["missing_results_bias_feeds_grade"] is not True:
        errors.append(
            "grade_linkage: missing-results-bias assessment must explicitly feed the GRADE dissemination/publication-bias domain"
        )
    return errors


def render(record: dict, errors: list[str], source: str) -> str:
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# Cochrane MECIR intervention-review profile",
        "",
        f"**Profile:** `{PROFILE}`  ",
        f"**Contract status:** **{status}**",
        "",
    ]
    if errors:
        lines += [f"## ⚠️ {len(errors)} profile violation(s)", ""]
        lines += [f"- {e}" for e in errors]
    else:
        lines += [
            "✅ All machine-checkable MECIR-oriented profile invariants are satisfied.",
            "",
            "This is **profile verification**, not official Cochrane certification or an editorial decision.",
        ]
    lines += [
        "",
        "---",
        f"*Generated by `cochrane_profile.py` from `{source}`. The check validates the declared "
        "record and human-actor invariants; it cannot establish that expert judgments are correct "
        "or that the named actors/authorship history is authentic.*",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Cochrane MECIR intervention-review profile record.")
    parser.add_argument("infile", nargs="?")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    source = args.infile or "stdin"
    try:
        raw_text = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"cochrane_profile: cannot read {source} ({exc})\n")
        return 2
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"cochrane_profile: input is not valid JSON ({exc})\n")
        return 2
    try:
        record = parse(raw)
    except InputError as exc:
        sys.stderr.write(f"cochrane_profile: {exc}\n")
        return 2

    errors = check(record)
    if args.json:
        json.dump(
            {
                "check": "cochrane_profile",
                "schema_version": JSON_ENVELOPE_VERSION,
                "issues": len(errors),
                "units": {"U_cochrane": len(errors)},
                "gates": {},
                "unattributed": 0,
                "detail": {"profile": PROFILE},
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1 if errors and args.strict else 0

    print(render(record, errors, source))
    return 1 if errors and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
