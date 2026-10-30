"""Acceptance checks for the Day 1/2 integration and setup boundary."""

import os
import shutil
from dataclasses import replace

import pytest

from src.application import SetupApplication, assemble_engine, configured_answer
from src.config import PROJECT_ROOT, ConfigurationError, load_settings


@pytest.fixture
def configured_root(tmp_path):
    (tmp_path / "configs").mkdir()
    shutil.copy(PROJECT_ROOT / "configs/config.yaml", tmp_path / "configs/config.yaml")
    return tmp_path


def test_config_paths_do_not_depend_on_working_directory(configured_root, monkeypatch):
    monkeypatch.chdir(configured_root.parent)
    settings = load_settings(root=configured_root, environ={})
    assert settings.index_dir == configured_root / "sec_vector_db"
    assert settings.raw_dir == configured_root / "data/raw"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_environment_precedence_and_secret_redaction(configured_root, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (configured_root / ".env").write_text("FINRAG_PORT=7861\nGEMINI_API_KEY=test-private-value\n")
    settings = load_settings(root=configured_root, environ={"FINRAG_PORT": "7862"})
    assert settings.port == 7862
    assert settings.gemini_api_key == "test-private-value"
    assert "test-private-value" not in repr(settings)
    assert "GEMINI_API_KEY" not in os.environ
    assert "test-private-value" not in str(SetupApplication(settings).readiness())


@pytest.mark.parametrize("overrides", [
    {"FINRAG_PORT": "bad"}, {"FINRAG_PORT": "0"}, {"FINRAG_PORT": "65536"},
    {"FINRAG_PROVIDER": "auto"}, {"FINRAG_PROVIDER": "mock"}, {"FINRAG_INDEX_DIR": ""},
])
def test_invalid_configuration_is_rejected(configured_root, overrides):
    with pytest.raises(ConfigurationError):
        load_settings(root=configured_root, environ=overrides)


def test_malformed_config_has_safe_error(configured_root):
    (configured_root / "configs/config.yaml").write_text("- private-configuration-value\n")
    with pytest.raises(ConfigurationError) as error:
        load_settings(root=configured_root, environ={})
    assert "private-configuration-value" not in str(error.value)


def test_missing_data_returns_no_fabricated_answer(configured_root):
    app = SetupApplication(load_settings(root=configured_root, environ={}))
    result = app.answer("What is revenue?")
    assert result["status"] == "not_ready"
    assert result["answer"] == ""
    assert result["evidence"] == []
    assert "No source filing" in result["message"]
    assert "No persistent Chroma" in result["message"]
    assert not app.settings.index_dir.exists()  # Startup must not create an empty index.


def test_existing_index_and_key_do_not_enable_unverified_backend(configured_root):
    settings = load_settings(root=configured_root, environ={
        "FINRAG_PROVIDER": "gemini", "FINRAG_MODEL": "unverified-model", "GEMINI_API_KEY": "test-only",
    })
    settings.index_dir.mkdir()
    (settings.index_dir / "chroma.sqlite3").touch()
    result = SetupApplication(settings).answer("What is revenue?")
    assert result["status"] == "not_ready"
    assert "not validated" in result["message"]
    assert result["answer"] == ""


def test_empty_question_is_invalid(configured_root):
    result = SetupApplication(load_settings(root=configured_root, environ={})).answer("  ")
    assert result["status"] == "invalid_input"
    assert result["answer"] == ""


def test_explicit_backend_wiring_and_configured_limits(configured_root):
    settings = replace(load_settings(root=configured_root, environ={}), top_k_text=5, top_k_tables=2)
    collection, encoder, llm = object(), object(), object()

    class Embeddings:
        def encode(self, text):
            assert text == "query"
            return [0.1, 0.2]

    engine = assemble_engine(settings, collection=collection, embedding_model=Embeddings(),
                             cross_encoder=encoder, llm_client=llm)
    assert engine.retriever.vector_collection is collection
    assert engine.retriever.embedding_fn("query") == [0.1, 0.2]
    assert engine.reranker.cross_encoder_model is encoder
    assert engine.llm_client is llm

    class RecordingEngine:
        def answer_financial_question(self, question, **kwargs):
            assert question == "query"
            return kwargs

    assert configured_answer(RecordingEngine(), settings, "query") == {
        "top_k_text": 5, "top_k_tables": 2, "rerank_top_n": 4,
    }


def test_backend_wiring_refuses_missing_dependencies(configured_root):
    settings = load_settings(root=configured_root, environ={})
    with pytest.raises(ValueError, match="explicitly"):
        assemble_engine(settings, collection=None, embedding_model=None,
                        cross_encoder=None, llm_client=None)
