#!/usr/bin/env python3
"""Validate a current-GRADE-Book certainty profile. Standard library only.

This is the versioned/current companion to ``grade_profile.py``. The legacy
checker remains available for existing 1.0 records and its RoB traceability
contract; this checker adds the decision-threshold, target-of-certainty,
absolute-effect, -3 downgrade, dissemination-bias, domain-overlap, and fuller
Summary-of-Findings semantics requested by RFC #23.

WHAT THIS CHECKS
  Closed-schema/current-guidance provenance; one certainty rating per result;
  explicit target and decision thresholds; effect data required by outcome type;
  all five current domains; whole-step downgrades including explicitly justified
  -3; legal upgrades; conservative explicit domain-overlap accounting; certainty
  arithmetic; and result-level Summary-of-Findings fields.

WHAT THIS CANNOT CHECK
  Whether thresholds are clinically/policy appropriate, whether effect estimates
  are correct, whether a domain judgment is substantively right, or whether an
  expert should have rated down/up. A clean record is structurally complete and
  internally consistent under its declared GRADE guidance snapshot; it is not an
  expert-certification of the judgment.

EXIT CODES
  0 clean, or violations found without --strict
  1 GRADE method/profile violations under --strict
  2 malformed input — no authoritative artifact is emitted
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys

SCHEMA_VERSIONS = {"2.0"}
JSON_ENVELOPE_VERSION = "1.0"
LEVELS = {"very_low": 1, "low": 2, "moderate": 3, "high": 4}
LEVEL_NAMES = {v: k for k, v in LEVELS.items()}
SYMBOLS = {4: "⊕⊕⊕⊕", 3: "⊕⊕⊕◯", 2: "⊕⊕◯◯", 1: "⊕◯◯◯"}
DESIGN_START = {"rct": "high", "nrsi": "low", "observational": "low", "case_series": "very_low"}
UPGRADE_MAX = {"large_effect": 2, "dose_response": 1, "opposing_confounding": 1}
CANONICAL_DOMAINS = (
    "risk_of_bias", "inconsistency", "indirectness", "imprecision", "dissemination_bias"
)
LEGACY_BIAS_ALIAS = "publication_bias"

ROOT_KEYS = {"schema_version", "review_type", "synthesis_mode", "grade_guidance", "results"}
GUIDANCE_KEYS = {"source", "profile", "as_of"}
RESULT_KEYS = {
    "id", "label", "outcome", "time_point", "study_ids", "design_mix", "starting_level",
    "starting_level_justification", "effect", "decision_thresholds", "target_of_certainty",
    "domains", "domain_overlap", "upgrades", "final", "certainty_statement", "footnotes",
}
EFFECT_KEYS = {
    "type", "measure", "relative_estimate", "relative_interval", "baseline_risk",
    "absolute_effect", "absolute_interval", "continuous_estimate", "continuous_interval",
    "participants", "studies",
}
INTERVAL_KEYS = {"lower", "upper"}
THRESHOLD_KEYS = {"label", "value", "unit", "direction", "rationale"}
DOMAIN_KEYS = {"rating", "note", "justification", "basis"}
OVERLAP_KEYS = {"domains", "shared_cause", "accounted_in"}

REVIEW_TYPES = {"systematic", "umbrella", "rapid"}
SYNTHESIS_MODES = {"outcome"}
EFFECT_TYPES = {"dichotomous", "continuous", "narrative"}
THRESHOLD_DIRECTIONS = {"above", "below", "within", "outside"}
ROB_BASES = {"confirmed_rob", "heuristic"}


class InputError(ValueError):
    """Malformed input (exit 2)."""


def _obj(value, ctx):
    if not isinstance(value, dict):
        raise InputError(f"{ctx}: expected an object, got {type(value).__name__}")
    return value


def _list(value, ctx):
    if not isinstance(value, list):
        raise InputError(f"{ctx}: expected a list, got {type(value).__name__}")
    return value


def _text(value, ctx, *, empty=False):
    if not isinstance(value, str):
        raise InputError(f"{ctx}: expected a string, got {type(value).__name__} {value!r}")
    out = value.strip()
    if not empty and not out:
        raise InputError(f"{ctx}: expected non-empty text")
    return out


def _number(value, ctx):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{ctx}: expected a finite JSON number, got {value!r}")
    if not math.isfinite(value):
        raise InputError(f"{ctx}: expected a finite JSON number, got {value!r}")
    return value


def _count(value, ctx):
    value = _number(value, ctx)
    if int(value) != value or value < 0:
        raise InputError(f"{ctx}: expected a whole non-negative count, got {value!r}")
    return int(value)


def _closed(value, allowed, ctx):
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise InputError(
            f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
            f"(expected one of: {', '.join(sorted(allowed))})"
        )


def _interval(value, ctx):
    value = _obj(value, ctx)
    _closed(value, INTERVAL_KEYS, ctx)
    if set(value) != INTERVAL_KEYS:
        raise InputError(f"{ctx}: both 'lower' and 'upper' are required")
    lower = _number(value["lower"], f"{ctx}.lower")
    upper = _number(value["upper"], f"{ctx}.upper")
    if lower > upper:
        raise InputError(f"{ctx}: lower bound exceeds upper bound")
    return {"lower": lower, "upper": upper}


def _rating(value, ctx):
    if isinstance(value, bool) or not isinstance(value, int) or value not in (0, -1, -2, -3):
        raise InputError(f"{ctx}: rating must be one of the integers 0, -1, -2, -3, got {value!r}")
    return value


def _predominant(design_mix: dict) -> str:
    nonzero = [(count, LEVELS[DESIGN_START[design]], design) for design, count in design_mix.items() if count]
    if not nonzero:
        raise InputError("design_mix: at least one study must contribute")
    max_count = max(row[0] for row in nonzero)
    tied = [row for row in nonzero if row[0] == max_count]
    # On a tie choose the weaker starting level; then lexical for determinism.
    return sorted(tied, key=lambda row: (row[1], row[2]))[0][2]


def parse(raw: dict) -> tuple[dict, list[str]]:
    _obj(raw, "record")
    _closed(raw, ROOT_KEYS, "record")
    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(
            f"record: unrecognised or missing schema_version {version!r} "
            f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})"
        )
    if raw.get("review_type") not in REVIEW_TYPES:
        raise InputError(f"record.review_type: expected one of {sorted(REVIEW_TYPES)!r}")
    if raw.get("synthesis_mode") not in SYNTHESIS_MODES:
        raise InputError("record.synthesis_mode: current/full GRADE requires 'outcome'")

    guidance = _obj(raw.get("grade_guidance"), "record.grade_guidance")
    _closed(guidance, GUIDANCE_KEYS, "record.grade_guidance")
    for field in GUIDANCE_KEYS:
        if field not in guidance:
            raise InputError(f"record.grade_guidance: missing required field {field!r}")
        _text(guidance[field], f"record.grade_guidance.{field}")
    if guidance["source"].strip().casefold() not in {"grade book", "gradebook"}:
        raise InputError("record.grade_guidance.source: current profile requires 'GRADE Book'")

    rows = _list(raw.get("results"), "record.results")
    if not rows:
        raise InputError("record.results: must not be empty")

    record = copy.deepcopy(raw)
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for i, result in enumerate(record["results"]):
        ctx = f"record.results[{i}]"
        _obj(result, ctx)
        _closed(result, RESULT_KEYS, ctx)
        for field in ("id", "label", "outcome", "time_point", "starting_level", "target_of_certainty", "final", "certainty_statement"):
            if field not in result:
                raise InputError(f"{ctx}: missing required field {field!r}")
            _text(result[field], f"{ctx}.{field}")
        if result["id"] in seen_ids:
            raise InputError(f"{ctx}.id: duplicate result id {result['id']!r}")
        seen_ids.add(result["id"])
        if result["starting_level"] not in LEVELS or result["final"] not in LEVELS:
            raise InputError(f"{ctx}: starting_level/final must be one of {sorted(LEVELS)!r}")
        if "starting_level_justification" in result:
            _text(result["starting_level_justification"], f"{ctx}.starting_level_justification", empty=True)

        study_ids = _list(result.get("study_ids"), f"{ctx}.study_ids")
        if not study_ids:
            raise InputError(f"{ctx}.study_ids: must not be empty")
        if len(study_ids) != len(set(study_ids)):
            raise InputError(f"{ctx}.study_ids: duplicates are not permitted")
        for j, sid in enumerate(study_ids):
            _text(sid, f"{ctx}.study_ids[{j}]")

        design_mix = _obj(result.get("design_mix"), f"{ctx}.design_mix")
        _closed(design_mix, set(DESIGN_START), f"{ctx}.design_mix")
        if not design_mix:
            raise InputError(f"{ctx}.design_mix: must not be empty")
        for design, count in design_mix.items():
            design_mix[design] = _count(count, f"{ctx}.design_mix.{design}")
        if sum(design_mix.values()) != len(study_ids):
            raise InputError(
                f"{ctx}.design_mix: counts sum to {sum(design_mix.values())}, but study_ids has {len(study_ids)} entries"
            )

        effect = _obj(result.get("effect"), f"{ctx}.effect")
        _closed(effect, EFFECT_KEYS, f"{ctx}.effect")
        for field in ("type", "measure", "participants", "studies"):
            if field not in effect:
                raise InputError(f"{ctx}.effect: missing required field {field!r}")
        _text(effect["type"], f"{ctx}.effect.type")
        _text(effect["measure"], f"{ctx}.effect.measure")
        if effect["type"] not in EFFECT_TYPES:
            raise InputError(f"{ctx}.effect.type: expected one of {sorted(EFFECT_TYPES)!r}")
        effect["participants"] = _count(effect["participants"], f"{ctx}.effect.participants")
        effect["studies"] = _count(effect["studies"], f"{ctx}.effect.studies")
        for interval_field in ("relative_interval", "absolute_interval", "continuous_interval"):
            if interval_field in effect:
                effect[interval_field] = _interval(effect[interval_field], f"{ctx}.effect.{interval_field}")
        for numeric in ("relative_estimate", "baseline_risk", "absolute_effect", "continuous_estimate"):
            if numeric in effect:
                effect[numeric] = _number(effect[numeric], f"{ctx}.effect.{numeric}")

        thresholds = _list(result.get("decision_thresholds"), f"{ctx}.decision_thresholds")
        if not thresholds:
            raise InputError(f"{ctx}.decision_thresholds: current/full GRADE requires at least one threshold")
        for j, threshold in enumerate(thresholds):
            tctx = f"{ctx}.decision_thresholds[{j}]"
            _obj(threshold, tctx)
            _closed(threshold, THRESHOLD_KEYS, tctx)
            for field in ("label", "unit", "direction", "rationale"):
                if field not in threshold:
                    raise InputError(f"{tctx}: missing required field {field!r}")
                _text(threshold[field], f"{tctx}.{field}")
            if "value" not in threshold:
                raise InputError(f"{tctx}: missing required field 'value'")
            threshold["value"] = _number(threshold["value"], f"{tctx}.value")
            if threshold["direction"] not in THRESHOLD_DIRECTIONS:
                raise InputError(f"{tctx}.direction: expected one of {sorted(THRESHOLD_DIRECTIONS)!r}")

        domains = _obj(result.get("domains"), f"{ctx}.domains")
        has_current = "dissemination_bias" in domains
        has_legacy = LEGACY_BIAS_ALIAS in domains
        if has_current and has_legacy:
            raise InputError(f"{ctx}.domains: use dissemination_bias or publication_bias, not both")
        if has_legacy:
            domains["dissemination_bias"] = domains.pop(LEGACY_BIAS_ALIAS)
            warnings.append(
                f"result {result['id']}: legacy domain 'publication_bias' migrated to canonical 'dissemination_bias'"
            )
        _closed(domains, set(CANONICAL_DOMAINS), f"{ctx}.domains")
        missing = [name for name in CANONICAL_DOMAINS if name not in domains]
        if missing:
            raise InputError(f"{ctx}.domains: missing required domain(s) {', '.join(missing)}")
        for name in CANONICAL_DOMAINS:
            dctx = f"{ctx}.domains.{name}"
            domain = _obj(domains[name], dctx)
            _closed(domain, DOMAIN_KEYS, dctx)
            if "rating" not in domain or "note" not in domain:
                raise InputError(f"{dctx}: 'rating' and 'note' are required")
            domain["rating"] = _rating(domain["rating"], f"{dctx}.rating")
            _text(domain["note"], f"{dctx}.note")
            if "justification" in domain:
                _text(domain["justification"], f"{dctx}.justification", empty=True)
            if "basis" in domain:
                _text(domain["basis"], f"{dctx}.basis")
                if domain["basis"] not in ROB_BASES:
                    raise InputError(f"{dctx}.basis: expected one of {sorted(ROB_BASES)!r}")

        overlaps = _list(result.get("domain_overlap", []), f"{ctx}.domain_overlap")
        for j, overlap in enumerate(overlaps):
            octx = f"{ctx}.domain_overlap[{j}]"
            _obj(overlap, octx)
            _closed(overlap, OVERLAP_KEYS, octx)
            for field in OVERLAP_KEYS:
                if field not in overlap:
                    raise InputError(f"{octx}: missing required field {field!r}")
            names = _list(overlap["domains"], f"{octx}.domains")
            if len(names) < 2 or len(names) != len(set(names)):
                raise InputError(f"{octx}.domains: at least two distinct domains are required")
            for name in names:
                if name == LEGACY_BIAS_ALIAS:
                    name = "dissemination_bias"
                if name not in CANONICAL_DOMAINS:
                    raise InputError(f"{octx}.domains: unknown domain {name!r}")
            _text(overlap["shared_cause"], f"{octx}.shared_cause")
            _text(overlap["accounted_in"], f"{octx}.accounted_in")
            if overlap["accounted_in"] not in names:
                raise InputError(f"{octx}.accounted_in: must name one of the overlap domains")

        upgrades = _obj(result.get("upgrades", {}), f"{ctx}.upgrades")
        _closed(upgrades, set(UPGRADE_MAX), f"{ctx}.upgrades")
        for name, maximum in UPGRADE_MAX.items():
            if name in upgrades:
                value = upgrades[name]
                if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > maximum:
                    raise InputError(f"{ctx}.upgrades.{name}: expected integer 0..{maximum}")

        footnotes = _list(result.get("footnotes", []), f"{ctx}.footnotes")
        for j, note in enumerate(footnotes):
            _text(note, f"{ctx}.footnotes[{j}]")
    return record, warnings


def check(record: dict) -> list[str]:
    errors: list[str] = []
    for result in record["results"]:
        rid = result["id"]
        effect = result["effect"]
        domains = result["domains"]

        if effect["studies"] != len(result["study_ids"]):
            errors.append(
                f"result {rid}: effect.studies={effect['studies']} does not match {len(result['study_ids'])} study_ids"
            )
        if effect["type"] == "dichotomous":
            required = (
                "relative_estimate", "relative_interval", "baseline_risk",
                "absolute_effect", "absolute_interval",
            )
            missing = [field for field in required if field not in effect]
            if missing:
                errors.append(
                    f"result {rid}: dichotomous outcome missing decision-relevant effect field(s): {', '.join(missing)}"
                )
        elif effect["type"] == "continuous":
            missing = [field for field in ("continuous_estimate", "continuous_interval") if field not in effect]
            if missing:
                errors.append(f"result {rid}: continuous outcome missing {', '.join(missing)}")
        elif effect["type"] == "narrative":
            if effect["participants"] == 0 or effect["studies"] == 0:
                errors.append(f"result {rid}: narrative outcome must still identify contributing studies/participants")

        predominant = _predominant(result["design_mix"])
        expected = DESIGN_START[predominant]
        if result["starting_level"] != expected and not (
            result.get("starting_level_justification") or ""
        ).strip():
            errors.append(
                f"result {rid}: starting_level {result['starting_level']!r} does not match predominant design {predominant!r} ({expected}) and has no justification"
            )

        for name, domain in domains.items():
            if domain["rating"] == -3 and not (domain.get("justification") or "").strip():
                errors.append(f"result {rid}: {name} rating -3 requires an explicit extremely-serious justification")
        rob = domains["risk_of_bias"]
        if record["review_type"] in {"systematic", "umbrella"} and rob.get("basis") != "confirmed_rob":
            errors.append(
                f"result {rid}: strict {record['review_type']} current-GRADE profile requires risk_of_bias basis confirmed_rob"
            )

        overlap_domains: set[tuple[str, str]] = set()
        for overlap in result.get("domain_overlap", []):
            names = ["dissemination_bias" if n == LEGACY_BIAS_ALIAS else n for n in overlap["domains"]]
            accounted = "dissemination_bias" if overlap["accounted_in"] == LEGACY_BIAS_ALIAS else overlap["accounted_in"]
            for i, left in enumerate(names):
                for right in names[i + 1:]:
                    pair = tuple(sorted((left, right)))
                    if pair in overlap_domains:
                        errors.append(f"result {rid}: domain-overlap pair {pair!r} is declared more than once")
                    overlap_domains.add(pair)
            nonzero = [name for name in names if domains[name]["rating"] < 0]
            if len(nonzero) > 1:
                errors.append(
                    f"result {rid}: overlap {names!r} declares shared cause accounted in {accounted!r}, but multiple overlapping domains are downgraded ({', '.join(nonzero)}); this double-counts the declared concern"
                )
            if accounted not in names:
                errors.append(f"result {rid}: overlap accounted_in {accounted!r} is outside its domain set")

        upgrades = result.get("upgrades", {})
        upgrade_total = sum(upgrades.values())
        if upgrade_total:
            if DESIGN_START[predominant] == "high" or result["starting_level"] == "high":
                errors.append(f"result {rid}: upgrades are not permitted for a body starting at high certainty")
            if any(domain["rating"] < 0 for domain in domains.values()):
                errors.append(f"result {rid}: upgrades may not be applied while unresolved downgrade concerns remain")

        raw = LEVELS[result["starting_level"]] + sum(d["rating"] for d in domains.values()) + upgrade_total
        calculated = max(1, min(4, raw))
        if LEVELS[result["final"]] != calculated:
            errors.append(
                f"result {rid}: certainty arithmetic yields {LEVEL_NAMES[calculated]} ({calculated}) but final is {result['final']} ({LEVELS[result['final']]})"
            )
    return errors


def _cell(value):
    return str(value).replace("|", "&#124;").replace("\n", "<br>")


def render(record: dict, errors: list[str], warnings: list[str], source: str) -> str:
    guidance = record["grade_guidance"]
    lines = [
        "# GRADE evidence profile — current GRADE Book mode",
        "",
        f"**Guidance:** {guidance['source']} / {guidance['profile']} / as of {guidance['as_of']}  ",
        "**Synthesis mode:** outcome-level GRADE",
        "",
    ]
    if warnings:
        lines += ["## Migration notes", ""] + [f"- {w}" for w in warnings] + [""]
    if errors:
        lines += [f"## ⚠️ {len(errors)} violation(s)", ""] + [f"- {e}" for e in errors] + [""]
    else:
        lines += ["✅ Current-GRADE structural and arithmetic checks passed.", ""]

    lines += [
        "## Summary of Findings",
        "",
        "| ID | Outcome / time point | Effect | Participants (studies) | Decision target / threshold | Certainty | Explanation |",
        "|:--|:--|:--|--:|:--|:--|:--|",
    ]
    for result in record["results"]:
        effect = result["effect"]
        if effect["type"] == "dichotomous":
            effect_text = (
                f"{effect['measure']}={effect.get('relative_estimate', '—')} "
                f"(CI {effect.get('relative_interval', {}).get('lower', '—')}–{effect.get('relative_interval', {}).get('upper', '—')}); "
                f"baseline={effect.get('baseline_risk', '—')}; absolute={effect.get('absolute_effect', '—')} "
                f"(CI {effect.get('absolute_interval', {}).get('lower', '—')}–{effect.get('absolute_interval', {}).get('upper', '—')})"
            )
        elif effect["type"] == "continuous":
            effect_text = (
                f"{effect['measure']}={effect.get('continuous_estimate', '—')} "
                f"(CI {effect.get('continuous_interval', {}).get('lower', '—')}–{effect.get('continuous_interval', {}).get('upper', '—')})"
            )
        else:
            effect_text = f"{effect['measure']} — narrative/no pooled estimate"
        thresholds = "; ".join(
            f"{t['label']} {t['direction']} {t['value']} {t['unit']}" for t in result["decision_thresholds"]
        )
        certainty = f"{result['final'].upper()} {SYMBOLS[LEVELS[result['final']]]}"
        lines.append(
            f"| {_cell(result['id'])} | {_cell(result['outcome'])} / {_cell(result['time_point'])} | "
            f"{_cell(effect_text)} | {effect['participants']} ({effect['studies']}) | "
            f"{_cell(result['target_of_certainty'])}; {_cell(thresholds)} | {certainty} | "
            f"{_cell(result['certainty_statement'])} |"
        )
        for footnote in result.get("footnotes", []):
            lines.append(f"\n- **{_cell(result['id'])}:** {_cell(footnote)}")

    lines += [
        "",
        "## Certainty statements keyed to targets",
        "",
    ]
    for result in record["results"]:
        lines.append(
            f"- **{_cell(result['id'])}:** {result['final'].replace('_', ' ').title()} certainty "
            f"for the declared target — {_cell(result['target_of_certainty'])}. "
            f"Reviewer statement: {_cell(result['certainty_statement'])}"
        )

    lines += [
        "",
        "---",
        f"*Generated by `grade_profile_current.py` from `{source}`. This current-mode check validates "
        "the declared GRADE structure, decision context, domain accounting, and arithmetic. It cannot "
        "decide whether the expert thresholds or domain judgments are substantively correct.*",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a current GRADE Book certainty profile.")
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
        sys.stderr.write(f"grade_profile_current: cannot read {source} ({exc})\n")
        return 2
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"grade_profile_current: input is not valid JSON ({exc})\n")
        return 2
    try:
        record, warnings = parse(raw)
    except InputError as exc:
        sys.stderr.write(f"grade_profile_current: {exc}\n")
        return 2

    errors = check(record)
    if args.json:
        json.dump(
            {
                "check": "grade_profile_current",
                "schema_version": JSON_ENVELOPE_VERSION,
                "issues": len(errors),
                "units": {"U_grade_current": len({e.split(':', 1)[0] for e in errors})},
                "gates": {},
                "unattributed": 0,
                "detail": {"guidance_as_of": record["grade_guidance"]["as_of"], "migration_warnings": len(warnings)},
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1 if errors and args.strict else 0
    print(render(record, errors, warnings, source))
    return 1 if errors and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
