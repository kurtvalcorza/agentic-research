#!/usr/bin/env python3
"""Current-GRADE entry point with preserved RoB traceability and target semantics.

The schema-2.0 parser/renderer lives in ``grade_profile_current_core.py``. This
entry point adds the cross-artifact invariants that must remain shared with the
legacy GRADE path: a ``confirmed_rob`` claim has to resolve against the upstream
human-gated appraisal record, and a declared target/threshold relation is checked
when the effect interval makes the relation objectively decidable.

WHAT THIS CHECKS
  Everything in the current-GRADE core, plus result-level appraisal resolution
  for strict systematic/umbrella reviews, appraisal-design reconciliation, and a
  conservative interval-versus-threshold contradiction check.

WHAT THIS CANNOT CHECK
  Whether a threshold is clinically/policy appropriate, whether a target or GRADE
  domain judgment is substantively correct, whether a recorded human confirmation
  is authentic, or what a free-text statement semantically means. The target check
  uses only the structured target_threshold record and flags only an interval that
  lies wholly on the opposite side of a one-sided threshold.

EXIT CODES
  0 clean, or violations found without --strict
  1 GRADE method/profile violations under --strict
  2 malformed input — no authoritative artifact is emitted
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_sibling(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, _HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load GRADE implementation {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_core = _load_sibling("grade_profile_current_core.py", "_grade_profile_current_core")
_legacy = _load_sibling("grade_profile.py", "_grade_profile_legacy_for_current")

# Preserve the public/module API of the original current checker. Single-underscore
# helpers are deliberately re-exported too because the repository's tests exercise
# coercion contracts directly.
for _name in dir(_core):
    if not _name.startswith("__") and _name not in {"parse", "check", "main"}:
        globals()[_name] = getattr(_core, _name)

InputError = _core.InputError

TARGET_THRESHOLD_KEYS = {"threshold_label", "effect_basis", "claim"}
TARGET_EFFECT_BASES = {"absolute", "relative", "continuous", "narrative"}
TARGET_CLAIMS = {"meets", "does_not_meet"}
INTERVAL_BY_BASIS = {
    "absolute": "absolute_interval",
    "relative": "relative_interval",
    "continuous": "continuous_interval",
}
STRICT_ROB_TYPES = {"systematic", "umbrella"}


def _target_record(value, result: dict, ctx: str) -> dict:
    value = _core._obj(value, ctx)
    _core._closed(value, TARGET_THRESHOLD_KEYS, ctx)
    missing = sorted(TARGET_THRESHOLD_KEYS - set(value))
    if missing:
        raise InputError(f"{ctx}: missing required field(s) {', '.join(missing)}")
    target = {
        "threshold_label": _core._text(value["threshold_label"], f"{ctx}.threshold_label"),
        "effect_basis": _core._text(value["effect_basis"], f"{ctx}.effect_basis"),
        "claim": _core._text(value["claim"], f"{ctx}.claim"),
    }
    if target["effect_basis"] not in TARGET_EFFECT_BASES:
        raise InputError(
            f"{ctx}.effect_basis: expected one of {sorted(TARGET_EFFECT_BASES)!r}"
        )
    if target["claim"] not in TARGET_CLAIMS:
        raise InputError(f"{ctx}.claim: expected one of {sorted(TARGET_CLAIMS)!r}")
    labels = [threshold["label"] for threshold in result["decision_thresholds"]]
    if len(labels) != len(set(labels)):
        raise InputError(f"{ctx}: decision-threshold labels must be unique for target resolution")
    if target["threshold_label"] not in labels:
        raise InputError(
            f"{ctx}.threshold_label: {target['threshold_label']!r} does not name a declared decision threshold"
        )
    return target


def parse(raw: dict) -> tuple[dict, list[str]]:
    """Parse schema 2.0 while keeping extension fields outside the frozen core."""
    cleaned = copy.deepcopy(raw)
    extensions: list[dict] = []
    raw_results = cleaned.get("results") if isinstance(cleaned, dict) else None
    if isinstance(raw_results, list):
        for result in raw_results:
            ext = {}
            if isinstance(result, dict):
                if "appraised_result" in result:
                    ext["appraised_result"] = result.pop("appraised_result")
                if "target_threshold" in result:
                    ext["target_threshold"] = result.pop("target_threshold")
            extensions.append(ext)

    record, warnings = _core.parse(cleaned)
    for i, result in enumerate(record["results"]):
        ctx = f"record.results[{i}]"
        ext = extensions[i] if i < len(extensions) else {}
        rob = result["domains"]["risk_of_bias"]
        appraised = ext.get("appraised_result")
        if appraised is not None:
            appraised = _core._text(appraised, f"{ctx}.appraised_result")
            result["appraised_result"] = appraised
        if record["review_type"] in STRICT_ROB_TYPES and rob.get("basis") == "confirmed_rob":
            if not appraised:
                raise InputError(
                    f"{ctx}.appraised_result: strict confirmed_rob current GRADE requires "
                    "the exact upstream result_assessed target"
                )

        if "target_threshold" not in ext:
            raise InputError(
                f"{ctx}.target_threshold: current/full GRADE requires a structured "
                "threshold target in addition to target_of_certainty prose"
            )
        result["target_threshold"] = _target_record(
            ext["target_threshold"], result, f"{ctx}.target_threshold"
        )
    return record, warnings


def parse_appraisal(raw: dict) -> dict:
    """Reuse the legacy checker's appraisal parser as the single schema authority."""
    try:
        return _legacy.parse_appraisal(raw)
    except _legacy.InputError as exc:
        raise InputError(str(exc)) from exc


def _threshold_position(result: dict) -> str | None:
    """Return meets/does_not_meet/crosses when a one-sided interval is decidable."""
    target = result["target_threshold"]
    basis = target["effect_basis"]
    if basis == "narrative":
        return None
    interval_field = INTERVAL_BY_BASIS[basis]
    interval = result["effect"].get(interval_field)
    if not isinstance(interval, dict):
        return None
    threshold = next(
        row for row in result["decision_thresholds"]
        if row["label"] == target["threshold_label"]
    )
    value = threshold["value"]
    lower, upper = interval["lower"], interval["upper"]
    if threshold["direction"] == "below":
        if upper < value:
            return "meets"
        if lower >= value:
            return "does_not_meet"
        return "crosses"
    if threshold["direction"] == "above":
        if lower > value:
            return "meets"
        if upper <= value:
            return "does_not_meet"
        return "crosses"
    # A single scalar threshold is insufficient to decide 'within'/'outside'.
    return None


def _trace_rob(record: dict, appraisal: dict | None) -> list[str]:
    errors: list[str] = []
    for result in record["results"]:
        rid = result["id"]
        rob = result["domains"]["risk_of_bias"]
        if record["review_type"] not in STRICT_ROB_TYPES or rob.get("basis") != "confirmed_rob":
            continue
        if appraisal is None:
            errors.append(
                f"result {rid}: confirmed_rob basis requires --rob appraisal evidence; "
                "the basis string is not itself traceability"
            )
            continue

        target = result["appraised_result"]
        observed_designs: list[str] = []
        all_resolved = True
        for sid in result["study_ids"]:
            key = (sid, target)
            appraised = appraisal.get(key)
            if appraised is None:
                all_resolved = False
                errors.append(
                    f"result {rid}: study {sid!r} does not resolve to an appraisal for "
                    f"result_assessed {target!r}"
                )
                continue
            observed_designs.append(appraised["design"])
            if appraised.get("instrument_mismatch"):
                errors.append(
                    f"result {rid}: study {sid!r} uses instrument {appraised['instrument']!r} "
                    f"but design {appraised['design']!r} requires {appraised['expected_instrument']!r}"
                )
            for violation in appraised.get("violations", []):
                errors.append(f"result {rid}: study {sid!r} appraisal violation: {violation}")
            if not appraised.get("confirmed"):
                errors.append(
                    f"result {rid}: study {sid!r} appraisal for {target!r} is not human-confirmed"
                )

        if all_resolved:
            observed = dict(Counter(observed_designs))
            declared = {name: count for name, count in result["design_mix"].items() if count}
            if observed != declared:
                errors.append(
                    f"result {rid}: design_mix {declared!r} does not match resolved appraisal "
                    f"designs {observed!r}"
                )
    return errors


def _check_targets(record: dict) -> list[str]:
    errors: list[str] = []
    for result in record["results"]:
        rid = result["id"]
        target = result["target_threshold"]
        basis = target["effect_basis"]
        if basis != "narrative" and INTERVAL_BY_BASIS[basis] not in result["effect"]:
            errors.append(
                f"result {rid}: target_threshold effect_basis {basis!r} requires "
                f"effect.{INTERVAL_BY_BASIS[basis]}"
            )
            continue
        position = _threshold_position(result)
        if position is not None and position != "crosses" and position != target["claim"]:
            threshold = next(
                row for row in result["decision_thresholds"]
                if row["label"] == target["threshold_label"]
            )
            interval = result["effect"][INTERVAL_BY_BASIS[basis]]
            errors.append(
                f"result {rid}: declared target claims the {basis} effect {target['claim'].replace('_', ' ')} "
                f"threshold {threshold['label']!r}, but interval [{interval['lower']}, {interval['upper']}] "
                f"lies wholly on the opposite side of {threshold['direction']} {threshold['value']}"
            )
    return errors


def check(record: dict, appraisal: dict | None = None) -> list[str]:
    errors = list(_core.check(record))
    errors.extend(_trace_rob(record, appraisal))
    errors.extend(_check_targets(record))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a current GRADE Book certainty profile.")
    parser.add_argument("infile", nargs="?")
    parser.add_argument("--rob", help="risk-of-bias appraisal JSON used to resolve confirmed_rob claims")
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

    appraisal = None
    if args.rob:
        try:
            rob_text = open(args.rob, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError) as exc:
            sys.stderr.write(f"grade_profile_current: cannot read appraisal {args.rob} ({exc})\n")
            return 2
        try:
            rob_raw = json.loads(rob_text)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"grade_profile_current: appraisal is not valid JSON ({exc})\n")
            return 2
        try:
            appraisal = parse_appraisal(rob_raw)
        except InputError as exc:
            sys.stderr.write(f"grade_profile_current: appraisal error: {exc}\n")
            return 2

    errors = check(record, appraisal)
    if args.json:
        json.dump(
            {
                "check": "grade_profile_current",
                "schema_version": JSON_ENVELOPE_VERSION,
                "issues": len(errors),
                "units": {"U_grade_current": len({e.split(':', 1)[0] for e in errors})},
                "gates": {},
                "unattributed": 0,
                "detail": {
                    "guidance_as_of": record["grade_guidance"]["as_of"],
                    "migration_warnings": len(warnings),
                    "rob_supplied": bool(args.rob),
                },
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
