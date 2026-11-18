"""PRD R5/R6/R7/R10/R12: frozen development validation, not final A-G acceptance.

Freeze before execution. Actual local HTTP answers never receive reference values.
Retrieval-only dense versus RRF60 uses the same original questions, source records,
query vectors, explicit filing/scope filters and candidate depths. No claim of
independent human labels, official benchmark performance, RAGAS or final acceptance.
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
import warnings
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_local_workspace import private_token  # noqa: E402
from src.validation_metrics import clustered_interval, ranked_operand_metrics  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def source_check(record, soups):
    """Read original inline fact, scale and period independently of answer code."""
    m = record["metadata"]
    soup = soups[m["source_sha256"]]
    nodes = soup.select(m["source_locator"])
    if len(nodes) != 1:
        raise ValueError("Original source locator is not unique")
    node = nodes[0]
    facts = ([node] if node.name.lower().endswith("nonfraction") else node.find_all(
        lambda n: n.name and n.name.lower().endswith("nonfraction")))
    facts = [f for f in facts if f.get("name") == m["metric"] and f.get("contextref") == m["context_ref"]]
    if len(facts) != 1:
        raise ValueError("Original fact metric/context differs from reference")
    fact = facts[0]
    raw = fact.get_text("", strip=True)
    number = re.sub(r"[\s,$()]", "", raw).replace("−", "-")
    value = Decimal(number) if number not in {"—", "–", "-"} else Decimal(0)
    if fact.get("sign") == "-" or raw.startswith("("):
        value = -abs(value)
    value = value.scaleb(int(fact.get("scale", "0")))
    if value != Decimal(m["normalized_value_decimal"]):
        raise ValueError("Original inline value/scale differs from reference")
    # Incorporated exhibits may carry facts whose contexts live in the main10-K.
    context_source = m.get("context_source_sha256", m["source_sha256"])
    context = soups[context_source].find(id=m["context_ref"])
    end = context.find(lambda n: n.name and n.name.lower().split(":")[-1] in {"enddate", "instant"}) if context else None
    if end is None or end.get_text(strip=True) != m["period_end"]:
        raise ValueError(f"Original context period differs: {record['evidence_id']} expected {m['period_end']}, actual {end.get_text(strip=True) if end else 'missing'}")
    return {"source_sha256": m["source_sha256"], "locator": m["source_locator"],
            "metric": m["metric"], "context_ref": m["context_ref"], "period_end": m["period_end"],
            "context_source_sha256": context_source,
            "inline_display": raw, "normalized_value": str(value), "checked": True}


def prepare(output):
    if (output / "manifest.json").exists():
        raise ValueError("Frozen run exists; use run, or choose a new directory")
    output.mkdir(parents=True, exist_ok=True)
    bank = json.loads((ROOT / "outputs/finrag-final-20261118/sample-questions.json").read_text())
    filings = bank["filings"]
    cases, proofs = [], {}
    for filing in filings:
        accession = filing["accession"]
        package = json.loads((ROOT / f"output/nov17/corpus/records/{accession}.json").read_text())
        records = package["variants"]["C"]["records"]
        by_id = {r["evidence_id"]: r for r in records}
        profile = json.loads((ROOT / "data/corpus_html_profiles.json").read_text())[accession]
        names = [accession + ".html.gz"]
        if profile.get("exhibit"):
            names.append(profile["exhibit"]["filename"] + ".gz")
        soups = {}
        for name in names:
            raw = gzip.decompress((ROOT / "data/source/corpus" / name).read_bytes())
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
                soups[hashlib.sha256(raw).hexdigest()] = BeautifulSoup(raw, "lxml")
        for q in bank["questions"]:
            if q["accession"] != accession or q["type"] not in {"Numerical", "Comparison"}:
                continue
            groups, operand_values = [], []
            for identity in q["source_ids"]:
                record = by_id[identity]
                proof = source_check(record, soups)
                proofs[identity] = proof
                m = record["metadata"]
                # Count equivalent repeated occurrences as one required financial fact.
                keys = ("accession", "metric", "scope", "period_kind", "period_start", "period_end", "normalized_unit", "normalized_value_decimal")
                groups.append([r["evidence_id"] for r in records if all(r["metadata"].get(k) == m.get(k) for k in keys)])
                operand_values.append((m, Decimal(proof["normalized_value"])))
            value = None
            if operand_values:
                if "gross margin" in q["question"].lower():
                    revenue = next(v for m, v in operand_values if m["metric"].split(":")[-1] in {"Revenues", "Revenue", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"})
                    gross = next((v for m, v in operand_values if m["metric"].endswith(":GrossProfit")), None)
                    if gross is None:
                        cost = next(v for m, v in operand_values if "CostOf" in m["metric"])
                        gross = revenue - cost
                    value = gross / revenue * 100
                    unit = "percent"
                elif q["type"] == "Comparison":
                    pairs = sorted(operand_values, key=lambda p: p[0]["period_end"])
                    value = (pairs[-1][1] - pairs[0][1]) / pairs[0][1] * 100
                    unit = "percent"
                else:
                    value, unit = operand_values[0][1], "USD"
                if abs(value - Decimal(q["expected"].split()[0])) > Decimal("0.00000001"):
                    raise ValueError("Independent original-value calculation differs from question reference")
            cases.append({"id": q["id"], "category": "numerical", "accession": accession,
                "input": {"question": q["question"], "ticker": filing["ticker"], "accession": accession,
                          "value_period_end": filing["period_end"], "scope": "consolidated", "period_kind": "duration", "mode": "auto"},
                "reference": {"expected_status": "ok" if groups else "insufficient_evidence", "value": str(value) if value is not None else None,
                              "unit": unit if groups else None, "operand_groups": groups, "original_source_verified": bool(groups)}})
    def add(identity, ticker, year, question, reference, mode="auto"):
        filing = next(f for f in filings if f["ticker"] == ticker and f["period_end"].startswith(year))
        cases.append({"id": identity, "category": "robustness", "accession": filing["accession"],
                      "input": {"question": question, "ticker": ticker, "accession": filing["accession"],
                                "value_period_end": filing["period_end"], "scope": "consolidated", "period_kind": "duration", "mode": mode},
                      "reference": reference})
    rejects = [
        ("wrong-company", "AAPL", "2025", "What was Microsoft's revenue in FY2025?"),
        ("wrong-year", "AAPL", "2021", "How much revenue did Apple report in FY2025?"),
        ("unknown-company", "AAPL", "2025", "How much revenue did Tesla report in FY2025?"),
        ("live-price", "AAPL", "2025", "What is Apple's stock price today?"),
        ("quarter", "MSFT", "2025", "What was Microsoft's Q2 revenue in FY2025?"),
        ("prediction", "AAPL", "2025", "Predict Apple's revenue for FY2026."),
        ("cross-company", "AAPL", "2025", "Compare Apple and Microsoft revenue in FY2025."),
        ("non-adjacent", "AAPL", "2025", "What was Apple's revenue growth from FY2021 to FY2025?")]
    for identity, ticker, year, question in rejects:
        add(identity, ticker, year, question, {"expected_status": "invalid_request", "kind": "guard"})
    add("component-azure", "MSFT", "2025", "How much revenue did Microsoft report from Azure in FY2025?",
        {"kind": "unsupported_component", "expected_status": "refuse_or_clarify", "forbidden_total": "281724000000",
         "note": "No independently labelled Azure-specific answer; refuse/clarify instead of silently returning consolidated total."})
    add("component-iphone", "AAPL", "2025", "How much revenue did Apple report from iPhone in FY2025?",
        {"kind": "unsupported_component", "expected_status": "refuse_or_clarify", "forbidden_total": "416161000000",
         "note": "Current scope is consolidated; do not substitute total sales for iPhone sales."})
    add("margin-relative-percent", "AAPL", "2021", "By what percentage did Apple's gross margin increase from FY2020 to FY2021?",
        {"kind": "relative_margin", "value": "9.274942904673689867808751534", "unit": "percent", "expected_status": "ok",
         "note": "Relative growth is9.27%; absolute change3.55percentage points is a different quantity."})
    add("compound-metrics", "AAPL", "2025", "What were Apple's revenue and net income in FY2025?",
        {"kind": "compound", "expected_status": "two_values_or_clarification", "required_values": ["416161000000", "112010000000"]})
    for ticker, year in [("AAPL", "2025"), ("MSFT", "2025"), ("NVDA", "2024"), ("IBM", "2024"), ("CSCO", "2024"), ("ORCL", "2024")]:
        filing = next(f for f in filings if f["ticker"] == ticker and f["period_end"].startswith(year))
        cases.append({"id": f"narrative-{ticker}-{year}", "category": "narrative_manual", "accession": filing["accession"],
            "input": {"question": f"What risks does {filing['issuer']} describe in its FY{year} annual report?",
                      "ticker": ticker, "accession": filing["accession"], "value_period_end": filing["period_end"],
                      "scope": "consolidated", "period_kind": "duration", "mode": "narrative"},
            "reference": {"review_status": "unreviewed", "rubric": ["Each material claim supported by the included original source", "No contradicted/invented claim", "Relevant and complete within cited scope"], "reviewer": None}})
    (output / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    (output / "reference-source-checks.json").write_text(json.dumps(proofs, indent=2) + "\n")
    files = [ROOT / "outputs/finrag-final-20261118/sample-questions.json", ROOT / "data/application_filings.json",
             ROOT / "data/corpus_html_profiles.json", ROOT / "output/nov17/corpus/coverage.json",
             ROOT / "scripts/evaluate_workspace.py", *sorted((ROOT / "src").rglob("*.py"))]
    manifest = {"created_at_utc": datetime.now(UTC).isoformat(), "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "study": "PRD-aligned development application validation and table-cell retrieval component comparison",
        "final_prd_experiment": False, "independently_reviewed": False, "held_out": False,
        "case_count": len(cases), "by_category": {k: sum(c["category"] == k for c in cases) for k in {c["category"] for c in cases}},
        "reference_origin": "Existing development question bank; numerical values recomputed from original inline facts/scale/context. No independent human review; financial interpretation shares parsed metric labels.",
        "controls": {"relative_tolerance": 0.01, "wrong_unit_or_period_fails": True, "zero_policy": "No zero-reference cases selected", "seed": 42, "bootstrap_resamples": 10000,
                     "retrieval_depth_each_stream": 10, "rrf_k": 60, "primary_generator": "Interactive deterministic calculator for known numeric programs; configured pinned Gemma for narrative. Not an A-G answer-model comparison."},
        "inputs": {str(p.relative_to(ROOT)): digest(p) for p in files},
        "cases_sha256": digest(output / "cases.json"), "reference_checks_sha256": digest(output / "reference-source-checks.json")}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"frozen_cases": len(cases), "original_inline_operands_checked": len(proofs), "by_category": manifest["by_category"], "held_out": False}), flush=True)


def frozen(output):
    manifest = json.loads((output / "manifest.json").read_text())
    for name, expected in manifest["inputs"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("Frozen code/source changed; use a new declared evaluation run")
    if digest(output / "cases.json") != manifest["cases_sha256"] or digest(output / "reference-source-checks.json") != manifest["reference_checks_sha256"]:
        raise ValueError("Frozen references changed")
    return manifest, json.loads((output / "cases.json").read_text())


def assess(case, result):
    ref = case["reference"]
    category = case["category"]
    evidence = result.get("evidence", [])
    included = result.get("included_evidence_ids", [])
    ids = [r.get("evidence_id", r.get("id")) for r in evidence]
    isolated = bool(evidence) and all(r.get("metadata", {}).get("accession") == case["accession"] for r in evidence)
    citation_identity = bool(ids) and len(ids) == len(set(ids)) and set(ids) == set(included)
    unit_ok, period_ok, relative_error, correct = False, False, None, False
    calc = (result.get("calculations") or [{}])[0]
    if category == "narrative_manual":
        return {"automated_correct": None, "manual_review": "pending", "citation_identity": citation_identity, "accession_isolated": isolated}
    if ref.get("expected_status") == "invalid_request":
        correct = result.get("status") == "invalid_request" and not result.get("answer")
    elif ref.get("expected_status") == "insufficient_evidence":
        correct = result.get("status") == "insufficient_evidence" and not result.get("answer")
    elif ref.get("kind") in {"unsupported_component", "compound"}:
        if result.get("status") in {"invalid_request", "insufficient_evidence"} and not result.get("answer"):
            correct = True
        elif ref.get("kind") == "compound":
            got = {c.get("result") for c in result.get("calculations", [])}
            correct = result.get("status") == "ok" and set(ref["required_values"]) <= got and isolated
    elif result.get("status") == "ok" and calc.get("status") == "ok":
        try:
            predicted, expected = Decimal(calc["result"]), Decimal(ref["value"])
            relative_error = str(abs(predicted - expected) / abs(expected))
            unit_ok = calc.get("unit") == ref["unit"]
            allowed_ends = {p["end"] for p in calc.get("program", {}).get("periods", [])}
            period_ok = bool(allowed_ends) and max(allowed_ends) == case["input"]["value_period_end"]
            groups = ref.get("operand_groups", [])
            operands_present = all(set(group) & set(included) for group in groups)
            correct = Decimal(relative_error) <= Decimal("0.01") and unit_ok and period_ok and isolated and citation_identity and operands_present
        except (KeyError, ArithmeticError):
            pass
    return {"automated_correct": bool(correct), "unit_correct": unit_ok, "period_correct": period_ok,
            "relative_error": relative_error, "citation_identity": citation_identity, "accession_isolated": isolated}


def run_http(output):
    _, cases = frozen(output)
    token = private_token(ROOT / "output/nov17/local-service.json")
    headers = {"Authorization": "Bearer " + token}
    health = requests.get("http://127.0.0.1:8000/health", headers=headers, timeout=10).json()
    if health.get("status") != "ready" or len(health.get("supported_filings", [])) != 18:
        raise ValueError("Expected 18-filing runtime is not ready")
    path = output / "http-results.jsonl"
    existing = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    by_id = {c["id"]: c for c in cases}
    for row in existing:
        if row["id"] not in by_id or row["input_sha256"] != hashlib.sha256(encoded(by_id[row["id"]]["input"])).hexdigest():
            raise ValueError("Saved output differs from frozen inputs")
    done = {r["id"] for r in existing}
    for case in cases:
        if case["id"] in done:
            continue
        start = time.perf_counter()
        try:
            response = requests.post("http://127.0.0.1:8000/answer", headers=headers, json=case["input"], timeout=250)
            result = response.json()
        except requests.RequestException as exc:
            result = {"status": "transport_error", "answer": "", "message": type(exc).__name__}
        row = {"id": case["id"], "category": case["category"], "accession": case["accession"],
               "input_sha256": hashlib.sha256(encoded(case["input"])).hexdigest(),
               "latency_seconds": time.perf_counter() - start, "result": result, "score": assess(case, result)}
        with path.open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(case["id"], result.get("status"), row["score"].get("automated_correct"), round(row["latency_seconds"], 3), flush=True)


def run_retrieval(output, model_cache):
    _, cases = frozen(output)
    from src.indexing.bge import BGEEncoder
    from src.indexing.store import ExactStore
    from src.retrieval.bm25 import BM25Retriever, reciprocal_rank_fusion
    store = ExactStore(ROOT / "output/nov17/corpus/C")
    encoder = BGEEncoder(cache_folder=str(model_cache), local_files_only=True)
    bm25 = BM25Retriever(store.records)
    chosen = [c for c in cases if c["category"] == "numerical" and c["reference"]["operand_groups"]]
    start = time.perf_counter()
    # Both methods consume the exact same once-computed query vector per question.
    vectors = encoder.encode([c["input"]["question"] for c in chosen], query=True)
    embedding_seconds = time.perf_counter() - start
    rows = []
    for case, vector in zip(chosen, vectors, strict=True):
        filters = {"ticker": case["input"]["ticker"], "accession": case["accession"], "scope": "consolidated", "type": "table_cell"}
        start = time.perf_counter()
        dense = store.search(vector, k=10, filters=filters)
        dense_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        # BM25's stream API selects type through top_k_tables, unlike ExactStore.
        lexical = bm25.retrieve(case["input"]["question"], top_k_text=0, top_k_tables=10,
                               filters={k: v for k, v in filters.items() if k != "type"})["table_evidence"]
        fused = reciprocal_rank_fusion([dense, lexical], k=60)[:10]
        lexical_and_fusion_ms = (time.perf_counter() - start) * 1000
        dense_ids, fused_ids = [r["evidence_id"] for r in dense], [r["evidence_id"] for r in fused]
        rows.append({"id": case["id"], "accession": case["accession"], "filters": filters,
                     "dense_ids": dense_ids, "bm25_ids": [r["evidence_id"] for r in lexical], "hybrid_ids": fused_ids,
                     "dense": ranked_operand_metrics(dense_ids, case["reference"]["operand_groups"]),
                     "hybrid": ranked_operand_metrics(fused_ids, case["reference"]["operand_groups"]),
                     "dense_search_ms": dense_ms, "bm25_plus_rrf_increment_ms": lexical_and_fusion_ms})
        print("retrieval", case["id"], flush=True)
    report = {"scope": "Retrieval-only component comparison, fixed canonical C table cells and per-filing consolidated eligibility. Not full C/D generation or final A-G runs.",
              "embedding_batch_seconds": embedding_seconds, "case_count": len(rows), "candidate_count": len(store.records),
              "query_encoder": encoder.spec.manifest_fields(), "same_query_vector_both_methods": True,
              "expansion": "Original question only; no named-metric query expansion or typed lookup", "rows": rows}
    (output / "retrieval-results.json").write_text(json.dumps(report, indent=2) + "\n")


def summarize(output):
    manifest, cases = frozen(output)
    rows = [json.loads(line) for line in (output / "http-results.jsonl").read_text().splitlines()]
    if len(rows) != len(cases) or len({r["id"] for r in rows}) != len(cases):
        raise ValueError("Incomplete output ledger; resume HTTP run before scoring")
    by_id = {c["id"]: c for c in cases}
    numeric = [r for r in rows if r["category"] == "numerical" and by_id[r["id"]]["reference"]["expected_status"] == "ok"]
    refusals = [r for r in rows if r["category"] == "numerical" and by_id[r["id"]]["reference"]["expected_status"] != "ok"]
    safety = [r for r in rows if r["category"] == "robustness"]
    narrative = [r for r in rows if r["category"] == "narrative_manual"]
    def counts(group):
        return {"passed": sum(bool(r["score"]["automated_correct"]) for r in group), "total": len(group)}
    def timing(group):
        values = sorted(r["latency_seconds"] for r in group)
        return {"median_seconds": statistics.median(values), "p95_seconds": values[round(0.95 * (len(values) - 1))],
                "n": len(values), "scope": "One local HTTP request per case; warm prepared runtime. No Vercel/network/cold-start claim."}
    summary = {"study": manifest["study"], "final_prd_experiment": False, "held_out": False, "independent_human_review": False,
               "numerical_reference_agreement": counts(numeric), "expected_numeric_refusal": counts(refusals), "robustness": counts(safety),
               "numerical_agreement_95ci": clustered_interval([{"accession": r["accession"], "correct": r["score"]["automated_correct"]} for r in numeric], "correct"),
               "numerical_latency": timing(numeric), "robustness_latency": timing(safety), "narrative_latency": timing(narrative),
               "narrative": {"requests": len(narrative), "successful_responses": sum(r["result"].get("status") == "ok" for r in narrative),
                             "citation_identity_passed": sum(r["score"]["citation_identity"] and r["score"]["accession_isolated"] for r in narrative),
                             "semantic_correctness": "UNREVIEWED; inspect claim-level original sources. Not RAGAS or an independent human score."},
               "failures": [{"id": r["id"], "question": by_id[r["id"]]["input"]["question"], "status": r["result"].get("status"),
                             "answer": r["result"].get("answer", ""), "score": r["score"]} for r in rows if r["score"].get("automated_correct") is False]}
    retrieval = json.loads((output / "retrieval-results.json").read_text())
    summary["retrieval"] = {"n": retrieval["case_count"], "scope": retrieval["scope"], "metrics": {}}
    for metric in ("recall_at_5", "recall_at_10", "complete_at_5", "complete_at_10", "mrr_at_10"):
        mapped = [{"accession": row["accession"], "dense": row["dense"][metric], "hybrid": row["hybrid"][metric],
                   "paired_delta": row["hybrid"][metric] - row["dense"][metric]} for row in retrieval["rows"]]
        summary["retrieval"]["metrics"][metric] = {name: clustered_interval(mapped, name) for name in ("dense", "hybrid", "paired_delta")}
    summary["retrieval"]["embedding_batch_seconds"] = retrieval["embedding_batch_seconds"]
    summary["retrieval"]["median_dense_search_ms"] = statistics.median(row["dense_search_ms"] for row in retrieval["rows"])
    summary["retrieval"]["median_added_bm25_rrf_ms"] = statistics.median(row["bm25_plus_rrf_increment_ms"] for row in retrieval["rows"])
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"failures", "retrieval"}}, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["prepare", "http", "retrieval", "summarize"])
    p.add_argument("--output", type=Path, default=ROOT / "output/validation-20261118-v1")
    p.add_argument("--model-cache", type=Path, default=ROOT / "output/models-http")
    a = p.parse_args()
    if a.action == "prepare":
        prepare(a.output)
    elif a.action == "http":
        run_http(a.output)
    elif a.action == "retrieval":
        run_retrieval(a.output, a.model_cache)
    else:
        summarize(a.output)


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
