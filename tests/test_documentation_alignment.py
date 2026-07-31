"""Keep user-facing workflow guidance aligned with the runnable contracts."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _load import load  # noqa: E402


REPO = pathlib.Path(__file__).resolve().parent.parent
README = REPO / "skills" / "validate-evidence" / "README.md"
SKILL = REPO / "skills" / "validate-evidence" / "SKILL.md"
DATA_MODEL = (
    REPO / "specs" / "001-standards-enforcement-parity" / "data-model.md"
)


class TestGradeWorkflowDocumentation(unittest.TestCase):
    def test_readme_grades_results_not_individual_studies(self):
        text = README.read_text(encoding="utf-8")
        self.assertNotIn("Grade per study", text)
        self.assertNotIn("Evidence Assessment: Study", text)
        self.assertIn("One certainty rating per protocol outcome or synthesis theme", text)
        self.assertIn("## Evidence Profile: All-cause mortality", text)

    def test_confirmed_rob_examples_name_the_generated_appraisal_path(self):
        expected = "../appraise-risk-of-bias/appraisal/risk-of-bias.json"
        obsolete = "../appraise-risk-of-bias/risk-of-bias.json"
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn(expected, text)
        self.assertNotIn(obsolete, text)


class TestChecklistDataModelDocumentation(unittest.TestCase):
    def test_neither_and_both_fields_have_distinct_classifications(self):
        text = DATA_MODEL.read_text(encoding="utf-8")
        self.assertIn("neither field is unaddressed", text)
        self.assertIn("method violation (exit 1", text)
        self.assertIn("both fields is malformed input (exit 2)", text)
        self.assertIn("emits no artifact", text)


if __name__ == "__main__":
    unittest.main()


class TestChecklistRowStructureClaims(unittest.TestCase):
    """The skill and the quickstart both describe the 27-vs-42 relationship.

    They described it wrongly: "a record addressing all 27 top-level numbers" is
    not a record the check can accept, because six of those numbers exist only as
    lettered rows. A reader following the sentence built a record that failed at
    exit 2 for a reason the sentence never mentions.
    """

    def test_the_row_counts_the_docs_state_are_true(self):
        pc = load("skills/prisma-flow/scripts/prisma_checklist.py")
        rows = [number for _, number, _ in pc.PRISMA_2020]
        bare = [n for n in rows if n.isdigit()]
        self.assertEqual(len(rows), 42)
        self.assertEqual(len(bare), 21)
        for number in ("10", "13", "16", "20", "23", "24"):
            with self.subTest(number=number):
                self.assertNotIn(number, bare)     # exists only as lettered rows

    def test_a_bare_expanding_number_is_malformed_not_incomplete(self):
        """The distinction the corrected prose now draws."""
        import io as _io
        import json as _json
        import tempfile as _tempfile
        from contextlib import redirect_stdout as _ro, redirect_stderr as _re
        from unittest import mock as _mock
        pc = load("skills/prisma-flow/scripts/prisma_checklist.py")
        rec = {"schema_version": "1.0", "variant": "prisma_2020",
               "items": [{"number": "13", "location": "p. 4"}]}
        with _tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "cl.json"
            p.write_text(_json.dumps(rec), encoding="utf-8")
            out, err = _io.StringIO(), _io.StringIO()
            with _mock.patch.object(sys, "argv", ["prisma_checklist.py", str(p), "--strict"]), \
                    _ro(out), _re(err):
                code = pc.main()
        self.assertEqual(code, 2)
        self.assertIn("'13' is not an item", err.getvalue())
