import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from src.charts.caption import caption_chart, validate_description
from src.charts.questions import audit_questions
from src.llm.client import UnifiedLLMClient


def description():
    return {"title": "Return", "chart_type": "line", "x_axis": "Year", "y_axis": None,
            "units": None, "periods": ["2021"], "series": ["Apple"],
            "readable_values": [], "unknowns": ["Exact point values are not printed."]}


def test_caption_schema_unknown_and_undeclared_numbers():
    assert validate_description(description())["readable_values"] == []
    d = description()
    d["unknowns"] = []
    with pytest.raises(ValueError):
        validate_description(d)
    d = description()
    d["readable_values"] = [{"period": "2022", "series": "Apple", "value": "100", "unit": "USD"}]
    with pytest.raises(ValueError):
        validate_description(d)


def test_original_image_hash_blocks_generation(tmp_path):
    path = tmp_path / 'chart.jpg'
    path.write_bytes(b'fixture')
    client = SimpleNamespace(provider="ollama", expected_digest="a" * 64, model="gemma3:4b")
    with pytest.raises(ValueError, match="hash"):
        caption_chart({"image_sha256": "b" * 64}, path, client)


def test_candidate_links_original_and_cannot_self_certify(tmp_path):
    raw = b'fixture'
    path = tmp_path / 'chart.jpg'
    path.write_bytes(raw)
    source = {"image_sha256": hashlib.sha256(raw).hexdigest(), "source_asset_id": "original", "accession": "a",
              "pdf_url": "https://example.org/report.pdf", "pdf_sha256": "b" * 64, "page": 22, "html_selector": "img"}
    class Client:
        provider, model, expected_digest, ollama_options = "ollama", "gemma3:4b", "a" * 64, {}
        def generate(self, prompt, **kwargs):
            assert kwargs["images"] and kwargs["response_format"]["properties"]["readable_values"]["maxItems"] == 0
            return {"status": "ok", "provider": "ollama", "model": self.model,
                    "text": json.dumps(description()), "model_fingerprint": {"digest": self.expected_digest}}
    result = caption_chart(source, path, Client())
    assert result["status"] == "candidate" and result["metadata"]["independent_review"] == "pending"
    assert result["source"] == source and result["metadata"]["generated"] is True


def question(identity='q1', split='dev'):
    return {"id": identity, "split": split, "question": "Title?", "answer": "Return",
            "image_sha256": "a" * 64, "source_asset_id": "s", "source_locator": "img",
            "answer_basis": "Visible title", "independent_review": "pending"}


def test_shortfall_and_original_image_leakage():
    audit = audit_questions([question()])
    assert audit["shortfall"] == {"dev": 14, "heldout": 35} and not audit["evaluation_ready"]
    with pytest.raises(ValueError, match="crosses"):
        audit_questions([question(), question('q2', 'heldout')])
    other = copy.deepcopy(question('q2', 'heldout'))
    other['image_sha256'] = 'b' * 64
    other['original_image_group'] = 'same-chart'
    first = question()
    first['original_image_group'] = 'same-chart'
    with pytest.raises(ValueError, match="crosses"):
        audit_questions([first, other])


def test_pinned_model_mismatch_skips_generation(monkeypatch):
    monkeypatch.setattr('src.llm.ollama_profile.fingerprint', lambda *args: {"digest": "b" * 64})
    def forbidden(*args, **kwargs):
        pytest.fail("generation must not be requested for the wrong model digest")
    monkeypatch.setattr('requests.post', forbidden)
    response = UnifiedLLMClient(provider='ollama', ollama_model='gemma3:4b', expected_digest='a' * 64).generate('Hi')
    assert response['error_code'] == 'digest_mismatch' and not response['success']


def test_changed_digest_after_generation_rejected(monkeypatch):
    snapshots = iter([{"digest": "a" * 64}, {"digest": "b" * 64}])
    monkeypatch.setattr('src.llm.ollama_profile.fingerprint', lambda *args: next(snapshots))
    monkeypatch.setattr('requests.post', lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: {
        "done": True, "model": "gemma3:4b", "response": "Hi"}))
    response = UnifiedLLMClient(provider='ollama', ollama_model='gemma3:4b', expected_digest='a' * 64).generate('Hi')
    assert response['error_code'] == 'digest_mismatch'


def test_chart_stage_is_opt_in_and_unreviewed_captions_cannot_enter_prompt():
    from src.pipeline.finrag_engine import FinRAGEngine
    content = 'Generated description: exact final value unknown.'
    chart = {'evidence_id':'chart1', 'content':content,
             'source':{'image_sha256':'a'*64, 'pdf_url':'https://example.org/report.pdf', 'page':22, 'source_asset_id':'source1'},
             'metadata':{'type':'chart_description','independent_review':'pending','generated':True,
                         'image_sha256':'a'*64,'content_sha256':hashlib.sha256(content.encode()).hexdigest()}}
    class Retriever:
        def retrieve(self, **kwargs):
            return {'text_evidence': [chart], 'table_evidence': []}
    class Rank:
        def rerank(self, **kwargs):
            return kwargs['candidates']
    class Client:
        provider, model, calls = 'ollama','fixture',0
        def generate(self, prompt):
            self.calls += 1
            assert 'GENERATED CHART' in prompt
            return {'status':'ok', 'success':True,'provider':self.provider,'model':self.model,'text':'Unknown [chart1]'}
    c = Client()
    engine = FinRAGEngine(Retriever(), Rank(), c)
    assert engine.answer_financial_question('Exact final value?')['status'] == 'insufficient_evidence'
    engine.enable_chart_descriptions = True
    result = engine.answer_financial_question('Exact final value?')
    assert result['status'] == 'insufficient_evidence' and c.calls == 0
    assert result['excluded_evidence'][0]['reason'] == 'unapproved_chart_or_provenance'
    # Synthetic reviewed fixture only, never mark a real authored caption reviewed.
    chart['metadata']['independent_review'] = 'passed'
    result = engine.answer_financial_question('Exact final value?')
    assert result['status'] == 'ok' and result['included_evidence_ids'] == ['chart1'] and c.calls == 1


def test_truncated_provider_output_is_not_success(monkeypatch):
    monkeypatch.setattr('requests.post', lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: {
        'done':True, 'done_reason':'length', 'model':'gemma3:4b', 'response':'partial {'}))
    result = UnifiedLLMClient(provider='ollama',ollama_model='gemma3:4b').generate('Question')
    assert result['error_code'] == 'truncated_response' and result['text'] == ''


def test_same_image_cannot_evade_split_guard_by_relabelling_group():
    first, other = question(), question('q2','heldout')
    first['original_image_group'], other['original_image_group'] = 'one','two'
    with pytest.raises(ValueError, match='crosses'):
        audit_questions([first, other])


def test_author_correction_preserves_model_draft_and_review_pending(tmp_path):
    from src.charts.caption import apply_author_corrections
    raw = b'original'
    path = tmp_path / 'chart.jpg'
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    draft = {'status':'candidate','evidence_id':'caption1','description':description(),
             'metadata':{'image_sha256':digest,'independent_review':'pending'}}
    result = apply_author_corrections(draft, {'image_sha256':digest,'fields':{'units':'$'},
                                              'basis':'Visible dollar tick labels'}, path)
    assert result['raw_model_description']['units'] is None
    assert result['description']['units'] == '$' and result['metadata']['independent_review'] == 'pending'
    assert draft['description']['units'] is None
    with pytest.raises(ValueError, match='mismatch'):
        apply_author_corrections(draft, {'image_sha256':'wrong','fields':{'units':'$'},'basis':'labels'}, path)
