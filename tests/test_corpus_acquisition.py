"""Source identity and persistence failures must not count as acquired filings."""

import json
from pathlib import Path

import pytest

from scripts import acquire_corpus as corpus

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def filing():
    return json.loads((ROOT / "data/application_filings.json").read_bytes())[0]


def test_actual_cover_and_wrong_issuer_period(filing):
    payload = (ROOT / filing["rendition_path"]).read_bytes()
    result = corpus.inspect_pdf(payload, filing)
    assert result["identity_pages"] and result["page_count"] > 50
    for changed in ({"issuer": "Microsoft Corporation"}, {"period_end": "2022-09-24"}):
        with pytest.raises(ValueError, match="issuer/form/period"):
            corpus.inspect_pdf(payload, {**filing, **changed})
    with pytest.raises(ValueError, match="not a PDF"):
        corpus.inspect_pdf(b"<html>Access denied</html>", filing)


def test_checksum_mismatch_and_missing_source_fail_without_network(filing, tmp_path, monkeypatch):
    monkeypatch.setattr(corpus, "ROOT", tmp_path)
    local = tmp_path / "source.pdf"
    local.write_bytes((ROOT / filing["rendition_path"]).read_bytes())
    changed = {**filing, "rendition_path": "source.pdf", "rendition_sha256": "0" * 64}
    before = local.read_bytes()
    result = corpus.acquire(changed)
    assert result["status"] == "failed" and "checksum" in result["failure"]
    assert local.read_bytes() == before
    result = corpus.acquire({**changed, "rendition_path": "missing.pdf"})
    assert result["status"] == "missing"
    assert result["indexed_records"] == result["canonical_parsed_records"] == 0
