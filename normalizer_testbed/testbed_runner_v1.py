from __future__ import annotations

import sys
from typing import List

from normalizer_testbed.intent_types import (
    IntentObject,
    ConfidenceBucket,
    bucket_confidence,
    intent_as_dict,
)
from normalizer_testbed.normalizer_base import BaseNormalizer, EchoNormalizer
from normalizer_testbed.testcases_v1 import TestCase, get_test_cases_v1


def run_tests(normalizer: BaseNormalizer) -> int:
    cases: List[TestCase] = get_test_cases_v1()
    failures = []

    for idx, case in enumerate(cases, start=1):
        actual: IntentObject = normalizer.normalize(case.raw_text)
        expected = case.expected

        mismatches = []

        if actual.domain != expected.domain:
            mismatches.append(f"domain mismatch: expected='{expected.domain}', actual='{actual.domain}'")
        if actual.action != expected.action:
            mismatches.append(f"action mismatch: expected='{expected.action}', actual='{actual.action}'")
        if actual.search_term != expected.search_term:
            mismatches.append(f"search_term mismatch: expected='{expected.search_term}', actual='{actual.search_term}'")
        if actual.fuzzy_allowed != expected.fuzzy_allowed:
            mismatches.append(
                f"fuzzy_allowed mismatch: expected={expected.fuzzy_allowed}, actual={actual.fuzzy_allowed}"
            )

        # Parameters: only check keys present in expected.parameters
        for key, val in expected.parameters.items():
            if key not in actual.parameters:
                mismatches.append(f"missing parameter key: '{key}'")
            elif actual.parameters.get(key) != val:
                mismatches.append(
                    f"parameter mismatch for '{key}': expected='{val}', actual='{actual.parameters.get(key)}'"
                )

        expected_bucket = case.expected_confidence_bucket
        actual_bucket = bucket_confidence(actual.confidence)
        if actual_bucket != expected_bucket:
            mismatches.append(
                f"confidence bucket mismatch: expected={expected_bucket.name}, actual={actual_bucket.name}"
            )

        if mismatches:
            failures.append((case, mismatches))
            print(f"[!!] Test {idx} - {case.name}")
            for m in mismatches:
                print(f"     - {m}")
        else:
            print(f"[OK] Test {idx} - {case.name}")

    passed = len(cases) - len(failures)
    print(f"\nPassed {passed}/{len(cases)} tests.")
    return 0 if not failures else 1


if __name__ == "__main__":
    normalizer: BaseNormalizer = EchoNormalizer()
    exit_code = run_tests(normalizer)
    sys.exit(exit_code)

