"""Run real-model rebuild/restart checks; separate from offline unit tests."""

import argparse
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_index import accepted_input  # noqa: E402
from src.contracts import sha256  # noqa: E402
from src.evidence_audit import encoded  # noqa: E402
from src.indexing.bge import BGEEncoder, unit_vectors  # noqa: E402
from src.indexing.store import ExactStore, publish_filing  # noqa: E402


def reload_checks(store_path, cache):
    store = ExactStore(store_path)
    encoder = BGEEncoder(cache_folder=str(cache))
    checks = []
    for query, filters in (
        (
            "What were Apple total net sales in 2021?",
            {"ticker": "AAPL", "type": "table_cell", "period_end": "2021-09-25"},
        ),
        (
            "What risks arise from intense competition?",
            {"ticker": "AAPL", "type": "narrative_text", "section": "Item 1A"},
        ),
    ):
        vector = encoder.encode([query], query=True)[0]
        results = store.search(vector, k=3, filters=filters)
        assert results and all(
            all(r["metadata"].get(k) == v for k, v in filters.items()) for r in results
        )
        # Independent NumPy dot products check the FAISS cosine scores.
        q = unit_vectors(vector[None, :], 1)[0]
        by_id = {r["evidence_id"]: i for i, r in enumerate(store.records)}
        assert all(
            np.isclose(r["score"], store.vectors[by_id[r["evidence_id"]]] @ q, atol=1e-6)
            for r in results
        )
        if filters["type"] == "table_cell":
            assert results[0]["metadata"]["normalized_value"] == 365817000000
            assert "Total net sales" in results[0]["content"]
            assert results[0]["metadata"]["parent_table_id"] in store.parents
        checks.append({"query": query, "filters": filters, "results": results})
    assert store.query("revenue", encoder, filters={"ticker": "MSFT"}) == []
    try:
        encoder.encode(["financial " * 600])
    except ValueError as exc:
        assert "token limit" in str(exc)
    else:
        raise AssertionError("Overlong input was silently truncated")
    return {
        "status": "passed",
        "process_id": "fresh_subprocess",
        "queries": checks,
        "numpy_cosine_agrees": True,
        "unindexed_company_returns_empty": True,
        "overlong_text_rejected": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=ROOT / "data/processed/nov04")
    parser.add_argument("--audit", type=Path, default=ROOT / "output/shanay/canonical_audit.json")
    parser.add_argument("--store", type=Path, default=ROOT / "data/index/bge-faiss")
    parser.add_argument("--model-cache", type=Path, default=ROOT / "output/models")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "output/nov06/index-verification.json"
    )
    parser.add_argument("--reload-only", action="store_true")
    args = parser.parse_args()
    start = time.monotonic()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.reload_only:
        args.output.write_bytes(encoded(reload_checks(args.store, args.model_cache)))
        return
    records, parents, provenance = accepted_input(args.package, args.audit)
    encoder = BGEEncoder(cache_folder=str(args.model_cache))
    vectors = encoder.encode([r["content"] for r in records])
    first = publish_filing(args.store, records, parents, vectors, provenance)
    second = publish_filing(args.store, records, parents, vectors, provenance)
    fresh = publish_filing(
        args.output.parent / "rebuilt-store", records, parents, vectors, provenance
    )
    assert first == second == fresh
    reload_report = args.output.parent / "reload.json"
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--reload-only",
            "--store",
            str(args.store),
            "--model-cache",
            str(args.model_cache),
            "--output",
            str(reload_report),
        ],
        check=True,
    )
    report = {
        "status": "passed",
        "fixture_scope": "one independently accepted Apple 2021 filing; not benchmark evaluation",
        "build": first,
        "candidate_types": dict(Counter(r["metadata"]["type"] for r in records)),
        "parents_stored_separately": len(parents),
        "identical_rerun_and_fresh_store": True,
        "fresh_process": json.loads(reload_report.read_bytes()),
        "seconds": round(time.monotonic() - start, 2),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packages": {
            p: importlib.metadata.version(p)
            for p in ("sentence-transformers", "transformers", "torch", "faiss-cpu", "numpy")
        },
        "code_sha256": {
            str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p.read_bytes())
            for p in [
                *sorted((ROOT / "src/indexing").glob("*.py")),
                Path(__file__).resolve(),
                ROOT / "scripts/build_index.py",
            ]
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "records": len(records),
                "generation": first["generation"],
                "seconds": report["seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
