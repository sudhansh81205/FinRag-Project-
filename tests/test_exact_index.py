"""Real FAISS storage tests with declared synthetic vectors, no model download."""

import copy
import json

import numpy as np
import pytest

from src.contracts import sha256
from src.indexing import store as storage
from src.indexing.bge import EmbeddingSpec, unit_vectors
from src.indexing.store import ExactStore, publish_filing
from src.retrieval.dense import DenseRetriever

A = "0000320193-21-000105"
B = "0001564590-21-039151"


@pytest.fixture
def tmp_path(tmp_path_factory):
    # Keep nested content-addressed paths under Windows' default path limit.
    return tmp_path_factory.mktemp("idx")


def record(name, accession=A, ticker="AAPL"):
    content = "Synthetic test evidence " + name
    return {
        "evidence_id": accession + ":" + name,
        "content": content,
        "metadata": {
            "accession": accession,
            "ticker": ticker,
            "section": "Item 7",
            "source_url": "https://example.com/synthetic",
            "source_locator": "#" + name,
            "source_sha256": "a" * 64,
            "type": "narrative_text",
            "record_schema_version": 1,
            "content_sha256": sha256(content.encode()),
            "parser_version": "synthetic-test-v1",
        },
    }


def vectors(*values):
    array = np.zeros((len(values), 768), dtype=np.float32)
    for row, (x, y) in enumerate(values):
        array[row, :2] = [x, y]
    return unit_vectors(array, len(values))


def test_exact_cosine_filter_before_limit_ties_and_reopen(tmp_path):
    records = [record("z"), record("a"), record("b")]
    matrix = vectors((1, 0), (1, 0), (0, 1))
    first = publish_filing(tmp_path, records, [], matrix, {"test_only": True})
    second = publish_filing(tmp_path, records, [], matrix, {"test_only": True})
    assert first == second
    publish_filing(
        tmp_path, [record("ms", B, "MSFT")], [], vectors((0.5, 0.5)), {"test_only": True}
    )
    store = ExactStore(tmp_path)
    results = store.search(matrix[0], k=20)
    assert [r["evidence_id"] for r in results] == [A + ":a", A + ":z", B + ":ms", A + ":b"]
    assert np.allclose([r["score"] for r in results], [1, 1, 2**-0.5, 0])
    filtered = store.search(matrix[0], k=1, filters={"ticker": "MSFT"})
    assert len(filtered) == 1 and filtered[0]["evidence_id"] == B + ":ms"
    assert filtered[0]["eligible_count"] == 1
    assert store.search(matrix[0], filters={"ticker": "UNKNOWN"}) == []
    assert store.search(matrix[0], filters={"ticker": []}) == []
    assert store.search(matrix[0], k=0) == []
    assert ExactStore(tmp_path).search(matrix[0], k=20) == results


def test_replace_removes_stale_rows_only_for_target_and_failed_write_preserves_catalog(tmp_path):
    publish_filing(tmp_path, [record("old1"), record("old2")], [], vectors((1, 0), (0, 1)), {})
    publish_filing(tmp_path, [record("other", B, "MSFT")], [], vectors((1, 0)), {})
    catalog = json.loads((tmp_path / "catalog.json").read_bytes())
    publish_filing(tmp_path, [record("new")], [], vectors((1, 0)), {})
    updated = json.loads((tmp_path / "catalog.json").read_bytes())
    assert updated["filings"][B] == catalog["filings"][B]
    assert (tmp_path / "filings" / A / catalog["filings"][A]).is_dir()
    assert {r["evidence_id"] for r in ExactStore(tmp_path).records} == {A + ":new", B + ":other"}
    before = (tmp_path / "catalog.json").read_bytes()
    with pytest.raises(ValueError, match="dimension"):
        publish_filing(tmp_path, [record("bad")], [], np.ones((1, 384)), {})
    assert (tmp_path / "catalog.json").read_bytes() == before
    assert len(ExactStore(tmp_path).records) == 2


@pytest.mark.parametrize(
    "filename",
    [
        "index.faiss",
        "records.json",
        "candidate_ids.json",
        "candidate_metadata.json",
        "parent_tables.json",
        "manifest.json",
        "provenance.json",
    ],
)
def test_every_persistent_artifact_is_bound_and_corruption_fails(tmp_path, filename):
    built = publish_filing(tmp_path, [record("one")], [], vectors((1, 0)), {})
    path = tmp_path / "filings" / A / built["generation"] / filename
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum"):
        ExactStore(tmp_path)


def test_duplicates_bad_model_nonfinite_zero_and_invalid_filters(tmp_path):
    r = record("one")
    with pytest.raises(ValueError, match="Duplicate"):
        publish_filing(tmp_path, [r, copy.deepcopy(r)], [], vectors((1, 0), (0, 1)), {})
    for bad in (np.zeros((1, 768)), np.full((1, 768), np.nan), np.full((1, 768), np.inf)):
        with pytest.raises(ValueError):
            publish_filing(tmp_path, [r], [], bad, {})
    publish_filing(tmp_path, [r], [], vectors((1, 0)), {})
    with pytest.raises(ValueError, match="rebuild"):
        ExactStore(tmp_path, spec=EmbeddingSpec(embedding_revision="f" * 40))
    store = ExactStore(tmp_path)
    for bad_filter in ({"unknown": "x"}, {"ticker": {"$ne": "AAPL"}}, {"ticker": [True]}):
        with pytest.raises(ValueError):
            store.search(vectors((1, 0))[0], filters=bad_filter)
    with pytest.raises(ValueError):
        store.search(vectors((1, 0))[0], k=True)
    with pytest.raises(ValueError, match="shape"):
        store.search(np.ones((2, 384)))


def test_disabled_dense_streams_make_no_encoder_call(tmp_path):
    publish_filing(tmp_path, [record("one")], [], vectors((1, 0)), {})

    class Encoder:
        spec = EmbeddingSpec()
        calls = 0

        def encode(self, texts, *, query):
            self.calls += 1
            assert query
            return vectors((1, 0))

    encoder = Encoder()
    adapter = DenseRetriever(ExactStore(tmp_path), encoder)
    result = adapter.retrieve("question", 0, 0)
    assert result["text_evidence"] == result["table_evidence"] == []
    assert encoder.calls == 0
    result = adapter.retrieve("question", 1, 0)
    assert len(result["text_evidence"]) == 1 and result["table_evidence"] == []
    assert encoder.calls == 1


def test_writer_lock_cannot_replace_active_store(tmp_path):
    publish_filing(tmp_path, [record("one")], [], vectors((1, 0)), {})
    before = (tmp_path / "catalog.json").read_bytes()
    (tmp_path / ".writer.lock").write_text("test other writer")
    with pytest.raises(ValueError, match="writer lock"):
        publish_filing(tmp_path, [record("two")], [], vectors((1, 0)), {})
    assert (tmp_path / "catalog.json").read_bytes() == before


def test_failed_catalog_switch_preserves_old_active_filing(tmp_path, monkeypatch):
    publish_filing(tmp_path, [record("old")], [], vectors((1, 0)), {})
    before = (tmp_path / "catalog.json").read_bytes()
    replace = storage.os.replace

    def fail_catalog(source, destination):
        if destination.name == "catalog.json":
            raise OSError("synthetic disk failure at publication")
        return replace(source, destination)

    monkeypatch.setattr(storage.os, "replace", fail_catalog)
    with pytest.raises(OSError, match="disk failure"):
        publish_filing(tmp_path, [record("new")], [], vectors((0, 1)), {})
    assert (tmp_path / "catalog.json").read_bytes() == before
    assert [r["evidence_id"] for r in ExactStore(tmp_path).records] == [A + ":old"]
    assert not (tmp_path / ".writer.lock").exists()
    monkeypatch.setattr(storage.os, "replace", replace)
    publish_filing(tmp_path, [record("new")], [], vectors((0, 1)), {})
    assert [r["evidence_id"] for r in ExactStore(tmp_path).records] == [A + ":new"]
