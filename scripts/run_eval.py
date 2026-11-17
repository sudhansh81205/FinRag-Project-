"""Compatibility refusal for the retired evaluator; use run_benchmarks.py.

Retained because regression tests and older callers must never revive the old
mock/automatic-provider evaluation path. This module does not execute a study.
"""


def run_evaluation_suite(provider=None):
    raise RuntimeError(
        "Evaluation is not ready through this retired entry point. "
        "Use scripts/run_benchmarks.py with source-bound inputs and actual acceptance. "
        "Mock/auto evaluation is forbidden."
    )


if __name__ == "__main__":
    raise SystemExit("Legacy evaluation disabled. Use scripts/run_benchmarks.py --help.")
