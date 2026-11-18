"""Validate source identity, scoring and saved generation context."""

import json

from run_evaluation import REPO, load_suite, metrics

ROOT = REPO / "docs/validation/official-source"
for name in ("FinanceBench", "FinQA", "TAT-QA"):
    cases, records, hashes = load_suite(name)
    ids = {r["evidence_id"] for r in records}
    base = ROOT / "results" / name
    manifest = json.loads((base / "manifest.json").read_text())
    assert manifest["input_sha256"] == hashes
    rows = json.loads((base / "rankings.json").read_text())
    assert [r["case_id"] for r in rows] == [c["case_id"] for c in cases]
    for case, row in zip(cases, rows, strict=True):
        assert len(row["ranked_ids"]) == len(set(row["ranked_ids"]))
        assert set(row["ranked_ids"]) <= ids
        assert row["gold_ids"] == sorted(set(case["gold"].get("gold_evidence_ids", [])))
        assert row["metrics"] == metrics(row["ranked_ids"], row["gold_ids"])
        assert not row["missing_gold_ids"]
    pilot = json.loads((base / "generation-pilot.json").read_text())
    assert pilot["case_id"] == cases[0]["case_id"]
    assert {r["evidence_id"] for r in pilot["included_context"]} <= set(rows[0]["ranked_ids"])
    assert pilot["result"]["model"] == "gemma3:4b"
    if (base / "dense-hybrid-rankings.json").exists():
        dense = json.loads((base / "dense-hybrid-rankings.json").read_text())
        assert len(dense) == len(cases)
        for case, row in zip(cases, dense, strict=True):
            for method in ("dense", "hybrid"):
                ranking = row[method + "_ids"]
                assert len(ranking) == len(set(ranking)) == 10
                assert set(ranking) <= ids
                assert row[method] == metrics(ranking, case["gold"].get("gold_evidence_ids", []))
    print(name, "source hashes, per-case metrics and actual included pilot contexts PASS")
