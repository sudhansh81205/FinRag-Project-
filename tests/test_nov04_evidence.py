"""November 4 source regressions use the actual table grid and checked PDF pages."""

import copy
import gzip
import json
from pathlib import Path

import pytest

from scripts.prepare_evidence import ROOT, prepare, validate_records
from src.ingestion.filing_parser import ParseError, sha256, validate_source
from src.ingestion.pdf_evidence import corroborate_pdf, original_chart
from src.ingestion.statement_cells import displayed_amount, fact_attributes, json_number


@pytest.fixture(scope="module")
def evidence(tmp_path_factory):
    output = tmp_path_factory.mktemp("evidence")
    prepare(output)
    return json.loads((output / "evidence.json").read_text(encoding="utf8")), output


def test_statement_cells_and_display_sign(evidence):
    package, _ = evidence
    records = package["cells"]
    parents = {r["evidence_id"]: r for r in package["parent_tables"]}
    assert len(parents) == 3 and len({r["evidence_id"] for r in records}) == len(records) == 219
    for record in records:
        c = record["metadata"]
        grid = parents[record["metadata"]["parent_table_id"]]["source_rows"][c["row_index"]]
        assert c["column_index"] in [col["column"] for col in grid["cells"]]
        assert record["metadata"]["content_sha256"] == sha256(record["content"].encode())

    def selected(label, metric):
        return next(
            r["metadata"]
            for r in records
            if r["metadata"]["row_label"] == label
            and r["metadata"]["metric"].endswith(metric)
            and r["metadata"]["column_header"].endswith("2021")
        )

    sales = selected("Total net sales", "RevenueFromContractWithCustomerExcludingAssessedTax")
    assert (sales["period_start"], sales["period_end"], sales["normalized_value"]) == (
        "2020-09-27",
        "2021-09-25",
        365817000000,
    )
    assets = selected("Total assets", ":Assets")
    assert (assets["period_kind"], assets["normalized_value"]) == ("instant", 351002000000)
    eps = selected("Diluted", "EarningsPerShareDiluted")
    assert (eps["row_group"], eps["unit"], eps["normalized_value"]) == (
        "Earnings per share:",
        "USD/share",
        5.61,
    )
    outflow = selected("Repurchases of common stock", "PaymentsForRepurchaseOfCommonStock")
    assert outflow["normalized_value"] == -85971000000 and outflow["xbrl_sign"] is None
    assert displayed_amount("", 6) is None
    with pytest.raises(ParseError, match="Unsupported displayed"):
        displayed_amount("12 or 13", 6)


def test_pdf_matches_source_year_columns_and_rejects_changed_value(evidence):
    package, _ = evidence
    checks = package["pdf_corroboration"]
    cells = {r["evidence_id"]: r for r in package["cells"]}
    assert len(checks) == len({c["canonical_id"] for c in checks}) == 11
    assert {c["page"] for c in checks} == {32, 34, 36}
    assert all(c["source_spans"] and c["canonical_id"] in cells for c in checks)
    row = next(
        c
        for c in checks
        if c["row_label"] == "Total assets" and c["column_header"].endswith("2020")
    )
    assert "323,888" in row["raw_value"]
    wrong = json.loads(json.dumps(package["cells"]))
    next(r for r in wrong if r["evidence_id"] == row["canonical_id"])["metadata"][
        "normalized_value_decimal"
    ] = "0"
    spec = json.loads((ROOT / "data/source/apple-2021-renditions.json").read_text())
    with pytest.raises(ParseError, match="PDF/HTML disagreement"):
        corroborate_pdf(ROOT / spec["path"], spec, wrong)


def test_chart_asset_and_invalid_locator(evidence):
    package, output = evidence
    (chart,) = package["chart_sources"]
    assert chart["page"] == 22
    assert sha256((output / chart["asset"]).read_bytes()) == chart["image_sha256"]
    spec = json.loads((ROOT / "data/source/apple-2021-renditions.json").read_text())
    manifest = json.loads((ROOT / "data/filing_manifest.json").read_text())
    soup = validate_source(
        gzip.decompress((ROOT / manifest["source_archive"]).read_bytes()), manifest
    )
    spec["chart"]["html_selector"] = "img"
    with pytest.raises(ParseError, match="uniquely"):
        original_chart(Path(spec["path"]), spec, soup)


def test_canonical_package_and_every_cell_source(evidence):
    package, output = evidence
    schema = json.loads((ROOT / "data/contracts/canonical_record.schema.json").read_bytes())
    records = package["narratives"] + package["parent_tables"] + package["cells"]
    validate_records(records, schema)
    assert len(records) == 538
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert manifest["record_count"] == 538 and manifest["candidate_count"] == 535
    for filename, digest in manifest["files_sha256"].items():
        assert sha256((output / filename).read_bytes()) == digest
    filing = json.loads((ROOT / "data/filing_manifest.json").read_bytes())
    soup = validate_source((output / "source.html").read_bytes(), filing)
    parents = {r["evidence_id"]: r for r in package["parent_tables"]}
    for record in package["cells"]:
        meta = record["metadata"]
        (node,) = soup.select(meta["source_locator"])
        (fact,) = node.find_all("ix:nonfraction")
        parent = parents[meta["parent_table_id"]]
        assert node.find_parent("table") is soup.select_one(parent["metadata"]["source_locator"])
        grid = parent["source_rows"][meta["row_index"]]
        assert node.find_parent("tr") is soup.select_one(grid["source_locator"])
        assert (fact["name"], fact["contextref"]) == (meta["metric"], meta["context_ref"])
        assert meta["normalized_value"] == json_number(meta["normalized_value_decimal"])
        assert meta["scale"] == 10 ** meta["scale_power10"]
        assert meta["source_file"] == "source.html"
    # A blank with a real typed context stays missing, never a fabricated zero.
    ids = {node["id"]: node for node in soup.find_all(id=True)}
    assert fact_attributes(fact, ids, "—")["normalized_value"] is None


@pytest.mark.parametrize("defect", ["legacy_type", "missing_period", "bad_hash", "duplicate"])
def test_canonical_rejection(evidence, defect):
    package, _ = evidence
    record = copy.deepcopy(package["cells"][0])
    records = [record]
    if defect == "legacy_type":
        record["metadata"]["type"] = "financial_cell"
    elif defect == "missing_period":
        del record["metadata"]["period_end"]
    elif defect == "bad_hash":
        record["content"] = "changed"
    else:
        records.append(copy.deepcopy(record))
    schema = json.loads((ROOT / "data/contracts/canonical_record.schema.json").read_bytes())
    with pytest.raises(ParseError):
        validate_records(records, schema)
