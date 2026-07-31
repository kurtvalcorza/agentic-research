"""Differential test: grade_profile.py and rob_appraisal.py must agree.

Three of the four review rounds on PR #3 found the same defect wearing different
clothes — one check accepting an appraisal record the other rejects. Each was
fixed individually, which is how the fourth one got written.

This tests the CLASS rather than the instances. It mutates a valid appraisal in
every way the schema allows to be wrong, runs BOTH checks over each mutation, and
asserts they reach the same accept/reject verdict.

Why two checks exist at all: constitution Principle III forbids importing across
skills, so grade_profile.py carries its own copy of the appraisal schema in order
to stay usable standalone. Duplication is only safe if it cannot drift, and this
is the guard.

The comparison is at the EXIT-CODE level, not merely "does it reject". Comparing
acceptance alone was not enough: three findings in one round were records both
checks rejected and classified differently — a missing appraisal domain, an
overall more favourable than its worst domain, and an empty `domains` object were
readable method violations (exit 1, with diagnostics) to rob_appraisal.py and
malformed input (exit 2, no artifact) to grade_profile.py. A guard that asks only
"did both reject?" cannot see that, which is why all three survived it.

So the contract under test is: readable method violations — including a
recognized instrument paired with the wrong design, an incomplete appraisal, and
an incoherent overall judgment — are exit 1 in BOTH checks; structurally
malformed records are exit 2 in both.

Standard library only.
"""
from __future__ import annotations

import copy
import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load, fixture  # noqa: E402

gp = load("skills/validate-evidence/scripts/grade_profile.py")
ra = load("skills/appraise-risk-of-bias/scripts/rob_appraisal.py")

INSTRUMENT_FIXTURES = {
    "rct": ("rob2", {"randomization": "low", "deviations": "low", "missing_data": "low",
                     "measurement": "low", "selection_of_result": "low"}),
    "nrsi": ("robins_i", {"confounding": "low", "participant_selection": "low",
                          "intervention_classification": "low", "deviations": "low",
                          "missing_data": "low", "outcome_measurement": "low",
                          "selection_of_result": "low"}),
    "observational": ("nos", {"selection": 4, "comparability": 2,
                              "outcome_or_exposure": 3}),
    "dta": ("quadas2", {"patient_selection": {"risk_of_bias": "low", "applicability": "low"},
                        "index_test": {"risk_of_bias": "low", "applicability": "low"},
                        "reference_standard": {"risk_of_bias": "low", "applicability": "low"},
                        "flow_and_timing": {"risk_of_bias": "low"}}),
}

# The profile references exactly these ids, so every appraised study is in scope
# for grade_profile's traceability check. Otherwise an unreferenced study would be
# invisible to it and register as a false divergence.
STUDY_IDS = ["P1", "P3", "P5", "P7"]

# Sentinel for "remove this key entirely". An absent key and a key set to null are
# different inputs, and only one of them can be written as a JSON value.
DELETE = object()


def mutations():
    """Every way the schema allows an appraisal to be wrong, per design."""
    for design, (instrument, domains) in INSTRUMENT_FIXTURES.items():
        first = list(domains)[0]
        cases = [
            ("baseline (must be accepted)", {}),
            ("overall out of vocabulary", {"overall": "nonsense"}),
            ("overall missing", {"overall": None}),
            ("overall wrong type", {"overall": []}),
            ("wrong instrument", {"instrument": "rob2" if instrument != "rob2" else "nos"}),
            ("unknown instrument", {"instrument": "made_up"}),
            ("unknown design", {"design": "made_up"}),
            ("design missing", {"design": None}),
            ("extra domain", {"domains": dict(domains, extra_key="low")}),
            ("missing domain", {"domains": {k: v for k, v in list(domains.items())[1:]}}),
            ("empty domains", {"domains": {}}),
            # Absent is not the same input as present-and-empty: both checks default
            # the key, so both must reach the incomplete-appraisal violation rather
            # than one of them treating the absence as unreadable.
            ("domains key absent", {"domains": DELETE}),
            ("evidence key absent", {"evidence": DELETE}),
            ("domain wrong type", {"domains": dict(domains, **{first: []})}),
            ("confirmed_by object", {"confirmed_by": {}}),
            ("confirmed_by blank", {"confirmed_by": "   "}),
            ("confirmed_by missing", {"confirmed_by": None}),
            ("confirmed_at missing", {"confirmed_at": None}),
            ("confirmed_at wrong type", {"confirmed_at": 20260726}),
            ("evidence wrong type", {"evidence": []}),
            ("evidence explicit null", {"evidence": None}),
            ("evidence unknown domain", {"evidence": {"made_up": "p. 4"}}),
            ("evidence value wrong type", {"evidence": {first: 123}}),
            ("evidence value blank", {"evidence": {first: "   "}}),
            ("id blank", {"id": "  "}),
            ("unknown study key", {"bogus_field": "x"}),
        ]
        if instrument == "rob2":
            cases += [
                ("overall better than worst domain",
                 {"domains": dict(domains, randomization="high")}),
                ("overall better than worst, justified",
                 {"domains": dict(domains, randomization="high"),
                  "overall_justification": "Balanced across arms; analysis unchanged."}),
            ]
        if instrument == "robins_i":
            # Round 5 slipped through because the matrix had instrument-specific
            # mutations for rob2, nos and quadas2 and NONE for robins_i. A
            # differential that skips an instrument cannot detect that instrument
            # diverging, which is the same lesson as the omitted _stars coercer.
            cases += [
                ("no_information domain with overall low",
                 {"domains": dict(domains, confounding="no_information")}),
                ("no_information domain with overall low, justified",
                 {"domains": dict(domains, confounding="no_information"),
                  "overall_justification": "Confounding unreported but design precludes it."}),
                ("no_information domain with a non-low overall",
                 {"domains": dict(domains, confounding="no_information"),
                  "overall": "moderate"}),
                ("every domain no_information",
                 {"domains": {k: "no_information" for k in domains}}),
                ("critical domain with overall low",
                 {"domains": dict(domains, confounding="critical")}),
            ]
        if instrument == "nos":
            cases += [
                ("stars over the block maximum", {"domains": dict(domains, comparability=9)}),
                ("stars as an integral float", {"domains": dict(domains, comparability=2.0)}),
                ("band mismatch", {"domains": dict(domains, selection=0)}),
                ("stars negative", {"domains": dict(domains, comparability=-1)}),
            ]
        if instrument == "quadas2":
            cases += [
                ("applicability omitted",
                 {"domains": {k: ({"risk_of_bias": "low"} if isinstance(v, dict) else v)
                              for k, v in domains.items()}}),
                ("applicability out of vocabulary",
                 {"domains": dict(domains, index_test={"risk_of_bias": "low",
                                                       "applicability": "nope"})}),
            ]
        for label, override in cases:
            yield design, instrument, label, override


def build(design, override):
    """Apply the mutation to every study, except id mutations.

    An id override must hit ONE study only — applying a blank id to all four would
    also make them duplicates, so the record would fail for a second reason and the
    test could not attribute the verdict. (An earlier version appended the blank to
    each id instead, which produced valid-but-different ids and made the two checks
    look like they disagreed when both were behaving correctly.)
    """
    instrument, domains = INSTRUMENT_FIXTURES[design]
    id_override = "id" in override
    body = {k: v for k, v in override.items() if k != "id"}
    studies = []
    for n, sid in enumerate(STUDY_IDS):
        s = {"id": sid, "design": design, "instrument": instrument,
             "domains": copy.deepcopy(domains), "overall": "low",
             "result_assessed": 'diagnostic accuracy at 12 months',
             "confirmed_by": "K. Valcorza", "confirmed_at": "2026-07-26"}
        s.update({k: copy.deepcopy(v) for k, v in body.items() if v is not DELETE})
        for k, v in body.items():
            if v is DELETE:
                s.pop(k, None)
        if id_override and n == 0:
            s["id"] = override["id"]
        studies.append(s)
    return {"schema_version": "1.0", "studies": studies}


class TestChecksAgree(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.profile = json.loads(
            fixture("grade-profile.valid.json").read_text(encoding="utf-8"))

    def _write(self, obj, name):
        p = pathlib.Path(self.dir.name) / name
        p.write_text(json.dumps(obj), encoding="utf-8")
        return p

    def _profile_for(self, design):
        """A certainty record whose design_mix matches the appraisal under test, so
        the distribution reconcile is not what fires."""
        rec = copy.deepcopy(self.profile)
        r = rec["results"][0]
        r["design_mix"] = {d: 0 for d in gp.DESIGNS}
        r["design_mix"][design] = len(STUDY_IDS)
        r["starting_level"] = gp.DESIGN_START[design]
        start = gp.LEVELS[r["starting_level"]]
        r["final"] = gp.LEVEL_NAMES[max(1, min(4, start - 1))]
        return rec

    def _gp_exit(self, design, rob):
        out, err = io.StringIO(), io.StringIO()
        argv = ["gp.py", str(self._write(self._profile_for(design), "p.json")),
                "--rob", str(self._write(rob, "r.json")), "--strict"]
        with mock.patch.object(sys, "argv", argv), redirect_stdout(out), redirect_stderr(err):
            return gp.main()

    def _ra_exit(self, rob):
        out, err = io.StringIO(), io.StringIO()
        argv = ["ra.py", str(self._write(rob, "r2.json")), "--strict"]
        with mock.patch.object(sys, "argv", argv), redirect_stdout(out), redirect_stderr(err):
            return ra.main()

    def _gp_rejects(self, design, rob):
        return self._gp_exit(design, rob) != 0

    def _ra_rejects(self, rob):
        return self._ra_exit(rob) != 0

    def test_both_checks_reach_the_same_verdict(self):
        divergences = []
        for design, instrument, label, override in mutations():
            rob = build(design, override)
            g = self._gp_rejects(design, rob)
            r = self._ra_rejects(rob)
            if g != r:
                divergences.append(
                    f"{design}/{instrument} — {label}: grade_profile "
                    f"{'rejects' if g else 'ACCEPTS'}, rob_appraisal "
                    f"{'rejects' if r else 'ACCEPTS'}")
        self.assertEqual(divergences, [],
                         "the two checks disagree about the same file:\n  "
                         + "\n  ".join(divergences))

    def test_both_checks_classify_the_same_file_the_same_way(self):
        """The stronger claim: agreeing to reject is not agreeing.

        1 and 2 mean different things to a caller — one says "your review breaks a
        rule, here are the diagnostics", the other says "this file cannot be read,
        no artifact was produced". A record that draws both answers leaves the
        reader unable to tell which is true of their file, and the check that says
        2 withholds the diagnostics the other one prints.
        """
        divergences = []
        for design, instrument, label, override in mutations():
            rob = build(design, override)
            g = self._gp_exit(design, rob)
            r = self._ra_exit(rob)
            if g != r:
                divergences.append(
                    f"{design}/{instrument} — {label}: grade_profile exits {g}, "
                    f"rob_appraisal exits {r}")
        self.assertEqual(divergences, [],
                         "the two checks classify the same file differently:\n  "
                         + "\n  ".join(divergences))

    def _uncited(self, design, override):
        """The same mutation, on an appraisal NO result cites.

        The matrix above cites every appraised study by construction, so it could
        not see how an uncited entry was judged — and that is where the two checks
        diverged: a misspelled domain name in an uncited appraisal exited 2 while a
        MISSING domain in the same entry was accepted silently.
        """
        rob = build(design, {})                       # four clean, cited studies
        instrument, domains = INSTRUMENT_FIXTURES[design]
        extra = {"id": "P9", "design": design, "instrument": instrument,
                 "domains": copy.deepcopy(domains), "overall": "low",
                 "result_assessed": "diagnostic accuracy at 12 months",
                 "confirmed_by": "K. Valcorza", "confirmed_at": "2026-07-26"}
        extra.update({k: copy.deepcopy(v) for k, v in override.items()
                      if v is not DELETE and k != "id"})
        for k, v in override.items():
            if v is DELETE:
                extra.pop(k, None)
        rob["studies"].append(extra)
        return rob

    # Mutations that leave the appraisal VALID and only remove its human sign-off.
    # These are the one documented divergence: rob_appraisal.py reports every
    # unconfirmed appraisal, while grade_profile.py checks confirmation where a
    # rating relies on it — an appraisal awaiting sign-off for some other result is
    # not a reason to fail this certainty record. Pinned so the carve-out cannot
    # quietly widen.
    CONFIRMATION_ONLY = {"confirmed_by blank", "confirmed_by missing",
                         "confirmed_at missing"}

    def test_an_uncited_appraisal_is_classified_the_same_way(self):
        divergences = []
        for design, instrument, label, override in mutations():
            if label.startswith("id ") or "unknown study key" in label:
                continue        # identity mutations are about the cited set, not this
            rob = self._uncited(design, override)
            g, r = self._gp_exit(design, rob), self._ra_exit(rob)
            if label in self.CONFIRMATION_ONLY:
                if not (r != 0 and g == 0):
                    divergences.append(
                        f"{design}/{instrument} — {label}: expected the documented "
                        f"confirmation carve-out (rob_appraisal rejects, "
                        f"grade_profile accepts), got {r} and {g}")
            elif g != r:
                divergences.append(
                    f"{design}/{instrument} — {label}: grade_profile exits {g}, "
                    f"rob_appraisal exits {r}")
        self.assertEqual(divergences, [],
                         "the two checks disagree about an UNCITED appraisal:\n  "
                         + "\n  ".join(divergences))

    def test_the_matrix_actually_covers_something(self):
        """Guard against the differential passing because it tested nothing."""
        cases = list(mutations())
        self.assertGreater(len(cases), 70)
        self.assertEqual(len({d for d, _, _, _ in cases}), 4)

    def test_baseline_is_accepted_by_both(self):
        """If the baseline were rejected, every mutation would agree vacuously."""
        for design in INSTRUMENT_FIXTURES:
            with self.subTest(design=design):
                rob = build(design, {})
                self.assertFalse(self._gp_rejects(design, rob))
                self.assertFalse(self._ra_rejects(rob))


class TestSharedSchemaConstants(unittest.TestCase):
    """The duplicated constants themselves, compared directly."""

    def test_study_key_sets_agree(self):
        self.assertEqual(gp.APPRAISAL_STUDY_KEYS, ra.STUDY_KEYS)

    def test_design_instrument_maps_agree(self):
        self.assertEqual(gp.APPRAISAL_DESIGN_INSTRUMENT, ra.DESIGN_INSTRUMENT)

    def test_domain_definitions_agree(self):
        self.assertEqual(gp.INSTRUMENT_DOMAINS, ra.DOMAINS)

    def test_nos_bands_agree(self):
        self.assertEqual(gp.NOS_BANDS, ra.NOS_BANDS)


if __name__ == "__main__":
    unittest.main()
