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

  Whether an appraisal has been signed off by a human, EXCEPT where a rating relies
  on it. A supplied --rob record is checked as a record — every appraisal in it must
  be structurally sound and internally coherent, cited or not — but confirmation
  governs whether a rating MAY REST on a judgment, so it is checked only for the
  studies a `confirmed_rob` result actually cites. An appraisal awaiting sign-off
  for some other result is rob_appraisal.py's H_rob count to report, not a reason to
  fail this certainty record.

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
  python grade_profile.py record.json --rob rob.json --strict --json   # counts only

MACHINE-READABLE OUTPUT (--json)
  Replaces the artifact with the envelope contracts/cli-contract.md defines:

    {"check": "grade_profile", "schema_version": "1.0", "issues": 5,
     "units": {"U_grade": 2, "U_rob_trace": 1}, "gates": {}, "unattributed": 1}

  This is the only check producing TWO units, and they overlap on purpose: an
  unresolved reference both fails its result (U_grade, counted per result) and is
  the traceability work outstanding (U_rob_trace, counted per reference). Neither
  may be derived from the other. `U_rob_trace` is emitted only when `--rob` is
  supplied — without an appraisal record nothing was traced, and reporting 0 would
  claim every reference resolved. `unattributed` counts violations of the appraisal
  record itself, which belong to no certainty unit.

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

# Version of the --json ENVELOPE, not of the input record. A consumer validates it
# before reading any count, so a script whose output shape changes is rejected
# rather than silently mis-read as the shape the consumer expects.
JSON_ENVELOPE_VERSION = "1.0"

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
UPGRADE_MAX = {"large_effect": 2, "dose_response": 1, "opposing_confounding": 1}
UPGRADES = tuple(UPGRADE_MAX)
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


def _opt_key(v, name: str) -> str:
    """An optional text field whose value is used VERBATIM as a lookup key.

    Same contract as _opt_str, minus the strip: `appraised_result` is matched
    exactly against the appraisal record's own `result_assessed`, which is stored
    unstripped. Normalising one side of an exact comparison hides the near-miss it
    exists to catch — ' mortality at 12 months' silently resolved to the unpadded
    target and the mistyped reference reported clean.

    A blank value is NOT malformed input. Rejecting it here fired on every result,
    including a `heuristic` one whose target is never read at all — so a rapid
    review carrying a leftover empty string went from a clean profile to exit 2 and
    no output. It is a readable record that fails to name a target, which is the
    same thing as omitting it: reported at exit 1, by the check that actually
    consults the field, with a message that names the fix.
    """
    if v is None:
        return ""
    if not isinstance(v, str):
        raise InputError(f"{name}: expected a string, got {type(v).__name__} {v!r}")
    return v


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


def _upgrade(v, ctx: str, maximum: int) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= maximum:
        allowed = ", ".join(str(i) for i in range(maximum + 1))
        raise InputError(f"{ctx}: upgrade must be one of the integers {allowed}, got {v!r}")
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
    upgrades = {
        u: _upgrade(upgrades_raw.get(u, 0), f"{ctx}.upgrades.{u}", UPGRADE_MAX[u])
        for u in UPGRADES
    }

    return {"id": rid, "label": _opt_str(r.get("label"), f"{ctx}.label") or rid, "study_ids": study_ids,
            "design_mix": mix, "starting_level": start,
            "starting_level_justification": _opt_str(
                r.get("starting_level_justification"), f"{ctx}.starting_level_justification"),
            "domains": domains, "upgrades": upgrades, "final": final,
            "certainty_statement": _str(r.get("certainty_statement"),
                                        f"{ctx}.certainty_statement").strip(),
            "appraised_result": _opt_key(r.get("appraised_result"),
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


def _validate_appraisal_domains(instrument: str, domains: dict, ctx: str) -> list[str]:
    """Validate the instrument's EXACT domain names and value vocabulary.

    This duplicates rob_appraisal.py's schema, deliberately: constitution
    Principle III forbids importing across skills, and this check must be usable
    standalone. `test_coercion_conformance.py` asserts the two definitions stay
    identical, so the duplication cannot drift.

    Validating only the domain COUNT was not enough: five arbitrary keys satisfied
    it, so the two checks disagreed about the same file — rob_appraisal rejected it
    while this one reported clean.

    Returns the appraisal's METHOD VIOLATIONS (an absent domain), and raises
    InputError only for what is genuinely unreadable (an unrecognised domain name
    or a value outside the instrument's vocabulary). rob_appraisal.py draws the
    line in exactly that place — an incomplete appraisal is a readable record that
    breaks a rule, so it exits 1 with diagnostics rather than 2 with none — and
    collapsing both into InputError here denied the reader those diagnostics.
    """
    expected = INSTRUMENT_DOMAINS[instrument]
    missing = [d for d in expected if d not in domains]
    extra = sorted(set(domains) - set(expected))
    if extra:
        # An unrecognised domain name cannot be interpreted at all: it may be a
        # misspelling of a required domain, so reading past it would report the
        # right verdict for the wrong reason.
        raise InputError(f"{ctx}.domains: {instrument} defines "
                         f"{', '.join(expected)} — unrecognised {', '.join(extra)}")

    violations = []
    if missing:
        violations.append(f"{instrument} requires domain(s) {', '.join(missing)}, "
                          f"which are absent")

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
    return violations


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

    Returns the METHOD VIOLATIONS it finds. These are judgments about a readable
    record, which rob_appraisal.py reports as exit-1 diagnostics; raising InputError
    for them here made the same file exit 2 with no artifact, so the two checks
    disagreed about severity even once they agreed about validity.
    """
    if justification:
        return []                               # a recorded override, as the sibling allows

    if instrument == "nos":
        total = sum(domains.get(d, 0) for d in INSTRUMENT_DOMAINS["nos"])
        band = _nos_band(int(total))
        if overall != band:
            return [f"Newcastle-Ottawa total is {int(total)}/9, which bands as "
                    f"'{band}', but overall is '{overall}'. The bands are "
                    f"conventional — record an overall_justification to override"]
        return []

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
    violations = []
    if no_info and overall == "low":
        violations.append(
            f"overall 'low' while domain(s) {', '.join(no_info)} report no "
            f"information — absence of evidence is not evidence of low risk; "
            f"record an overall_justification if this is intended")

    if not ordered:
        return violations
    worst_domain = max(ordered, key=lambda d: ordered[d])
    worst = ordered[worst_domain]
    declared = INSTRUMENT_SEVERITY[instrument][overall]
    if declared is not None and declared < worst:
        shown = domains[worst_domain]
        if instrument == "quadas2":
            shown = shown["risk_of_bias"]
        violations.append(
            f"overall '{overall}' is more favourable than its worst domain "
            f"({worst_domain} = '{shown}') — record an overall_justification if "
            f"this is intended")
    return violations


def _validate_appraisal_evidence(instrument: str | None, value, ctx: str) -> None:
    """Mirror rob_appraisal.py's optional-but-typed evidence schema.

    The appraisal remains valid when the key is absent or the object is empty.
    When it is supplied, however, ignoring its shape lets this standalone
    consumer accept backing that the owning appraisal check rejects.
    """
    if not isinstance(value, dict):
        raise InputError(f"{ctx}: expected an object mapping domain keys to quoted "
                         f"supporting text, got {type(value).__name__} {value!r}")
    if instrument is not None:
        _no_unknown_keys(value, set(INSTRUMENT_DOMAINS[instrument]), ctx)
    for name, text in value.items():
        _str(text, f"{ctx}.{name}")


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
        if not isinstance(instrument, str) or instrument not in INSTRUMENT_DOMAINS:
            raise InputError(f"{ctx}.instrument: must be one of "
                             f"{', '.join(sorted(INSTRUMENT_DOMAINS))}, got {instrument!r}")
        instrument_mismatch = instrument != expected

        # An absent or empty `domains` object is an INCOMPLETE appraisal, not an
        # unreadable one: rob_appraisal.py defaults the key to {} and reports the
        # absent domains as a method violation. Demanding a non-empty object here
        # made the same file exit 2 with no diagnostics while the owning check
        # exited 1 with them.
        domains = _obj(s.get("domains", {}), f"{ctx}.domains")
        overall = s.get("overall")
        overall_justification = _opt_str(
            s.get("overall_justification"), f"{ctx}.overall_justification")
        violations: list[str] = []
        override_load_bearing = False
        if instrument_mismatch:
            # Mirror rob_appraisal.py: a recognized instrument paired with the
            # wrong design is a readable method violation, not malformed JSON.
            # It reports the mismatch and stops, so the domains are never measured
            # against an instrument that was never the right yardstick.
            for name, value in domains.items():
                if isinstance(value, bool) or not isinstance(
                        value, (str, int, float, dict)):
                    raise InputError(
                        f"{ctx}.domains.{name}: unsupported value {value!r}")
            overall = _str(overall, f"{ctx}.overall")
            _validate_appraisal_evidence(
                None, s.get("evidence", {}), f"{ctx}.evidence")
        else:
            domain_violations = _validate_appraisal_domains(instrument, domains, ctx)
            violations += domain_violations
            _validate_appraisal_evidence(
                instrument, s.get("evidence", {}), f"{ctx}.evidence")
            if not isinstance(overall, str) or overall not in INSTRUMENT_OVERALLS[instrument]:
                raise InputError(f"{ctx}.overall: must be one of "
                                 f"{', '.join(sorted(INSTRUMENT_OVERALLS[instrument]))} "
                                 f"for {instrument}, got {overall!r}")
            if not domain_violations:
                # An incomplete appraisal cannot be judged against its own domains,
                # so rob_appraisal.py stops at the missing-domain violation. Running
                # the comparison anyway would report a second, derived violation
                # that disappears the moment the first is fixed.
                violations += _validate_appraisal_overall(
                    instrument, domains, overall, overall_justification, ctx)
                # Whether the override is LOAD-BEARING: would this appraisal have
                # been a method violation without it? An override that suppresses a
                # real violation has to reach the artifact even when no certainty
                # rating rests on the appraisal, because it is doing the work that
                # makes the supplied record legal.
                if overall_justification:
                    override_load_bearing = bool(_validate_appraisal_overall(
                        instrument, domains, overall, "", ctx))

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
                    "expected_instrument": expected,
                    "instrument_mismatch": instrument_mismatch,
                    "result_assessed": result_assessed, "confirmed": bool(by and at),
                    # Kept for the artifact, not for the check: an overall_justification
                    # is what makes an otherwise-invalid appraisal legal, so a rating
                    # resting on it must show it — and so must the record, when the
                    # override is what suppressed a violation.
                    "overall_justification": overall_justification,
                    "override_load_bearing": override_load_bearing,
                    # Method violations of the appraisal itself, carried rather than
                    # raised so this check classifies them the way their owning check
                    # does: exit 1 with diagnostics, not exit 2 with none.
                    "violations": violations}
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

def arithmetic(r: dict) -> tuple[int, int, int, bool]:
    """(downgrades, upgrades, computed level, whether the sum was CLAMPED).

    GRADE certainty is bounded at high and very low, so a sum outside that range is
    pulled back to the bound. The clamp is what makes `high +2 = high` "consistent"
    — true, and invisible on the page, so a reader checking the arithmetic in the
    rendered row found it not adding up and could not tell whether the record was
    wrong or the renderer was. Both callers derive it here so they cannot disagree.

    Meaningful only when every domain is present; the caller checks that first.
    """
    downgrades = sum(d["rating"] for d in r["domains"].values())
    upgrades = sum(r["upgrades"].values())
    raw = LEVELS[r["starting_level"]] + downgrades + upgrades
    computed = max(1, min(4, raw))
    return downgrades, upgrades, computed, raw != computed


def check(rec: dict, appraisal: dict | None,
          rob_supplied: bool) -> tuple[list[str], set, int]:
    """Return (method violations, ids of the results that have at least one,
    unresolved appraisal references).

    The id set is what `U_grade` is DEFINED as — results that fail, not diagnostics
    emitted. One result can raise four, and a loop counting messages would record
    four units of outstanding work for one broken result, corrupting the weighted
    total and the plateau history that routes the whole review.

    The third value is `U_rob_trace`, summed over the results whose traceability was
    actually examined. It is a SEPARATE unit from `U_grade` and the two overlap on
    purpose: an unresolved reference both fails its result (U_grade) and is itself
    the traceability work outstanding (U_rob_trace). They are weighted separately by
    the loop, so neither may be derived from the other.
    """
    errs: list[str] = []
    rtype = rec["review_type"]
    # Appraisals whose violations a result already reported, so the record-level
    # sweep below does not say the same thing twice.
    reported: set = set()
    failing: set = set()
    rob_trace = 0

    for r in rec["results"]:
        rid = r["id"]
        before = len(errs)
        gate_here = 0

        # Rule 1 — every domain present. A missing domain is reported by name; it is
        # NEVER read as a judgment of "no concern".
        missing = [d for d in DOMAINS if d not in r["domains"]]
        if missing:
            errs.append(f"result {rid}: missing downgrade domain(s) {', '.join(missing)} — "
                        f"an absent domain is not a judgment of 'no concern'")

        # Rule 4 — starting level anchored to the predominant design. Decidable
        # without the domains, so it is checked even when one is absent: skipping
        # every remaining rule on a missing domain hid work the reviewer would only
        # discover on the next cycle, one violation at a time.
        pred = predominant_design(r["design_mix"])
        expected = DESIGN_START[pred]
        if r["starting_level"] != expected and not r["starting_level_justification"]:
            errs.append(
                f"result {rid}: starting_level '{r['starting_level']}' does not match the "
                f"predominant design '{pred}' (n={r['design_mix'][pred]} of "
                f"{sum(r['design_mix'].values())}), which implies '{expected}'. "
                f"Record a starting_level_justification if the deviation is intended")

        upgrade_total = sum(r["upgrades"].values())

        # Rule 6 — TWO independent bars, and three previous versions of this check
        # enforced one of them while dropping the other:
        #
        #   `pred == "rct"`            caught randomized bodies, missed dta.
        #   `DESIGN_START[pred]`       caught the design, ignored the declared level,
        #                              so a body justified UP to high took +2 and had
        #                              it absorbed by the ceiling.
        #   `LEVELS[starting_level]`   caught the declared level, ignored the design,
        #                              so an RCT body justified DOWN to low could be
        #                              upgraded straight back to high.
        #
        # That last one is the worst of the three, because Rule 4 tells the reviewer
        # to add the justification: step one reports the starting level, step two
        # accepts a randomized body raised to high ⊕⊕⊕⊕ on large-effect. GRADE
        # reserves rating-up for NON-RANDOMIZED evidence, and nothing may be raised
        # above high. Both bars, named separately so the message says which one bit.
        if upgrade_total:
            if pred == "rct":
                errs.append(
                    f"result {rid}: upgrades applied to a body of randomized trials — "
                    f"GRADE reserves rating up for non-randomized evidence, whatever "
                    f"starting level the record declares")
            elif DESIGN_START[pred] == "high":
                # dta. NOT the randomization reason — diagnostic-accuracy studies
                # ARE non-randomized, so telling their author to supply
                # non-randomized evidence names something the record already
                # satisfies and cannot be acted on. The bar is the ceiling: GRADE
                # rates a body of accuracy studies as starting high, and this check
                # does not model rating one up.
                errs.append(
                    f"result {rid}: upgrades applied to a body of {pred} studies, which "
                    f"GRADE rates as starting at high — this check does not model "
                    f"rating a diagnostic-accuracy body up, so the adjustment could "
                    f"only be absorbed by the ceiling")
            elif LEVELS[r["starting_level"]] >= LEVELS["high"]:
                errs.append(
                    f"result {rid}: upgrades applied to a result already declaring a "
                    f"starting level of '{r['starting_level']}' — nothing rates above "
                    f"high, so the adjustment could only be absorbed by the ceiling")

        # Rule 5 — no upgrade over an unresolved downgrade. Decidable from the
        # domains that ARE present: a recorded -1 is unresolved whether or not some
        # other domain is missing, and only the arithmetic below needs the full set.
        if upgrade_total:
            applied = [n for n, d in r["domains"].items() if d["rating"] < 0]
            if applied:
                errs.append(f"result {rid}: upgrades applied while downgrade(s) remain "
                            f"({', '.join(applied)}) — GRADE does not permit raising certainty "
                            f"over unresolved serious concerns")

        if not missing:
            # Rule 5 (arithmetic) — the reconciliation, reported like the flow diagram's.
            downgrades, _, computed, _ = arithmetic(r)
            declared = LEVELS[r["final"]]
            if computed != declared:
                errs.append(
                    f"result {rid}: {r['starting_level']}({LEVELS[r['starting_level']]}) "
                    f"{downgrades:+d} downgrades {upgrade_total:+d} upgrades = "
                    f"{LEVEL_NAMES[computed]}({computed}), but final = "
                    f"{r['final']}({declared}) — difference of {declared - computed:+d}")

        # Rule 9 — the basis for the risk-of-bias domain. Independently decidable,
        # so an absent publication_bias domain must not conceal a certainty rating
        # resting on an appraisal that cannot back it.
        if "risk_of_bias" in r["domains"]:
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
                    trace_errs, gate_errs, unresolved = _check_traceability(r, appraisal)
                    errs.extend(trace_errs)
                    errs.extend(gate_errs)
                    gate_here = len(gate_errs)
                    rob_trace += unresolved
                    reported |= {(s, r["appraised_result"]) for s in r["study_ids"]
                                 if (s, r["appraised_result"]) in appraisal}

        # Human-gate violations are reported but never booked as U_grade: a result
        # whose ONLY outstanding item is a missing signature is finished as far as
        # this check is concerned, and must reach BLOCKED_ON_HUMAN rather than
        # keeping the auto-repair loop turning until it declares a plateau.
        if len(errs) - before - gate_here > 0:
            failing.add(rid)

    if appraisal is not None:
        errs.extend(_check_appraisal_record(appraisal, reported))

    return errs, failing, rob_trace


def _appraisal_problems(item: dict) -> list[str]:
    """Everything wrong with one appraisal, in rob_appraisal.py's own words.

    ONE source for the claim text, wrapped differently by each reporting site: a
    cited appraisal names the certainty result it undermines, an uncited one names
    the record. Two checks can agree a file is bad and disagree about WHY, and a
    reviewer fixing what one names is then told by the other that something else is
    wrong — so the wording is shared, and `test_differential_appraisal.py` compares
    the claims rather than only the exit codes.
    """
    problems = []
    if item["instrument_mismatch"]:
        # The instrument is the root cause, so it is reported first and alone: the
        # domains were never measured against it, exactly as the sibling stops here.
        problems.append(f"design {item['design']!r} calls for "
                        f"{item['expected_instrument']}, but {item['instrument']} "
                        f"was applied")
    problems += item["violations"]
    return problems


def _check_appraisal_record(appraisal: dict, reported: set) -> list[str]:
    """Method violations in the supplied appraisal record that no result reported.

    A supplied --rob record is judged AS A RECORD, not only where a rating happens
    to cite it. Reporting violations solely per referenced study produced an
    incoherent split: a misspelled domain name in an unreferenced appraisal killed
    the run at exit 2, while a MISSING domain in that same appraisal was accepted
    silently and a clean profile printed. Same entry, same file, opposite verdicts.

    Human confirmation is deliberately not swept here. Whether a judgment has been
    signed off governs whether a RATING MAY RELY ON IT, so it belongs to the result
    that relies on it — an appraisal awaiting sign-off for some other result is
    rob_appraisal.py's H_rob count, not a reason to fail this certainty record.
    """
    errs = []
    for key in sorted(appraisal):
        if key in reported:
            continue
        sid, target = key
        item = appraisal[key]
        # The instrument mismatch is carried as its own flag rather than in
        # `violations`, because a cited appraisal reports it with the certainty
        # result it undermines. Uncited, it is still a method violation of the
        # record — and leaving it out of this sweep was one more instance of the
        # split this function exists to close.
        for violation in _appraisal_problems(item):
            errs.append(
                f"appraisal record: study {sid} (result: {target!r}) is not a valid "
                f"appraisal — {violation}. It backs no certainty rating here, but a "
                f"--rob record must be a valid appraisal record; rob_appraisal.py "
                f"reports this as a method violation")
    return errs


def _check_traceability(r: dict, appraisal: dict) -> tuple[list[str], list[str], int]:
    """Rules 10 and 12 — references resolve to the RIGHT appraisal, and the body
    judgment coheres with them.

    An appraisal targets one result. Resolving on study id alone let a study
    appraised for mortality back a certainty rating about quality of life, which is
    the wrong risk-of-bias evidence for that claim.

    Returns (violations, HUMAN-GATE violations, UNRESOLVED REFERENCE COUNT). The
    second list is reported like any other, but must not be counted into U_grade: a
    missing signature is not auto-reducible work, and booking it as such made the
    loop route the agent back to this check to repair something only a person can
    clear. The contract says it three times — an unconfirmed appraisal belongs
    exclusively to H_rob.

    The third value is `U_rob_trace`, DEFINED by the contract as references that do
    not resolve at the named `(study, result)` target. It counts REFERENCES, not
    diagnostics: three unresolved studies raise one message naming all three, and a
    loop counting messages would book one unit of work for three broken references.
    When the target itself is blank or unknown, NONE of the result's references can
    resolve, so every one of them counts — reporting 0 there would say the
    traceability was clean when in truth it could not be attempted.
    """
    errs, gate = [], []
    rid = r["id"]
    target = r["appraised_result"]

    if not target.strip():
        supplied = " (it is present but blank)" if target else ""
        return ([f"result {rid}: 'appraised_result' is required when the risk-of-bias "
                f"basis is 'confirmed_rob'{supplied} — it names which appraised result "
                f"backs this certainty rating, since an appraisal targets one result, "
                f"not a whole study"], [], len(r["study_ids"]))

    known_targets = sorted({k[1] for k in appraisal})
    if target not in known_targets:
        # Report the near-miss rather than resolving it. Targets are matched
        # exactly, so ' mortality' and 'mortality' are different targets — naming
        # the neighbour is what turns "not found" into a fixable message.
        near = {t.strip().lower(): t for t in known_targets}.get(target.strip().lower())
        hint = (f"; nearest is {near!r} — targets are matched exactly, including "
                f"surrounding whitespace" if near else "")
        return ([f"result {rid}: appraised_result {target!r} does not appear in the "
                 f"appraisal record (it appraises: "
                 f"{', '.join(repr(t) for t in known_targets)}){hint}"], [],
                len(r["study_ids"]))

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

    # Method violations of the appraisal, reported here rather than raised during
    # parsing so that a readable-but-invalid appraisal exits 1 with diagnostics,
    # exactly as rob_appraisal.py reports it. An appraisal its own instrument
    # rejects cannot back a confirmed_rob basis, so such a study is also excluded
    # from the coherence comparison below.
    for sid in resolved:
        for violation in _appraisal_problems(appraisal[(sid, target)]):
            errs.append(
                f"result {rid}: study {sid} (result: {target!r}) appraisal is not "
                f"valid — {violation}. rob_appraisal.py reports this as a method "
                f"violation, so it cannot back a 'confirmed_rob' basis")

    unconfirmed = [s for s in resolved if not appraisal[(s, target)]["confirmed"]]
    if unconfirmed:
        gate.append(f"result {rid}: study reference(s) {', '.join(unconfirmed)} have no "
                    f"human confirmation, so they cannot back a 'confirmed_rob' basis "
                    f"— this is a HUMAN GATE (H_rob), not auto-reducible work, so it "
                    f"is excluded from U_grade")

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
    confirmed = [s for s in resolved
                 if appraisal[(s, target)]["confirmed"]
                 and not appraisal[(s, target)]["instrument_mismatch"]
                 and not appraisal[(s, target)]["violations"]]
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
    # A reference is untraceable whether the appraisal is missing entirely or is
    # present for a DIFFERENT result — both mean this certainty rating is backed by
    # nothing at the target it names.
    return errs, gate, len(unresolved) + len(wrong_target)


# --- generation --------------------------------------------------------------

def _keyed_as(rec: dict) -> str:
    if rec["synthesis_mode"] == "outcome":
        return ("Certainty is keyed to **protocol outcomes** (GRADE as published).")
    return ("Certainty is keyed to **synthesis themes** — a SWiM adaptation of GRADE, not "
            "GRADE as published by the GRADE Working Group.")


def _markdown_text(value: object) -> str:
    """Render caller-controlled text without breaking out of the list item it sits in."""
    return str(value).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def _markdown_cell(value: object) -> str:
    """Render caller-controlled text without creating extra table cells or rows."""
    return _markdown_text(value).replace("|", "&#124;")


def evidence_profile(rec: dict, appraisal: dict | None = None) -> str:
    lines = ["## Evidence profile", "", _keyed_as(rec), ""]
    provisional = any(r["domains"].get("risk_of_bias", {}).get("basis") == "heuristic"
                      for r in rec["results"])
    if provisional:
        lines += ["> ⚠️ **PROVISIONAL** — at least one result's risk-of-bias domain rests on an "
                  "estimate rather than a confirmed appraisal.", ""]
    # RECORDED CONTENT IS NEVER HIDDEN. Two narrower gates have stood here and each
    # dropped a disclosure from a passing artifact: first `review_type == "rapid"`,
    # which lost scoping and narrative reviews; then a review-type test nested
    # inside `if provisional`, which lost every record whose results all use
    # confirmed_rob — including the rapid ones the first version handled. Two
    # records differing in a recorded methodological shortcut rendered
    # byte-identically under both.
    #
    # The disclosure is now printed whenever it is present, and the line says only
    # what it is. What varies is whether it LICENSES anything, and that is the
    # sentence's job, not the renderer's: a heuristic basis is illegal in a
    # systematic or umbrella review whatever is disclosed, and the check reports
    # that separately.
    if rec["streamlined_method_disclosed"]:
        licenses = (" It does not permit a heuristic risk-of-bias basis in a "
                    f"{rec['review_type']} review, which requires confirmed appraisal."
                    if rec["review_type"] in CONFIRMED_ROB_REQUIRED else "")
        lines += [f"> **Streamlined method disclosed:** "
                  f"{_markdown_text(rec['streamlined_method_disclosed'])}{licenses}", ""]
    # The ID is a column, not a decoration: only `id` is required to be unique, so
    # two results may legitimately carry the same label. Rendering the label alone
    # made those rows indistinguishable and discarded the identifier every
    # diagnostic uses ("result O1: ..."), leaving the reader nothing to match on.
    # Upgrades are a column, not a footnote. They are the only adjustment that
    # RAISES certainty, so a row without them cannot be reconciled: `low + 2 = high`
    # read as an unexplained jump from low to high, and the reader had no way to
    # tell an upgrade from an arithmetic error.
    lines += ["| ID | Result | Studies | Predominant design | Start | RoB | Incons. | Indir. | "
              "Imprec. | Pub. bias | Up | Final |",
              "|:--|:--|--:|:--|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--|"]
    for r in rec["results"]:
        d = r["domains"]
        # Zero renders as "0", not "+0": a downgrade should stand out from its absence.
        cells = [(str(d[n]["rating"]) if n in d else "—") for n in DOMAINS]
        final_idx = LEVELS[r["final"]]
        upgrade_total = sum(r["upgrades"].values())
        bound = " ⌁" if (_all_domains_present(r) and arithmetic(r)[3]) else ""
        lines.append(
            f"| {_markdown_cell(r['id'])} | {_markdown_cell(r['label'])} | "
            f"{len(r['study_ids'])} | "
            f"{predominant_design(r['design_mix'])} | "
            f"{_start_cell(r)} | " + " | ".join(cells) +
            f" | {'+' + str(upgrade_total) if upgrade_total else '0'}"
            f" | {r['final'].replace('_', ' ')} {SYMBOLS[final_idx]}{bound} |")
    lines.append("")
    shown: set = set()
    for r in rec["results"]:
        notes = _result_notes(r, appraisal)
        if notes:
            lines.append(f"- **{_markdown_text(r['label'])}** ({_markdown_text(r['id'])})")
            lines.extend(notes)
        # Only what the notes ACTUALLY rendered, which is the same condition
        # _result_notes uses. Marking every cited study as shown regardless meant a
        # heuristic result naming an appraised_result suppressed the record-level
        # block without ever printing the override itself.
        if (appraisal is not None and r["appraised_result"]
                and r["domains"].get("risk_of_bias", {}).get("basis") == "confirmed_rob"):
            shown |= {(s, r["appraised_result"]) for s in r["study_ids"]}
    lines += _unattached_overrides(appraisal, shown)
    return "\n".join(lines)


def _unattached_overrides(appraisal: dict | None, shown: set) -> list[str]:
    """Load-bearing overrides in the --rob record that no result's notes carried.

    An `overall_justification` that suppresses a real method violation is what
    makes the supplied record legal. Rendering it only where a rating RESTS on it
    was too narrow: with a heuristic basis, or an appraisal nothing cites, the run
    exits 0 while the human sign-off that suppressed the violation appears on no
    page the reviewer reads. Deleting that same justification exits 1 — so the
    artifact was hiding precisely the thing holding it clean.
    """
    if appraisal is None:
        return []
    rows = [(key, item) for key, item in sorted(appraisal.items())
            if item["override_load_bearing"] and key not in shown]
    if not rows:
        return []
    lines = ["", "**Appraisal overrides in the supplied record.** Each of these "
                 "suppressed a method violation that `rob_appraisal.py` would "
                 "otherwise report; no certainty rating here rests on them."]
    for (sid, target), item in rows:
        lines.append(f"- *{_markdown_text(sid)}* (result: {_markdown_text(target)}): "
                     f"{_markdown_text(item['overall_justification'])}")
    return lines


def _all_domains_present(r: dict) -> bool:
    return all(d in r["domains"] for d in DOMAINS)


def _departs_from_design(r: dict) -> bool:
    """Whether the starting level differs from the one the predominant design implies."""
    return r["starting_level"] != DESIGN_START[predominant_design(r["design_mix"])]


def _is_justified_departure(r: dict) -> bool:
    """A departure from the design's implied level that a justification permits.

    Both the marker and its footnote hang off this ONE predicate. Marking on the
    departure while noting on the justification made them disagree in exactly the
    violating case — an UNJUSTIFIED departure printed a † pointing at a footnote
    that did not exist, so without --strict the artifact promised the reader an
    explanation the record never gave.
    """
    return _departs_from_design(r) and bool(r["starting_level_justification"])


def _start_cell(r: dict) -> str:
    """The starting level, marked when a justification is what makes it legal.

    Marking on the mere PRESENCE of a justification flagged conforming rows as
    anomalies: a record may record its reasoning for a level that needed no
    exception, and presenting that to a manuscript reader as a departure is the
    opposite of what the marker is for.
    """
    return r["starting_level"] + (" †" if _is_justified_departure(r) else "")


def _result_notes(r: dict, appraisal: dict | None = None) -> list[str]:
    """Every recorded rationale the result relies on, in the order it is applied.

    An exception the record needs in order to be legal must be visible to the
    reader of the artifact. Three of them were computed, honoured by the check, and
    then dropped on the way to the page — the starting-level justification when it
    was doing real work, the upgrades, and the risk-of-bias coherence override —
    so a reader saw a rating with no way to reach the reasoning that permitted it.
    """
    notes = []
    if r["starting_level_justification"]:
        marker = "† " if _is_justified_departure(r) else ""
        notes.append(f"  - {marker}*starting level*: "
                     f"{_markdown_text(r['starting_level_justification'])}")
    if _all_domains_present(r):
        _, _, computed, clamped = arithmetic(r)
        if clamped:
            # The bound is why `high +2 = high` reconciles. Unmarked, the rendered
            # row simply does not add up, and the reader cannot tell whether the
            # record is wrong or the table is.
            raw = LEVELS[r["starting_level"]] + sum(
                d["rating"] for d in r["domains"].values()) + sum(r["upgrades"].values())
            notes.append(
                f"  - ⌁ *certainty bound*: {r['starting_level']}"
                f"({LEVELS[r['starting_level']]}) with the adjustments below sums to "
                f"{raw}, held at {LEVEL_NAMES[computed]}({computed}) — GRADE certainty "
                f"does not run above high or below very low")
    for name in DOMAINS:
        if name in r["domains"] and r["domains"][name]["note"]:
            notes.append(f"  - *{name.replace('_', ' ')}*: "
                         f"{_markdown_text(r['domains'][name]['note'])}")
    rob = r["domains"].get("risk_of_bias", {})
    if rob.get("coherence_justification"):
        notes.append(f"  - *risk of bias — coherence override*: "
                     f"{_markdown_text(rob['coherence_justification'])}")
    applied = [(u, n) for u, n in r["upgrades"].items() if n]
    if applied:
        notes.append("  - *upgrades*: " + ", ".join(
            f"{u.replace('_', ' ')} (+{n})" for u, n in applied))
    # An appraisal's own override is the exception one level down: it is what makes
    # an otherwise-invalid appraisal legal, and a rating resting on that appraisal
    # inherits the exception without ever showing it.
    #
    # Only where a rating actually rests on it. A heuristic basis rests on no
    # appraisal at all, so listing human-signed overrides beneath a banner saying
    # this result's risk of bias is an ESTIMATE credits it with backing it does not
    # have — the same overclaim, one level down.
    rests_on_appraisal = r["domains"].get("risk_of_bias", {}).get("basis") == "confirmed_rob"
    if appraisal is not None and rests_on_appraisal and r["appraised_result"]:
        overrides = [(s, appraisal[(s, r["appraised_result"])]["overall_justification"])
                     for s in r["study_ids"]
                     if (s, r["appraised_result"]) in appraisal
                     and appraisal[(s, r["appraised_result"])]["overall_justification"]]
        for sid, text in overrides:
            notes.append(f"  - *appraisal override — {_markdown_text(sid)}*: "
                         f"{_markdown_text(text)}")
    return notes


def summary_of_findings(rec: dict) -> str:
    lines = ["## Summary of findings", "",
             "| ID | Result | Studies | Certainty | What this means |",
             "|:--|:--|--:|:--|:--|"]
    for r in rec["results"]:
        idx = LEVELS[r["final"]]
        lines.append(f"| {_markdown_cell(r['id'])} | {_markdown_cell(r['label'])} | "
                     f"{len(r['study_ids'])} | "
                     f"{SYMBOLS[idx]} {r['final'].replace('_', ' ').upper()} | "
                     f"{_markdown_cell(r['certainty_statement'])} |")
    return "\n".join(lines)


def confirmation_limitation(rec: dict, rob_supplied: bool) -> str:
    """FR-015 — state, wherever human confirmation is CHECKED, what the check means.

    With --rob this command reads `confirmed_by`/`confirmed_at` and lets them back a
    `confirmed_rob` basis, so it checks human confirmation and owes the reader the
    same limitation rob_appraisal.py prints. Saying only that a domain judgment
    might be wrong invites the stronger reading — that the confirmation itself was
    verified — which is exactly what no check here can establish.
    """
    if not rob_supplied:
        return ""
    if not any(r["domains"].get("risk_of_bias", {}).get("basis") == "confirmed_rob"
               for r in rec["results"]):
        return ""
    return ("\n> A `confirmed_rob` basis rests on a confirmation record being PRESENT in the "
            "appraisal record — a name and a date. This check cannot establish that a human "
            "made the judgment, or who that person was.")


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
    ap.add_argument("--json", action="store_true",
                    help="emit the machine-readable counts envelope instead of the profile")
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
    # UnicodeDecodeError is a ValueError, not an OSError, so a file that is not
    # valid UTF-8 escaped both this handler and the JSON one below it: traceback and
    # exit 1, where the contract says exit 2 with no artifact.
    except (OSError, UnicodeDecodeError) as e:
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
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            sys.stderr.write(f"grade_profile: cannot read --rob {args.rob} ({e})\n")
            return 2
        except InputError as e:
            sys.stderr.write(f"grade_profile: {e}\n")
            return 2

    try:
        rec = parse(data)
        errs, failing, rob_trace = check(rec, appraisal, rob_supplied=bool(args.rob))
    except InputError as e:
        # No artifact on malformed input: a record that cannot be read must not
        # produce a document that looks authoritative.
        sys.stderr.write(f"grade_profile: {e}\n")
        return 2

    # Violations belonging to the appraisal record supplied via --rob rather than to
    # a certainty result. Computed once, for both output modes: the artifact prints
    # it as a note and --json reports it as unattributed, and the two must agree.
    record_level = len(errs) - sum(1 for e in errs if e.startswith("result "))

    if args.json:
        # U_rob_trace is emitted ONLY when --rob was supplied. Without an appraisal
        # record no traceability was attempted, and reporting 0 would state that
        # every reference resolved — a consumer must see the unit as ABSENT rather
        # than read an unrun check as a clean one.
        units = {"U_grade": len(failing)}
        if args.rob:
            units["U_rob_trace"] = rob_trace
        json.dump({
            "check": "grade_profile",
            "schema_version": JSON_ENVELOPE_VERSION,
            "issues": len(errs),
            "units": units,
            "gates": {},
            "unattributed": record_level,
            "detail": {"failing_results": sorted(failing)},
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if (errs and args.strict) else 0

    print(f"# GRADE certainty — {rec['review_type']} review\n")
    print(evidence_profile(rec, appraisal))
    print()
    print(summary_of_findings(rec))
    print("\n## Check\n")
    if errs:
        print(f"⚠️ **{len(errs)} issue(s)** — fix before reporting:")
        for e in errs:
            # Escaped like every other rendering site. These messages embed
            # caller-controlled ids and result targets, so an id containing a
            # newline split one diagnostic into two list items — the second one
            # free to assert whatever it liked, directly beneath a real finding.
            print(f"- {_markdown_text(e)}")
    else:
        print("✅ Every result is complete, legal under GRADE, and arithmetically consistent.")
    # U_grade is DEFINED as the number of RESULTS this check fails, so the number
    # has to be emitted rather than counted off the diagnostics. One result can
    # raise four messages, and a loop counting messages books four units of
    # outstanding work for one broken result — inflating the weighted total and the
    # plateau history that routes the whole review.
    named = ", ".join(_markdown_text(rid) for rid in sorted(failing))
    print(f"\n**U_grade: {len(failing)}** result(s) with at least one issue"
          f"{' (' + named + ')' if failing else ''}.")
    if record_level:
        print(f"\n> {record_level} further violation(s) belong to the appraisal record "
              f"supplied via `--rob`, not to a certainty result, so they are outside "
              f"`U_grade`. `rob_appraisal.py` reports them against that record.")
    print(confirmation_limitation(rec, bool(args.rob)))
    print(provenance(source))
    return 1 if (errs and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
