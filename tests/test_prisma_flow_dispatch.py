from __future__ import annotations

import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from _load import load

pf = load("skills/prisma-flow/scripts/prisma_flow.py")


def _run(rec, *args):
    out, err = io.StringIO(), io.StringIO()
    d = tempfile.TemporaryDirectory()
    try:
        p = pathlib.Path(d.name) / "counts.json"
        p.write_text(json.dumps(rec), encoding="utf-8")
        with mock.patch.object(sys, "argv", ["prisma_flow.py", str(p), *args]), \
                redirect_stdout(out), redirect_stderr(err):
            code = pf.main()
        return code, out.getvalue(), err.getvalue()
    finally:
        d.cleanup()


class PrismaFlowDispatchTests(unittest.TestCase):
    def test_updated_variants_are_detected_explicitly(self):
        for variant in (
            "updated_databases_registers",
            "updated_databases_registers_other_methods",
        ):
            with self.subTest(variant=variant):
                self.assertEqual(variant, pf._declared_variant(json.dumps({"variant": variant})))

    def test_legacy_record_without_variant_is_not_reclassified(self):
        self.assertIsNone(pf._declared_variant('{"schema_version":"1.0"}'))

    def test_an_unrecognised_variant_is_named_by_declared_variant(self):
        self.assertEqual("not_a_variant", pf._declared_variant('{"variant":"not_a_variant"}'))
        self.assertNotIn("not_a_variant", pf._UPDATED_VARIANTS)

    def test_legacy_public_api_is_reexported(self):
        # These are core helpers/constants exercised throughout the pre-existing
        # test suite; the dispatcher must not hide them.
        self.assertTrue(hasattr(pf, "validate_record"))
        self.assertTrue(hasattr(pf, "reconcile"))
        self.assertTrue(hasattr(pf, "RECORD_KEYS"))


class PrismaFlowDispatchMainTests(unittest.TestCase):
    """F24-06: main() itself must fail closed on a mistyped variant, naming the
    variant rather than deferring to the legacy engine's closed-schema rejection
    of the whole updated-only key set."""

    def test_mistyped_variant_is_named_directly_not_left_to_the_legacy_schema(self):
        rec = {
            "schema_version": "1.0", "variant": "updated_database_register",  # typo
            "identified_databases": {"MEDLINE": 100}, "identified_registers": {},
            "duplicates_removed": 0, "removed_other_reasons": 0,
            "records_screened": 100, "records_excluded_title_abstract": 70,
            "reports_sought": 30, "reports_not_retrieved": 2, "reports_assessed": 28,
            "reports_excluded": {}, "new_studies_included_databases": 28,
            "previous_studies_included": 15, "previous_reports_included": 18,
            "new_studies_included": 28, "new_reports_included": 28,
            "updated_studies_included": 43, "updated_reports_included": 46,
        }
        code, out, err = _run(rec, "--strict")
        self.assertEqual(code, 2)
        self.assertIn("record.variant", err)
        self.assertIn("updated_database_register", err)
        # The previous diagnostic buried the typo behind the unrelated updated-only
        # keys; this asserts the new message no longer leads with them.
        self.assertNotIn("new_reports_included", err)

    def test_omitted_variant_on_an_updated_shaped_record_is_still_left_to_legacy(self):
        """Unchanged behaviour: no `variant` key at all is not this dispatcher's
        business to diagnose — the legacy engine's own closed schema rejects the
        updated-only keys it does not recognise."""
        rec = {
            "schema_version": "1.0",
            "previous_studies_included": 15, "previous_reports_included": 18,
            "new_studies_included": 10, "new_reports_included": 12,
            "updated_studies_included": 25, "updated_reports_included": 30,
        }
        code, out, err = _run(rec, "--strict")
        self.assertEqual(code, 2)
        self.assertNotIn("record.variant", err)

    def test_unhashable_variant_fails_closed_without_crashing(self):
        """A `variant` that is itself a list is not a string the dispatcher can
        recognise, but it must still fail closed at exit 2 rather than crash with
        an unhandled TypeError on set membership (`[...] in _UPDATED_VARIANTS`)."""
        code, out, err = _run({"schema_version": "1.0", "variant": ["oops"]}, "--strict")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_valid_updated_variant_still_dispatches_and_reconciles(self):
        rec = {
            "schema_version": "1.0", "variant": "updated_databases_registers",
            "identified_databases": {"MEDLINE": 100}, "identified_registers": {"CENTRAL": 20},
            "duplicates_removed": 20, "removed_other_reasons": 0,
            "records_screened": 100, "records_excluded_title_abstract": 70,
            "reports_sought": 30, "reports_not_retrieved": 2, "reports_assessed": 28,
            "reports_excluded": {"wrong population": 18}, "new_studies_included_databases": 10,
            "previous_studies_included": 15, "previous_reports_included": 18,
            "new_studies_included": 10, "new_reports_included": 12,
            "updated_studies_included": 25, "updated_reports_included": 30,
        }
        code, out, err = _run(rec, "--strict")
        self.assertEqual(code, 0, msg=out + err)
        self.assertIn("updated-review flow", out)

    def test_argparse_based_parsing_accepts_flags_before_the_positional_file(self):
        """F24-07: the dispatcher used to select the input path with
        `not arg.startswith("-")`, a manual scan that argparse.parse_known_args()
        replaces. Flags interleaved around the positional file must still resolve
        to the same file, in either order."""
        rec = {"schema_version": "1.0", "identified_databases": {"OpenAlex": 10},
               "studies_included_total": 0}
        code_first, out1, _ = _run(rec, "--json")
        d = tempfile.TemporaryDirectory()
        try:
            p = pathlib.Path(d.name) / "counts.json"
            p.write_text(json.dumps(rec), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(sys, "argv", ["prisma_flow.py", "--json", str(p)]), \
                    redirect_stdout(out), redirect_stderr(err):
                code_flag_before = pf.main()
        finally:
            d.cleanup()
        self.assertEqual(code_first, code_flag_before)
        self.assertEqual(out1, out.getvalue())


if __name__ == "__main__":
    unittest.main()
