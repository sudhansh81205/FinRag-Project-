"""Day 3 regressions: no evidence/no provider can produce financial success."""

import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.run_eval import run_evaluation_suite
from src.llm.client import UnifiedLLMClient
from src.pipeline.finrag_engine import FinRAGEngine


@pytest.fixture
def evidence():
    return {"id": "fixture-services", "content": "Services sales: 2021 USD millions 68,425.",
            "metadata": {"type": "financial_table", "source_locator": "test-only"}}


def engine_with(evidence, client):
    retriever = Mock()
    retriever.retrieve.return_value = {"text_evidence": [], "table_evidence": evidence}
    reranker = Mock()
    reranker.rerank.side_effect = lambda **kw: kw["candidates"]
    return FinRAGEngine(retriever, reranker, client)


def real_stub():
    client = Mock(provider="ollama", model="configured-model")
    client.generate.return_value = {"success": True, "status": "ok", "provider": "ollama",
                                    "model": "configured-model", "text": "68,425 million USD in 2021"}
    return client


@pytest.mark.parametrize("provider", ["auto", "typo", ""])
def test_unknown_or_automatic_provider_is_rejected(provider):
    with pytest.raises(ValueError, match="explicit"):
        UnifiedLLMClient(provider=provider)


def test_mock_needs_explicit_test_setting():
    with pytest.raises(ValueError, match="test-only"):
        UnifiedLLMClient(provider="mock")
    result = UnifiedLLMClient(provider="mock", allow_mock=True).generate("fixture")
    assert result["status"] == "test_only"
    assert "365,817" not in result["text"]


def test_mock_cannot_produce_financial_success(evidence):
    client = UnifiedLLMClient(provider="mock", allow_mock=True)
    result = engine_with([evidence], client).answer_financial_question("Services sales?")
    assert result["status"] == "service_error"
    assert result["answer"] == ""
    with pytest.raises(ValueError, match="real provider"):
        engine_with([evidence], client).run_baseline_comparison("Services sales?")


@pytest.mark.parametrize("provider", ["mock", "auto", "gemini", None])
def test_legacy_evaluator_cannot_report_false_success(provider):
    with pytest.raises(RuntimeError, match="not ready"):
        run_evaluation_suite(provider)


@pytest.mark.parametrize("records", [[], [{"content": "  ", "metadata": {"type": "financial_table"}}],
                                     [{"content": "unsupported", "metadata": {"type": "other"}}]])
def test_missing_evidence_never_calls_provider(records):
    client = real_stub()
    result = engine_with(records, client).answer_financial_question("Services sales?")
    assert result["status"] == "insufficient_evidence"
    assert result["answer"] == ""
    client.generate.assert_not_called()


def test_provider_success_requires_evidence(evidence):
    client = real_stub()
    result = engine_with([evidence], client).answer_financial_question("Services sales?")
    assert result["status"] == "ok"
    assert result["included_evidence_ids"] == [evidence["id"]]
    assert result["evidence"] == [evidence]
    assert "68,425" in result["answer"]
    assert "Services sales" in client.generate.call_args.args[0]


@pytest.mark.parametrize("reply", [
    {"success": False, "status": "service_error", "text": "fake fallback answer"},
    {"success": True, "status": "ok", "text": "  "},
    {"success": True, "text": "missing status"},
    {"success": True, "status": "ok", "provider": "mock", "text": "fake answer"},
])
def test_failed_or_invalid_provider_response_is_never_an_answer(evidence, reply):
    client = real_stub()
    client.generate.return_value = reply
    result = engine_with([evidence], client).answer_financial_question("Services sales?")
    assert result["status"] == "service_error"
    assert result["answer"] == ""


def test_thrown_exception_is_sanitized(evidence):
    client = real_stub()
    client.generate.side_effect = RuntimeError("secret-value-in-provider-error")
    result = engine_with([evidence], client).answer_financial_question("Services sales?")
    assert result["status"] == "service_error"
    assert "secret-value" not in str(result)


def test_retrieval_failure_is_not_missing_evidence(evidence):
    client = real_stub()
    engine = engine_with([evidence], client)
    engine.retriever.retrieve.return_value = {"text_error": "private backend diagnostic"}
    result = engine.answer_financial_question("Services sales?")
    assert result["status"] == "service_error"
    assert "private backend" not in str(result)
    client.generate.assert_not_called()


@pytest.mark.parametrize("question", ["", "  ", None, 123])
def test_invalid_requests_are_rejected(question):
    client = real_stub()
    result = engine_with([], client).answer_financial_question(question)
    assert result["status"] == "invalid_request"
    client.generate.assert_not_called()


@pytest.mark.parametrize("response", [
    SimpleNamespace(status_code=401, text="secret reflected by server"),
    SimpleNamespace(status_code=200, json=lambda: {"response": "", "done": True, "model": "model"}),
    SimpleNamespace(status_code=200, json=lambda: {"response": "answer", "done": False, "model": "model"}),
    SimpleNamespace(status_code=200, json=lambda: {"response": "answer", "done": True, "model": "other"}),
])
def test_bad_ollama_responses_are_not_success(monkeypatch, response):
    monkeypatch.setattr("requests.post", Mock(return_value=response))
    result = UnifiedLLMClient(provider="ollama", ollama_model="model").generate("question")
    assert not result["success"]
    assert result["text"] == ""
    assert "secret" not in str(result)


def test_ollama_call_uses_only_the_configured_model(monkeypatch):
    request = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {
        "response": "source answer", "done": True, "model": "model",
    }))
    monkeypatch.setattr("requests.post", request)
    result = UnifiedLLMClient(provider="ollama", ollama_model="model").generate("question")
    assert result["status"] == "ok"
    assert request.call_count == 1
    assert request.call_args.kwargs["json"]["model"] == "model"
    assert request.call_args.kwargs["timeout"] > 0


def test_gemini_credential_failure_is_sanitized_without_fallback(monkeypatch):
    # A stub SDK exercises authentication failure without sending secrets over a network.
    import sys

    api = Mock()
    api.models.generate_content.side_effect = RuntimeError("401 invalid key: test-secret")
    factory = Mock(return_value=api)
    types = SimpleNamespace(HttpOptions=lambda **kw: kw, HttpRetryOptions=lambda **kw: kw,
                            GenerateContentConfig=lambda **kw: kw)
    sdk = SimpleNamespace(Client=factory, types=types)
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=sdk))
    monkeypatch.setitem(sys.modules, "google.genai", sdk)
    before = dict(os.environ)
    client = UnifiedLLMClient(provider="gemini", gemini_model="chosen-model", gemini_api_key="test-secret")
    result = client.generate("question")
    assert result["status"] == "service_error"
    assert result["text"] == ""
    assert "test-secret" not in str(result)
    assert api.models.generate_content.call_count == 1
    assert api.models.generate_content.call_args.kwargs["model"] == "chosen-model"
    assert dict(os.environ) == before


def test_missing_key_and_model_never_succeed():
    assert UnifiedLLMClient(provider="gemini", gemini_model="model").generate("q")["error_code"] == "credentials_missing"
    assert UnifiedLLMClient(provider="ollama").generate("q")["error_code"] == "not_configured"
