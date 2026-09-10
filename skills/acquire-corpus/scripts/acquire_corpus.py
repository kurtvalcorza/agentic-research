#!/usr/bin/env python3
"""Build a literature corpus with an OpenAlex keyless baseline and optional orx enrichment.

Standard library only. OpenResearch is an optional external executable; if it is
absent or an enriched sub-source fails, the keyless OpenAlex path remains usable.

The structured source of truth is ``corpus/acquisition-record.json``. The
human-readable ``corpus/search-log.md`` is generated from that record.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request

OPENALEX_BASE = "https://api.openalex.org/works"
UA = "acquire-corpus/2.0 (agentic-research; mailto:{})"
SCHEMA_VERSION = "1.0"
ORX_TIMEOUT_SECONDS = 5.0
ORX_VERSION_TIMEOUT_SECONDS = 2.0
ENRICHMENT_FAILURE_BUDGET_SECONDS = 15.0
ORX_STRATEGIES = ("keyword", "embedding", "openalex", "biorxiv")
STRATEGY_SUB_SOURCE = {
    "keyword": "alphaxiv",
    "embedding": "alphaxiv",
    "openalex": "openalex",
    "biorxiv": "biorxiv",
}
SUPPORTED_LITHIT_KEYS = {
    "source", "id", "title", "abstract", "publicationDate",
    "votes", "citations", "snippets",
}
SUPPORTED_LITHIT_SOURCES = {"alphaxiv", "openalex", "biorxiv"}
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)


class EnrichmentFailure(RuntimeError):
    """An optional enrichment call/response is unusable and must fall back keyless."""

    def __init__(self, reason: str, *, elapsed: float = 0.0):
        super().__init__(reason)
        self.reason = reason
        self.elapsed = max(0.0, float(elapsed))


@dataclass(frozen=True)
class AcquisitionConfig:
    queries: tuple[str, ...]
    output_dir: Path
    from_date: str = ""
    to_date: str = ""
    work_type: str = ""
    language: str = ""
    max_results: int = 200
    mailto: str = ""
    run_date: str = ""
    keyless_only: bool = False
    orx_limit: int = 15
    orx_strategies: tuple[str, ...] = ORX_STRATEGIES
    orx_prioritize: str = "default"


def _http_json(url: str, mailto: str = "", timeout: float = 30.0):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA.format(mailto or "anonymous@example.com")}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _reconstruct_abstract(inv) -> str:
    if not inv:
        return ""
    positions = []
    for word, idxs in inv.items():
        for idx in idxs:
            positions.append((idx, word))
    positions.sort()
    return " ".join(word for _, word in positions)


def _openalex_record(work: dict) -> dict:
    return {
        "openalex_id": work.get("id"),
        "doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
        "title": work.get("title"),
        "authors": [
            item.get("author", {}).get("display_name", "")
            for item in (work.get("authorships") or [])
        ][:8],
        "year": work.get("publication_year"),
        "venue": ((work.get("primary_location") or {}).get("source") or {}).get("display_name"),
        "type": work.get("type"),
        "is_retracted": bool(work.get("is_retracted")),
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "cited_by_count": work.get("cited_by_count"),
        "referenced_works": work.get("referenced_works") or [],
    }


def keyless_openalex_search(query: str, config: AcquisitionConfig) -> list[dict]:
    """Mirror search_openalex.py's baseline record shape and fail-soft paging."""
    filters = []
    if config.from_date:
        filters.append(f"from_publication_date:{config.from_date}")
    if config.to_date:
        filters.append(f"to_publication_date:{config.to_date}")
    if config.work_type:
        filters.append(f"type:{config.work_type}")
    if config.language:
        filters.append(f"language:{config.language}")

    params = {"search": query, "per_page": "200", "cursor": "*"}
    if filters:
        params["filter"] = ",".join(filters)
    if config.mailto:
        params["mailto"] = config.mailto

    out: list[dict] = []
    seen = set()
    while len(out) < config.max_results:
        url = f"{OPENALEX_BASE}?{urllib.parse.urlencode(params)}"
        try:
            data = _http_json(url, config.mailto, timeout=30.0)
        except Exception:  # preserve the existing keyless fail-soft behavior
            break
        if not isinstance(data, dict):
            break
        results = data.get("results", [])
        if not isinstance(results, list) or not results:
            break
        for work in results:
            if not isinstance(work, dict):
                continue
            rec = _openalex_record(work)
            key = rec["doi"] or rec["openalex_id"]
            if key in seen:
                continue
            seen.add(key)
            out.append(rec)
            if len(out) >= config.max_results:
                break
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
        params["cursor"] = cursor
        time.sleep(0.25)
    return out


def _clean_doi(value) -> str:
    if not isinstance(value, str):
        return ""
    doi = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):].strip()
            break
    return doi if DOI_RE.match(doi) else ""


def _year_from_publication_date(value):
    if not isinstance(value, str) or len(value) < 4 or not value[:4].isdigit():
        return None
    year = int(value[:4])
    return year if 1000 <= year <= 3000 else None


def _norm_title(value) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", value.casefold())).strip()


def _valid_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_lithit_response(raw, strategy: str) -> tuple[list[dict], Counter]:
    """Validate a complete LitHit response and normalize supported records.

    Unknown top-level keys reject the entire response. Within a supported shape,
    records missing required discovery fields are counted and dropped.
    """
    if not isinstance(raw, list):
        raise EnrichmentFailure("transport-top-level-not-array")

    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise EnrichmentFailure(f"unsupported-schema:record-{idx}-not-object")
        unknown = sorted(set(item) - SUPPORTED_LITHIT_KEYS)
        if unknown:
            raise EnrichmentFailure(
                "unsupported-schema:unknown-key:" + ",".join(unknown)
            )

    normalized: list[dict] = []
    drops: Counter = Counter()

    for item in raw:
        source = item.get("source")
        source_id = item.get("id")
        title = item.get("title")
        if (
            not isinstance(source, str)
            or source not in SUPPORTED_LITHIT_SOURCES
            or not isinstance(source_id, str)
            or not source_id.strip()
            or not isinstance(title, str)
            or not title.strip()
        ):
            drops["missing-or-invalid-required-discovery-field"] += 1
            continue
        expected_source = STRATEGY_SUB_SOURCE.get(strategy)
        if expected_source is None or source != expected_source:
            raise EnrichmentFailure(
                f"unsupported-schema:source-strategy-mismatch:{source}:{strategy}"
            )

        abstract = item.get("abstract")
        if abstract is not None and not isinstance(abstract, str):
            drops["invalid-abstract"] += 1
            continue
        if "votes" in item and item["votes"] is not None and not _valid_int(item["votes"]):
            drops["invalid-votes"] += 1
            continue
        if "citations" in item and item["citations"] is not None and not _valid_int(item["citations"]):
            drops["invalid-citations"] += 1
            continue
        if "snippets" in item and not isinstance(item["snippets"], list):
            drops["invalid-snippets"] += 1
            continue
        publication_date = item.get("publicationDate")
        if publication_date is not None and not isinstance(publication_date, str):
            drops["invalid-publication-date"] += 1
            continue

        clean_id = source_id.strip()
        rec = {
            "source": "orx",
            "sub_source": source,
            "source_id": clean_id,
            "orx_strategy": strategy,
            "title": title.strip(),
        }
        doi = _clean_doi(clean_id)
        if doi:
            rec["doi"] = doi
        year = _year_from_publication_date(publication_date)
        if year is not None:
            rec["year"] = year
        if abstract:
            rec["abstract"] = abstract
        if item.get("citations") is not None:
            rec["cited_by_count"] = item["citations"]
        if item.get("votes") is not None:
            rec["orx_votes"] = item["votes"]
        if item.get("snippets"):
            rec["orx_snippets"] = item["snippets"]
        normalized.append(rec)

    if raw and not normalized:
        raise EnrichmentFailure("zero-normalizable-records")
    return normalized, drops


def _openalex_candidate_matches(rec: dict, candidate: dict, *, direct: bool) -> bool:
    title = _norm_title(rec.get("title"))
    cand_title = _norm_title(candidate.get("title"))
    if not title or not cand_title:
        return False
    similarity = SequenceMatcher(None, title, cand_title).ratio()
    if similarity < (0.85 if direct else 0.95):
        return False

    rec_year = rec.get("year")
    cand_year = candidate.get("publication_year")
    if isinstance(rec_year, int) and isinstance(cand_year, int):
        if abs(rec_year - cand_year) > 1:
            return False

    rec_doi = _clean_doi(rec.get("doi"))
    cand_doi = _clean_doi(candidate.get("doi"))
    if rec_doi and cand_doi and rec_doi.casefold() != cand_doi.casefold():
        return False
    return True


def resolve_openalex_metadata(
    rec: dict,
    config: AcquisitionConfig,
    *,
    http_json=_http_json,
) -> dict | None:
    """Resolve authors/year conservatively through the keyless OpenAlex source."""
    source_id = rec.get("source_id", "")
    doi = _clean_doi(rec.get("doi"))
    direct = False

    if rec.get("sub_source") in {"openalex", "biorxiv"} and re.fullmatch(r"W\d+", source_id):
        direct = True
        url = f"{OPENALEX_BASE}/{urllib.parse.quote(source_id)}"
    elif doi:
        direct = True
        url = f"{OPENALEX_BASE}/doi:{urllib.parse.quote(doi)}"
    else:
        params = {"search": rec["title"], "per_page": "5"}
        if config.mailto:
            params["mailto"] = config.mailto
        url = f"{OPENALEX_BASE}?{urllib.parse.urlencode(params)}"

    try:
        data = http_json(url, config.mailto, timeout=ORX_TIMEOUT_SECONDS)
    except Exception:
        return None

    candidates = [data] if direct and isinstance(data, dict) else (
        data.get("results", []) if isinstance(data, dict) else []
    )
    if not isinstance(candidates, list):
        return None

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if not _openalex_candidate_matches(rec, candidate, direct=direct):
            continue
        authors = [
            a.get("author", {}).get("display_name", "").strip()
            for a in (candidate.get("authorships") or [])
            if isinstance(a, dict)
        ]
        authors = [a for a in authors if a][:8]
        year = candidate.get("publication_year")
        if not authors or not isinstance(year, int):
            continue
        resolved = {"authors": authors, "year": year}
        resolved_doi = _clean_doi(candidate.get("doi"))
        if resolved_doi:
            resolved["doi"] = resolved_doi
        venue = ((candidate.get("primary_location") or {}).get("source") or {}).get("display_name")
        if isinstance(venue, str) and venue.strip():
            resolved["venue"] = venue.strip()
        work_type = candidate.get("type")
        if isinstance(work_type, str) and work_type.strip():
            resolved["type"] = work_type.strip()
        if "is_retracted" in candidate and isinstance(candidate.get("is_retracted"), bool):
            resolved["is_retracted"] = candidate["is_retracted"]
        return resolved
    return None


def admit_enriched_hit(
    rec: dict,
    config: AcquisitionConfig,
    *,
    resolver=resolve_openalex_metadata,
) -> tuple[dict | None, dict | None]:
    """Return (admitted, unresolved) while enforcing the safe-admission minimum."""
    metadata = resolver(rec, config)
    authors = metadata.get("authors") if isinstance(metadata, dict) else None
    year = (
        metadata.get("year")
        if isinstance(metadata, dict) and isinstance(metadata.get("year"), int)
        else rec.get("year")
    )

    if not isinstance(authors, list) or not authors or not isinstance(year, int):
        unresolved = dict(rec)
        unresolved["reason"] = "bibliographic-metadata-unresolved"
        return None, unresolved

    admitted = dict(rec)
    admitted["authors"] = authors
    admitted["year"] = year
    if isinstance(metadata, dict):
        for key in ("doi", "venue", "type", "is_retracted"):
            if key in metadata:
                admitted[key] = metadata[key]
    admitted["identifier_less"] = not bool(_clean_doi(admitted.get("doi")))
    return admitted, None


def run_orx_discover(
    executable: str,
    strategy: str,
    query: str,
    config: AcquisitionConfig,
    *,
    runner=subprocess.run,
) -> tuple[list, float]:
    cmd = [
        executable, "discover", strategy, query,
        "--limit", str(config.orx_limit),
        "--prioritize", config.orx_prioritize,
    ]
    if config.from_date:
        cmd.extend(["--published-after", config.from_date])
    if config.to_date:
        cmd.extend(["--published-before", config.to_date])

    started = time.monotonic()
    try:
        result = runner(
            cmd,
            capture_output=True,
            text=True,
            timeout=ORX_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        raise EnrichmentFailure("timeout", elapsed=max(elapsed, ORX_TIMEOUT_SECONDS)) from exc
    except OSError as exc:
        elapsed = time.monotonic() - started
        raise EnrichmentFailure("command-surface-failure", elapsed=elapsed) from exc

    elapsed = time.monotonic() - started
    if result.returncode != 0:
        raise EnrichmentFailure("command-surface-failure", elapsed=elapsed)
    text = result.stdout.strip()
    if not text:
        raise EnrichmentFailure("empty-transport", elapsed=elapsed)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnrichmentFailure("malformed-transport", elapsed=elapsed) from exc
    if not isinstance(raw, list):
        raise EnrichmentFailure("transport-top-level-not-array", elapsed=elapsed)
    return raw, elapsed


def read_orx_version(
    executable: str,
    *,
    runner=subprocess.run,
) -> str | None:
    try:
        result = runner(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=ORX_VERSION_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    line = result.stdout.strip().splitlines()
    return line[0].strip() if line and line[0].strip() else None


def _reason_counts(counter: Counter) -> list[dict]:
    return [{"reason": key, "count": counter[key]} for key in sorted(counter)]


def _query_entry(
    *,
    backend: str,
    sub_source: str,
    strategy: str,
    query: str,
    run_date: str,
    outcome: str,
    returned_count: int = 0,
    drops: Counter | None = None,
    admitted: int = 0,
    unresolved: int = 0,
    unresolved_reasons: Counter | None = None,
    circuit_open: bool = False,
    orx_version: str | None = None,
    failure_reason: str | None = None,
) -> dict:
    return {
        "backend": backend,
        "sub_source": sub_source,
        "strategy": strategy,
        "query": query,
        "date": run_date,
        "outcome": outcome,
        "returned_count": returned_count,
        "normalization_drops": _reason_counts(drops or Counter()),
        "admitted_enriched_count": admitted,
        "unresolved_enrichment_count": unresolved,
        "unresolved_reasons": _reason_counts(unresolved_reasons or Counter()),
        "circuit_open": circuit_open,
        "orx_version": orx_version,
        "failure_reason": failure_reason,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for rec in records:
            handle.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _md_cell(value) -> str:
    if value is None:
        return "—"
    return str(value).replace("|", "&#124;").replace("\n", "<br>")


def render_search_log(record: dict) -> str:
    mode = record["enrichment_mode"]
    lines = [
        "# Search log",
        "",
        f"- Run date: **{record['run_date']}**",
        f"- Enrichment mode: **{mode}**",
        f"- OpenResearch executable available: **{'yes' if record['orx_available'] else 'no'}**",
        "",
    ]
    if mode == "keyless-only":
        lines += [
            "> This run was intentionally restricted to the keyless baseline by the reviewer.",
            "",
        ]

    degraded = [
        q for q in record["queries"]
        if q["outcome"] in {"failed-and-fell-back", "skipped-circuit-open"}
    ]
    if degraded:
        lines += [
            "> **Enrichment degradation:** one or more intended enrichment searches did not "
            "complete. Those queries fell back to the keyless baseline or were skipped after a "
            "sub-source circuit opened. See the outcome column below.",
            "",
        ]

    lines += [
        "| Backend | Source | Strategy | Query | Date | Outcome | Returned | Admitted | Unresolved | Circuit | Version |",
        "|:--|:--|:--|:--|:--|:--|--:|--:|--:|:--:|:--|",
    ]
    for q in record["queries"]:
        lines.append(
            "| {backend} | {source} | {strategy} | {query} | {date} | {outcome} | "
            "{returned} | {admitted} | {unresolved} | {circuit} | {version} |".format(
                backend=_md_cell(q["backend"]),
                source=_md_cell(q["sub_source"]),
                strategy=_md_cell(q["strategy"]),
                query=_md_cell(q["query"]),
                date=_md_cell(q["date"]),
                outcome=_md_cell(q["outcome"]),
                returned=q["returned_count"],
                admitted=q["admitted_enriched_count"],
                unresolved=q["unresolved_enrichment_count"],
                circuit="open" if q["circuit_open"] else "closed",
                version=_md_cell(q["orx_version"]),
            )
        )

    disclosure = record["reproducibility_disclosure"]
    lines += ["", "## Reproducibility", ""]
    if disclosure["requires_openresearch"]:
        lines += [
            "This search is **not fully reproducible without OpenResearch**. The following "
            "successful enrichment searches used it:",
            "",
        ]
        for item in disclosure["successful_enrichment"]:
            lines.append(
                f"- `{item['strategy']}` / `{item['sub_source']}` — "
                f"{item['query']} ({item['orx_version']})"
            )
    else:
        lines.append(
            "OpenResearch is not required to reproduce the candidate set produced by this run."
        )

    unresolved = record["unresolved"]
    if unresolved["count"]:
        lines += [
            "",
            "## Unresolved enrichment",
            "",
            f"**{unresolved['count']}** discovered hit(s) could not satisfy the safe-admission "
            f"minimum. Review `{unresolved['path']}` before treating the acquisition as complete. "
            "These hits are not candidates and must not enter screening until their bibliographic "
            "metadata is resolved.",
        ]

    lines += [
        "",
        "## Method limits",
        "",
        "- OpenResearch source ranking/truncation may be opaque.",
        "- This workflow does not characterize recall against the review question.",
        "- Source coverage is not quantified by this log.",
        "",
        "---",
        "",
        "*Generated from `corpus/acquisition-record.json` by `acquire_corpus.py`; "
        "the JSON record is the source of truth.*",
        "",
    ]
    return "\n".join(lines)


def acquire(
    config: AcquisitionConfig,
    *,
    keyless_search=keyless_openalex_search,
    orx_runner=run_orx_discover,
    metadata_resolver=resolve_openalex_metadata,
    which=shutil.which,
    version_reader=read_orx_version,
) -> dict:
    if not config.queries or any(not q.strip() for q in config.queries):
        raise ValueError("at least one non-empty query is required")
    if config.max_results < 1 or config.orx_limit < 1 or config.orx_limit > 200:
        raise ValueError("result limits must be positive and orx-limit must be <= 200")
    if any(strategy not in ORX_STRATEGIES for strategy in config.orx_strategies):
        raise ValueError("unsupported orx strategy")

    output_dir = config.output_dir
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    run_date = config.run_date or date.today().isoformat()
    candidates: list[dict] = []
    unresolved_records: list[dict] = []
    entries: list[dict] = []
    disclosure_entries: list[dict] = []

    detected_executable = which("orx")
    orx_available = bool(detected_executable)
    executable = None if config.keyless_only else detected_executable
    orx_version = version_reader(executable) if executable else None
    circuits = {source: False for source in SUPPORTED_LITHIT_SOURCES}
    failure_wait = 0.0

    for q_index, query in enumerate(config.queries, 1):
        query = query.strip()
        keyless = keyless_search(query, config)
        candidates.extend(keyless)
        _write_jsonl(raw_dir / f"openalex-q{q_index:03d}.jsonl", keyless)
        entries.append(
            _query_entry(
                backend="keyless",
                sub_source="openalex",
                strategy="search",
                query=query,
                run_date=run_date,
                outcome="answered" if keyless else "empty",
                returned_count=len(keyless),
            )
        )

        if not executable:
            continue

        for strategy in config.orx_strategies:
            sub_source = STRATEGY_SUB_SOURCE[strategy]
            if circuits[sub_source] or failure_wait >= ENRICHMENT_FAILURE_BUDGET_SECONDS:
                reason = (
                    "sub-source-circuit-open"
                    if circuits[sub_source]
                    else "run-failure-budget-exhausted"
                )
                entries.append(
                    _query_entry(
                        backend="orx",
                        sub_source=sub_source,
                        strategy=strategy,
                        query=query,
                        run_date=run_date,
                        outcome="skipped-circuit-open",
                        circuit_open=True,
                        orx_version=orx_version,
                        failure_reason=reason,
                    )
                )
                continue

            try:
                raw, _elapsed = orx_runner(executable, strategy, query, config)
            except EnrichmentFailure as exc:
                circuits[sub_source] = True
                failure_wait += min(exc.elapsed, ORX_TIMEOUT_SECONDS)
                entries.append(
                    _query_entry(
                        backend="orx",
                        sub_source=sub_source,
                        strategy=strategy,
                        query=query,
                        run_date=run_date,
                        outcome="failed-and-fell-back",
                        circuit_open=True,
                        orx_version=orx_version,
                        failure_reason=exc.reason,
                    )
                )
                continue

            _write_json(raw_dir / f"orx-{strategy}-q{q_index:03d}.json", raw)
            try:
                normalized, drops = normalize_lithit_response(raw, strategy)
            except EnrichmentFailure as exc:
                circuits[sub_source] = True
                entries.append(
                    _query_entry(
                        backend="orx",
                        sub_source=sub_source,
                        strategy=strategy,
                        query=query,
                        run_date=run_date,
                        outcome="failed-and-fell-back",
                        returned_count=len(raw),
                        circuit_open=True,
                        orx_version=orx_version,
                        failure_reason=exc.reason,
                    )
                )
                continue

            _write_jsonl(
                raw_dir / f"orx-{strategy}-q{q_index:03d}.normalized.jsonl",
                normalized,
            )

            admitted: list[dict] = []
            unresolved: list[dict] = []
            unresolved_reasons: Counter = Counter()
            for rec in normalized:
                accepted, pending = admit_enriched_hit(
                    rec, config, resolver=metadata_resolver
                )
                if accepted is not None:
                    admitted.append(accepted)
                elif pending is not None:
                    unresolved.append(pending)
                    unresolved_reasons[pending["reason"]] += 1

            candidates.extend(admitted)
            unresolved_records.extend(unresolved)
            outcome = "empty" if not raw else "answered"
            entries.append(
                _query_entry(
                    backend="orx",
                    sub_source=sub_source,
                    strategy=strategy,
                    query=query,
                    run_date=run_date,
                    outcome=outcome,
                    returned_count=len(raw),
                    drops=drops,
                    admitted=len(admitted),
                    unresolved=len(unresolved),
                    unresolved_reasons=unresolved_reasons,
                    circuit_open=False,
                    orx_version=orx_version,
                )
            )
            disclosure_entries.append(
                {
                    "query": query,
                    "strategy": strategy,
                    "sub_source": sub_source,
                    "orx_version": orx_version,
                }
            )

    _write_jsonl(output_dir / "candidates.jsonl", candidates)
    unresolved_path = output_dir / "enrichment-unresolved.jsonl"
    _write_jsonl(unresolved_path, unresolved_records)

    record = {
        "schema_version": SCHEMA_VERSION,
        "run_date": run_date,
        "enrichment_mode": "keyless-only" if config.keyless_only else "auto",
        "orx_available": orx_available,
        "queries": entries,
        "reproducibility_disclosure": {
            "requires_openresearch": bool(disclosure_entries),
            "successful_enrichment": disclosure_entries,
        },
        "unresolved": {
            "count": len(unresolved_records),
            "path": unresolved_path.as_posix(),
        },
    }
    _write_json(output_dir / "acquisition-record.json", record)
    (output_dir / "search-log.md").write_text(
        render_search_log(record), encoding="utf-8", newline="\n"
    )
    return record


def _parse_args(argv=None) -> AcquisitionConfig:
    parser = argparse.ArgumentParser(
        description="Build a keyless OpenAlex corpus with optional orx discovery enrichment."
    )
    parser.add_argument("--query", action="append", required=True,
                        help="Search query; repeat to run multiple concept queries.")
    parser.add_argument("--output-dir", default="corpus")
    parser.add_argument("--from", dest="from_date", default="")
    parser.add_argument("--to", dest="to_date", default="")
    parser.add_argument("--type", dest="work_type", default="")
    parser.add_argument("--lang", dest="language", default="")
    parser.add_argument("--max", dest="max_results", type=int, default=200)
    parser.add_argument("--mailto", default="")
    parser.add_argument("--run-date", default="")
    parser.add_argument("--keyless-only", action="store_true")
    parser.add_argument("--orx-limit", type=int, default=15)
    parser.add_argument("--orx-source", dest="orx_strategies", action="append",
                        choices=ORX_STRATEGIES,
                        help="Enrichment strategy to run; repeat. Default: all supported strategies.")
    parser.add_argument("--orx-prioritize", default="default",
                        choices=("historical", "default", "recency", "popular"))
    args = parser.parse_args(argv)
    return AcquisitionConfig(
        queries=tuple(args.query),
        output_dir=Path(args.output_dir),
        from_date=args.from_date,
        to_date=args.to_date,
        work_type=args.work_type,
        language=args.language,
        max_results=args.max_results,
        mailto=args.mailto,
        run_date=args.run_date,
        keyless_only=args.keyless_only,
        orx_limit=args.orx_limit,
        orx_strategies=tuple(args.orx_strategies or ORX_STRATEGIES),
        orx_prioritize=args.orx_prioritize,
    )


def main(argv=None) -> int:
    config = _parse_args(argv)
    acquire(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
