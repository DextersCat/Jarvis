# Normalizer Testbed v1.0beta

This package is a small, self-contained harness for developing and validating the JARVIS normalizer/intent manager. It deliberately avoids any dependency on the rest of the JARVIS codebase.

Contents:
- `intent_types.py`: Defines the canonical `IntentObject`, confidence buckets, and helpers.
- `normalizer_base.py`: Base interface plus a stub `EchoNormalizer`.
- `testcases_v1.py`: Golden test cases (v1.0beta).
- `testbed_runner_v1.py`: CLI runner that executes the golden tests against a provided normalizer.

Usage:
```bash
python -m normalizer_testbed.testbed_runner_v1
```

Current behaviour:
- The default `EchoNormalizer` is a stub and will fail the golden tests. Replace it with a real normalizer (e.g., LLM-backed) to validate implementations against the golden set.

Notes:
- Pure Python, stdlib-only. No external dependencies.
- Keep this harness decoupled; it is intended as a drop-in test utility for future normalizer iterations.
