#!/usr/bin/env python3
"""
grade_profile.py — check a GRADE certainty record and generate the evidence profile
and summary-of-findings tables from it. Standard library only.

WHAT THIS CHECKS
  Completeness, internal consistency, and legality under GRADE's own rules:
  every downgrade domain present, judgments in whole steps, the starting level
  anchored to the predominant design, the certainty arithmetic adding up, upgrades
  applied only where GRADE permits them, and — with --rob — every study cited as
  confirmed actually resolving to a confirmed appraisal.

WHAT THIS CANNOT CHECK
  Full GRADE for diagnostic test accuracy. A `dta` body starts HIGH here, per GRADE
  guidance, but published GRADE-DTA rates SENSITIVITY and SPECIFICITY as separate
  outcomes each with their own certainty. This check grades one certainty per
  result, so a DTA profile here is a simplification the reviewer must be aware of.

  Without --rob, whether design_mix describes the studies actually cited. The
  totals must match study_ids, but only a supplied appraisal record lets the
  DISTRIBUTION be verified -- and the distribution is what sets the starting
  level. A heuristic-basis record (rapid reviews) is therefore weaker evidence
  than a confirmed one, which is part of why systematic and umbrella reviews may
  not use it.

  Whether a judgment was RIGHT. That "inconsistency: serious" was the correct call
  is a matter of expertise this script has no access to. A clean result means the
  profile is complete, legal and arithmetically sound — nothing more. It also
  cannot tell whether the studies cited exist, only whether they appear in the
  appraisal record you supplied.

INPUT — a JSON record (file arg or stdin). See the skill for the full schema:
{
  "schema_version": "1.0",
  "review_type": "systematic",          # systematic|scoping|rapid|umbrella|narrative
  "synthesis_mode": "outcome",          # outcome (true GRADE) | theme (SWiM adaptation)
  "results": [{
    "id": "O1", "label": "...",
    "study_ids": ["P1", "P3"],
    "design_mix": {"rct": 4, "nrsi": 0, "observational": 0, "case_series": 0},
    "starting_level": "high",
    "domains": {
      "risk_of_bias":     {"rating": 0, "basis": "confirmed_rob", "note": "..."},
      "inconsistency":    {"rating": -1, "note": "..."},
      "indirectness":     {"rating": 0, "note": "..."},
      "imprecision":      {"rating": 0, "note": "..."},
      "publication_bias": {"rating": 0, "note": "..."}
    },
    "final": "moderate",
    "certainty_statement": "..."
  }]
}

USAGE
  python grade_profile.py record.json
  python grade_profile.py record.json --rob risk-of-bias.json --strict
  echo '{...}' | python grade_profile.py --strict

EXIT CODES
  0 clean, or violations found without --strict
  1 method violation under --strict
  2 malformed input — the record could not be read, so no artifact is emitted
"""
from __future__ import annotations

import argparse
import json
import math
import sys

SCHEMA_VERSIONS = {"1.0"}

REVIEW_TYPES = {"systematic", "scoping", "rapid", "umbrella", "narrative"}
SYNTHESIS_MODES = {"outcome", "theme"}

# Review types whose risk-of-bias domain must rest on confirmed appraisal.
# Rapid reviews may use the heuristic when the shortcut is disclosed; scoping and
# narrative reviews do not grade certainty at all.
CONFIRMED_ROB_REQUIRED = {"systematic", "umbrella"}

LEVELS = {"very_low": 1, "low": 2, "moderate": 3, "high": 4}
LEVEL_NAMES = {v: k for k, v in LEVELS.items()}
SYMBOLS = {4: "⊕⊕⊕⊕", 3: "⊕⊕⊕◯", 2: "⊕⊕◯◯", 1: "⊕◯◯◯"}

DOMAINS = ("risk_of_bias", "inconsistency", "indirectness", "imprecision", "publication_bias")
UPGRADES = ("large_effect", "dose_response", "opposing_confounding")
DESIGNS = ("rct", "nrsi", "observational", "dta", "case_series")

# Starting level implied by the design that PREDOMINATES in the body of evidence.
# Anchoring to the predominant design (rather than to the strongest single study
# present) is the whole point: one randomized trial among eight cross-sectional
# studies does not start the body at HIGH.
DESIGN_START = {"rct": "high", "nrsi": "low", "observational": "low",
                # Diagnostic test accuracy: GRADE rates a body of accuracy studies
                # as starting HIGH, not low — mapping it onto "observational" would
                # understate certainty by two levels.
                #   GRADE Guidance 31, J Clin Epidemiol 2021 (S0895-4356(21)00117-7)
                #   Schunemann et al., J Clin Epidemiol 2019 (S0895-4356(18)31069-2)
                "dta": "high",
                "case_series": "very_low"}

# Designs the appraisal taxonomy can express. `case_series` has no risk-of-bias
# instrument, so a body containing case series cannot be fully traced through --rob
# and its distribution cannot be reconciled — stated rather than silently mismatched.
APPRAISABLE_DESIGNS = ("rct", "nrsi", "observational", "dta")

# Mirrors rob_appraisal.STUDY_KEYS; the conformance test asserts they stay equal.
APPRAISAL_STUDY_KEYS = {"id", "design", "instrument", "result_assessed", "domains",
                        "evidence", "overall", "overall_justification",
                        "confirmed_by", "confirmed_at"}

RECORD_KEYS = {"schema_version", "review_type", "synthesis_mode",
               "streamlined_method_disclosed", "results"}
RESULT_KEYS = {"id", "label", "study_ids", "design_mix", "starting_level",
               "starting_level_justification", "domains", "upgrades", "final",
               "certainty_statement", "appraised_result"}
DOMAIN_KEYS = {"rating", "note", "basis", "coherence_justification"}

ROB_BASES = {"confirmed_rob", "heuristic"}


class InputError(ValueError):
    """The record cannot be read. Fails closed: exit 2, no artifact emitted."""


# --- input coercion (shared contract; mirrored in prisma_flow.py) -------------

def _int(v, name: str) -> int:
    """Coerce a count, rejecting anything that is not a whole, non-negative JSON number.

    A quoted count such as "4" is malformed input, not a number to parse — silent
    coercion is the behaviour the fail-closed principle forbids.
    """
    if isinstance(v, bool):
        raise InputError(f"{name}: expected an integer count, got boolean {v!r}")
    if isinstance(v, int):
        iv = v
    elif isinstance(v, float):
        if not math.isfinite(v):
            raise InputError(f"{name}: count must be a finite number, got {v!r}")
        if not v.is_integer():
            raise InputError(f"{name}: count must be a whole number, got {v!r}")
        iv = int(v)
    else:
        raise InputError(f"{name}: count must be a JSON number, got {v!r}")
    if iv < 0:
        raise InputError(f"{name}: count must be non-negative, got {iv}")
    return iv


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

    Never coerce with str() and never test bare truthiness: str({}) is "{}" and
    `True` is truthy, so either would let malformed input satisfy a check that only
    asks "is this non-empty?".
    """
    if v is None:
        return ""
    if not isinstance(v, str):
        raise InputError(f"{name}: expected a string, got {type(v).__name__} {v!r}")
    return v.strip()


def _no_unknown_keys(d: dict, allowed: set, ctx: str) -> None:
    """Reject unrecognised keys rather than ignoring them.

    A misspelled domain name must not read as an absent domain: that would report
    the right verdict for the wrong reason, and the reviewer would 'fix' the wrong
    thing and get a pass.
    """
    unknown = sorted(set(d) - allowed)
    if unknown:
        raise InputError(f"{ctx}: unrecognised key(s) {', '.join(repr(k) for k in unknown)} "
                         f"(expected one of: {', '.join(sorted(allowed))})")


def _rating(v, ctx: str) -> int:
    """GRADE moves in whole steps. There is no half-downgrade."""
    if isinstance(v, bool) or not isinstance(v, int):
        raise InputError(f"{ctx}: rating must be the integer 0, -1 or -2, got {v!r}")
    if v not in (0, -1, -2):
        raise InputError(f"{ctx}: rating must be 0, -1 or -2 (whole steps only), got {v}")
    return v


def _upgrade(v, ctx: str) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or v not in (0, 1, 2):
        raise InputError(f"{ctx}: upgrade must be the integer 0, 1 or 2, got {v!r}")
    return v


# --- parsing -----------------------------------------------------------------

def parse(raw: dict) -> dict:
    """Validate structure and vocabulary. Raises InputError (exit 2) on malformed input."""
    _obj(raw, "record")

    # An aggregate certainty across results is not a thing GRADE defines. Rejecting
    # the key makes the error unrepresentable rather than merely discouraged.
    for key in ("overall_certainty", "overall_grade", "weighted_certainty", "aggregate_certainty"):
        if key in raw:
            raise InputError(
                f"record: {key!r} is not permitted — GRADE defines no certainty aggregated "
                f"across results. Report each result's certainty separately.")

    _no_unknown_keys(raw, RECORD_KEYS, "record")

    version = raw.get("schema_version")
    if version is None:
        raise InputError("record: 'schema_version' is required "
                         f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})")
    # isinstance FIRST: `[] in {"1.0"}` raises TypeError (unhashable), which would
    # surface as a traceback and exit 1 instead of the documented exit 2.
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(f"record: unrecognised schema_version {version!r} "
                         f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})")

    review_type = raw.get("review_type")
    if not isinstance(review_type, str) or review_type not in REVIEW_TYPES:
        raise InputError(f"record: review_type must be one of "
                         f"{', '.join(sorted(REVIEW_TYPES))}, got {review_type!r}")

    mode = raw.get("synthesis_mode")
    if not isinstance(mode, str) or mode not in SYNTHESIS_MODES:
        raise InputError(f"record: synthesis_mode must be 'outcome' or 'theme', got {mode!r}")

    results = raw.get("results")
    if not isinstance(results, list):
        raise InputError("record: 'results' must be a list")
    if not results:
        # Fail closed: nothing to check is a failure, not a pass.
        raise InputError("record: 'results' is empty — there is nothing to check")

    seen_ids = set()
    parsed = []
    for i, r in enumerate(results):
        parsed.append(_parse_result(r, i, seen_ids))

    return {"schema_version": version, "review_type": review_type, "synthesis_mode": mode,
            "streamlined_method_disclosed": _opt_str(
                raw.get("streamlined_method_disclosed"), "record.streamlined_method_disclosed"),
            "results": parsed}


def _parse_result(r, i: int, seen_ids: set) -> dict:
    ctx = f"results[{i}]"
    _obj(r, ctx)
    _no_unknown_keys(r, RESULT_KEYS, ctx)

    rid = _str(r.get("id"), f"{ctx}.id")
    if rid in seen_ids:
        raise InputError(f"{ctx}.id: duplicate result id {rid!r} — every reference to it "
                         f"would be ambiguous")
    seen_ids.add(rid)
    ctx = f"result {rid}"

    study_ids = r.get("study_ids")
    if not isinstance(study_ids, list) or not study_ids:
        raise InputError(f"{ctx}.study_ids: expected a non-empty list")
    for s in study_ids:
        _str(s, f"{ctx}.study_ids")
    dupes = sorted({s for s in study_ids if study_ids.count(s) > 1})
    if dupes:
        raise InputError(f"{ctx}.study_ids: duplicate identifier(s) "
                         f"{', '.join(repr(d) for d in dupes)}")

    design_mix = _obj(r.get("design_mix", {}), f"{ctx}.design_mix")
    _no_unknown_keys(design_mix, set(DESIGNS), f"{ctx}.design_mix")
    mix = {d: _int(design_mix.get(d, 0), f"{ctx}.design_mix.{d}") for d in DESIGNS}
    if sum(mix.values()) == 0:
        raise InputError(f"{ctx}.design_mix: no studies recorded — the starting level "
                         f"cannot be anchored")
    # The design mix determines the starting certainty level, so it must describe
    # the body actually cited. Left unchecked, `{"rct": 100}` over four
    # observational studies starts the body at HIGH while the generated tables
    # faithfully report four studies, and every downstream number inherits it.
    if sum(mix.values()) != len(study_ids):
        raise InputError(
            f"{ctx}.design_mix: counts total {sum(mix.values())} but {len(study_ids)} "
            f"studies are cited in study_ids — the mix must describe the body it "
            f"anchors, since it determines the starting level")

    start = r.get("starting_level")
    if not isinstance(start, str) or start not in LEVELS:
        raise InputError(f"{ctx}.starting_level: must be one of "
                         f"{', '.join(LEVELS)}, got {start!r}")
    final = r.get("final")
    if not isinstance(final, str) or final not in LEVELS:
        raise InputError(f"{ctx}.final: must be one of {', '.join(LEVELS)}, got {final!r}")

    domains_raw = _obj(r.get("domains", {}), f"{ctx}.domains")
    # Unknown domain key -> malformed (exit 2). Missing domain -> violation (exit 1),
    # handled in check(). The distinction is deliberate.
    _no_unknown_keys(domains_raw, set(DOMAINS), f"{ctx}.domains")
    domains = {}
    for name, d in domains_raw.items():
        dctx = f"{ctx}.domains.{name}"
        _obj(d, dctx)
        allowed = DOMAIN_KEYS if name == "risk_of_bias" else DOMAIN_KEYS - {"basis", "coherence_justification"}
        _no_unknown_keys(d, allowed, dctx)
        entry = {"rating": _rating(d.get("rating"), dctx),
                 "note": _opt_str(d.get("note"), f"{dctx}.note")}
        if name == "risk_of_bias":
            basis = d.get("basis")
            if not isinstance(basis, str) or basis not in ROB_BASES:
                raise InputError(f"{dctx}.basis: must be 'confirmed_rob' or 'heuristic', "
                                 f"got {basis!r}")
            entry["basis"] = basis
            entry["coherence_justification"] = _opt_str(
                d.get("coherence_justification"), f"{dctx}.coherence_justification")
        domains[name] = entry

    upgrades_raw = _obj(r.get("upgrades", {}), f"{ctx}.upgrades")
    # The closed set is what makes "importance of findings" unrepresentable — it is
    # not a GRADE upgrade reason, and certainty must never rise because a result matters.
    _no_unknown_keys(upgrades_raw, set(UPGRADES), f"{ctx}.upgrades")
    upgrades = {u: _upgrade(upgrades_raw.get(u, 0), f"{ctx}.upgrades.{u}") for u in UPGRADES}

    return {"id": rid, "label": _opt_str(r.get("label"), f"{ctx}.label") or rid, "study_ids": study_ids,
            "design_mix": mix, "starting_level": start,
            "starting_level_justification": _opt_str(
                r.get("starting_level_justification"), f"{ctx}.starting_level_justification"),
            "domains": domains, "upgrades": upgrades, "final": final,
            "certainty_statement": _opt_str(r.get("certainty_statement"),
                                            f"{ctx}.certainty_statement"),
            "appraised_result": _opt_str(r.get("appraised_result"),
                                         f"{ctx}.appraised_result")}


# --- appraisal record (read via --rob; NEVER imported from the sibling skill) --

# This script is standalone by design (it never imports the appraisal skill), so it
# must validate the appraisal record itself rather than assume the other check ran.
# A record carrying only ids and confirmations is a STUB, not an appraisal, and must
# not be able to fabricate backing for `basis: confirmed_rob`.
#
# Duplicated deliberately, per the same reasoning as the coercion helpers; the
# conformance test keeps it aligned with rob_appraisal.py.
APPRAISAL_DESIGN_INSTRUMENT = {"rct": "rob2", "nrsi": "robins_i",
                               "observational": "nos", "dta": "quadas2"}
INSTRUMENT_OVERALLS = {
    "rob2": {"low", "some_concerns", "high"},
    "robins_i": {"low", "moderate", "serious", "critical", "no_information"},
    "nos": {"low", "moderate", "high"},
    "quadas2": {"low", "unclear", "high"},
}
# The EXACT domain names, not merely how many. Checking cardinality let a record of
# five arbitrary keys ({"a": null, "b": false, ...}) satisfy an RCT appraisal and
# fabricate confirmed backing — cardinality is not completeness.
INSTRUMENT_DOMAINS = {
    "rob2": ("randomization", "deviations", "missing_data", "measurement",
             "selection_of_result"),
    "robins_i": ("confounding", "participant_selection", "intervention_classification",
                 "deviations", "missing_data", "outcome_measurement", "selection_of_result"),
    "nos": ("selection", "comparability", "outcome_or_exposure"),
    "quadas2": ("patient_selection", "index_test", "reference_standard", "flow_and_timing"),
}
NOS_MAX = {"selection": 4, "comparability": 2, "outcome_or_exposure": 3}
QUADAS_APPLICABILITY = ("patient_selection", "index_test", "reference_standard")
HIGH_RISK_OVERALLS = {"high", "serious", "critical"}

# Which design each instrument appraises — used to reconcile design_mix against the
# studies actually referenced, not merely against how many there are.
INSTRUMENT_DESIGN = {v: k for k, v in APPRAISAL_DESIGN_INSTRUMENT.items()}


def _validate_appraisal_domains(instrument: str, domains: dict, ctx: str) -> None:
    """Validate the instrument's EXACT domain names and value vocabulary.

    This duplicates rob_appraisal.py's schema, deliberately: constitution
    Principle III forbids importing across skills, and this check must be usable
    standalone. `test_coercion_conformance.py` asserts the two definitions stay
    identical, so the duplication cannot drift.

    Validating only the domain COUNT was not enough: five arbitrary keys satisfied
    it, so the two checks disagreed about the same file — rob_appraisal rejected it
    while this one reported clean.
    """
    expected = INSTRUMENT_DOMAINS[instrument]
    missing = [d for d in expected if d not in domains]
    extra = sorted(set(domains) - set(expected))
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missing {', '.join(missing)}")
        if extra:
            parts.append(f"unrecognised {', '.join(extra)}")
        raise InputError(f"{ctx}.domains: {instrument} defines "
                         f"{', '.join(expected)} — {'; '.join(parts)}")

    for name, value in domains.items():
        dctx = f"{ctx}.domains.{name}"
        if instrument == "nos":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InputError(f"{dctx}: expected an integer star count, got {value!r}")
            if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
                raise InputError(f"{dctx}: star count must be a whole number, got {value!r}")
            if not 0 <= int(value) <= NOS_MAX[name]:
                raise InputError(f"{dctx}: star count must be between 0 and "
                                 f"{NOS_MAX[name]}, got {value!r}")
        elif instrument == "quadas2":
            if not isinstance(value, dict):
                raise InputError(f"{dctx}: expected an object with a risk_of_bias "
                                 f"judgment, got {type(value).__name__} {value!r}")
            # Only the first three domains carry applicability; an applicability key
            # on flow_and_timing is illegal, and a misspelled key alongside a correct
            # one would otherwise be read straight past by .get().
            allowed = {"risk_of_bias"} | ({"applicability"}
                                          if name in QUADAS_APPLICABILITY else set())
            _no_unknown_keys(value, allowed, dctx)
            rob = value.get("risk_of_bias")
            if not isinstance(rob, str) or rob not in INSTRUMENT_OVERALLS["quadas2"]:
                raise InputError(f"{dctx}.risk_of_bias: must be one of "
                                 f"{', '.join(sorted(INSTRUMENT_OVERALLS['quadas2']))}, "
                                 f"got {rob!r}")
            if name in QUADAS_APPLICABILITY:
                app = value.get("applicability")
                if not isinstance(app, str) or app not in INSTRUMENT_OVERALLS["quadas2"]:
                    raise InputError(f"{dctx}.applicability: must be one of "
                                     f"{', '.join(sorted(INSTRUMENT_OVERALLS['quadas2']))}, "
                                     f"got {app!r}")
        else:
            if not isinstance(value, str) or value not in INSTRUMENT_OVERALLS[instrument]:
                raise InputError(f"{dctx}: must be one of "
                                 f"{', '.join(sorted(INSTRUMENT_OVERALLS[instrument]))} "
                                 f"for {instrument}, got {value!r}")


# Severity ranks for the overall-vs-worst-domain check, mirroring rob_appraisal.py.
# None means "not orderable" (ROBINS-I no_information) and is excluded from the
# comparison rather than guessed at.
INSTRUMENT_SEVERITY = {
    "rob2": {"low": 0, "some_concerns": 1, "high": 2},
    "robins_i": {"low": 0, "moderate": 1, "serious": 2, "critical": 3, "no_information": None},
    "quadas2": {"low": 0, "unclear": 1, "high": 2},
    "nos": {"low": 0, "moderate": 1, "high": 2},
}
NOS_BANDS = ((7, "low"), (4, "moderate"), (0, "high"))


def _nos_band(total: int) -> str:
    for threshold, band in NOS_BANDS:
        if total >= threshold:
            return band
    return "high"


def _validate_appraisal_overall(instrument, domains, overall, justification, ctx):
    """The overall must not be more favourable than the study's worst domain.

    Ported from rob_appraisal.py so the two checks agree about the same file. An
    appraisal declaring `overall: low` over a `high` domain is invalid there and was
    being consumed here as favourable backing, letting a zero risk-of-bias downgrade
    stand on an appraisal its own instrument rejects.
    """
    if justification:
        return                                  # a recorded override, as the sibling allows

    if instrument == "nos":
        total = sum(domains.get(d, 0) for d in INSTRUMENT_DOMAINS["nos"])
        band = _nos_band(int(total))
        if overall != band:
            raise InputError(
                f"{ctx}: Newcastle-Ottawa total is {int(total)}/9, which bands as "
                f"'{band}', but overall is '{overall}' and no overall_justification "
                f"is recorded — rob_appraisal.py rejects this record")
        return

    ranks = {}
    for name, value in domains.items():
        v = value["risk_of_bias"] if instrument == "quadas2" else value
        ranks[name] = INSTRUMENT_SEVERITY[instrument][v]
    ordered = {d: r for d, r in ranks.items() if r is not None}
    no_info = [d for d, r in ranks.items() if r is None]

    # Filtering out the unorderable domains must not silently exonerate them.
    # ROBINS-I 'no_information' is dropped from the worst-domain comparison because
    # it cannot be ranked — but an overall of 'low' while a domain reports nothing
    # is a claim the record has to justify. Absence of evidence is not evidence of
    # low risk, and rob_appraisal.py rejects exactly this.
    if no_info and overall == "low":
        raise InputError(
            f"{ctx}: overall 'low' while domain(s) {', '.join(no_info)} report no "
            f"information, and no overall_justification is recorded — absence of "
            f"evidence is not evidence of low risk, and rob_appraisal.py rejects "
            f"this record")

    if not ordered:
        return
    worst_domain = max(ordered, key=lambda d: ordered[d])
    worst = ordered[worst_domain]
    declared = INSTRUMENT_SEVERITY[instrument][overall]
    if declared is not None and declared < worst:
        shown = domains[worst_domain]
        if instrument == "quadas2":
            shown = shown["risk_of_bias"]
        raise InputError(
            f"{ctx}: overall '{overall}' is more favourable than its worst domain "
            f"({worst_domain} = '{shown}') and no overall_justification is recorded "
            f"— rob_appraisal.py rejects this record, so it cannot back a "
            f"confirmed_rob basis")


def parse_appraisal(raw: dict) -> dict:
    """Return {study_id: {'overall': str, 'confirmed': bool}} from an appraisal record.

    Validates the fields it consumes. A malformed appraisal record MUST NOT be able
    to back a `confirmed_rob` basis: that would defeat the traceability the human
    gate exists to provide.
    """
    _obj(raw, "appraisal record")
    # Closed root schema, mirroring rob_appraisal.py. Without it a misspelled root
    # field ("studiez") is malformed input there and silently ignored here — the
    # acceptance divergence this whole class of finding is about.
    _no_unknown_keys(raw, {"schema_version", "studies"}, "appraisal record")
    version = raw.get("schema_version")
    if not isinstance(version, str) or version not in SCHEMA_VERSIONS:
        raise InputError(f"appraisal record: unrecognised or missing schema_version {version!r}")
    studies = raw.get("studies")
    if not isinstance(studies, list) or not studies:
        raise InputError("appraisal record: 'studies' is missing or empty")
    out = {}
    for i, s in enumerate(studies):
        ctx = f"appraisal studies[{i}]"
        _obj(s, ctx)
        # Principle IV: unknown keys are rejected, never ignored. Without this a
        # misspelled field in the appraisal record is malformed input to
        # rob_appraisal.py and invisible here — the same disagreement class that
        # produced the last three rounds of findings.
        _no_unknown_keys(s, APPRAISAL_STUDY_KEYS, ctx)
        sid = _str(s.get("id"), f"{ctx}.id")
        result_assessed = _str(s.get("result_assessed"), f"{ctx}.result_assessed")

        # A real appraisal states what was appraised and how. Without this, a stub
        # of {id, overall, confirmed_by, confirmed_at} would satisfy a
        # `confirmed_rob` claim while containing no appraisal at all.
        design = s.get("design")
        if not isinstance(design, str) or design not in APPRAISAL_DESIGN_INSTRUMENT:
            raise InputError(f"{ctx}.design: must be one of "
                             f"{', '.join(sorted(APPRAISAL_DESIGN_INSTRUMENT))}, got {design!r}")
        instrument = s.get("instrument")
        expected = APPRAISAL_DESIGN_INSTRUMENT[design]
        if instrument != expected:
            raise InputError(f"{ctx}.instrument: design '{design}' calls for "
                             f"'{expected}', got {instrument!r}")

        domains = s.get("domains")
        if not isinstance(domains, dict) or not domains:
            raise InputError(f"{ctx}.domains: a confirmed appraisal must record its "
                             f"domain judgments, got {domains!r}")
        _validate_appraisal_domains(instrument, domains, ctx)

        overall = s.get("overall")
        if not isinstance(overall, str) or overall not in INSTRUMENT_OVERALLS[instrument]:
            raise InputError(f"{ctx}.overall: must be one of "
                             f"{', '.join(sorted(INSTRUMENT_OVERALLS[instrument]))} "
                             f"for {instrument}, got {overall!r}")

        _validate_appraisal_overall(instrument, domains, overall,
                                    _opt_str(s.get("overall_justification"),
                                             f"{ctx}.overall_justification"), ctx)

        # Strings only — str({}) would be "{}", truthy and non-empty, and would
        # silently satisfy the confirmation test.
        by = _opt_str(s.get("confirmed_by"), f"{ctx}.confirmed_by")
        at = _opt_str(s.get("confirmed_at"), f"{ctx}.confirmed_at")

        # Identity is (study, result): an appraisal targets one result, so a study
        # contributing to two outcomes has two entries with different judgments.
        key = (sid, result_assessed)
        if key in out:
            raise InputError(f"appraisal record: study {sid!r} is appraised twice for "
                             f"result {result_assessed!r}")
        prior = next((v["design"] for k, v in out.items() if k[0] == sid), None)
        if prior is not None and prior != design:
            raise InputError(f"appraisal record: study {sid!r} is appraised as both "
                             f"{prior!r} and {design!r} — a study has one design")
        out[key] = {"overall": overall, "design": design, "instrument": instrument,
                    "result_assessed": result_assessed, "confirmed": bool(by and at)}
    return out


def predominant_design(mix: dict) -> str:
    """The design the body mostly consists of; ties resolve to the WEAKER design.

    Strength is derived from DESIGN_START rather than a separate hand-maintained
    order, so adding a design cannot leave this function stale. A hand-kept order
    dict is exactly what raised KeyError when 'dta' was added.
    """
    def rank(design):
        return LEVELS[DESIGN_START[design]]
    # Highest count wins; on a tie the weaker starting level wins; then name, so the
    # result is deterministic.
    return max(mix.items(), key=lambda kv: (kv[1], -rank(kv[0]), kv[0]))[0]


# --- checking ----------------------------------------------------------------

def check(rec: dict, appraisal: dict | None, rob_supplied: bool) -> list[str]:
    """Return a list of method violations (empty = clean)."""
    errs: list[str] = []
    rtype = rec["review_type"]

    for r in rec["results"]:
        rid = r["id"]

        # Rule 1 — every domain present. A missing domain is reported by name; it is
        # NEVER read as a judgment of "no concern".
        missing = [d for d in DOMAINS if d not in r["domains"]]
        if missing:
            errs.append(f"result {rid}: missing downgrade domain(s) {', '.join(missing)} — "
                        f"an absent domain is not a judgment of 'no concern'")
            continue  # arithmetic below would be meaningless

        # Rule 4 — starting level anchored to the predominant design.
        pred = predominant_design(r["design_mix"])
        expected = DESIGN_START[pred]
        if r["starting_level"] != expected and not r["starting_level_justification"]:
            errs.append(
                f"result {rid}: starting_level '{r['starting_level']}' does not match the "
                f"predominant design '{pred}' (n={r['design_mix'][pred]} of "
                f"{sum(r['design_mix'].values())}), which implies '{expected}'. "
                f"Record a starting_level_justification if the deviation is intended")

        downgrades = sum(d["rating"] for d in r["domains"].values())
        upgrade_total = sum(r["upgrades"].values())

        # Rules 5/6 — upgrades are for non-randomized bodies with no downgrade applied.
        if upgrade_total:
            if pred == "rct":
                errs.append(f"result {rid}: upgrades applied to a body of randomized trials — "
                            f"GRADE permits upgrading only for non-randomized evidence")
            if downgrades < 0:
                applied = [n for n, d in r["domains"].items() if d["rating"] < 0]
                errs.append(f"result {rid}: upgrades applied while downgrade(s) remain "
                            f"({', '.join(applied)}) — GRADE does not permit raising certainty "
                            f"over unresolved serious concerns")

        # Rule 5 (arithmetic) — the reconciliation, reported like the flow diagram's.
        computed = max(1, min(4, LEVELS[r["starting_level"]] + downgrades + upgrade_total))
        declared = LEVELS[r["final"]]
        if computed != declared:
            errs.append(
                f"result {rid}: {r['starting_level']}({LEVELS[r['starting_level']]}) "
                f"{downgrades:+d} downgrades {upgrade_total:+d} upgrades = "
                f"{LEVEL_NAMES[computed]}({computed}), but final = "
                f"{r['final']}({declared}) — difference of {declared - computed:+d}")

        # Rule 9 — the basis for the risk-of-bias domain.
        basis = r["domains"]["risk_of_bias"]["basis"]
        if basis == "heuristic":
            if rtype in CONFIRMED_ROB_REQUIRED:
                errs.append(f"result {rid}: risk_of_bias basis is 'heuristic', but a "
                            f"{rtype} review requires confirmed appraisal")
            elif rtype == "rapid" and not rec["streamlined_method_disclosed"]:
                errs.append(f"result {rid}: risk_of_bias basis is 'heuristic' for a rapid "
                            f"review without 'streamlined_method_disclosed' — the shortcut "
                            f"must be stated")
        else:
            # Rule 11 — a confirmed basis claimed with nothing to check it against
            # is not accepted on trust.
            if not rob_supplied:
                errs.append(f"result {rid}: risk_of_bias basis is 'confirmed_rob' but no "
                            f"appraisal record was supplied (--rob) — the claim cannot be "
                            f"taken on trust")
            elif appraisal is not None:
                errs.extend(_check_traceability(r, appraisal))

    return errs


def _check_traceability(r: dict, appraisal: dict) -> list[str]:
    """Rules 10 and 12 — references resolve to the RIGHT appraisal, and the body
    judgment coheres with them.

    An appraisal targets one result. Resolving on study id alone let a study
    appraised for mortality back a certainty rating about quality of life, which is
    the wrong risk-of-bias evidence for that claim.
    """
    errs = []
    rid = r["id"]
    target = r["appraised_result"]

    if not target:
        return [f"result {rid}: 'appraised_result' is required when the risk-of-bias "
                f"basis is 'confirmed_rob' — it names which appraised result backs "
                f"this certainty rating, since an appraisal targets one result, not "
                f"a whole study"]

    known_targets = sorted({k[1] for k in appraisal})
    if target not in known_targets:
        return [f"result {rid}: appraised_result {target!r} does not appear in the "
                f"appraisal record (it appraises: {', '.join(repr(t) for t in known_targets)})"]

    resolved, unresolved, wrong_target = [], [], []
    for sid in r["study_ids"]:
        if (sid, target) in appraisal:
            resolved.append(sid)
        elif any(k[0] == sid for k in appraisal):
            others = sorted(k[1] for k in appraisal if k[0] == sid)
            wrong_target.append(f"{sid} (appraised for {', '.join(repr(o) for o in others)}, "
                                f"not {target!r})")
        else:
            near = {k[0].lower().strip(): k[0] for k in appraisal}.get(sid.lower().strip())
            unresolved.append(f"{sid!r} (appraisal has {near!r} — identifiers are "
                              f"matched exactly)" if near else repr(sid))

    if unresolved:
        errs.append(f"result {rid}: study reference(s) not found in the appraisal "
                    f"record: {'; '.join(unresolved)}")
    if wrong_target:
        errs.append(f"result {rid}: study reference(s) appraised for a DIFFERENT "
                    f"result: {'; '.join(wrong_target)} — the wrong risk-of-bias "
                    f"evidence cannot back this certainty rating")

    unconfirmed = [s for s in resolved if not appraisal[(s, target)]["confirmed"]]
    if unconfirmed:
        errs.append(f"result {rid}: study reference(s) {', '.join(unconfirmed)} have no "
                    f"human confirmation, so they cannot back a 'confirmed_rob' basis")

    # Design distribution, reconciled against the appraisals actually resolved.
    if r["design_mix"].get("case_series"):
        errs.append(
            f"result {rid}: design_mix includes {r['design_mix']['case_series']} case "
            f"series, which have no risk-of-bias instrument and cannot appear in an "
            f"appraisal record — the design distribution cannot be verified for this "
            f"body, only its total")
    elif resolved and len(resolved) == len(r["study_ids"]):
        actual = {d: 0 for d in DESIGNS}
        for sid in resolved:
            design = appraisal[(sid, target)]["design"]
            if design not in actual:
                errs.append(f"result {rid}: study {sid} is appraised as {design!r}, which "
                            f"has no design_mix category")
                continue
            actual[design] += 1
        if actual != r["design_mix"]:
            shown = ", ".join(f"{d}={n}" for d, n in actual.items() if n)
            claimed = ", ".join(f"{d}={n}" for d, n in r["design_mix"].items() if n)
            errs.append(
                f"result {rid}: design_mix claims {claimed}, but the referenced "
                f"appraisals are {shown} — the mix sets the starting level, so it "
                f"must match the body it describes")

    # Coherence: only the clearly-contradictory ends are flagged.
    confirmed = [s for s in resolved if appraisal[(s, target)]["confirmed"]]
    if confirmed and not r["domains"]["risk_of_bias"]["coherence_justification"]:
        highs = [s for s in confirmed
                 if appraisal[(s, target)]["overall"] in HIGH_RISK_OVERALLS]
        lows = [s for s in confirmed if appraisal[(s, target)]["overall"] == "low"]
        rating = r["domains"]["risk_of_bias"]["rating"]
        if rating == 0 and len(highs) * 2 > len(confirmed):
            errs.append(
                f"result {rid}: risk_of_bias rated 0 (no concern) while {len(highs)} of "
                f"{len(confirmed)} confirmed studies are high risk — record a "
                f"coherence_justification if this is intended")
        elif rating == -2 and lows and len(lows) == len(confirmed):
            errs.append(
                f"result {rid}: risk_of_bias downgraded -2 (very serious) while all "
                f"{len(confirmed)} confirmed studies are low risk — record a "
                f"coherence_justification if this is intended")
    return errs


# --- generation --------------------------------------------------------------

def _keyed_as(rec: dict) -> str:
    if rec["synthesis_mode"] == "outcome":
        return ("Certainty is keyed to **protocol outcomes** (GRADE as published).")
    return ("Certainty is keyed to **synthesis themes** — a SWiM adaptation of GRADE, not "
            "GRADE as published by the GRADE Working Group.")


def evidence_profile(rec: dict) -> str:
    lines = ["## Evidence profile", "", _keyed_as(rec), ""]
    provisional = any(r["domains"].get("risk_of_bias", {}).get("basis") == "heuristic"
                      for r in rec["results"])
    if provisional:
        lines += ["> ⚠️ **PROVISIONAL** — at least one result's risk-of-bias domain rests on an "
                  "estimate rather than a confirmed appraisal.", ""]
    lines += ["| Result | Studies | Predominant design | Start | RoB | Incons. | Indir. | "
              "Imprec. | Pub. bias | Final |",
              "|:--|--:|:--|:--|:--:|:--:|:--:|:--:|:--:|:--|"]
    for r in rec["results"]:
        d = r["domains"]
        # Zero renders as "0", not "+0": a downgrade should stand out from its absence.
        cells = [(str(d[n]["rating"]) if n in d else "—") for n in DOMAINS]
        final_idx = LEVELS[r["final"]]
        lines.append(
            f"| {r['label']} | {len(r['study_ids'])} | {predominant_design(r['design_mix'])} | "
            f"{r['starting_level']} | " + " | ".join(cells) +
            f" | {r['final'].replace('_', ' ')} {SYMBOLS[final_idx]} |")
    lines.append("")
    for r in rec["results"]:
        notes = [f"  - *{n.replace('_', ' ')}*: {r['domains'][n]['note']}"
                 for n in DOMAINS if n in r["domains"] and r["domains"][n]["note"]]
        if notes:
            lines.append(f"- **{r['label']}**")
            lines.extend(notes)
    return "\n".join(lines)


def summary_of_findings(rec: dict) -> str:
    lines = ["## Summary of findings", "",
             "| Result | Studies | Certainty | What this means |", "|:--|--:|:--|:--|"]
    for r in rec["results"]:
        idx = LEVELS[r["final"]]
        lines.append(f"| {r['label']} | {len(r['study_ids'])} | "
                     f"{SYMBOLS[idx]} {r['final'].replace('_', ' ').upper()} | "
                     f"{r['certainty_statement']} |")
    return "\n".join(lines)


def provenance(source: str) -> str:
    return (f"\n---\n\n*Generated by `grade_profile.py` from `{source}`. "
            f"This check verifies that each result's certainty is complete, legal and "
            f"arithmetically consistent — it cannot verify that a domain judgment was the "
            f"right call.*")


# --- main --------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check a GRADE certainty record and generate its evidence profile.")
    ap.add_argument("infile", nargs="?")
    ap.add_argument("--rob", metavar="PATH",
                    help="appraisal record, for confirming a 'confirmed_rob' basis")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if the record violates a rule")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 - not all streams support it
        pass

    source = args.infile or "stdin"
    try:
        if args.infile:
            with open(args.infile, encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except OSError as e:
        sys.stderr.write(f"grade_profile: cannot read {source} ({e})\n")
        return 2

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"grade_profile: input is not valid JSON ({e})\n")
        return 2

    appraisal = None
    if args.rob:
        try:
            with open(args.rob, encoding="utf-8") as fh:
                appraisal = parse_appraisal(json.loads(fh.read()))
        except (OSError, json.JSONDecodeError) as e:
            sys.stderr.write(f"grade_profile: cannot read --rob {args.rob} ({e})\n")
            return 2
        except InputError as e:
            sys.stderr.write(f"grade_profile: {e}\n")
            return 2

    try:
        rec = parse(data)
        errs = check(rec, appraisal, rob_supplied=bool(args.rob))
    except InputError as e:
        # No artifact on malformed input: a record that cannot be read must not
        # produce a document that looks authoritative.
        sys.stderr.write(f"grade_profile: {e}\n")
        return 2

    print(f"# GRADE certainty — {rec['review_type']} review\n")
    print(evidence_profile(rec))
    print()
    print(summary_of_findings(rec))
    print("\n## Check\n")
    if errs:
        print(f"⚠️ **{len(errs)} issue(s)** — fix before reporting:")
        for e in errs:
            print(f"- {e}")
    else:
        print("✅ Every result is complete, legal under GRADE, and arithmetically consistent.")
    print(provenance(source))
    return 1 if (errs and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
