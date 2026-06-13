#!/usr/bin/env python3
"""
kappa.py — inter-rater agreement for dual-reviewer screening. Standard library
only (math) — no dependencies.

Dual independent screening is the systematic-review gold standard; the modern
LLM analogue runs two independent screeners (two models or two prompts) and
adjudicates disagreements. This script quantifies how well the two agree
(Cohen's kappa — chance-corrected, because raw % agreement is inflated by the
include/exclude class imbalance) and, when a reference/gold column is supplied,
how each rater performs against it (sensitivity/recall + Matthews correlation,
the metrics the LLM-screening literature reports).

It also lists the DISAGREEMENTS — the records a third reviewer/human must
adjudicate.

INPUT — JSONL (one record per line) or CSV with a header. Each record needs an
id and two rater labels; a reference label is optional:
  {"id": "p001", "rater_a": "INCLUDE", "rater_b": "EXCLUDE", "reference": "INCLUDE"}
Labels are case-insensitive; INCLUDE/EXCLUDE (UNCERTAIN allowed, treated as its
own category for kappa; for MCC it is mapped to EXCLUDE unless --uncertain-include).

USAGE
  python kappa.py screening.jsonl
  python kappa.py screening.csv --a rater_a --b rater_b --ref reference
  python kappa.py screening.jsonl --json

OUTPUT
  Markdown (default): kappa, % agreement, interpretation, per-rater metrics vs
  reference (if given), and the disagreement list. --json for machine output.
  Exit 0 always (this is a measurement, not a gate) unless --min-kappa is set,
  in which case exit 1 if kappa < the floor (e.g. fail a run with poor agreement).
"""
from __future__ import annotations
import argparse, csv, json, math, sys


def load(path: str):
    rows = []
    if path and path.lower().endswith(".csv"):
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        src = open(path, encoding="utf-8") if path else sys.stdin
        for ln in src:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    return rows


def norm(label) -> str:
    return str(label or "").strip().upper()


def cohens_kappa(pairs: list[tuple[str, str]]) -> tuple[float, float, dict]:
    """Return (kappa, observed_agreement, confusion) for two raters."""
    n = len(pairs)
    if n == 0:
        return float("nan"), float("nan"), {}
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    conf = {(a, b): 0 for a in cats for b in cats}
    for a, b in pairs:
        conf[(a, b)] += 1
    po = sum(conf[(c, c)] for c in cats) / n
    a_marg = {c: sum(conf[(c, b)] for b in cats) / n for c in cats}
    b_marg = {c: sum(conf[(a, c)] for a in cats) / n for c in cats}
    pe = sum(a_marg[c] * b_marg[c] for c in cats)
    kappa = (po - pe) / (1 - pe) if (1 - pe) else float("nan")
    return kappa, po, conf


def interpret(k: float) -> str:
    if k != k:  # nan
        return "undefined"
    if k < 0: return "less than chance"
    if k < 0.20: return "slight"
    if k < 0.40: return "fair"
    if k < 0.60: return "moderate"
    if k < 0.80: return "substantial"
    return "almost perfect"


def vs_reference(rater: list[str], ref: list[str], uncertain_include: bool) -> dict:
    def bin_(x):
        x = norm(x)
        if x == "INCLUDE":
            return 1
        if x == "UNCERTAIN":
            return 1 if uncertain_include else 0
        return 0
    tp = tn = fp = fn = 0
    for r, g in zip(rater, ref):
        rb, gb = bin_(r), bin_(g)
        if rb and gb: tp += 1
        elif rb and not gb: fp += 1
        elif not rb and gb: fn += 1
        else: tn += 1
    sens = tp / (tp + fn) if (tp + fn) else float("nan")   # recall — the key SR metric
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denom) if denom else float("nan")
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "sensitivity_recall": sens,
            "specificity": spec, "precision": prec, "mcc": mcc}


def main() -> int:
    ap = argparse.ArgumentParser(description="Dual-reviewer agreement (Cohen's kappa) + reference metrics.")
    ap.add_argument("infile", nargs="?")
    ap.add_argument("--a", default="rater_a"); ap.add_argument("--b", default="rater_b")
    ap.add_argument("--ref", default="reference"); ap.add_argument("--id", default="id")
    ap.add_argument("--uncertain-include", action="store_true", help="count UNCERTAIN as INCLUDE for MCC")
    ap.add_argument("--min-kappa", type=float, default=None, help="exit 1 if kappa below this floor")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = load(args.infile)
    pairs = [(norm(r.get(args.a)), norm(r.get(args.b))) for r in rows]
    kappa, po, _ = cohens_kappa(pairs)
    disagreements = [r.get(args.id, i) for i, r in enumerate(rows) if norm(r.get(args.a)) != norm(r.get(args.b))]

    has_ref = any(args.ref in r and r.get(args.ref) not in (None, "") for r in rows)
    ref_metrics = None
    if has_ref:
        ref = [norm(r.get(args.ref)) for r in rows]
        ref_metrics = {
            "rater_a": vs_reference([norm(r.get(args.a)) for r in rows], ref, args.uncertain_include),
            "rater_b": vs_reference([norm(r.get(args.b)) for r in rows], ref, args.uncertain_include),
        }

    result = {"n": len(rows), "cohens_kappa": kappa, "observed_agreement": po,
              "interpretation": interpret(kappa), "n_disagreements": len(disagreements),
              "disagreements": disagreements, "vs_reference": ref_metrics}

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("# Dual-reviewer screening agreement\n")
        print(f"- Records double-screened: **{result['n']}**")
        kdisp = "n/a" if kappa != kappa else f"{kappa:.3f}"
        print(f"- Cohen's kappa: **{kdisp}** ({result['interpretation']})  ·  observed agreement: {po:.1%}")
        print(f"- Disagreements to adjudicate (3rd reviewer/human): **{len(disagreements)}**")
        if kappa == kappa and kappa < 0.60:
            print("\n> ⚠️ Kappa below 0.60 (moderate) — the criteria may be ambiguous. Pilot/refine criteria and re-screen before trusting the split.")
        if ref_metrics:
            print("\n## Vs reference (gold/adjudicated)\n")
            print("| Rater | Sensitivity/recall | Specificity | Precision | MCC |")
            print("|:--|:--|:--|:--|:--|")
            for k, m in ref_metrics.items():
                print(f"| {k} | {m['sensitivity_recall']:.3f} | {m['specificity']:.3f} | {m['precision']:.3f} | {m['mcc']:.3f} |")
            print("\n> Recall is the metric that matters for screening — a missed include is the costly error. Report it (and the chance-corrected MCC), not raw accuracy, which class imbalance inflates.")
        if disagreements:
            print("\n## Disagreements (adjudicate these)\n")
            print(", ".join(str(d) for d in disagreements[:50]) + (" …" if len(disagreements) > 50 else ""))

    if args.min_kappa is not None and kappa == kappa and kappa < args.min_kappa:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
