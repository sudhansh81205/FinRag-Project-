"""Inspect real dense rankings and original evidence without an answer model."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.indexing.bge import BGEEncoder  # noqa: E402
from src.indexing.store import ExactStore  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--store", type=Path, default=ROOT / "data/index/bge-faiss")
    parser.add_argument("--model-cache", type=Path, default=ROOT / "output/models")
    parser.add_argument("--filters", default="{}", help="Explicit JSON equality/list filters")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        store = ExactStore(args.store)
        encoder = BGEEncoder(cache_folder=str(args.model_cache))
        results = store.query(args.question, encoder, k=args.k, filters=json.loads(args.filters))
        print(
            json.dumps({"status": "ok" if results else "no_evidence", "results": results}, indent=2)
        )
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Dense query failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
