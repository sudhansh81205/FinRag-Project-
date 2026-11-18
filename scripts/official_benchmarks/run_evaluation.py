"""Official-corpus retrieval evaluation and bounded real-model pilot.

Runs in isolation from the deployed application. Gold IDs enter scoring only.
"""

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "docs/validation/official-source"
SOURCE_DIR = Path(
    os.environ.get("FINRAG_BENCHMARK_SOURCE_DIR", REPO / "output/benchmarks/official")
)
OUTPUT_DIR = Path(os.environ.get("FINRAG_BENCHMARK_OUTPUT", REPO / "output/official-evaluation"))
sys.path.insert(0, str(REPO))
from src.retrieval.bm25 import _tokenize  # noqa: E402
from src.validation_metrics import clustered_interval  # noqa: E402

SUITES = {
    "FinanceBench": ("financebench_full_document_150.json", "financebench_full_pages.json", 150),
    "FinQA": ("finqa_candidate_universe.json", "finqa_context_corpus.json", 1147),
    "TAT-QA": ("tatqa_candidate_universe.json", "tatqa_context_corpus.json", 1663),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)


def load_suite(name):
    case_name, corpus_name, count = SUITES[name]
    source = SOURCE_DIR
    cases = json.loads((source / case_name).read_bytes())
    corpus = json.loads((source / corpus_name).read_bytes())
    assert len(cases) == count
    records = []
    for item in corpus:
        if name == "FinanceBench" and not item["readable"]:
            continue
        if "rows" in item:
            text = "\n".join(" | ".join(map(str, row)) for row in item["rows"])
        else:
            text = item.get("text", "")
        if text.strip():
            records.append(
                {"evidence_id": item["evidence_id"], "text": text, "doc_name": item["doc_name"]}
            )
    assert len(records) == len({r["evidence_id"] for r in records})
    imported = json.loads((source / "import_manifest.json").read_bytes())["files_sha256"]
    for filename in (case_name, corpus_name):
        if filename in imported and digest(source / filename) != imported[filename]:
            raise ValueError(f"Imported source hash mismatch: {filename}")
    if name == "FinanceBench":
        bound = json.loads((source / "financebench_full_document_150.binding.json").read_bytes())
        assert digest(source / case_name) == bound["bound_dataset_sha256"]
        assert digest(source / corpus_name) == bound["full_page_corpus_sha256"]
    return (
        cases,
        records,
        {case_name: digest(source / case_name), corpus_name: digest(source / corpus_name)},
    )


class FastBM25:
    """Sparse vector implementation of the repository's k1=1.5, b=0.75 formula."""

    def __init__(self, texts):
        terms = [Counter(_tokenize(text)) for text in texts]
        lengths = np.array([sum(t.values()) for t in terms])
        avg = lengths.mean()
        df = Counter(term for row in terms for term in row)
        self.vocabulary = {term: i for i, term in enumerate(sorted(df))}
        data, row_ids, column_ids = [], [], []
        for row, counts in enumerate(terms):
            for term, frequency in counts.items():
                idf = math.log((len(texts) - df[term] + 0.5) / (df[term] + 0.5) + 1)
                weight = (
                    idf * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * lengths[row] / avg))
                )
                data.append(weight)
                row_ids.append(self.vocabulary[term])
                column_ids.append(row)
        self.matrix = csr_matrix((data, (row_ids, column_ids)), shape=(len(df), len(texts)))

    def score(self, query):
        indices = [self.vocabulary[t] for t in set(_tokenize(query)) if t in self.vocabulary]
        return np.asarray(self.matrix[indices].sum(axis=0)).ravel()


def metrics(ranking, gold):
    if len(ranking) != len(set(ranking)):
        raise ValueError("Ranked source IDs must be unique")
    relevant = set(gold)
    if not relevant:
        return None
    return {
        **{
            f"recall_at_{k}": len(relevant.intersection(ranking[:k])) / len(relevant)
            for k in (5, 10)
        },
        **{f"complete_at_{k}": float(relevant.issubset(ranking[:k])) for k in (5, 10)},
        "mrr_at_10": next((1 / i for i, eid in enumerate(ranking[:10], 1) if eid in relevant), 0),
        "ndcg_at_10": sum(
            1 / math.log2(i + 1) for i, eid in enumerate(ranking[:10], 1) if eid in relevant
        )
        / sum(1 / math.log2(i + 1) for i in range(1, min(10, len(relevant)) + 1)),
    }


def run_suite(name, output):
    cases, records, hashes = load_suite(name)
    folder = output / name
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {
        "suite": name,
        "cases": len(cases),
        "records": len(records),
        "input_sha256": hashes,
        "scope": "Pooled official pages, paragraphs and whole tables; BM25 baseline",
        "query": "original question only",
        "filters": "none; whole declared suite corpus",
        "ranking": "BM25 k1=1.5 b=0.75; positive scores; tie break by evidence ID",
        "gold_used_for": "scoring only",
        "model_calls": 0,
        "prd_mapping": "R7/R12 official-source retrieval baseline; outside cumulative A-G representation controls",
        "manual_acceptance": "User reported team chart review; reviewer and exact approved IDs unspecified",
    }
    existing = folder / "manifest.json"
    if existing.exists():
        assert json.loads(existing.read_text()) == manifest, (
            "Use a fresh directory for changed inputs"
        )
    else:
        write(existing, manifest)
    # Record provenance independently of gold annotations.
    write(
        folder / "source-map.json", [{k: v for k, v in r.items() if k != "text"} for r in records]
    )
    print(name, "building", len(records), "source records", flush=True)
    start = time.perf_counter()
    index = FastBM25([r["text"] for r in records])
    index_seconds = time.perf_counter() - start
    # Verify this acceleration against the existing implementation on a fixed subset.
    from src.retrieval.bm25 import BM25Index

    sample = [
        {"evidence_id": r["evidence_id"], "content": r["text"], "metadata": {}}
        for r in records[:20]
    ]
    reference = BM25Index(sample)
    accelerated = FastBM25([r["content"] for r in sample]).score(cases[0]["question"])
    assert np.allclose(
        accelerated, [reference.score(cases[0]["question"], i) for i in range(len(sample))]
    )
    ids = [r["evidence_id"] for r in records]
    id_set = set(ids)
    rows = []
    for case in cases:
        start = time.perf_counter()
        scores = index.score(case["question"])
        order = sorted(np.flatnonzero(scores > 0), key=lambda i: (-scores[i], ids[i]))[:10]
        ranking = [ids[i] for i in order]
        elapsed = time.perf_counter() - start
        gold = sorted(set(case["gold"].get("gold_evidence_ids", [])))
        rows.append(
            {
                "case_id": case["case_id"],
                "document": case["doc_name"],
                "question": case["question"],
                "ranked_ids": ranking,
                "scores": [float(scores[i]) for i in order],
                "gold_ids": gold,
                "missing_gold_ids": sorted(set(gold) - id_set),
                "metrics": metrics(ranking, gold),
                "retrieval_seconds": elapsed,
            }
        )
    write(folder / "rankings.json", rows)
    labelled = [r for r in rows if r["metrics"] is not None]
    summary = {
        "suite": name,
        "attempted": len(rows),
        "labelled": len(labelled),
        "unlabelled": len(rows) - len(labelled),
        "missing_source_cases": sum(bool(r["missing_gold_ids"]) for r in rows),
        "index_build_seconds": index_seconds,
        "median_retrieval_seconds": statistics.median(r["retrieval_seconds"] for r in rows),
        "metrics": {
            key: clustered_interval(
                [{"accession": r["document"], "value": r["metrics"][key]} for r in labelled],
                "value",
                samples=10000,
            )
            for key in labelled[0]["metrics"]
        },
    }
    write(folder / "summary.json", summary)
    print(name, json.dumps({k: v["estimate"] for k, v in summary["metrics"].items()}), flush=True)
    return summary


def pilot(output):
    from src.llm.client import UnifiedLLMClient

    profile = json.loads((REPO / "configs/gemma3-4b.json").read_text())
    client = UnifiedLLMClient.from_profile(profile)
    client.timeout_seconds = 180
    for name in SUITES:
        folder = output / name
        if (folder / "generation-pilot.json").exists():
            continue
        cases, records, _ = load_suite(name)
        case = cases[0]
        ranking = json.loads((folder / "rankings.json").read_text())[0]["ranked_ids"]
        by_id = {r["evidence_id"]: r for r in records}
        evidence = []
        budget = 8500
        for eid in ranking[:5]:
            record = by_id[eid]
            text = record["text"][: min(2200, budget)]
            if not text:
                break
            evidence.append({"evidence_id": eid, "text": text})
            budget -= len(text)
        prompt = (
            "Answer the financial question using only the source passages below. "
            "Cite source identifiers for each claim. If passages do not establish the answer, "
            "say insufficient evidence. Show calculation premises and units when calculating.\n"
            + "Question: "
            + case["question"]
            + "\nSources:\n"
            + "\n\n".join(f"[{r['evidence_id']}]\n{r['text']}" for r in evidence)
        )
        start = time.perf_counter()
        result = client.generate(prompt)
        row = {
            "case_id": case["case_id"],
            "question": case["question"],
            "included_context": evidence,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "model_profile_sha256": digest(REPO / "configs/gemma3-4b.json"),
            "latency_seconds": time.perf_counter() - start,
            "result": result,
            "semantic_score": "Pending claim-level review; automatic answer accuracy not established",
        }
        write(folder / "generation-pilot.json", row)
        print(
            name, "real model pilot", result["status"], round(row["latency_seconds"], 2), flush=True
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    output = OUTPUT_DIR
    output.mkdir(parents=True, exist_ok=True)
    if args.pilot:
        pilot(output)
    else:
        for suite in SUITES:
            run_suite(suite, output)


if __name__ == "__main__":
    main()
