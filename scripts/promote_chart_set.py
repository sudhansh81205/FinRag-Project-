"""Verify a real independent approval ledger and save its immutable label gate.

This command does not author approvals, change labels/splits or mark captions as
approved. Supply only a ledger completed by an authenticated independent human.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.parse_filing import json_bytes, write_atomic  # noqa: E402
from src.charts.dataset import load_reviewed_set  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--charts", type=Path, default=ROOT / "data/charts")
    parser.add_argument("--approvals", type=Path, required=True)
    parser.add_argument("--trusted-reviewer", action="append", required=True)
    parser.add_argument("--label-author", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        cases, _, audit = load_reviewed_set(args.charts, args.approvals,
            trusted_reviewers=args.trusted_reviewer, label_authors=args.label_author)
        report = {**audit, "case_ids": [case["id"] for case in cases],
                  "candidate_files_modified": False}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = {"status": "blocked", "evaluation_ready": False,
                  "reason": str(exc), "candidate_files_modified": False}
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(args.output, json_bytes(report))
    except OSError as exc:
        print(json.dumps({"status": "blocked", "output": None,
                          "reason": "report_destination_unwritable", "exception_type": type(exc).__name__}))
        return 1
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0 if report.get("evaluation_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
