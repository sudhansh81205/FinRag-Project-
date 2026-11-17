"""Prepared engine factory cannot silently alias unavailable variants/providers."""
from dataclasses import replace
from unittest.mock import Mock

import pytest

from src.benchmark.runtime import build_benchmark_engine
from src.config import load_settings


def test_explicit_factory_wires_requested_variant_and_settings(monkeypatch, tmp_path):
    factory = Mock(return_value=object())
    monkeypatch.setattr("src.benchmark.runtime.build_prepared_engine", factory)
    settings = replace(load_settings(environ={}), provider="ollama", model="gemma3:4b", ollama_digest="a" * 64)
    result = build_benchmark_engine(settings, variant="C", tokenizer_dir=tmp_path, model_cache=tmp_path)
    assert result is factory.return_value
    assert factory.call_args.args == (settings,)
    assert factory.call_args.kwargs["variant"] == "C"
    assert factory.call_args.kwargs["tokenizer_dir"] == tmp_path
    assert factory.call_args.kwargs["model_cache"] == tmp_path
    for variant in ["A", "B", "E", "F", "G"]:
        with pytest.raises(ValueError, match="unavailable"):
            build_benchmark_engine(settings, variant=variant, tokenizer_dir=tmp_path)
    assert factory.call_count == 1
    for changed in [replace(settings, provider="gemini"), replace(settings, model="llama3.2"), replace(settings, ollama_digest="")]:
        with pytest.raises(ValueError, match="Gemma"):
            build_benchmark_engine(changed, variant="D", tokenizer_dir=tmp_path)
    assert factory.call_count == 1


def test_real_factory_rejects_closed_acceptance_before_loading_models():
    settings = replace(load_settings(environ={}), provider="ollama", model="gemma3:4b", ollama_digest="a" * 64)
    with pytest.raises(ValueError, match="acceptance gates"):
        build_benchmark_engine(settings, variant="D")
