"""R2/R4/R12/R13 common controls: real paths, failure-preserving checks and gates."""

import hashlib
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.check_handoff import execute
from src.benchmark.gates import _check_artifacts
from src.runtime_support import model_cache, total_memory_bytes


def test_cache_defaults_match_build_and_preserve_overrides(tmp_path, monkeypatch):
    monkeypatch.delenv("SENTENCE_TRANSFORMERS_HOME", raising=False)
    assert model_cache(tmp_path) == tmp_path / "output/models"
    monkeypatch.setenv("SENTENCE_TRANSFORMERS_HOME", "shared-cache")
    assert model_cache(tmp_path) == tmp_path / "shared-cache"
    assert model_cache(tmp_path, "specific-cache") == tmp_path / "specific-cache"


def test_memory_reports_real_posix_values_or_unknown(monkeypatch):
    monkeypatch.setattr("src.runtime_support.platform.system", lambda: "Linux")
    monkeypatch.setattr("src.runtime_support.os.sysconf", lambda name: 4096 if name == "SC_PAGE_SIZE" else 1024,
                        raising=False)
    assert total_memory_bytes() == 4096 * 1024
    monkeypatch.setattr("src.runtime_support.os.sysconf", Mock(side_effect=OSError), raising=False)
    assert total_memory_bytes() is None


def test_windows_memory_api_success_and_failure(monkeypatch):
    monkeypatch.setattr("src.runtime_support.platform.system", lambda: "Windows")
    def populate(pointer):
        pointer._obj.total = 8 * 1024 ** 3
        return 1
    windll = SimpleNamespace(kernel32=SimpleNamespace(GlobalMemoryStatusEx=populate))
    monkeypatch.setattr("src.runtime_support.ctypes.windll", windll, raising=False)
    assert total_memory_bytes() == 8 * 1024 ** 3
    windll.kernel32.GlobalMemoryStatusEx = lambda _pointer: 0
    assert total_memory_bytes() is None


@pytest.mark.parametrize("path", ["../outside", "/outside", "C:/outside", "..\\outside"])
def test_acceptance_cannot_bind_files_outside_release_root(tmp_path, path):
    assert _check_artifacts({"artifacts": {path: "a" * 64}}, tmp_path)


def test_gate_binds_actual_file_and_rejects_change(tmp_path):
    path = tmp_path / "artifact.json"
    path.write_bytes(b"accepted")
    record = {"artifacts": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}}
    assert not _check_artifacts(record, tmp_path)
    path.write_bytes(b"changed")
    assert _check_artifacts(record, tmp_path)


def test_check_runner_preserves_failures_and_redacts_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("FINRAG_API_TOKEN", "private-test-token")
    monkeypatch.setattr("scripts.check_handoff.subprocess.run", lambda *_args, **_kwargs:
                        SimpleNamespace(returncode=1, stdout="private-test-token", stderr="failed"))
    result = execute("pytest", ["python", "-m", "pytest"], tmp_path, tmp_path)
    assert result["status"] == "failed" and result["returncode"] == 1
    assert "private-test-token" not in (tmp_path / "pytest.txt").read_text()


def test_missing_executable_and_not_ready_smoke_remain_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.check_handoff.subprocess.run", Mock(side_effect=FileNotFoundError))
    assert execute("node", ["node"], tmp_path, tmp_path)["status"] == "blocked"
    monkeypatch.setattr("scripts.check_handoff.subprocess.run", lambda *_args, **_kwargs:
                        SimpleNamespace(returncode=2, stdout="not ready", stderr=""))
    assert execute("runtime", ["python"], tmp_path, tmp_path)["status"] == "blocked"


def test_web_builder_checks_own_root_gates_before_native_imports(tmp_path, monkeypatch):
    from src.web_api import build_prepared_engine

    seen = []
    monkeypatch.setattr("src.benchmark.gates.detect_available_gates",
                        lambda *args: seen.append(args) or set())
    with pytest.raises(ValueError, match="acceptance gates"):
        build_prepared_engine(SimpleNamespace(root=tmp_path))
    assert seen == [(tmp_path, tmp_path / "docs/reports/2026-11-16_gate_acceptance.json")]


def test_prepared_engine_passes_existing_build_cache_without_download(tmp_path, monkeypatch):
    import src.indexing.bge as bge
    from src.web_api import build_prepared_engine

    monkeypatch.delenv("SENTENCE_TRANSFORMERS_HOME", raising=False)
    monkeypatch.setattr("src.benchmark.gates.detect_available_gates", lambda *_args:
                        {"canonical_cells_and_parents", "bm25_index"})
    encoder = Mock(return_value=object())
    monkeypatch.setattr(bge, "BGEEncoder", encoder)
    monkeypatch.setitem(sys.modules, "src.indexing.store", SimpleNamespace(
        ExactStore=lambda _path: SimpleNamespace(records=[])))
    tokenizer = SimpleNamespace(encode=lambda *_args, **_kw: [1, 2])
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *_args, **_kw: tokenizer)))
    monkeypatch.setattr("src.llm.client.UnifiedLLMClient.from_settings", lambda _settings: object())
    monkeypatch.setattr("src.application.assemble_exact_engine", lambda *_args, **_kw: SimpleNamespace())
    build_prepared_engine(SimpleNamespace(root=tmp_path, index_dir=tmp_path / "index",
                                         ollama_num_ctx=8192, ollama_num_predict=512),
                          tokenizer_dir=str(tmp_path))
    encoder.assert_called_once_with(cache_folder=str(tmp_path / "output/models"), local_files_only=True)
