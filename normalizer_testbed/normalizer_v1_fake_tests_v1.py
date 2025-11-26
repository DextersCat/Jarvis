from __future__ import annotations

import unittest

from normalizer_testbed.intent_types import bucket_confidence
from normalizer_testbed.normalizer_v1_fake import FakeNormalizerV1
from normalizer_testbed.testcases_v1 import get_test_cases_v1


class FakeNormalizerV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = FakeNormalizerV1()
        self.cases = get_test_cases_v1()

    def test_golden_cases(self):
        for case in self.cases:
            with self.subTest(case=case.name):
                actual = self.normalizer.normalize(case.raw_text)
                expected = case.expected

                # Field comparisons
                self.assertEqual(actual.domain, expected.domain, f"domain mismatch for {case.name}")
                self.assertEqual(actual.action, expected.action, f"action mismatch for {case.name}")
                self.assertEqual(actual.search_term, expected.search_term, f"search_term mismatch for {case.name}")
                self.assertEqual(actual.fuzzy_allowed, expected.fuzzy_allowed, f"fuzzy flag mismatch for {case.name}")

                # Parameters: only keys present in expected.parameters
                for key, val in expected.parameters.items():
                    self.assertIn(key, actual.parameters, f"missing parameter '{key}' for {case.name}")
                    self.assertEqual(actual.parameters.get(key), val, f"parameter '{key}' mismatch for {case.name}")

                # Confidence bucket
                self.assertEqual(
                    bucket_confidence(actual.confidence),
                    case.expected_confidence_bucket,
                    f"confidence bucket mismatch for {case.name}",
                )


if __name__ == "__main__":
    unittest.main()

