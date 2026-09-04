from __future__ import annotations

import json
import unittest

from _load import load

pf = load("skills/prisma-flow/scripts/prisma_flow.py")


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

    def test_unknown_variant_is_left_for_legacy_closed_schema_to_reject(self):
        self.assertEqual("not_a_variant", pf._declared_variant('{"variant":"not_a_variant"}'))
        self.assertNotIn("not_a_variant", pf._UPDATED_VARIANTS)

    def test_legacy_public_api_is_reexported(self):
        # These are core helpers/constants exercised throughout the pre-existing
        # test suite; the dispatcher must not hide them.
        self.assertTrue(hasattr(pf, "validate_record"))
        self.assertTrue(hasattr(pf, "reconcile"))
        self.assertTrue(hasattr(pf, "RECORD_KEYS"))


if __name__ == "__main__":
    unittest.main()
