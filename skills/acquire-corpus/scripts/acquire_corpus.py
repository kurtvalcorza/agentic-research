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
import sys
import time
import urllib.parse
import urllib.request

OPENALEX_BASE = "https://api.openalex.org/works"
UA = "acquire-corpus/2.0 (agentic-research; mailto:{})"
SCHEMA_VERSION = "1.1"
ORX_TIMEOUT_SECONDS = 5.0
ORX_VERSION_TIMEOUT_SECONDS = 2.0
ENRICHMENT_FAILURE_BUDGET_SECONDS = 15.0
# Metadata completion for enriched hits goes to OpenAlex over HTTP. Each lookup has
# the same five-second deadline as an ``orx discover`` call and its failure wait is
# charged to the same run-level budget; one transport failure opens the completion
# circuit for the remainder of the run (FR-033 / SC-003).
METADATA_SUB_SOURCE = "openalex-metadata"
ARXIV_DOI_PREFIX = "10.48550/arxiv."
ARXIV_ID_RE = re.compile(
    r"^(?:arxiv:)?((?:\d{4}\.\d{4,5})|(?:[a-z\-]+(?:\.[A-Z]{2})?/\d{7}))(?:v\d+)?$",
    re.IGNORECASE,
)
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

    def __init__(self, reason: str, *, elapsed: float = 0.0, drops: Counter | None = None):
        super().__init__(reason)
        self.reason = reason
        self.elapsed = max(0.0, float(elapsed))
        # Normalization-drop counts accumulated before the failure was raised, so a
        # zero-normalizable response still reports every drop by count and reason
        # (FR-008 / SC-009).
        self.drops: Counter = Counter(drops or {})


@dataclass(frozen=True)
class KeylessSearchResult:
    """Records plus completion state for one keyless OpenAlex search.

    ``complete`` is False when paging stopped because of a transport or malformed-
    response failure rather than because the source was exhausted or the result
    limit was reached. ``records`` then holds whatever was accumulated before the
    failure, so a first-page failure is zero records but NOT a zero-result search.
    """

    records: list[dict]
    complete: bool = True
    failure_reason: str | None = None
    pages_fetched: int = 0


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


def keyless_openalex_search(
    query: str,
    config: AcquisitionConfig,
    *,
    http_json=None,
) -> KeylessSearchResult:
    """Mirror search_openalex.py's baseline record shape and fail-soft paging.

    Fail-soft means acquisition continues and the keyless exit code is unchanged;
    it does not mean the failure is forgotten. The returned completion state lets
    the acquisition record distinguish "returned zero" from "did not complete".
    """
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

    http_json = http_json or _http_json
    out: list[dict] = []
    seen = set()
    pages = 0
    while len(out) < config.max_results:
        url = f"{OPENALEX_BASE}?{urllib.parse.urlencode(params)}"
        page = pages + 1
        try:
            data = http_json(url, config.mailto, timeout=30.0)
        except Exception as exc:  # fail-soft: keep going keyless, but say so
            return KeylessSearchResult(
                out, complete=False, pages_fetched=pages,
                failure_reason=f"keyless-transport-failure:page-{page}:{type(exc).__name__}",
            )
        if not isinstance(data, dict):
            return KeylessSearchResult(
                out, complete=False, pages_fetched=pages,
                failure_reason=f"keyless-malformed-response:page-{page}:top-level-not-object",
            )
        pages = page
        results = data.get("results", [])
        if not isinstance(results, list):
            return KeylessSearchResult(
                out, complete=False, pages_fetched=pages,
                failure_reason=f"keyless-malformed-response:page-{page}:results-not-array",
            )
        if not results:
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
    return KeylessSearchResult(out, complete=True, pages_fetched=pages)


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
        raise EnrichmentFailure("zero-normalizable-records", drops=drops)
    return normalized, drops


def _arxiv_id(rec: dict) -> str:
    """Return the version-stripped arXiv identifier carried by an alphaXiv hit, or ''."""
    if rec.get("sub_source") != "alphaxiv":
        return ""
    match = ARXIV_ID_RE.match(str(rec.get("source_id", "")).strip())
    return match.group(1) if match else ""


def _candidate_urls(candidate: dict) -> list[str]:
    urls = []
    locations = list(candidate.get("locations") or [])
    primary = candidate.get("primary_location")
    if isinstance(primary, dict):
        locations.append(primary)
    for loc in locations:
        if not isinstance(loc, dict):
            continue
        for key in ("landing_page_url", "pdf_url"):
            value = loc.get(key)
            if isinstance(value, str) and value:
                urls.append(value.casefold())
    return urls


def _identity_corroborated(rec: dict, candidate: dict) -> bool:
    """True only when a stable identifier on the hit matches one on the candidate.

    Title similarity and a year window are NOT identity: two different studies can
    share both. Without an identifier match the completion stays unresolved
    (FR-031 / SC-014).
    """
    rec_doi = _clean_doi(rec.get("doi")).casefold()
    cand_doi = _clean_doi(candidate.get("doi")).casefold()
    if rec_doi and cand_doi and rec_doi == cand_doi:
        return True
    source_id = str(rec.get("source_id", "")).strip()
    cand_id = candidate.get("id")
    if (
        rec.get("sub_source") in {"openalex", "biorxiv"}
        and re.fullmatch(r"W\d+", source_id)
        and isinstance(cand_id, str)
        and cand_id.rstrip("/").rsplit("/", 1)[-1] == source_id
    ):
        return True
    arxiv = _arxiv_id(rec).casefold()
    if arxiv:
        if cand_doi == ARXIV_DOI_PREFIX + arxiv:
            return True
        needles = (f"arxiv.org/abs/{arxiv}", f"arxiv.org/pdf/{arxiv}")
        if any(n in url for url in _candidate_urls(candidate) for n in needles):
            return True
    return False


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
    if not direct and not _identity_corroborated(rec, candidate):
        # A title-search candidate must corroborate identity independently of
        # title/year; otherwise the hit remains unresolved.
        return False
    return True


def _is_not_found(exc: BaseException) -> bool:
    return getattr(exc, "code", None) == 404


def resolve_openalex_metadata(
    rec: dict,
    config: AcquisitionConfig,
    *,
    http_json=_http_json,
) -> dict | None:
    """Resolve authors/year conservatively through the keyless OpenAlex source.

    Exactly one bounded HTTP request per hit, addressed by a stable identifier
    (OpenAlex work id, DOI, or arXiv DOI). Returns ``None`` when the hit carries no
    stable identifier, when OpenAlex does not know it, or when the candidate does
    not match. Raises ``EnrichmentFailure`` (with ``elapsed``) on timeout or
    transport failure so the caller can charge the run-level failure budget.
    """
    source_id = rec.get("source_id", "")
    doi = _clean_doi(rec.get("doi"))
    arxiv = _arxiv_id(rec)
    direct = False

    if rec.get("sub_source") in {"openalex", "biorxiv"} and re.fullmatch(r"W\d+", source_id):
        direct = True
        url = f"{OPENALEX_BASE}/{urllib.parse.quote(source_id)}"
    elif doi:
        direct = True
        url = f"{OPENALEX_BASE}/doi:{urllib.parse.quote(doi)}"
    elif arxiv:
        # alphaXiv identifiers are arXiv identifiers; OpenAlex indexes arXiv
        # preprints under the DataCite DOI 10.48550/arXiv.<id>, a stable identifier.
        direct = True
        url = f"{OPENALEX_BASE}/doi:{urllib.parse.quote(ARXIV_DOI_PREFIX + arxiv)}"
    else:
        # No stable identifier on the hit means no title-search candidate could
        # corroborate identity; do not spend a request that cannot resolve.
        return None

    started = time.monotonic()
    try:
        data = http_json(url, config.mailto, timeout=ORX_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        elapsed = time.monotonic() - started
        raise EnrichmentFailure(
            "metadata-completion-timeout", elapsed=max(elapsed, ORX_TIMEOUT_SECONDS)
        ) from exc
    except Exception as exc:
        elapsed = time.monotonic() - started
        if _is_not_found(exc):
            return None  # the identifier is simply unknown to OpenAlex
        raise EnrichmentFailure("metadata-completion-transport-failure", elapsed=elapsed) from exc

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
    """Return (admitted, unresolved) while enforcing the safe-admission minimum.

    A resolver may return metadata, ``None`` (nothing verifiable), or raise
    ``EnrichmentFailure``; the failure reason becomes the unresolved reason so the
    record says WHY completion did not happen (budget/circuit/transport vs. no
    verifiable match).
    """
    try:
        metadata = resolver(rec, config)
    except EnrichmentFailure as exc:
        unresolved = dict(rec)
        unresolved["reason"] = exc.reason
        return None, unresolved
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


class _BoundedMetadataCompleter:
    """Wrap a metadata resolver with the run-level failure budget and a circuit.

    - Repeated lookups for the same stable identifier are served from a cache, so
      the same paper discovered by several strategies costs one request.
    - The first transport failure opens the ``openalex-metadata`` circuit for the
      rest of the run; no automatic retry (FR-033).
    - Every failure wait is charged to the shared ``failure_wait`` budget, and once
      the budget is exhausted no further completion request is attempted.
    Skipped hits are unresolved with a machine-readable reason, never admitted.
    """

    def __init__(self, resolver, budget: "_FailureBudget"):
        self._resolver = resolver
        self._budget = budget
        self._cache: dict[str, dict | None] = {}
        self.circuit_open = False
        self.attempts = 0

    @staticmethod
    def _key(rec: dict) -> str:
        doi = _clean_doi(rec.get("doi")).casefold()
        if doi:
            return f"doi:{doi}"
        arxiv = _arxiv_id(rec).casefold()
        if arxiv:
            return f"arxiv:{arxiv}"
        return f"{rec.get('sub_source')}:{str(rec.get('source_id', '')).strip()}"

    def __call__(self, rec: dict, config: AcquisitionConfig) -> dict | None:
        key = self._key(rec)
        if key in self._cache:
            return self._cache[key]
        if self.circuit_open:
            raise EnrichmentFailure("metadata-completion-skipped:circuit-open")
        if self._budget.exhausted:
            raise EnrichmentFailure("metadata-completion-skipped:run-failure-budget-exhausted")
        self.attempts += 1
        try:
            resolved = self._resolver(rec, config)
        except EnrichmentFailure as exc:
            self.circuit_open = True
            self._budget.charge(exc.elapsed)
            raise
        self._cache[key] = resolved
        return resolved


class _FailureBudget:
    """Cumulative enrichment failure wait for one run (SC-003: <= 15 s)."""

    def __init__(self, limit: float = ENRICHMENT_FAILURE_BUDGET_SECONDS):
        self.limit = limit
        self.waited = 0.0

    def charge(self, elapsed: float) -> None:
        self.waited += min(max(0.0, float(elapsed)), ORX_TIMEOUT_SECONDS)

    @property
    def exhausted(self) -> bool:
        return self.waited >= self.limit


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


def _loss_summary(candidates: list[dict], unresolved_records: list[dict]) -> dict:
    """FR-022 counts, derived from the records actually written (not re-declared)."""
    admitted_enriched = [c for c in candidates if c.get("source") == "orx"]
    return {
        "admitted_enriched_count": len(admitted_enriched),
        "admitted_doi_less_count": sum(
            1 for c in admitted_enriched if not _clean_doi(c.get("doi"))
        ),
        "unresolved_count": len(unresolved_records),
        "unresolved_missing_authors_count": sum(
            1 for u in unresolved_records
            if not (isinstance(u.get("authors"), list) and u.get("authors"))
        ),
        "unresolved_missing_year_count": sum(
            1 for u in unresolved_records if not isinstance(u.get("year"), int)
        ),
        "metadata_completion_skipped_count": sum(
            1 for u in unresolved_records
            if str(u.get("reason", "")).startswith("metadata-completion-")
        ),
    }


def _method_disclosure(entries: list[dict], config: AcquisitionConfig) -> dict:
    """FR-012: structured disclosure of opaque enriched ranking/truncation."""
    successful = [
        q for q in entries if q["backend"] == "orx" and q["outcome"] in {"answered", "empty"}
    ]
    return {
        "opaque_ranking_or_truncation": bool(successful),
        "affected_sub_sources": sorted({q["sub_source"] for q in successful}),
        "orx_limit": config.orx_limit if successful else None,
        "orx_prioritize": config.orx_prioritize if successful else None,
        "is_deduplication_step": False,
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
    incomplete = [q for q in record["queries"] if q["outcome"] == "incomplete"]
    if incomplete:
        lines += [
            "> **Keyless baseline incomplete:** one or more keyless OpenAlex searches stopped "
            "on a transport or malformed-response failure before the source was exhausted. "
            "Their returned counts are partial, not zero-result or complete answers; see the "
            "failure column and re-run those queries before treating acquisition as complete.",
            "",
        ]

    lines += [
        "| Backend | Source | Strategy | Query | Date | Outcome | Returned | Dropped | Admitted | Unresolved | Circuit | Version | Failure |",
        "|:--|:--|:--|:--|:--|:--|--:|--:|--:|--:|:--:|:--|:--|",
    ]
    for q in record["queries"]:
        lines.append(
            "| {backend} | {source} | {strategy} | {query} | {date} | {outcome} | "
            "{returned} | {dropped} | {admitted} | {unresolved} | {circuit} | {version} | "
            "{failure} |".format(
                backend=_md_cell(q["backend"]),
                source=_md_cell(q["sub_source"]),
                strategy=_md_cell(q["strategy"]),
                query=_md_cell(q["query"]),
                date=_md_cell(q["date"]),
                outcome=_md_cell(q["outcome"]),
                returned=q["returned_count"],
                dropped=sum(item["count"] for item in q["normalization_drops"]),
                admitted=q["admitted_enriched_count"],
                unresolved=q["unresolved_enrichment_count"],
                circuit="open" if q["circuit_open"] else "closed",
                version=_md_cell(q["orx_version"]),
                failure=_md_cell(q["failure_reason"]),
            )
        )
    dropped = [
        (q, item) for q in record["queries"] for item in q["normalization_drops"]
    ]
    if dropped:
        lines += ["", "### Normalization drops", ""]
        for q, item in dropped:
            lines.append(
                f"- `{q['strategy']}` / `{q['sub_source']}` — {q['query']}: "
                f"{item['count']} × `{item['reason']}`"
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

    loss = record["loss_summary"]
    lines += [
        "",
        "## Loss summary",
        "",
        f"- Admitted enriched records: **{loss['admitted_enriched_count']}**",
        f"- Admitted enriched records without a DOI: **{loss['admitted_doi_less_count']}**",
        f"- Unresolved enriched hits: **{loss['unresolved_count']}** "
        f"(missing verified authors: {loss['unresolved_missing_authors_count']}; "
        f"missing verified year: {loss['unresolved_missing_year_count']}; "
        f"metadata completion skipped by budget/circuit: "
        f"{loss['metadata_completion_skipped_count']})",
        "",
        "Admitted DOI-less records lack exact DOI matching downstream but retain their "
        "`source_id`, verified authors, and verified year, so `dedupe-records` keeps its "
        "author/year collision guards. Unresolved sparse hits are intentionally withheld from "
        "automatic deduplication to prevent title-only false merges; they need manual or "
        "later bibliographic resolution (title/author/year reverse lookup) before screening.",
    ]

    method = record["method_disclosure"]
    lines += ["", "## Method limits", ""]
    if method["opaque_ranking_or_truncation"]:
        lines.append(
            "- OpenResearch enrichment applied opaque ranking/truncation for sub-source(s) "
            + ", ".join(f"`{s}`" for s in method["affected_sub_sources"])
            + f" (`--limit {method['orx_limit']}`, `--prioritize {method['orx_prioritize']}`). "
            "This selection is a source-side method limit; it is **not** the review's "
            "deduplication step."
        )
    else:
        lines.append(
            "- No successful OpenResearch enrichment contributed to this run, so no opaque "
            "source-side ranking/truncation applies."
        )
    lines += [
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
    budget = _FailureBudget()
    completer = _BoundedMetadataCompleter(metadata_resolver, budget)

    for q_index, query in enumerate(config.queries, 1):
        query = query.strip()
        keyless_result = keyless_search(query, config)
        if isinstance(keyless_result, KeylessSearchResult):
            keyless = list(keyless_result.records)
            keyless_complete = keyless_result.complete
            keyless_failure = keyless_result.failure_reason
        else:  # a plain record list means a completed search
            keyless = list(keyless_result)
            keyless_complete = True
            keyless_failure = None
        candidates.extend(keyless)
        _write_jsonl(raw_dir / f"openalex-q{q_index:03d}.jsonl", keyless)
        if keyless_complete:
            keyless_outcome = "answered" if keyless else "empty"
            keyless_failure = None
        else:
            # Neither a genuine zero-result search nor a fully answered one: the
            # transport stopped before the source was exhausted (P1-3).
            keyless_outcome = "incomplete"
            keyless_failure = keyless_failure or "keyless-transport-failure"
        entries.append(
            _query_entry(
                backend="keyless",
                sub_source="openalex",
                strategy="search",
                query=query,
                run_date=run_date,
                outcome=keyless_outcome,
                returned_count=len(keyless),
                failure_reason=keyless_failure,
            )
        )

        if not executable:
            continue

        for strategy in config.orx_strategies:
            sub_source = STRATEGY_SUB_SOURCE[strategy]
            if circuits[sub_source] or budget.exhausted:
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
                budget.charge(exc.elapsed)
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
                        drops=exc.drops,
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
                    rec, config, resolver=completer
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
        "loss_summary": _loss_summary(candidates, unresolved_records),
        "method_disclosure": _method_disclosure(entries, config),
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
    record = acquire(config)
    # Keep the pre-feature keyless diagnostic: say on stderr when a keyless search
    # stopped early. Exit semantics are unchanged (FR-003); the canonical record
    # already carries the outcome, so this is a courtesy, not the source of truth.
    for q in record["queries"]:
        if q["backend"] == "keyless" and q["outcome"] == "incomplete":
            sys.stderr.write(
                f"[search] stopped: {q['query']!r} {q['failure_reason']} "
                f"(returned {q['returned_count']} before the failure)\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
