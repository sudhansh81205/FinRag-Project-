"""Inventory the explicitly selected datasets without inventing exclusions/approval."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.benchmark.inventory import build_inventory  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-dir", type=Path, required=True,
                        help="Explicit official import or smoke-fixture directory")
    parser.add_argument("--output", type=Path, default=ROOT / "output/benchmarks/case_inventory.json")
    args = parser.parse_args()
    result = build_inventory(args.benchmark_dir, ROOT / "data/charts")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Inventoried {result['total_selected_cases']} actual selected cases; acceptance remains pending.")


if __name__ == "__main__":
    main()
