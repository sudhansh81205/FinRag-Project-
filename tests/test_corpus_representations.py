import gzip
import json
from pathlib import Path

import pytest

from src.indexing.representations import matched_representations
from src.ingestion.corpus import open_html, parse_corpus_filing
from src.ingestion.filing_parser import ParseError, clean_text

ROOT = Path(__file__).resolve().parents[1]
ACCESSION = "0000320193-24-000123"


@pytest.fixture(scope="module")
def filing_inputs():
    raw = gzip.decompress((ROOT / "data/source/corpus" / f"{ACCESSION}.html.gz").read_bytes())
    filing = next(
        f
        for f in json.loads((ROOT / "data/application_filings.json").read_bytes())
        if f["accession"] == ACCESSION
    )
    profile = json.loads((ROOT / "data/corpus_html_profiles.json").read_bytes())[ACCESSION]
    return raw, filing, profile


def test_original_statement_cell_and_matched_representations(filing_inputs):
    raw, filing, profile = filing_inputs
    extracted = parse_corpus_filing(raw, filing, profile)
    cell = next(
        x
        for x in extracted["cells"]
        if x["metadata"]["row_label"] == "Total net sales"
        and x["metadata"]["period_end"] == "2024-09-28"
    )
    m = cell["metadata"]
    soup = open_html(raw, profile["sha256"])
    assert m["raw_value"] == "391,035"
    assert m["normalized_value_decimal"] == "391035000000"
    assert m["normalized_unit"] == "USD"
    assert clean_text(soup.select_one(m["source_locator"])) == "391,035"
    assert extracted["omitted_cells"] == {
        "Income statement": {},
        "Balance sheet": {},
        "Cash flow statement": {},
    }
    variants = matched_representations(
        extracted["narrative_blocks"], extracted["parents"], extracted["cells"]
    )
    a, b, c = (variants[k][0] for k in "ABC")

    def kind(records, name):
        return [r for r in records if r["metadata"]["type"] == name]

    assert kind(a, "financial_table") == kind(b, "financial_table")
    assert kind(b, "narrative_text") == kind(c, "narrative_text")
    assert kind(a, "narrative_text") != kind(b, "narrative_text")
    assert m["parent_table_id"] in {p["evidence_id"] for p in variants["C"][1]}
    flat = next(r for r in b if cell["evidence_id"] in r["metadata"].get("source_evidence_ids", []))
    assert flat["metadata"]["period_end"] == "2024-09-28"
    assert "Total net sales | 2024-09-28 | 391,035 | USD |" in flat["content"]


def test_changed_source_wrong_issuer_and_wrong_statement_fail(filing_inputs):
    raw, filing, profile = filing_inputs
    with pytest.raises(ParseError, match="checksum"):
        parse_corpus_filing(raw + b" ", filing, profile)
    with pytest.raises(ParseError, match="CIK"):
        parse_corpus_filing(raw, {**filing, "cik": "0000789019"}, profile)
    with pytest.raises(ParseError, match="Incorrect pinned statement"):
        parse_corpus_filing(raw, filing, {**profile, "tables": [22, 22, 26]})
