"""R4/R12: actual model identity and full-prompt refusal before inference."""

import hashlib
from unittest.mock import Mock

import pytest

from src.llm.client import UnifiedLLMClient
from src.llm.token_budget import BudgetedClient, GGUFTokenCounter


def test_complete_prompt_limit_blocks_provider_before_any_call():
    client = UnifiedLLMClient(provider="ollama", ollama_model="gemma3:4b")
    client.generate = Mock()
    wrapper = BudgetedClient(client, lambda _: 3001)
    result = wrapper.generate("instructions plus evidence plus question")
    assert result["error_code"] == "prompt_token_budget" and not result["success"]
    client.generate.assert_not_called()


def test_valid_prompt_preserves_structured_planner_and_reports_measured_budget():
    client = UnifiedLLMClient(provider="ollama", ollama_model="gemma3:4b", expected_digest="pinned")
    client.generate = Mock(return_value={"status": "ok", "text": "source-bound response"})
    wrapper = BudgetedClient(client, lambda _: 100)
    schema = {"type": "object"}
    result = wrapper.generate("complete prompt", response_format=schema)
    client.generate.assert_called_once_with("complete prompt", response_format=schema)
    assert wrapper.expected_digest == "pinned" and result["prompt_budget"]["used"] == 100


def test_context_capacity_accounts_for_output_and_template():
    with pytest.raises(ValueError, match="exceed"):
        BudgetedClient(Mock(), lambda _: 1, input_tokens=4096)


def test_failed_tokenizer_and_unmeasured_vision_never_call_provider():
    client = UnifiedLLMClient(provider="ollama", ollama_model="gemma3:4b")
    client.generate = Mock()
    wrapper = BudgetedClient(client, Mock(side_effect=RuntimeError("unavailable")))
    assert wrapper.generate("prompt")["error_code"] == "tokenizer_failed"
    assert wrapper.generate("prompt", images=["image"])["error_code"] == "unmeasured_image_budget"
    client.generate.assert_not_called()


def test_gguf_counter_rejects_remote_service_or_changed_model_bytes(tmp_path):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"GGUF fixture")
    with pytest.raises(ValueError, match="loopback"):
        GGUFTokenCounter("https://example.com", model, "bad")
    with pytest.raises(ValueError, match="pinned"):
        GGUFTokenCounter("http://127.0.0.1:1234", model, "bad")


def test_counter_checks_loaded_model_again_after_service_restart(tmp_path, monkeypatch):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"GGUF fixture")
    response = Mock()
    response.json.return_value = {"model_path": str(model)}
    monkeypatch.setattr("src.llm.token_budget.requests.get", Mock(return_value=response))
    post = Mock()
    post.return_value.json.return_value = {"tokens": [1, 2, 3]}
    monkeypatch.setattr("src.llm.token_budget.requests.post", post)
    counter = GGUFTokenCounter("http://127.0.0.1:1234", model, hashlib.sha256(model.read_bytes()).hexdigest())
    assert counter("source") == 3
    response.json.return_value = {"model_path": str(tmp_path / "foreign.gguf")}
    with pytest.raises(ValueError, match="different"):
        counter("source")
    assert post.call_count == 1
