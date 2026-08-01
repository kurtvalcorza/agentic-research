"""Coverage for skills/screen-literature/scripts/kappa.py.

kappa.py gates a screening run via --min-kappa, so its arithmetic and its exit
behaviour both matter. Standard library only.
"""
from __future__ import annotations

import io
import json
import math
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402

kp = load("skills/screen-literature/scripts/kappa.py")


def jsonl(rows):
    d = tempfile.TemporaryDirectory()
    p = pathlib.Path(d.name) / "screen.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return d, p


class TestCohensKappa(unittest.TestCase):
    def test_perfect_agreement_is_one(self):
        pairs = [("INCLUDE", "INCLUDE")] * 5 + [("EXCLUDE", "EXCLUDE")] * 5
        k, po, _ = kp.cohens_kappa(pairs)
        self.assertAlmostEqual(k, 1.0)
        self.assertAlmostEqual(po, 1.0)

    def test_hand_computed_value(self):
        """20 records: 8 both-include, 7 both-exclude, 3 a-only, 2 b-only.

        po = 15/20 = 0.75
        a marginals: INCLUDE 11/20, EXCLUDE 9/20
        b marginals: INCLUDE 10/20, EXCLUDE 10/20
        pe = 0.55*0.50 + 0.45*0.50 = 0.50
        kappa = (0.75 - 0.50) / (1 - 0.50) = 0.5
        """
        pairs = ([("INCLUDE", "INCLUDE")] * 8 + [("EXCLUDE", "EXCLUDE")] * 7
                 + [("INCLUDE", "EXCLUDE")] * 3 + [("EXCLUDE", "INCLUDE")] * 2)
        k, po, _ = kp.cohens_kappa(pairs)
        self.assertAlmostEqual(po, 0.75)
        self.assertAlmostEqual(k, 0.5)

    def test_chance_level_agreement_is_about_zero(self):
        pairs = ([("INCLUDE", "INCLUDE")] * 25 + [("INCLUDE", "EXCLUDE")] * 25
                 + [("EXCLUDE", "INCLUDE")] * 25 + [("EXCLUDE", "EXCLUDE")] * 25)
        k, _, _ = kp.cohens_kappa(pairs)
        self.assertAlmostEqual(k, 0.0)

    def test_worse_than_chance_is_negative(self):
        pairs = [("INCLUDE", "EXCLUDE")] * 5 + [("EXCLUDE", "INCLUDE")] * 5
        k, _, _ = kp.cohens_kappa(pairs)
        self.assertLess(k, 0)

    def test_single_category_yields_undefined_kappa(self):
        """Everyone agrees on one label: pe = 1, so kappa is 0/0.

        Undefined is the mathematically honest answer — there is no variance to
        correct for chance against.
        """
        k, po, _ = kp.cohens_kappa([("INCLUDE", "INCLUDE")] * 10)
        self.assertTrue(math.isnan(k))
        self.assertAlmostEqual(po, 1.0)

    def test_empty_input_is_undefined(self):
        k, po, conf = kp.cohens_kappa([])
        self.assertTrue(math.isnan(k))
        self.assertTrue(math.isnan(po))
        self.assertEqual(conf, {})


class TestInterpretation(unittest.TestCase):
    def test_bands(self):
        for k, label in [(-0.1, "less than chance"), (0.1, "slight"), (0.3, "fair"),
                         (0.5, "moderate"), (0.7, "substantial"), (0.9, "almost perfect")]:
            with self.subTest(kappa=k):
                self.assertEqual(kp.interpret(k), label)

    def test_nan_is_undefined(self):
        self.assertEqual(kp.interpret(float("nan")), "undefined")

    def test_060_boundary_is_substantial(self):
        """0.60 is the documented target floor, and must not read as 'moderate'."""
        self.assertEqual(kp.interpret(0.60), "substantial")


class TestVsReference(unittest.TestCase):
    def test_recall_and_mcc(self):
        rater = ["INCLUDE", "INCLUDE", "EXCLUDE", "EXCLUDE"]
        ref = ["INCLUDE", "EXCLUDE", "INCLUDE", "EXCLUDE"]
        m = kp.vs_reference(rater, ref, uncertain_include=False)
        self.assertEqual((m["tp"], m["fp"], m["fn"], m["tn"]), (1, 1, 1, 1))
        self.assertAlmostEqual(m["sensitivity_recall"], 0.5)
        self.assertAlmostEqual(m["mcc"], 0.0)

    def test_uncertain_defaults_to_exclude(self):
        m = kp.vs_reference(["UNCERTAIN"], ["INCLUDE"], uncertain_include=False)
        self.assertEqual(m["fn"], 1)

    def test_uncertain_include_flag_switches_it(self):
        m = kp.vs_reference(["UNCERTAIN"], ["INCLUDE"], uncertain_include=True)
        self.assertEqual(m["tp"], 1)

    def test_missed_include_shows_as_a_false_negative(self):
        """A missed include is the costly screening error; it must be visible."""
        m = kp.vs_reference(["EXCLUDE"] * 10, ["INCLUDE"] * 2 + ["EXCLUDE"] * 8, False)
        self.assertEqual(m["fn"], 2)
        self.assertAlmostEqual(m["sensitivity_recall"], 0.0)


class TestFormatting(unittest.TestCase):
    def test_nan_never_renders_as_literal_nan(self):
        self.assertEqual(kp._md(float("nan")), "n/a")
        self.assertEqual(kp._md(float("inf")), "n/a")

    def test_json_output_is_valid_json(self):
        """NaN must not leak into the JSON payload as a bare token."""
        safe = kp._json_safe({"k": float("nan"), "nested": [float("inf"), 1.5]})
        text = json.dumps(safe, allow_nan=False)
        self.assertIn("null", text)
        self.assertEqual(json.loads(text)["nested"][1], 1.5)


class TestNormalisation(unittest.TestCase):
    def test_labels_are_case_and_space_insensitive(self):
        self.assertEqual(kp.norm(" include "), "INCLUDE")

    def test_none_becomes_empty(self):
        self.assertEqual(kp.norm(None), "")


class TestCli(unittest.TestCase):
    def run_cli(self, rows, *args):
        d, p = jsonl(rows)
        self.addCleanup(d.cleanup)
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["kappa.py", str(p), *args]), \
                redirect_stdout(out), redirect_stderr(err):
            code = kp.main()
        return code, out.getvalue(), err.getvalue()

    AGREE = [{"id": f"p{i}", "rater_a": "INCLUDE", "rater_b": "INCLUDE"} for i in range(5)] + \
            [{"id": f"q{i}", "rater_a": "EXCLUDE", "rater_b": "EXCLUDE"} for i in range(5)]
    SPLIT = [{"id": f"p{i}", "rater_a": "INCLUDE", "rater_b": "EXCLUDE"} for i in range(5)] + \
            [{"id": f"q{i}", "rater_a": "EXCLUDE", "rater_b": "EXCLUDE"} for i in range(5)]

    def test_reports_disagreements(self):
        code, out, _ = self.run_cli(self.SPLIT)
        self.assertEqual(code, 0)
        self.assertIn("Disagreements to adjudicate", out)
        self.assertIn("p0", out)

    def test_low_kappa_warns(self):
        _, out, _ = self.run_cli(self.SPLIT)
        self.assertIn("Kappa below 0.60", out)

    def test_min_kappa_fails_a_poor_run(self):
        code, _, _ = self.run_cli(self.SPLIT, "--min-kappa", "0.60")
        self.assertEqual(code, 1)

    def test_min_kappa_passes_a_good_run(self):
        code, _, _ = self.run_cli(self.AGREE, "--min-kappa", "0.60")
        self.assertEqual(code, 0)

    def test_malformed_line_is_skipped_with_a_warning(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / "s.jsonl"
        p.write_text('{"id":"a","rater_a":"INCLUDE","rater_b":"INCLUDE"}\n{oops\n',
                     encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["kappa.py", str(p)]), \
                redirect_stdout(out), redirect_stderr(err):
            code = kp.main()
        self.assertEqual(code, 0)
        self.assertIn("skipping malformed line 2", err.getvalue())

    def test_json_mode_emits_parseable_output(self):
        _, out, _ = self.run_cli(self.SPLIT, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["n"], 10)
        self.assertEqual(payload["n_disagreements"], 5)


class TestMinKappaGateOnUndefinedKappa(unittest.TestCase):
    """PRE-EXISTING BEHAVIOUR — documented here rather than silently changed.

    `--min-kappa` skips the comparison when kappa is NaN (`kappa == kappa` is a
    NaN guard). NaN arises in two very different situations:

      1. Both raters used a single shared label — perfect agreement, no variance.
         Passing is defensible.
      2. The input was EMPTY — nothing was screened at all. Passing is a
         fail-open hole in a gating script, which constitution Principle IV
         forbids.

    These tests pin current behaviour so the second case is visible and can be
    raised as its own change rather than folded into this feature's diff.
    """

    def run_file(self, text, *args):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = pathlib.Path(d.name) / "s.jsonl"
        p.write_text(text, encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["kappa.py", str(p), *args]), \
                redirect_stdout(out), redirect_stderr(err):
            code = kp.main()
        return code, out.getvalue(), err.getvalue()

    def test_single_label_agreement_passes_the_gate(self):
        rows = "\n".join(json.dumps({"id": f"p{i}", "rater_a": "INCLUDE",
                                     "rater_b": "INCLUDE"}) for i in range(10))
        code, out, _ = self.run_file(rows + "\n", "--min-kappa", "0.60")
        self.assertEqual(code, 0)
        self.assertIn("n/a", out)   # kappa renders as n/a, never a literal 'nan'

    def test_empty_input_currently_passes_the_gate(self):
        """⚠️ Fail-open: nothing screened, yet --min-kappa reports success."""
        code, out, _ = self.run_file("", "--min-kappa", "0.60")
        self.assertEqual(code, 0, "behaviour changed — update the finding in tasks.md T060")
        self.assertIn("**0**", out)


if __name__ == "__main__":
    unittest.main()
