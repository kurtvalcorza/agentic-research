#!/usr/bin/env python3
"""Check OpenResearch enrichment disclosure in an acquire-corpus acquisition record.

Standard library only.

WHAT THIS CHECKS
  The canonical acquisition record is closed-schema and structurally well formed;
  successful OpenResearch discovery calls carry an OpenResearch version and are
  represented in the reproducibility disclosure; and the disclosure does not claim
  OpenResearch is unnecessary when a successful enriched search was part of the run.

WHAT THIS CANNOT CHECK
  Whether provenance values are truthful, whether the OpenResearch version string is
  authentic, whether source attribution is correct, whether candidate/raw artifact
  counts match files on disk, whether bibliographic completion is correct, or whether
  the search achieved adequate recall. This is a disclosure gate, not a PRISMA-S
  compliance validator.

EXIT CODES
  0 clean, or issues found without --strict
  1 method violation under --strict
  2 malformed input — no authoritative artifact/envelope is emitted
"""
from __future__ import annotations

import argparse
import json
import math
import sys

SCHEMA_VERSIONS = {"1.0"}
JSON_ENVELOPE_VERSION = "1.0"
CHECK_NAME = "acquisition_disclosure"

RECORD_KEYS = {
    "schema_version", "run_date", "enrichment_mode", "orx_available", "queries",
    "reproducibility_disclosure", "unresolved",
}
QUERY_KEYS = {
    "backend", "sub_source", "strategy", "query", "date", "outcome",
    "returned_count", "normalization_drops", "admitted_enriched_count",
    "unresolved_enrichment_count", "unresolved_reasons", "circuit_open",
    "orx_version", "failure_reason",
}
REASON_KEYS = {"reason", "count"}
DISCLOSURE_KEYS = {"requires_openresearch", "successful_enrichment"}
DISCLOSURE_ITEM_KEYS = {"query", "strategy", "sub_source", "orx_version"}
UNRESOLVED_KEYS = {"count", "path"}

BACKENDS = {"keyless", "orx"}
OUTCOMES = {"answered", "empty", "failed-and-fell-back", "skipped-circuit-open"}
ENRICHMENT_MODES = {"auto", "keyless-only"}


class InputError(ValueError):
    """Malformed input: exit 2."""


def _obj(value, ctx: str) -> dict:
    if not isinstance(value, dict):
        raise InputError(f"{ctx}: expected an object, got {type(value).__name__}")
    return value


def _no_unknown_keys(value: dict, allowed: set[str], ctx: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise InputError(
            f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
            f"(expected one of: {', '.join(sorted(allowed))})"
        )


def _text(value, ctx: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{ctx}: expected a non-empty string, got {value!r}")
    return value.strip()


def _nullable_text(value, ctx: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InputError(f"{ctx}: expected string or null, got {type(value).__name__}")
    return value.strip() or None


def _bool(value, ctx: str) -> bool:
    if not isinstance(value, bool):
        raise InputError(f"{ctx}: expected a boolean, got {value!r}")
    return value


def _count(value, ctx: str) -> int:
    if isinstance(value, bool):
        raise InputError(f"{ctx}: expected an integer count, got boolean {value!r}")
    if isinstance(value, int):
        number = value
    elif isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise InputError(f"{ctx}: expected a whole finite number, got {value!r}")
        number = int(value)
    else:
        raise InputError(f"{ctx}: expected a JSON number, got {value!r}")
    if number < 0:
        raise InputError(f"{ctx}: count must be non-negative, got {number}")
    return number


def _parse_reasons(value, ctx: str) -> list[dict]:
    if not isinstance(value, list):
        raise InputError(f"{ctx}: expected a list")
    out = []
    seen = set()
    for idx, item in enumerate(value):
        item_ctx = f"{ctx}[{idx}]"
        _obj(item, item_ctx)
        _no_unknown_keys(item, REASON_KEYS, item_ctx)
        reason = _text(item.get("reason"), f"{item_ctx}.reason")
        if reason in seen:
            raise InputError(f"{item_ctx}.reason: duplicate reason {reason!r}")
        seen.add(reason)
        out.append({"reason": reason, "count": _count(item.get("count"), f"{item_ctx}.count")})
    return out


def _parse_query(value, index: int) -> dict:
    ctx = f"queries[{index}]"
    _obj(value, ctx)
    _no_unknown_keys(value, QUERY_KEYS, ctx)

    backend = value.get("backend")
    if backend not in BACKENDS:
        raise InputError(f"{ctx}.backend: expected one of {sorted(BACKENDS)}, got {backend!r}")
    outcome = value.get("outcome")
    if outcome not in OUTCOMES:
        raise InputError(f"{ctx}.outcome: expected one of {sorted(OUTCOMES)}, got {outcome!r}")

    parsed = {
        "backend": backend,
        "sub_source": _text(value.get("sub_source"), f"{ctx}.sub_source"),
        "strategy": _text(value.get("strategy"), f"{ctx}.strategy"),
        "query": _text(value.get("query"), f"{ctx}.query"),
        "date": _text(value.get("date"), f"{ctx}.date"),
        "outcome": outcome,
        "returned_count": _count(value.get("returned_count"), f"{ctx}.returned_count"),
        "normalization_drops": _parse_reasons(
            value.get("normalization_drops"), f"{ctx}.normalization_drops"
        ),
        "admitted_enriched_count": _count(
            value.get("admitted_enriched_count"), f"{ctx}.admitted_enriched_count"
        ),
        "unresolved_enrichment_count": _count(
            value.get("unresolved_enrichment_count"), f"{ctx}.unresolved_enrichment_count"
        ),
        "unresolved_reasons": _parse_reasons(
            value.get("unresolved_reasons"), f"{ctx}.unresolved_reasons"
        ),
        "circuit_open": _bool(value.get("circuit_open"), f"{ctx}.circuit_open"),
        "orx_version": _nullable_text(value.get("orx_version"), f"{ctx}.orx_version"),
        "failure_reason": _nullable_text(value.get("failure_reason"), f"{ctx}.failure_reason"),
    }

    if backend == "keyless":
        if parsed["admitted_enriched_count"] or parsed["unresolved_enrichment_count"]:
            raise InputError(
                f"{ctx}: keyless query cannot report enriched admission/unresolved counts"
            )
        if parsed["orx_version"] is not None:
            raise InputError(f"{ctx}: keyless query must use null orx_version")
    if outcome in {"failed-and-fell-back", "skipped-circuit-open"}:
        if not parsed["failure_reason"]:
            raise InputError(f"{ctx}: {outcome} requires failure_reason")
    elif parsed["failure_reason"] is not None:
        raise InputError(f"{ctx}: {outcome} must not carry failure_reason")
    return parsed


def _parse_disclosure(value) -> dict:
    ctx = "reproducibility_disclosure"
    _obj(value, ctx)
    _no_unknown_keys(value, DISCLOSURE_KEYS, ctx)
    required = _bool(value.get("requires_openresearch"), f"{ctx}.requires_openresearch")
    items = value.get("successful_enrichment")
    if not isinstance(items, list):
        raise InputError(f"{ctx}.successful_enrichment: expected a list")
    parsed_items = []
    for idx, item in enumerate(items):
        item_ctx = f"{ctx}.successful_enrichment[{idx}]"
        _obj(item, item_ctx)
        _no_unknown_keys(item, DISCLOSURE_ITEM_KEYS, item_ctx)
        parsed_items.append({
            "query": _text(item.get("query"), f"{item_ctx}.query"),
            "strategy": _text(item.get("strategy"), f"{item_ctx}.strategy"),
            "sub_source": _text(item.get("sub_source"), f"{item_ctx}.sub_source"),
            "orx_version": _nullable_text(item.get("orx_version"), f"{item_ctx}.orx_version"),
        })
    return {"requires_openresearch": required, "successful_enrichment": parsed_items}


def parse(raw: dict) -> dict:
    _obj(raw, "record")
    _no_unknown_keys(raw, RECORD_KEYS, "record")

    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(
            f"record: unrecognised or missing schema_version {version!r} "
            f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})"
        )
    run_date = _text(raw.get("run_date"), "record.run_date")
    mode = raw.get("enrichment_mode")
    if mode not in ENRICHMENT_MODES:
        raise InputError(
            f"record.enrichment_mode: expected one of {sorted(ENRICHMENT_MODES)}, got {mode!r}"
        )
    available = _bool(raw.get("orx_available"), "record.orx_available")

    queries = raw.get("queries")
    if not isinstance(queries, list):
        raise InputError("record.queries: expected a list")
    if not queries:
        raise InputError("record.queries: empty — there is nothing to check")
    parsed_queries = [_parse_query(item, idx) for idx, item in enumerate(queries)]

    disclosure = _parse_disclosure(raw.get("reproducibility_disclosure"))

    unresolved = raw.get("unresolved")
    _obj(unresolved, "record.unresolved")
    _no_unknown_keys(unresolved, UNRESOLVED_KEYS, "record.unresolved")
    unresolved_count = _count(unresolved.get("count"), "record.unresolved.count")
    unresolved_path = _text(unresolved.get("path"), "record.unresolved.path")

    if mode == "keyless-only" and any(q["backend"] == "orx" for q in parsed_queries):
        raise InputError("record: keyless-only mode cannot contain orx query entries")

    return {
        "schema_version": version,
        "run_date": run_date,
        "enrichment_mode": mode,
        "orx_available": available,
        "queries": parsed_queries,
        "reproducibility_disclosure": disclosure,
        "unresolved": {"count": unresolved_count, "path": unresolved_path},
    }


def _sig(query: dict) -> tuple[str, str, str, str | None]:
    return (
        query["query"], query["strategy"], query["sub_source"], query.get("orx_version")
    )


def check(record: dict) -> list[str]:
    issues: list[str] = []
    successful = [
        q for q in record["queries"]
        if q["backend"] == "orx" and q["outcome"] in {"answered", "empty"}
    ]
    successful_sigs = {_sig(q) for q in successful}
    disclosure = record["reproducibility_disclosure"]
    disclosed_sigs = {
        (item["query"], item["strategy"], item["sub_source"], item["orx_version"])
        for item in disclosure["successful_enrichment"]
    }

    for q in record["queries"]:
        if q["backend"] != "orx":
            continue
        if q["outcome"] in {"failed-and-fell-back", "skipped-circuit-open"} and not q["circuit_open"]:
            issues.append(
                f"{q['outcome']} enrichment {q['strategy']}/{q['sub_source']} for "
                f"{q['query']!r} is recorded with circuit_open=false"
            )
        reason_total = sum(item["count"] for item in q["unresolved_reasons"])
        if reason_total != q["unresolved_enrichment_count"]:
            issues.append(
                f"unresolved reason-count mismatch for {q['strategy']}/{q['sub_source']} "
                f"{q['query']!r}: reasons total {reason_total}, but query count = "
                f"{q['unresolved_enrichment_count']}"
            )
        if q["outcome"] in {"answered", "empty"}:
            normalized_total = (
                q["admitted_enriched_count"]
                + q["unresolved_enrichment_count"]
                + sum(item["count"] for item in q["normalization_drops"])
            )
            if normalized_total != q["returned_count"]:
                issues.append(
                    f"returned-count mismatch for {q['strategy']}/{q['sub_source']} "
                    f"{q['query']!r}: admitted + unresolved + drops = {normalized_total}, "
                    f"but returned_count = {q['returned_count']}"
                )

    for q in successful:
        if not q["orx_version"]:
            issues.append(
                f"successful enrichment {q['strategy']}/{q['sub_source']} for "
                f"{q['query']!r} has no OpenResearch version"
            )

    if successful and not disclosure["requires_openresearch"]:
        issues.append(
            f"{len(successful)} successful enrichment search(es) are recorded, but "
            "reproducibility_disclosure.requires_openresearch is false"
        )
    if not successful and disclosure["requires_openresearch"]:
        issues.append(
            "reproducibility_disclosure.requires_openresearch is true, but no successful "
            "enrichment search is recorded"
        )

    missing = successful_sigs - disclosed_sigs
    extra = disclosed_sigs - successful_sigs
    if missing:
        issues.append(
            f"reproducibility disclosure omits {len(missing)} successful enrichment search(es)"
        )
    if extra:
        issues.append(
            f"reproducibility disclosure names {len(extra)} enrichment search(es) that are not "
            "successful query entries"
        )

    unresolved_sum = sum(
        q["unresolved_enrichment_count"]
        for q in record["queries"]
        if q["backend"] == "orx"
    )
    if unresolved_sum != record["unresolved"]["count"]:
        issues.append(
            f"unresolved count mismatch: query entries total {unresolved_sum}, but "
            f"record.unresolved.count = {record['unresolved']['count']}"
        )
    return issues


def render(record: dict, issues: list[str], source: str) -> str:
    successful = sum(
        q["backend"] == "orx" and q["outcome"] in {"answered", "empty"}
        for q in record["queries"]
    )
    lines = [
        "# Acquisition disclosure",
        "",
        f"- Source record: `{source}`",
        f"- Enrichment mode: `{record['enrichment_mode']}`",
        f"- Successful enriched searches: **{successful}**",
        f"- Unresolved enriched hits: **{record['unresolved']['count']}**",
        "",
        "## Acquisition disclosure check",
        "",
    ]
    if issues:
        lines += [
            f"⚠️ **{len(issues)} issue(s)** — fix before reporting:",
            "",
            *[f"- {issue}" for issue in issues],
        ]
    else:
        lines.append("✅ Enrichment disclosure is structurally complete and internally consistent.")
    lines += [
        "",
        "### What this check cannot verify",
        "",
        "It cannot verify the truthfulness of provenance or version strings, source attribution, "
        "candidate-file counts, correctness of metadata resolution, or search recall. A clean "
        "result is not PRISMA-S compliance.",
        "",
    ]
    return "\n".join(lines)


def _load(path: str | None):
    try:
        if path:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle), path
        return json.load(sys.stdin), "<stdin>"
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(str(exc)) from exc


def _json_envelope(issues: list[str]) -> dict:
    return {
        "check": CHECK_NAME,
        "schema_version": JSON_ENVELOPE_VERSION,
        "issues": len(issues),
        "units": {},
        "gates": {},
        "unattributed": len(issues),
        "detail": {"violations": issues},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check acquire-corpus enrichment disclosure.")
    parser.add_argument("record", nargs="?")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        raw, source = _load(args.record)
        record = parse(raw)
    except InputError as exc:
        sys.stderr.write(f"{CHECK_NAME}: malformed input: {exc}\n")
        return 2

    issues = check(record)
    if args.as_json:
        print(json.dumps(_json_envelope(issues), ensure_ascii=False, sort_keys=True))
    else:
        print(render(record, issues, source))
    return 1 if args.strict and issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
