"""R7/R12: actual publisher-shape boundaries and meaningful leakage failures."""

import json

import pytest

from src.benchmark.importers import (
    evidence_id,
    financebench_records,
    finqa_records,
    read_source,
    tatqa_records,
)
from src.benchmark.loaders import _parse_raw_record, verify_gold_separation


def test_finqa_uses_raw_context_not_official_retriever_or_model_input():
    raw = {"id": "ACME/2020/p1-1", "filename": "ACME/2020/p1.pdf",
           "pre_text": ["Original source."], "post_text": ["Original footer."],
           "table": [["year", "amount"], ["2020", "10"]],
           "table_retrieved": [{"content": "LEAKED ANSWER"}],
           "qa": {"question": "What is the amount?", "answer": "10", "exe_ans": 10,
                  "program": "GOLD PROGRAM", "gold_inds": {"table_1": "10", "text_0": "source"},
                  "model_input": ["GOLD SELECTED INPUT"]}}
    rows, corpus = finqa_records([raw])
    case, gold = _parse_raw_record(rows[0])
    inputs = case.to_eval_input()
    assert verify_gold_separation(inputs)
    for forbidden in ("LEAKED ANSWER", "GOLD PROGRAM", "GOLD SELECTED INPUT"):
        assert forbidden not in json.dumps(inputs)
        assert forbidden not in json.dumps(corpus)
    assert gold.gold_value_numeric == 10
    assert set(gold.gold_evidence_ids) <= {r["evidence_id"] for r in corpus}
    assert case.provenance_class == "authentic_source_bound"


def test_financebench_selected_pages_remain_gold_only():
    raw = [{"financebench_id": "fb1", "company": "ACME", "doc_name": "ACME_2020_10K",
            "question": "What was revenue?", "question_type": "metrics-generated",
            "answer": "$10", "justification": "GOLD REASONING",
            "evidence": [{"evidence_text_full_page": "GOLD SELECTED PAGE"}]}]
    docs = [{"doc_name": "ACME_2020_10K", "doc_period": 2020, "doc_link": "https://example.com/source.pdf"}]
    rows, required = financebench_records(raw, docs)
    case, gold = _parse_raw_record(rows[0])
    assert case.context_text == () and case.context_tables == ()
    assert "GOLD" not in json.dumps(case.to_eval_input())
    assert gold.gold_value_numeric == 10
    assert required == docs
    assert rows[0]["gold"]["official_evidence"] == raw[0]["evidence"]


def test_tatqa_retains_unlabelled_source_context_and_declines_to_invent_issuer():
    raw = [{"table": {"uid": "opaque-doc", "table": [["Year", "2020"], ["Cash", "10"]]},
            "paragraphs": [{"uid": "p1", "order": 1, "text": "Raw report paragraph."}],
            "questions": [{"uid": "q1", "question": "What is cash?", "answer": 10,
                           "scale": "million", "derivation": "10", "facts": ["GOLD FACT"],
                           "mappings": [{"table": [1, 1]}, {"paragraph_1": [0, 3]}]}]}]
    rows, corpus = tatqa_records(raw)
    case, gold = _parse_raw_record(rows[0])
    assert case.company == "" and case.fiscal_year is None
    assert case.doc_name == "opaque-doc"
    assert "GOLD FACT" not in json.dumps(case.to_eval_input())
    assert "mappings" not in json.dumps(case.to_eval_input())
    assert set(gold.gold_evidence_ids) == {r["evidence_id"] for r in corpus}


def test_source_bytes_cannot_be_relabelled_as_pinned_official_data(tmp_path):
    (tmp_path / "finqa.json").write_text("[]")
    with pytest.raises(ValueError, match="checksum mismatch"):
        read_source(tmp_path, "finqa")


def test_shared_context_identity_does_not_depend_on_question_or_gold():
    ident = evidence_id("FinQA", "doc", "text", "Source paragraph")
    assert ident == evidence_id("FinQA", "doc", "text", "Source paragraph")
    assert ident != evidence_id("FinQA", "other-doc", "text", "Source paragraph")
    assert ident != evidence_id("FinQA", "doc", "text", "Changed source paragraph")


def test_full_document_binding_uses_every_page_and_keeps_gold_annotations_separate(tmp_path):
    from src.benchmark.importers import bind_financebench_pages, digest

    raw = [{"financebench_id": "fb1", "company": "ACME", "doc_name": "ACME_2020_10K",
            "question": "What was revenue?", "question_type": "metrics-generated", "answer": "10",
            "evidence": [{"doc_name": "ACME_2020_10K", "evidence_page_num": 1,
                          "evidence_text": "ANNOTATOR SECRET"}]}]
    rows, _ = financebench_records(raw, [{"doc_name": "ACME_2020_10K", "doc_period": 2020}])
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps(rows))
    pages = tmp_path / "financebench_full_pages.json"
    pages.write_text(json.dumps([
        {"doc_name": "ACME_2020_10K", "page_index": 0, "text": "Unselected source", "readable": True},
        {"doc_name": "ACME_2020_10K", "page_index": 1, "text": "", "readable": False},
        {"doc_name": "ACME_2020_10K", "page_index": 2, "text": "Another source page", "readable": True},
    ]))
    (tmp_path / "financebench_context_manifest.json").write_text(json.dumps({
        "corpus_sha256": digest(pages.read_bytes()), "gold_selected_pages_used": False}))
    output = tmp_path / "bound.json"
    report = bind_financebench_pages(cases, pages, output)
    case, gold = _parse_raw_record(json.loads(output.read_text())[0])
    assert case.context_text == ("Unselected source", "Another source page")
    assert "ANNOTATOR SECRET" not in json.dumps(case.to_eval_input())
    assert gold.gold_evidence_ids == ("FinanceBench:ACME_2020_10K:page:1",)
    assert len(report["shortfalls"]) == 1 and not report["final_experiment_ready"]
    pages.write_text("[]")
    with pytest.raises(ValueError, match="identity"):
        bind_financebench_pages(cases, pages, output)


def test_pdf_restore_refuses_changed_bytes_and_path_escape():
    import hashlib

    from scripts.restore_financebench_documents import restore_one, verify_document

    payload = b"%PDF-source"
    spec = {"size": len(payload), "sha": hashlib.sha1(b"blob 11\x00" + payload).hexdigest()}
    assert verify_document(payload, spec) == hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError, match="checksum"):
        verify_document(b"%PDF-change", spec)
    with pytest.raises(ValueError, match="outside"):
        restore_one({"path": "../secret.pdf"}, None, False)
