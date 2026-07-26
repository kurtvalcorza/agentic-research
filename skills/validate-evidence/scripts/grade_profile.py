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
DESIGNS = ("rct", "nrsi", "observational", "case_series")

# Starting level implied by the design that PREDOMINATES in the body of evidence.
# Anchoring to the predominant design (rather than to the strongest single study
# present) is the whole point: one randomized trial among eight cross-sectional
# studies does not start the body at HIGH.
DESIGN_START = {"rct": "high", "nrsi": "low", "observational": "low", "case_series": "very_low"}

RECORD_KEYS = {"schema_version", "review_type", "synthesis_mode",
               "streamlined_method_disclosed", "results"}
RESULT_KEYS = {"id", "label", "study_ids", "design_mix", "starting_level",
               "starting_level_justification", "domains", "upgrades", "final",
               "certainty_statement"}
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
    if version not in SCHEMA_VERSIONS:
        raise InputError(f"record: unrecognised schema_version {version!r} "
                         f"(recognised: {', '.join(sorted(SCHEMA_VERSIONS))})")

    review_type = raw.get("review_type")
    if review_type not in REVIEW_TYPES:
        raise InputError(f"record: review_type must be one of "
                         f"{', '.join(sorted(REVIEW_TYPES))}, got {review_type!r}")

    mode = raw.get("synthesis_mode")
    if mode not in SYNTHESIS_MODES:
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
            "streamlined_method_disclosed": raw.get("streamlined_method_disclosed"),
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

    start = r.get("starting_level")
    if start not in LEVELS:
        raise InputError(f"{ctx}.starting_level: must be one of "
                         f"{', '.join(LEVELS)}, got {start!r}")
    final = r.get("final")
    if final not in LEVELS:
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
        entry = {"rating": _rating(d.get("rating"), dctx), "note": d.get("note", "")}
        if name == "risk_of_bias":
            basis = d.get("basis")
            if basis not in ROB_BASES:
                raise InputError(f"{dctx}.basis: must be 'confirmed_rob' or 'heuristic', "
                                 f"got {basis!r}")
            entry["basis"] = basis
            entry["coherence_justification"] = d.get("coherence_justification")
        domains[name] = entry

    upgrades_raw = _obj(r.get("upgrades", {}), f"{ctx}.upgrades")
    # The closed set is what makes "importance of findings" unrepresentable — it is
    # not a GRADE upgrade reason, and certainty must never rise because a result matters.
    _no_unknown_keys(upgrades_raw, set(UPGRADES), f"{ctx}.upgrades")
    upgrades = {u: _upgrade(upgrades_raw.get(u, 0), f"{ctx}.upgrades.{u}") for u in UPGRADES}

    return {"id": rid, "label": r.get("label", rid), "study_ids": study_ids,
            "design_mix": mix, "starting_level": start,
            "starting_level_justification": r.get("starting_level_justification"),
            "domains": domains, "upgrades": upgrades, "final": final,
            "certainty_statement": r.get("certainty_statement", "")}


# --- appraisal record (read via --rob; NEVER imported from the sibling skill) --

def parse_appraisal(raw: dict) -> dict:
    """Return {study_id: {'overall': str, 'confirmed': bool}} from an appraisal record."""
    _obj(raw, "appraisal record")
    version = raw.get("schema_version")
    if version not in SCHEMA_VERSIONS:
        raise InputError(f"appraisal record: unrecognised or missing schema_version {version!r}")
    studies = raw.get("studies")
    if not isinstance(studies, list) or not studies:
        raise InputError("appraisal record: 'studies' is missing or empty")
    out = {}
    for i, s in enumerate(studies):
        _obj(s, f"appraisal studies[{i}]")
        sid = _str(s.get("id"), f"appraisal studies[{i}].id")
        if sid in out:
            raise InputError(f"appraisal record: duplicate study id {sid!r}")
        confirmed = bool(str(s.get("confirmed_by", "")).strip()
                         and str(s.get("confirmed_at", "")).strip())
        out[sid] = {"overall": s.get("overall"), "confirmed": confirmed}
    return out


def predominant_design(mix: dict) -> str:
    """The design the body mostly consists of; ties resolve to the WEAKER design."""
    order = {"rct": 3, "nrsi": 2, "observational": 1, "case_series": 0}
    best = max(mix.items(), key=lambda kv: (kv[1], -order[kv[0]]))
    return best[0]


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
    """Rules 10 and 12 — references resolve, and the body judgment coheres with them."""
    errs = []
    rid = r["id"]

    unresolved = [s for s in r["study_ids"] if s not in appraisal]
    if unresolved:
        # Exact matching means a case or whitespace near-miss surfaces here rather
        # than being silently reconciled.
        hints = []
        lowered = {k.lower().strip(): k for k in appraisal}
        for s in unresolved:
            near = lowered.get(s.lower().strip())
            if near:
                hints.append(f"{s!r} (appraisal has {near!r} — identifiers are matched exactly)")
            else:
                hints.append(repr(s))
        errs.append(f"result {rid}: study reference(s) not found in the appraisal record: "
                    f"{'; '.join(hints)}")

    resolved = [s for s in r["study_ids"] if s in appraisal]
    unconfirmed = [s for s in resolved if not appraisal[s]["confirmed"]]
    if unconfirmed:
        errs.append(f"result {rid}: study reference(s) {', '.join(unconfirmed)} have no "
                    f"human confirmation, so they cannot back a 'confirmed_rob' basis")

    # Rule 12 — coherence. Only the clearly-contradictory ends are flagged; the wide
    # middle is judgement, and this script may only assert what is decidable.
    confirmed = [s for s in resolved if appraisal[s]["confirmed"]]
    if confirmed and not r["domains"]["risk_of_bias"]["coherence_justification"]:
        highs = [s for s in confirmed if appraisal[s]["overall"] in ("high", "serious", "critical")]
        lows = [s for s in confirmed if appraisal[s]["overall"] == "low"]
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
        raw = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()
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
            appraisal = parse_appraisal(json.loads(open(args.rob, encoding="utf-8").read()))
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
