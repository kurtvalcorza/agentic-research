#!/usr/bin/env python3
"""Check OpenResearch enrichment disclosure in an acquire-corpus acquisition record.

Standard library only.

WHAT THIS CHECKS
  The canonical acquisition record is closed-schema and structurally well formed;
  successful OpenResearch discovery calls carry an OpenResearch version and are
  represented in the reproducibility disclosure; and the disclosure does not claim
  OpenResearch is unnecessary when a successful enriched search was part of the run.
  For schema 1.1 records it also reconciles the loss summary (admitted DOI-less,
  unresolved missing authors/year) and the opaque-ranking method disclosure against
  the query entries, requires a zero-normalizable fallback to account for every
  dropped record, and requires an incomplete keyless search to carry its failure.

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

SCHEMA_VERSIONS = {"1.0", "1.1"}
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
LOSS_SUMMARY_KEYS = {
    "admitted_enriched_count", "admitted_doi_less_count", "unresolved_count",
    "unresolved_missing_authors_count", "unresolved_missing_year_count",
    "metadata_completion_skipped_count",
}
METHOD_DISCLOSURE_KEYS = {
    "opaque_ranking_or_truncation", "affected_sub_sources", "orx_limit",
    "orx_prioritize", "is_deduplication_step",
}
RECORD_KEYS_1_1 = RECORD_KEYS | {"loss_summary", "method_disclosure"}

BACKENDS = {"keyless", "orx"}
OUTCOMES = {"answered", "empty", "failed-and-fell-back", "skipped-circuit-open"}
# 1.1 adds `incomplete`: a keyless search that stopped on a transport/malformed
# response failure before the source was exhausted. It is neither `empty` (a
# genuine zero-result search) nor `answered` (a complete one).
OUTCOMES_1_1 = OUTCOMES | {"incomplete"}
ZERO_NORMALIZABLE = "zero-normalizable-records"
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


def _parse_query(value, index: int, outcomes: set[str] = OUTCOMES) -> dict:
    ctx = f"queries[{index}]"
    _obj(value, ctx)
    _no_unknown_keys(value, QUERY_KEYS, ctx)

    backend = value.get("backend")
    if backend not in BACKENDS:
        raise InputError(f"{ctx}.backend: expected one of {sorted(BACKENDS)}, got {backend!r}")
    outcome = value.get("outcome")
    if outcome not in outcomes:
        raise InputError(f"{ctx}.outcome: expected one of {sorted(outcomes)}, got {outcome!r}")

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
    if outcome == "incomplete" and backend != "keyless":
        raise InputError(f"{ctx}: incomplete is a keyless outcome; orx failures fall back")
    if outcome in {"failed-and-fell-back", "skipped-circuit-open", "incomplete"}:
        if not parsed["failure_reason"]:
            raise InputError(f"{ctx}: {outcome} requires failure_reason")
    elif parsed["failure_reason"] is not None:
        raise InputError(f"{ctx}: {outcome} must not carry failure_reason")
    return parsed


def _parse_loss_summary(value) -> dict:
    ctx = "loss_summary"
    _obj(value, ctx)
    _no_unknown_keys(value, LOSS_SUMMARY_KEYS, ctx)
    parsed = {}
    for key in sorted(LOSS_SUMMARY_KEYS):
        if key not in value:
            raise InputError(f"{ctx}.{key}: missing")
        parsed[key] = _count(value.get(key), f"{ctx}.{key}")
    return parsed


def _parse_method_disclosure(value) -> dict:
    ctx = "method_disclosure"
    _obj(value, ctx)
    _no_unknown_keys(value, METHOD_DISCLOSURE_KEYS, ctx)
    for key in sorted(METHOD_DISCLOSURE_KEYS):
        if key not in value:
            raise InputError(f"{ctx}.{key}: missing")
    sources = value.get("affected_sub_sources")
    if not isinstance(sources, list) or any(
        not isinstance(item, str) or not item.strip() for item in sources
    ):
        raise InputError(f"{ctx}.affected_sub_sources: expected a list of non-empty strings")
    if len(set(sources)) != len(sources):
        raise InputError(f"{ctx}.affected_sub_sources: duplicate sub-source")
    limit = value.get("orx_limit")
    if limit is not None:
        limit = _count(limit, f"{ctx}.orx_limit")
    return {
        "opaque_ranking_or_truncation": _bool(
            value.get("opaque_ranking_or_truncation"), f"{ctx}.opaque_ranking_or_truncation"
        ),
        "affected_sub_sources": [item.strip() for item in sources],
        "orx_limit": limit,
        "orx_prioritize": _nullable_text(value.get("orx_prioritize"), f"{ctx}.orx_prioritize"),
        "is_deduplication_step": _bool(
            value.get("is_deduplication_step"), f"{ctx}.is_deduplication_step"
        ),
    }


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
    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(
            f"record: unrecognised or missing schema_version {version!r} "
            f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})"
        )
    modern = version != "1.0"
    _no_unknown_keys(raw, RECORD_KEYS_1_1 if modern else RECORD_KEYS, "record")
    outcomes = OUTCOMES_1_1 if modern else OUTCOMES
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
    parsed_queries = [_parse_query(item, idx, outcomes) for idx, item in enumerate(queries)]

    disclosure = _parse_disclosure(raw.get("reproducibility_disclosure"))

    unresolved = raw.get("unresolved")
    _obj(unresolved, "record.unresolved")
    _no_unknown_keys(unresolved, UNRESOLVED_KEYS, "record.unresolved")
    unresolved_count = _count(unresolved.get("count"), "record.unresolved.count")
    unresolved_path = _text(unresolved.get("path"), "record.unresolved.path")

    if mode == "keyless-only" and any(q["backend"] == "orx" for q in parsed_queries):
        raise InputError("record: keyless-only mode cannot contain orx query entries")

    parsed = {
        "schema_version": version,
        "run_date": run_date,
        "enrichment_mode": mode,
        "orx_available": available,
        "queries": parsed_queries,
        "reproducibility_disclosure": disclosure,
        "unresolved": {"count": unresolved_count, "path": unresolved_path},
    }
    if modern:
        if "loss_summary" not in raw:
            raise InputError("record.loss_summary: missing (required from schema 1.1)")
        if "method_disclosure" not in raw:
            raise InputError("record.method_disclosure: missing (required from schema 1.1)")
        parsed["loss_summary"] = _parse_loss_summary(raw.get("loss_summary"))
        parsed["method_disclosure"] = _parse_method_disclosure(raw.get("method_disclosure"))
    return parsed


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
        elif q["failure_reason"] == ZERO_NORMALIZABLE:
            # FR-008 / SC-009: a non-empty response with zero normalizable records
            # must still account for every record it dropped, by count and reason.
            dropped = sum(item["count"] for item in q["normalization_drops"])
            if dropped != q["returned_count"]:
                issues.append(
                    f"zero-normalizable fallback for {q['strategy']}/{q['sub_source']} "
                    f"{q['query']!r} drops {dropped} record(s) but returned_count = "
                    f"{q['returned_count']}; every returned record must be dropped with a reason"
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

    if "loss_summary" in record:
        issues.extend(_check_loss_summary(record, successful))
    return issues


def _check_loss_summary(record: dict, successful: list[dict]) -> list[str]:
    issues: list[str] = []
    loss = record["loss_summary"]
    admitted_sum = sum(q["admitted_enriched_count"] for q in record["queries"])
    unresolved_count = record["unresolved"]["count"]
    if loss["admitted_enriched_count"] != admitted_sum:
        issues.append(
            f"loss summary admitted_enriched_count = {loss['admitted_enriched_count']}, but "
            f"query entries admit {admitted_sum}"
        )
    if loss["admitted_doi_less_count"] > loss["admitted_enriched_count"]:
        issues.append(
            f"loss summary admitted_doi_less_count = {loss['admitted_doi_less_count']} exceeds "
            f"admitted_enriched_count = {loss['admitted_enriched_count']}"
        )
    if loss["unresolved_count"] != unresolved_count:
        issues.append(
            f"loss summary unresolved_count = {loss['unresolved_count']}, but "
            f"record.unresolved.count = {unresolved_count}"
        )
    for key in (
        "unresolved_missing_authors_count",
        "unresolved_missing_year_count",
        "metadata_completion_skipped_count",
    ):
        if loss[key] > unresolved_count:
            issues.append(
                f"loss summary {key} = {loss[key]} exceeds unresolved count {unresolved_count}"
            )
    if (
        loss["unresolved_missing_authors_count"] + loss["unresolved_missing_year_count"]
        < unresolved_count
    ):
        issues.append(
            "loss summary does not explain every unresolved hit: missing-authors + "
            f"missing-year = {loss['unresolved_missing_authors_count'] + loss['unresolved_missing_year_count']}"
            f" < unresolved count {unresolved_count}"
        )

    method = record["method_disclosure"]
    successful_sources = sorted({q["sub_source"] for q in successful})
    if method["is_deduplication_step"]:
        issues.append("method disclosure labels source-side ranking/truncation as deduplication")
    if successful and not method["opaque_ranking_or_truncation"]:
        issues.append(
            f"{len(successful)} successful enrichment search(es) are recorded, but "
            "method_disclosure.opaque_ranking_or_truncation is false"
        )
    if not successful and method["opaque_ranking_or_truncation"]:
        issues.append(
            "method_disclosure.opaque_ranking_or_truncation is true, but no successful "
            "enrichment search is recorded"
        )
    if sorted(method["affected_sub_sources"]) != successful_sources:
        issues.append(
            f"method disclosure names sub-sources {sorted(method['affected_sub_sources'])}, "
            f"but successful enrichment used {successful_sources}"
        )
    if successful and method["orx_limit"] is None:
        issues.append("method disclosure omits the orx --limit applied to successful enrichment")
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
    ]
    if "loss_summary" in record:
        loss = record["loss_summary"]
        lines += [
            f"- Admitted DOI-less enriched records: **{loss['admitted_doi_less_count']}**",
            f"- Unresolved missing authors / year: **{loss['unresolved_missing_authors_count']}** / "
            f"**{loss['unresolved_missing_year_count']}**",
            "- Opaque enriched ranking/truncation disclosed: "
            f"**{'yes' if record['method_disclosure']['opaque_ranking_or_truncation'] else 'no'}**",
        ]
    lines += [
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
