#!/usr/bin/env python3
"""Validate the ``cochrane_intervention`` review profile. Standard library only.

WHAT THIS CHECKS
  A closed, auditable contract for the intervention-review controls in RFC #22:
  protocol completeness with a role-vocabulary expertise check (methodologist,
  statistician, topic expert); required search-source evidence with normalised
  source-name matching and a structured acquisition-manifest reference;
  record/report/study linkage; two distinct HUMAN full-text eligibility
  decisions bound to `protocol.team`, each carrying a recorded_at timestamp and
  an independence attestation, with a rationale required whenever reconciliation
  overturns a unanimous pair; two distinct HUMAN outcome extractions of
  structured, typed result-level effect data (binary/continuous/precomputed);
  two distinct HUMAN risk-of-bias assessments under the same independence and
  reconciliation controls; RoB 2 / ROBINS-I routing; a prespecified synthesis
  decision; and synthesis-level missing-results bias that is linked, by result
  id, into named GRADE outcomes rather than declared as a bare boolean.

WHAT THIS CANNOT CHECK
  Whether a search strategy is scientifically optimal, whether an eligibility,
  extraction, risk-of-bias, synthesis, or missing-results-bias judgment is
  correct, whether a named human really performed the recorded action (an
  independence attestation and a timestamp are self-declared, not
  authenticated), or whether the review satisfies Cochrane editorial/
  institutional requirements. A clean result means the declared MECIR-oriented
  profile contract is complete and internally consistent; it is not official
  Cochrane certification.

EXIT CODES
  0 clean, or violations found without --strict
  1 method/profile violations under --strict
  2 malformed input — no authoritative artifact is emitted
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

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
EXPERTISE_VOCAB = {
    "methodologist", "statistician", "topic_expert", "information_specialist",
    "consumer_representative",
}
REQUIRED_EXPERTISE = {"methodologist", "statistician", "topic_expert"}
SEARCH_KEYS = {"sources", "embase", "imported_corpus", "acquisition_manifest"}
SOURCE_KEYS = {
    "name", "interface", "strategy", "controlled_vocabulary", "free_text",
    "last_searched", "coverage", "filters_limits",
}
EMBASE_KEYS = {"available", "searched", "justification"}
ACQUISITION_MANIFEST_KEYS = {"reference", "digest", "captured_by"}
STUDY_KEYS = {"study_id", "reports", "primary_report", "design"}
SCREEN_KEYS = {
    "report_id", "reviewer_a", "reviewer_b", "reconciled_decision",
    "reconciliation_note", "exclusion_reason",
}
DECISION_KEYS = {"id", "actor_type", "decision", "recorded_at", "independence_attestation"}
EXTRACTION_KEYS = {
    "result_id", "study_id", "comparison", "outcome", "outcome_definition",
    "time_point", "analysis_population", "effect_measure", "source_location",
    "outcome_type", "extractor_a", "extractor_b", "reconciled_value",
    "reconciliation_note",
}
EXTRACTOR_KEYS = {"id", "actor_type", "value", "recorded_at", "independence_attestation"}
OUTCOME_TYPES = {"binary", "continuous", "precomputed_effect"}
GROUP_KEYS_BY_TYPE = {
    "binary": {"n", "events"},
    "continuous": {"n", "mean", "sd"},
}
PRECOMPUTED_KEYS = {"estimate", "ci_lower", "ci_upper", "se", "variance"}
PRECOMPUTED_REQUIRED = ("estimate", "ci_lower", "ci_upper")
PRECOMPUTED_OPTIONAL = ("se", "variance")
ROB_KEYS = {
    "result_id", "study_id", "design", "instrument", "assessor_a", "assessor_b",
    "reconciled_judgment", "reconciliation_note",
}
ASSESSOR_KEYS = {"id", "actor_type", "judgment", "recorded_at", "independence_attestation"}
SYNTHESIS_KEYS = {"method", "prespecified_decision_rule", "rationale"}
MRB_KEYS = {"result_id", "judgment", "rationale"}
GRADE_LINK_KEYS = {"linked_results"}
LINKED_RESULT_KEYS = {"result_id", "grade_outcome", "certainty_domain"}

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


def _number(value, ctx: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{ctx}: expected a number, got {type(value).__name__} {value!r}")
    return value


def _timestamp(value: str, ctx: str) -> str:
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise InputError(f"{ctx}: expected an ISO-8601 timestamp, got {value!r}") from exc
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


def _parse_decision_actor(value, fields: tuple[str, ...], keys: set[str], ctx: str) -> dict:
    actor = _obj(value, ctx)
    _closed(actor, keys, ctx)
    _required_text_fields(actor, ("id", "actor_type", "recorded_at", "independence_attestation") + fields, ctx)
    _timestamp(actor["recorded_at"], f"{ctx}.recorded_at")
    return actor


def _validate_effect_value(outcome_type: str, value, ctx: str) -> dict:
    obj = _obj(value, ctx)
    if outcome_type in GROUP_KEYS_BY_TYPE:
        _closed(obj, {"groups"}, ctx)
        groups = _required_nonempty_list(obj, "groups", ctx)
        if len(groups) != 2:
            raise InputError(f"{ctx}.groups: exactly two arms (intervention, comparator) are required")
        keys = GROUP_KEYS_BY_TYPE[outcome_type]
        for i, group in enumerate(groups):
            gctx = f"{ctx}.groups[{i}]"
            gobj = _obj(group, gctx)
            _closed(gobj, keys, gctx)
            for key in sorted(keys):
                if key not in gobj:
                    raise InputError(f"{gctx}: missing required field {key!r}")
                _number(gobj[key], f"{gctx}.{key}")
            if outcome_type == "binary" and gobj["events"] > gobj["n"]:
                raise InputError(f"{gctx}: events cannot exceed n")
    elif outcome_type == "precomputed_effect":
        _closed(obj, PRECOMPUTED_KEYS, ctx)
        for key in PRECOMPUTED_REQUIRED:
            if key not in obj:
                raise InputError(f"{ctx}: missing required field {key!r}")
            _number(obj[key], f"{ctx}.{key}")
        for key in PRECOMPUTED_OPTIONAL:
            if key in obj:
                _number(obj[key], f"{ctx}.{key}")
        if obj["ci_lower"] > obj["ci_upper"]:
            raise InputError(f"{ctx}: ci_lower cannot exceed ci_upper")
    else:
        raise InputError(f"{ctx}: unsupported outcome_type {outcome_type!r}")
    return obj


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
        roles = _required_nonempty_list(member, "roles", ctx)
        for j, item in enumerate(roles):
            _text(item, f"{ctx}.roles[{j}]")
        expertise = _required_nonempty_list(member, "expertise", ctx)
        for j, item in enumerate(expertise):
            text = _text(item, f"{ctx}.expertise[{j}]")
            if text not in EXPERTISE_VOCAB:
                raise InputError(
                    f"{ctx}.expertise[{j}]: {text!r} is not in the declared expertise "
                    f"vocabulary ({', '.join(sorted(EXPERTISE_VOCAB))})"
                )

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
        manifest = _obj(search["acquisition_manifest"], "record.search.acquisition_manifest")
        _closed(manifest, ACQUISITION_MANIFEST_KEYS, "record.search.acquisition_manifest")
        _required_text_fields(
            manifest, ("reference", "digest", "captured_by"), "record.search.acquisition_manifest"
        )

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
            reviewer = _parse_decision_actor(row.get(who), ("decision",), DECISION_KEYS, f"{ctx}.{who}")
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
                "outcome_type",
            ),
            ctx,
        )
        outcome_type = row["outcome_type"]
        if outcome_type not in OUTCOME_TYPES:
            raise InputError(
                f"{ctx}.outcome_type: expected one of {sorted(OUTCOME_TYPES)!r}, got {outcome_type!r}"
            )
        if "reconciled_value" not in row:
            raise InputError(f"{ctx}: missing required field 'reconciled_value'")
        row["reconciled_value"] = _validate_effect_value(
            outcome_type, row["reconciled_value"], f"{ctx}.reconciled_value"
        )
        for who in ("extractor_a", "extractor_b"):
            extractor = _parse_decision_actor(row.get(who), (), EXTRACTOR_KEYS, f"{ctx}.{who}")
            if "value" not in extractor:
                raise InputError(f"{ctx}.{who}: missing required field 'value'")
            extractor["value"] = _validate_effect_value(
                outcome_type, extractor["value"], f"{ctx}.{who}.value"
            )
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
            _parse_decision_actor(row.get(who), ("judgment",), ASSESSOR_KEYS, f"{ctx}.{who}")
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
    linked_results = _required_nonempty_list(grade, "linked_results", "record.grade_linkage")
    for i, entry in enumerate(linked_results):
        ctx = f"record.grade_linkage.linked_results[{i}]"
        _obj(entry, ctx)
        _closed(entry, LINKED_RESULT_KEYS, ctx)
        _required_text_fields(entry, ("result_id", "grade_outcome", "certainty_domain"), ctx)
    return raw


def _human_pair(a: dict, b: dict, ctx: str, errors: list[str], team_ids: set[str]) -> None:
    if a["actor_type"] != "human" or b["actor_type"] != "human":
        errors.append(f"{ctx}: both independent reviewers must be recorded as human actors")
    if a["id"] == b["id"]:
        errors.append(f"{ctx}: reviewer A and reviewer B must be distinct people")
    for label, actor in (("A", a), ("B", b)):
        if actor["id"] not in team_ids:
            errors.append(
                f"{ctx}: reviewer {label} {actor['id']!r} is not a declared member of protocol.team"
            )
    attestation_a = (a.get("independence_attestation") or "").strip().casefold()
    attestation_b = (b.get("independence_attestation") or "").strip().casefold()
    if attestation_a and attestation_a == attestation_b:
        errors.append(
            f"{ctx}: independence attestations for reviewer A and reviewer B must not be "
            "identical boilerplate"
        )


def _normalize_source_name(name: str) -> str:
    base = name.strip().casefold()
    if "(" in base:
        base = base.split("(", 1)[0].strip()
    return base


def check(record: dict) -> list[str]:
    errors: list[str] = []
    protocol = record["protocol"]

    team_ids = {member["id"] for member in protocol["team"]}
    if len(team_ids) < 2:
        errors.append("protocol.team: at least two distinct human review-team members are required")
    expertise = {e for member in protocol["team"] for e in member["expertise"]}
    for req in sorted(REQUIRED_EXPERTISE - expertise):
        errors.append(f"protocol.team: required expertise {req!r} is not recorded on any team member")

    source_names = {_normalize_source_name(s["name"]) for s in record["search"]["sources"]}
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
    manifest = record["search"].get("acquisition_manifest")
    if record["search"]["imported_corpus"]:
        if not manifest:
            errors.append(
                "search.acquisition_manifest: imported/pre-collected corpora require a "
                "conforming acquisition manifest"
            )
        elif manifest["captured_by"] not in team_ids:
            errors.append(
                "search.acquisition_manifest.captured_by: must be a declared protocol.team member"
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
        _human_pair(row["reviewer_a"], row["reviewer_b"], f"screening {rid}", errors, team_ids)
        a, b = row["reviewer_a"]["decision"], row["reviewer_b"]["decision"]
        note = (row.get("reconciliation_note") or "").strip()
        if a != b and not note:
            errors.append(f"screening {rid}: disagreement requires a reconciliation note")
        elif a == b and row["reconciled_decision"] != a and not note:
            errors.append(
                f"screening {rid}: reconciled decision overturns unanimous reviewers without "
                "a reconciliation note"
            )
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
        _human_pair(row["extractor_a"], row["extractor_b"], f"extraction {key!r}", errors, team_ids)
        value_a, value_b = row["extractor_a"]["value"], row["extractor_b"]["value"]
        note = (row.get("reconciliation_note") or "").strip()
        if value_a != value_b and not note:
            errors.append(f"extraction {key!r}: differing independent values require reconciliation")
        elif value_a == value_b and row["reconciled_value"] != value_a and not note:
            errors.append(
                f"extraction {key!r}: reconciled value overturns unanimous extractors without "
                "a reconciliation note"
            )

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
        _human_pair(row["assessor_a"], row["assessor_b"], f"risk_of_bias {key!r}", errors, team_ids)
        judgment_a, judgment_b = row["assessor_a"]["judgment"], row["assessor_b"]["judgment"]
        note = (row.get("reconciliation_note") or "").strip()
        if judgment_a != judgment_b and not note:
            errors.append(f"risk_of_bias {key!r}: differing judgments require reconciliation")
        elif judgment_a == judgment_b and row["reconciled_judgment"] != judgment_a and not note:
            errors.append(
                f"risk_of_bias {key!r}: reconciled judgment overturns unanimous assessors without "
                "a reconciliation note"
            )
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

    linked_result_ids = [entry["result_id"] for entry in record["grade_linkage"]["linked_results"]]
    if len(set(linked_result_ids)) != len(linked_result_ids):
        errors.append("grade_linkage.linked_results: duplicate result_id linkage")
    linked_set = set(linked_result_ids)
    for rid in sorted(mrb_by_result - linked_set):
        errors.append(
            f"grade_linkage: missing-results-bias result {rid!r} is not linked to a named "
            "GRADE outcome/certainty target"
        )
    for rid in sorted(linked_set - mrb_by_result):
        errors.append(
            f"grade_linkage: linked result {rid!r} has no corresponding missing_results_bias record"
        )
    return errors


def _independence_attestation_count(record: dict) -> int:
    return len(record["screening"]) + len(record["extractions"]) + len(record["risk_of_bias"])


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
        gated = _independence_attestation_count(record)
        lines += [
            "✅ All machine-checkable MECIR-oriented profile invariants are satisfied.",
            "",
            f"`{gated}` duplicate-decision pairs (screening/extraction/RoB) carry a "
            "self-declared independence attestation and a decision-maker id bound to "
            "`protocol.team`. **This attestation is self-declared and not independently "
            "authenticated by this checker** — it is a machine-checkable audit record, not "
            "proof that two humans acted independently.",
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
                "detail": {
                    "profile": PROFILE,
                    "independence_gated_decision_pairs": _independence_attestation_count(record),
                },
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
