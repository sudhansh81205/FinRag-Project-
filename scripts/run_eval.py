"""Historical evaluation entry point, retired until the checked split is available.

The old runner had no connected index and could report mock answers as success.
Use scripts/check_generation.py for Day 3 provider checks. The matched, checked
14-case evaluation is scheduled for November 9-12; it is not implemented here.
"""


def run_evaluation_suite(provider=None):
    raise RuntimeError(
        "Evaluation is not ready: connect a validated index, checked split and explicit real "
        "provider. Mock/auto evaluation is forbidden. Use scripts/check_generation.py today."
    )


if __name__ == "__main__":
    raise SystemExit(
        "Legacy evaluation disabled: no validated index or checked split is connected. "
        "Use scripts/check_generation.py for provider verification."
    )
