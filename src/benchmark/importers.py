"""R7/R12: import pinned publisher data without gold/retriever-label leakage.

FinQA and TAT-QA retain their complete labelled public test splits. FinanceBench
retains all 150 open questions, but its annotator-selected pages are gold-only:
they must not silently become an oracle retrieval corpus. None of these imports
asserts human acceptance, source-equivalent indexing or completed evaluation.
"""

import hashlib
import json
import re
from pathlib import Path

from .loaders import _parse_raw_record

SOURCES = {
    "financebench": {
        "filename": "financebench.jsonl", "repository": "patronus-ai/financebench",
        "revision": "cc39aeb4afdf33909ee1412188bf89035950c2eb",
        "path": "data/financebench_open_source.jsonl",
        "sha256": "a5a2aa673e573e55675fc3c0f9aa38c1cf59d2abc91edb077534f71f10a71877",
        "license": "Publisher open sample; repository license unspecified; retain locally with attribution",
        "split": "open_source_150", "expected_cases": 150,
    },
    "financebench_documents": {
        "filename": "financebench_documents.jsonl", "repository": "patronus-ai/financebench",
        "revision": "cc39aeb4afdf33909ee1412188bf89035950c2eb",
        "path": "data/financebench_document_information.jsonl",
        "sha256": "1c69127783879de8cdadb159d2181f39bc3123b8e0ebf74031c3969d69189575",
    },
    "finqa": {
        "filename": "finqa.json", "repository": "czyssrs/FinQA",
        "revision": "0f16e2867befa6840783e58be38c9efb9229d742", "path": "dataset/test.json",
        "sha256": "831dbfb2e785dbc227f895ce3f24046433467aec67b09db2bd6ac7692a8a30dc",
        "license": "MIT", "split": "public_test", "expected_cases": 1147,
    },
    "tatqa": {
        "filename": "tatqa.json", "repository": "NExTplusplus/TAT-QA",
        "revision": "870accc41953dcde885aabeb963d94aabdc0fbc3",
        "path": "dataset_raw/tatqa_dataset_test_gold.json",
        "sha256": "c4d08418359c1d76468dec420ee748a37f48c06b63cb8ec2766f19d5d314b597",
        "license": "MIT", "split": "test_gold_released_2024", "expected_cases": 1663,
    },
}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def source_url(source):
    return f"https://raw.githubusercontent.com/{source['repository']}/{source['revision']}/{source['path']}"


def read_source(directory, name):
    spec = SOURCES[name]
    payload = (Path(directory) / spec["filename"]).read_bytes()
    if digest(payload) != spec["sha256"]:
        raise ValueError(f"Official source checksum mismatch: {name}; never import changed bytes as this revision")
    text = payload.decode("utf-8")
    return ([json.loads(line) for line in text.splitlines() if line.strip()]
            if spec["filename"].endswith("jsonl") else json.loads(text))


def provenance(name, official_id):
    s = SOURCES[name]
    return {"official_dataset": s["repository"], "official_id": str(official_id),
            "official_version": s["revision"], "split": s["split"],
            "license": s["license"], "source_sha256": s["sha256"]}


def evidence_id(benchmark, document, kind, content):
    """Same document/content has one identity regardless of which question refers to it."""
    raw = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return f"{benchmark}:{document}:{kind}:{digest(raw)[:24]}"


def simple_numeric(value):
    if type(value) in {int, float}:
        return value
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        text = re.sub(r"^[$£€]", "", text)
        text = re.sub(r"%$", "", text)
        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
            return float(text)
    return None


def financebench_records(raw, documents):
    docs = {r["doc_name"]: r for r in documents}
    records, requirements = [], {}
    for r in raw:
        doc = docs[r["doc_name"]]
        requirements[r["doc_name"]] = doc
        # Keep selected support text/page annotations out of both retrieval inputs
        # and context preparation. Full documents must be restored independently.
        records.append({
            "case_id": r["financebench_id"], "benchmark": "FinanceBench",
            "benchmark_version": SOURCES["financebench"]["revision"],
            "question": r["question"], "company": r["company"],
            "fiscal_year": str(doc["doc_period"]), "doc_name": r["doc_name"],
            "question_type": r["question_type"], "context_text": [], "context_tables": [],
            "provenance": provenance("financebench", r["financebench_id"]),
            "gold": {"gold_answer": r["answer"], "gold_value_numeric": simple_numeric(r["answer"]),
                     "gold_justification": r.get("justification"),
                     "official_evidence": r["evidence"]},
        })
    return records, [requirements[k] for k in sorted(requirements)]


def finqa_records(raw):
    records, pool = [], {}
    for r in raw:
        doc, qa = r["filename"], r["qa"]
        texts = r["pre_text"] + r["post_text"]
        text_ids = [evidence_id("FinQA", doc, "text", t) for t in texts]
        table_id = evidence_id("FinQA", doc, "table", r["table"])
        for ident, content in zip(text_ids, texts, strict=True):
            pool[ident] = {"evidence_id": ident, "doc_name": doc, "kind": "text", "text": content}
        pool[table_id] = {"evidence_id": table_id, "doc_name": doc, "kind": "table", "rows": r["table"]}
        gold_ids = []
        for key in qa.get("gold_inds", {}):
            kind, index = key.rsplit("_", 1)
            if kind == "text":
                gold_ids.append(text_ids[int(index)])
            elif kind == "table":
                gold_ids.append(table_id)  # retrieval at whole-table granularity, explicitly declared
            else:
                raise ValueError(f"Unknown official support locator: {key}")
        parts = doc.split("/")
        records.append({
            "case_id": "FinQA:" + r["id"], "benchmark": "FinQA",
            "benchmark_version": SOURCES["finqa"]["revision"], "question": qa["question"],
            "company": parts[0], "fiscal_year": parts[1] if len(parts) > 1 else None,
            "doc_name": doc, "question_type": "numerical", "context_text": texts,
            "context_tables": [{"table_id": table_id, "rows": r["table"]}],
            "provenance": provenance("finqa", r["id"]),
            "gold": {"gold_answer": str(qa["answer"]), "gold_value_numeric": qa.get("exe_ans"),
                     "gold_program": {"official_program": qa.get("program")},
                     "gold_evidence_ids": sorted(set(gold_ids))},
        })
    return records, [pool[k] for k in sorted(pool)]


def tatqa_records(raw):
    records, pool = [], {}
    for r in raw:
        doc = r["table"]["uid"]  # dataset does not supply a verified issuer/filing; do not guess
        table_id = evidence_id("TAT-QA", doc, "table", r["table"]["table"])
        pool[table_id] = {"evidence_id": table_id, "doc_name": doc,
                          "kind": "table", "rows": r["table"]["table"]}
        text_ids = {}
        for para in r["paragraphs"]:
            ident = evidence_id("TAT-QA", doc, "text", para["text"])
            text_ids[str(para["order"])] = ident
            pool[ident] = {"evidence_id": ident, "doc_name": doc, "kind": "text", "text": para["text"]}
        for q in r["questions"]:
            gold_ids = []
            for mapping in q.get("mappings", []):
                for key in mapping:
                    if key == "table":
                        gold_ids.append(table_id)
                    elif key.startswith("paragraph_"):
                        gold_ids.append(text_ids[key.split("_", 1)[1]])
                    else:
                        raise ValueError(f"Unknown official support locator: {key}")
            answer = q["answer"]
            gold = {"gold_answer": answer if isinstance(answer, list) else str(answer),
                    "gold_value_numeric": simple_numeric(answer),
                    "gold_evidence_ids": sorted(set(gold_ids)),
                    "gold_program": {"official_derivation": q.get("derivation", "")},
                    "unit": q.get("scale") or None}
            records.append({
                "case_id": "TAT-QA:" + q["uid"], "benchmark": "TAT-QA",
                "benchmark_version": SOURCES["tatqa"]["revision"], "question": q["question"],
                "company": "", "fiscal_year": None, "doc_name": doc,
                "question_type": "hybrid", "context_text": [p["text"] for p in r["paragraphs"]],
                "context_tables": [{"table_id": table_id, "rows": r["table"]["table"]}],
                "provenance": provenance("tatqa", q["uid"]), "gold": gold,
            })
    return records, [pool[k] for k in sorted(pool)]


def import_official(source_dir, output_dir):
    """Validate source bytes and emit full splits plus question-independent corpora."""
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    fb, docs = financebench_records(read_source(source_dir, "financebench"),
                                   read_source(source_dir, "financebench_documents"))
    fq, fq_pool = finqa_records(read_source(source_dir, "finqa"))
    tq, tq_pool = tatqa_records(read_source(source_dir, "tatqa"))
    suites = {"financebench_open150.json": fb, "finqa_candidate_universe.json": fq,
              "tatqa_candidate_universe.json": tq}
    for name, records in suites.items():
        ids = set()
        for record in records:
            case, _ = _parse_raw_record(record)
            if case.case_id in ids:
                raise ValueError(f"Duplicate official case identity: {case.case_id}")
            ids.add(case.case_id)
        expected = SOURCES[{"financebench_open150.json": "financebench",
                            "finqa_candidate_universe.json": "finqa",
                            "tatqa_candidate_universe.json": "tatqa"}[name]]["expected_cases"]
        if len(records) != expected:
            raise ValueError(f"Official split count mismatch: {name}")
    payloads = {**suites, "finqa_context_corpus.json": fq_pool, "tatqa_context_corpus.json": tq_pool,
                "financebench_required_documents.json": docs}
    output_dir.mkdir(parents=True, exist_ok=True)
    encoded = {name: (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
               for name, value in payloads.items()}
    for name, payload in encoded.items():
        path = output_dir / name
        if path.exists() and path.read_bytes() != payload:
            raise ValueError(f"Destination has different data: {path}; choose a new directory")
    for name, payload in encoded.items():
        (output_dir / name).write_bytes(payload)
    manifest = {
        "schema_version": 1, "sources": SOURCES,
        "counts": {name: len(rows) for name, rows in payloads.items()},
        "files_sha256": {name: digest(payload) for name, payload in encoded.items()},
        "subsets": False,
        "gold_separation": "Only question plus raw contexts enter evaluation inputs; official retrieved/model_input/facts/mappings stay out",
        "retrieval_granularity": "whole table and individual paragraph; gold row mappings coarsened explicitly",
        "candidate_universe": "all contexts in each complete public test split, pooled before any question selection",
        "financebench_context_status": "84 full source documents still required; annotated evidence pages are never retrieval inputs",
        "tatqa_source_limit": "opaque context IDs; original issuer/accession not supplied, no invented application-filing binding",
        "independent_acceptance": "pending", "final_experiment_ready": False,
    }
    (output_dir / "import_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def bind_financebench_pages(case_path, pages_path, output_path):
    """Attach every full-document page; target page IDs remain in gold only.

    This establishes the input corpus, not the missing A-G benchmark adapter or
    independent acceptance. Unreadable annotated pages remain explicit shortfalls.
    """
    case_path, pages_path, output_path = Path(case_path), Path(pages_path), Path(output_path)
    corpus_manifest = json.loads((pages_path.parent / "financebench_context_manifest.json").read_bytes())
    payload = pages_path.read_bytes()
    if digest(payload) != corpus_manifest["corpus_sha256"] or corpus_manifest["gold_selected_pages_used"] is not False:
        raise ValueError("Full-document context identity or non-oracle corpus policy mismatch")
    groups = {}
    for page in json.loads(payload):
        groups.setdefault(page["doc_name"], []).append(page)
    cases = json.loads(case_path.read_bytes())
    shortfalls = []
    for case in cases:
        if case["benchmark"] != "FinanceBench" or case["doc_name"] not in groups:
            raise ValueError("Missing source document for an official FinanceBench case")
        pages = sorted(groups[case["doc_name"]], key=lambda p: p["page_index"])
        case["context_text"] = [p["text"] for p in pages if p["readable"]]
        case["gold"]["gold_evidence_ids"] = [f"FinanceBench:{e['doc_name']}:page:{e['evidence_page_num']}"
                                                    for e in case["gold"]["official_evidence"]]
        for e in case["gold"]["official_evidence"]:
            matching = [p for p in groups.get(e["doc_name"], []) if p["page_index"] == e["evidence_page_num"]]
            if not matching or not matching[0]["readable"]:
                shortfalls.append({"case_id": case["case_id"], "document": e["doc_name"],
                                   "page_index": e["evidence_page_num"], "reason": "gold_source_page_missing_or_unreadable"})
        _parse_raw_record(case)
    encoded = (json.dumps(cases, ensure_ascii=False) + "\n").encode()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.read_bytes() != encoded:
        raise ValueError("Bound case destination changed; choose a new path")
    output_path.write_bytes(encoded)
    report = {"cases": len(cases), "source_dataset_sha256": digest(case_path.read_bytes()),
              "full_page_corpus_sha256": digest(payload), "bound_dataset_sha256": digest(encoded),
              "all_full_document_pages_attached": True, "shortfalls": shortfalls,
              "source_equivalent_engine_adapter": "pending", "final_experiment_ready": False}
    output_path.with_suffix(".binding.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
