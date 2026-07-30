"""Keep user-facing workflow guidance aligned with the runnable contracts."""

import pathlib
import unittest


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
