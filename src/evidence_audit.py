"""Independent, offline acceptance predicates for the bounded Apple evidence package.

This module never calls the cell/PDF builders to certify their own output. It
checks saved records against source DOM facts, and keeps parents out of candidates.
It does not certify arbitrary filings, financial inference, or an existing index.
"""

import json
import math
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from bs4 import BeautifulSoup
from jsonschema import Draft202012Validator, FormatChecker
from pypdf import PdfReader

from src.contracts import sha256, strict_json, within
from src.ingestion.filing_parser import clean_text


class AuditError(ValueError):
    """A source, record or cross-record acceptance premise failed."""


def require(condition, reason):
    if not condition:
        raise AuditError(reason)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def pdf_text_anchors(page):
    """Read independent pypdf text baselines in unrotated PDF point coordinates.

    The bounded fixture uses an origin-zero, unrotated page. Unsupported page
    transforms fail closed rather than turning a guessed conversion into proof.
    These are text anchors, not an independent glyph-outline reconstruction.
    """
    require(not page.rotation, "pdf_position_unsupported_rotation")
    require(float(page.mediabox.left) == float(page.mediabox.bottom) == 0,
            "pdf_position_unsupported_page_origin")
    anchors = []

    def visit(text, cm, tm, _font, size):
        text = " ".join(text.split())
        if not text:
            return
        require(len(cm) == len(tm) == 6 and all(math.isfinite(v) for v in [*cm, *tm, size]),
                "pdf_position_invalid_transform")
        require(cm[1] == cm[2] == tm[1] == tm[2] == 0,
                "pdf_position_unsupported_transform")
        x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
        y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
        height = abs(float(size) * cm[3] * tm[3])
        require(height > 0, "pdf_position_invalid_font_scale")
        anchors.append({"text": text, "x": x, "y": y, "height": height})

    page.extract_text(visitor_text=visit)
    return anchors


def audit_pdf_spans(check, page, headers, anchors=None):
    """Bind saved spans to independently extracted value, row and year anchors.

    The check deliberately certifies the text baseline/row/column association,
    not exact glyph rectangle extents. A matching number elsewhere on the page
    is insufficient. Candidate rectangles are still checked for valid bounds.
    """
    anchors = pdf_text_anchors(page) if anchors is None else anchors
    width, height = float(page.mediabox.width), float(page.mediabox.height)
    spans = check["source_spans"]
    require(spans and " ".join(s["text"] for s in spans) == check["raw_value"], "pdf_spans")
    matched = []
    for span in spans:
        box = span.get("bbox")
        require(isinstance(box, (list, tuple)) and len(box) == 4
                and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        and math.isfinite(v) for v in box), "pdf_span_bbox_finite")
        origin = span.get("origin")
        require(origin in {"BOTTOMLEFT", "TOPLEFT"}, "pdf_span_coordinate_origin")
        x0, y0, x1, y1 = box
        require(x0 < x1 and y0 < y1, "pdf_span_bbox_non_degenerate")
        require(0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height,
                "pdf_span_bbox_within_page")
        if origin == "TOPLEFT":
            y0, y1 = height - y1, height - y0
        hits = []
        for candidate in anchors:
            if not (abs(candidate["x"] - x0) <= 1.0 and y0 - 1 <= candidate["y"] <= y1 + 1):
                continue
            # pypdf may emit parentheses separately from a negative value. Join
            # only independently located fragments on this one boxed baseline.
            fragments = sorted((a for a in anchors if x0 - 1 <= a["x"] <= x1 + 1
                and abs(a["y"] - candidate["y"]) <= 0.5), key=lambda a: a["x"])
            if re.sub(r"\s", "", "".join(a["text"] for a in fragments)) == re.sub(r"\s", "", span["text"]):
                hits.append(candidate)
        require(len(hits) == 1, "pdf_span_independent_text_anchor")
        anchor = hits[0]
        row = [a for a in anchors if a["text"] == check["row_label"]
               and abs(a["y"] - anchor["y"]) <= max(2.0, anchor["height"] * 0.3)
               and a["x"] < x0]
        require(len(row) == 1, "pdf_span_independent_row")
        years = [header[-4:] for header in headers]
        year_anchors = []
        for year in years:
            hits = [a for a in anchors if a["text"] == year and a["y"] > anchor["y"]]
            require(len(hits) == 1, "pdf_span_independent_year_header")
            year_anchors.append(hits[0])
        centers = [a["x"] + a["height"] for a in year_anchors]
        require(centers == sorted(centers) and len(centers) == len(set(centers)),
                "pdf_span_year_order")
        column = min(range(len(centers)), key=lambda i: abs(centers[i] - anchor["x"]))
        require(years[column] == check["column_header"][-4:], "pdf_span_independent_year_column")
        # A span must not cross into another comparative column. The 1-point
        # margin accommodates the independent baseline versus glyph box edges.
        left = 0 if column == 0 else (centers[column - 1] + centers[column]) / 2
        right = width if column + 1 == len(centers) else (centers[column] + centers[column + 1]) / 2
        require(left - 1 <= x0 < x1 <= right + 1, "pdf_span_crosses_year_column")
        matched.append(anchor)
    require(max(a["y"] for a in matched) - min(a["y"] for a in matched) <= 2,
            "pdf_span_mixed_rows")


def source_nodes(soup, selector, ids):
    """Resolve the parser's bounded ID/direct-child selectors without rescanning HTML."""
    current = soup
    for i, part in enumerate(selector.split(" > ")):
        if part.startswith("#") and i == 0:
            current = ids.get(part[1:])
        else:
            match = re.fullmatch(r"([a-z][a-z0-9:-]*):nth-of-type\(([1-9][0-9]*)\)", part)
            if match is None or current is None:
                return []
            children = current.find_all(match[1], recursive=False)
            index = int(match[2]) - 1
            current = children[index] if index < len(children) else None
        if current is None:
            return []
    return [current]


def source_grid(table):
    rows = []
    for node in table.find_all("tr"):
        require(node.find_parent("table") is table, "nested_table")
        cells, column = [], 0
        for cell in node.find_all(["td", "th"], recursive=False):
            span = int(cell.get("colspan", 1))
            require(span > 0 and int(cell.get("rowspan", 1)) == 1, "unsupported_grid_span")
            cells.append({"column": column, "colspan": span, "text": clean_text(cell)})
            column += span
        rows.append(cells)
    return rows


def amount(raw, exponent):
    compact = re.sub(r"[\s$,]", "", raw)
    if compact in {"", "-", "–", "—"}:
        return None
    require(bool(re.fullmatch(r"(?:\(\d+(?:\.\d+)?\)|-?\d+(?:\.\d+)?)", compact)), "invalid_amount")
    return Decimal(compact.replace("(", "-").replace(")", "")) * (Decimal(10) ** exponent)


def audit_cell(record, parents, soup, ids):
    m = record["metadata"]
    parent = parents.get(m["parent_table_id"])
    require(parent is not None, "missing_parent")
    pm = parent["metadata"]
    tables = source_nodes(soup, pm["source_locator"], ids)
    require(len(tables) == 1, "parent_locator")
    table = tables[0]
    nodes = source_nodes(soup, m["source_locator"], ids)
    require(len(nodes) == 1 and nodes[0].find_parent("table") is table, "cell_locator_parent")
    node = nodes[0]
    rows = table.find_all("tr")
    require(
        m["row_index"] < len(rows) and node.find_parent("tr") is rows[m["row_index"]], "cell_row"
    )
    grid = parent["source_rows"]
    headers = strict_json(pm["headers_json"])
    header_rows = [r for r in grid if all(h in [c["text"] for c in r["cells"]] for h in headers)]
    require(len(header_rows) == 1, "ambiguous_headers")
    starts = [next(c["column"] for c in header_rows[0]["cells"] if c["text"] == h) for h in headers]
    require(m["column_index"] in starts, "cell_column")
    index = starts.index(m["column_index"])
    stop = starts[index + 1] if index + 1 < len(starts) else float("inf")
    row = rows[m["row_index"]]
    dom_cells = row.find_all(["td", "th"], recursive=False)
    saved_cells = grid[m["row_index"]]["cells"]
    parts = [
        n
        for n, c in zip(dom_cells, saved_cells, strict=True)
        if starts[index] <= c["column"] < stop
    ]
    raw = " ".join(filter(None, (clean_text(n) for n in parts)))
    facts = [f for n in parts for f in n.find_all("ix:nonfraction")]
    require(len(facts) == 1 and facts[0].find_parent(["td", "th"]) is node, "ambiguous_cell_fact")
    fact = facts[0]
    context, unit = ids.get(fact.get("contextref")), ids.get(fact.get("unitref"))
    require(context is not None and unit is not None, "unresolved_context_or_unit")
    period = context.find("xbrli:period")
    require(period is not None, "missing_period")
    instant = period.find("xbrli:instant")
    if instant is not None:
        kind, start, end = "instant", None, instant.text
    else:
        kind = "duration"
        start, end = period.find("xbrli:startdate").text, period.find("xbrli:enddate").text
        require(date.fromisoformat(start) <= date.fromisoformat(end), "invalid_duration")
    measures = tuple(n.text for n in unit.find_all("xbrli:measure"))
    units = {
        ("iso4217:USD",): "USD",
        ("xbrli:shares",): "shares",
        ("iso4217:USD", "xbrli:shares"): "USD/share",
    }
    require(measures in units, "unsupported_unit")
    normalized_unit = units[measures]
    exponent = int(fact.get("scale", 0))
    value = amount(raw, exponent)
    dims = {n["dimension"]: n.text for n in context.find_all("xbrldi:explicitmember")}
    label = " ".join(c["text"] for c in saved_cells if c["column"] < starts[0] and c["text"])
    group = ""
    for earlier in grid[: m["row_index"]]:
        if not any(c["text"] for c in earlier["cells"] if c["column"] >= starts[0]):
            candidate = " ".join(
                c["text"] for c in earlier["cells"] if c["column"] < starts[0] and c["text"]
            )
            if candidate:
                group = candidate
    repeated = sum(bool(r["cells"]) and r["cells"][0]["text"] == label for r in grid) > 1
    qualifier = group if repeated else ""
    refs = sorted({ref for ref in fact.get("footnoterefs", "").split()})
    require(all(ref in ids for ref in refs), "unresolved_footnote")
    links = sorted({a["href"] for n in [dom_cells[0], *parts] for a in n.select("a[href]")})
    expected = {
        "raw_value": raw,
        "metric": fact["name"],
        "context_ref": context["id"],
        "unit_ref": unit["id"],
        "period_kind": kind,
        "period_start": start,
        "period_end": end,
        "unit": normalized_unit,
        "normalized_unit": normalized_unit,
        "currency": "USD" if "USD" in normalized_unit else None,
        "scale_power10": exponent,
        "scale": 10**exponent,
        "dimensions": dims,
        "scope": json.dumps(dims, sort_keys=True) if dims else "consolidated",
        "xbrl_sign": fact.get("sign"),
        "column_header": headers[index],
        "column_headers": [headers[index]],
        "row_label": label,
        "row_group": qualifier,
        "row_headers": [s for s in (qualifier, label) if s],
        "table_title": pm["table_title"],
        "footnote_links": links + ["#" + ref for ref in refs],
        "headers_json": pm["headers_json"],
        "periods_json": pm["periods_json"],
        "raw_unit": strict_json(pm["units_json"])["declared_text"],
    }
    for key, wanted in expected.items():
        require(m.get(key) == wanted, f"cell_{key}")
    require(
        strict_json(m["units_json"])
        == {
            "declared_text": expected["raw_unit"],
            "unit": normalized_unit,
            "scale_power10": exponent,
        },
        "cell_units_json",
    )
    header_end = datetime.strptime(headers[index].replace(",", ""), "%B %d %Y").date()
    if label.endswith("beginning balances"):
        starts_for_column = {
            c.find("xbrli:startdate").text
            for c in soup.find_all("xbrli:context")
            if c.find("xbrli:startdate")
            and c.find("xbrli:enddate")
            and c.find("xbrli:enddate").text == header_end.isoformat()
        }
        require(
            kind == "instant"
            and (date.fromisoformat(end) + timedelta(days=1)).isoformat() in starts_for_column,
            "opening_balance_period",
        )
    else:
        require(date.fromisoformat(end) == header_end, "header_period_mismatch")
    require(
        (m["normalized_value"] is None and m["normalized_value_decimal"] is None)
        if value is None
        else m["normalized_value"] is not None
        and Decimal(str(m["normalized_value"])) == value
        and Decimal(m["normalized_value_decimal"]) == value,
        "normalized_amount",
    )
    require(
        record["evidence_id"] == f"{parent['evidence_id']}:r{m['row_index']}:c{m['column_index']}",
        "cell_identity",
    )
    decimal_text = format(value, "f") if value is not None else None
    expected_content = " | ".join(
        filter(
            None,
            [
                pm["company"],
                pm["table_title"],
                qualifier,
                label,
                headers[index],
                raw or "[blank]",
                expected["raw_unit"],
                fact["name"],
                f"{decimal_text} {normalized_unit}" if value is not None else "missing",
            ],
        )
    )
    require(record["content"] == expected_content, "cell_readable_content")


def audit_package(directory: Path, root: Path) -> dict:
    """Return a reject ledger; never produce a successful empty/partial audit."""
    failures = []
    result = {
        "status": "failed",
        "profile": "apple-2021-cells-pdf-chart-sources",
        "failures": failures,
        "index_ready": False,
        "financial_inference_verified": False,
    }
    try:
        manifest = strict_json((directory / "manifest.json").read_text(encoding="utf-8"))
        package = strict_json((directory / "evidence.json").read_text(encoding="utf-8"))
        filing = strict_json((root / "data/filing_manifest.json").read_text(encoding="utf-8"))
        schema_bytes = (root / "data/contracts/canonical_record.schema.json").read_bytes()
        schema_hash = sha256(schema_bytes)
        require(
            manifest["record_schema_sha256"] == package["record_schema_sha256"] == schema_hash,
            "schema_hash",
        )
        spec = strict_json(
            (root / "data/source/apple-2021-renditions.json").read_text(encoding="utf-8")
        )
        require(
            manifest["profile"] == result["profile"]
            and package["accession"] == filing["accession"] == spec["accession"],
            "package_identity",
        )
        expected_files = {"evidence.json", "source.html", spec["chart"]["image_sha256"] + ".jpg"}
        require(set(manifest["files_sha256"]) == expected_files, "package_file_inventory")
        for filename, digest in manifest["files_sha256"].items():
            require(
                sha256(within(directory, filename).read_bytes()) == digest, f"file_hash:{filename}"
            )
        raw = (directory / "source.html").read_bytes()
        require(sha256(raw) == filing["raw_sha256"], "source_hash")
        pdf = manifest["pdf_source"]
        require(pdf == {"path": spec["path"], "sha256": spec["sha256"]}, "pdf_identity")
        require(sha256(within(root, pdf["path"]).read_bytes()) == pdf["sha256"], "pdf_hash")
        groups = [package[k] for k in ("narratives", "parent_tables", "cells")]
        records = sum(groups, [])
        require(all(groups), "empty_record_group")
        require([len(g) for g in groups] == [316, 3, 219], "bounded_profile_counts")
        require(len(records) == manifest["record_count"], "record_count")
        validator = Draft202012Validator(
            strict_json(schema_bytes.decode()), format_checker=FormatChecker()
        )
        identities = [r["evidence_id"] for r in records]
        require(len(identities) == len(set(identities)), "duplicate_identity")
        soup = BeautifulSoup(raw.decode("utf-8"), "lxml")
        ids = {n["id"]: n for n in soup.find_all(id=True)}
        order = {id(n): i for i, n in enumerate(soup.find_all(True))}
        boundaries = {}
        for section, following in (
            ("Item 1A", "Item 1B"),
            ("Item 7", "Item 7A"),
            ("Item 8", "Item 9"),
        ):
            endpoints = []
            for label in (section, following):
                targets = {
                    a["href"][1:]
                    for a in soup.select("a[href^='#']")
                    if clean_text(a).rstrip(".").casefold() == label.casefold()
                }
                require(len(targets) == 1, "section_anchor")
                endpoints.append(order[id(ids[next(iter(targets))])])
            boundaries[section] = endpoints
        parents = {r["evidence_id"]: r for r in package["parent_tables"]}
        for group, kind in zip(
            groups, ("narrative_text", "financial_table", "table_cell"), strict=True
        ):
            for record in group:
                identity = record["evidence_id"]
                try:
                    require(not list(validator.iter_errors(record)), "record_schema")
                    m = record["metadata"]
                    for key, wanted in (
                        ("type", kind),
                        ("accession", filing["accession"]),
                        ("ticker", filing["ticker"]),
                        ("company", filing["company"]),
                        ("filing_id", filing["accession"]),
                        ("fiscal_year", filing["fiscal_year"]),
                        ("source_url", filing["source_url"]),
                        ("source_sha256", filing["raw_sha256"]),
                        ("source_file", "source.html"),
                    ):
                        require(m.get(key) == wanted, f"record_{key}")
                    require(
                        sha256(record["content"].encode()) == m["content_sha256"], "content_hash"
                    )
                    nodes = source_nodes(soup, m["source_locator"], ids)
                    require(len(nodes) == 1, "source_locator")
                    require(m["section"] in boundaries, "unsupported_section")
                    begin, finish = boundaries[m["section"]]
                    require(begin < order[id(nodes[0])] < finish, "source_section")
                    require(
                        m["parser_version"]
                        == (
                            "apple-2021-html-cells-v2"
                            if kind == "table_cell"
                            else "apple-2021-html-v1"
                        ),
                        "parser_version",
                    )
                    if kind == "table_cell":
                        audit_cell(record, parents, soup, ids)
                    else:
                        expected_id = (
                            f"{m['accession']}:{m['section'].replace(' ', '').lower()}:"
                            f"{kind}:{sha256(m['source_locator'].encode())[:12]}:{m['content_sha256'][:16]}"
                        )
                        require(identity == expected_id, "record_identity")
                        if kind == "narrative_text":
                            source = clean_text(nodes[0])
                            require(
                                0 <= m["char_start"] < m["char_end"] <= len(source),
                                "narrative_range",
                            )
                            require(
                                source[m["char_start"] : m["char_end"]] == record["content"],
                                "narrative_source_text",
                            )
                        else:
                            require(m["parent_table_id"] == identity, "parent_identity")
                            require(
                                [r["cells"] for r in record["source_rows"]]
                                == source_grid(nodes[0]),
                                "parent_grid",
                            )
                            previous = nodes[0].find_previous(
                                string=re.compile("in millions", re.I)
                            )
                            require(
                                previous is not None
                                and clean_text(previous.parent)
                                == strict_json(m["units_json"])["declared_text"],
                                "parent_unit_declaration",
                            )
                            require(m["table_title"] in filing["proposed_tables"], "parent_title")
                            title_node = nodes[0].find_previous(
                                string=re.compile(r"^Consolidated (Statements|Balance)", re.I)
                            )
                            require(
                                title_node is not None
                                and clean_text(title_node.parent).casefold()
                                == m["table_title"].casefold(),
                                "parent_source_title",
                            )
                            hs = strict_json(m["headers_json"])
                            grid = record["source_rows"]
                            hi = next(
                                i
                                for i, row in enumerate(grid)
                                if all(h in [c["text"] for c in row["cells"]] for h in hs)
                            )
                            starts = [
                                next(c["column"] for c in grid[hi]["cells"] if c["text"] == h)
                                for h in hs
                            ]
                            require(
                                strict_json(m["periods_json"]) == [int(h[-4:]) for h in hs],
                                "parent_periods",
                            )
                            lines = [" | ".join(["Row label", *hs])]
                            for row in grid[hi + 1 :]:
                                values = [[] for _ in range(len(hs) + 1)]
                                for cell in row["cells"]:
                                    if cell["text"]:
                                        values[
                                            sum(cell["column"] >= start for start in starts)
                                        ].append(cell["text"])
                                if any(values):
                                    lines.append(" | ".join(" ".join(v) for v in values))
                            require(
                                record["content"]
                                == f"{m['table_title']}\nDeclared units: {strict_json(m['units_json'])['declared_text']}\n"
                                + "\n".join(lines),
                                "parent_readable_content",
                            )
                            for saved, node in zip(
                                record["source_rows"], nodes[0].find_all("tr"), strict=True
                            ):
                                matched = source_nodes(soup, saved["source_locator"], ids)
                                require(
                                    len(matched) == 1 and matched[0] is node, "parent_row_locator"
                                )
                except (
                    AuditError,
                    KeyError,
                    TypeError,
                    ValueError,
                    AttributeError,
                    IndexError,
                ) as exc:
                    failures.append(
                        {
                            "evidence_id": identity,
                            "reason": str(exc)
                            if isinstance(exc, AuditError)
                            else "malformed_record",
                        }
                    )
        # Inline facts embedded in row labels (par value/authorized shares) are
        # not comparative value columns. Count only the latter for completeness.
        expected_cells = 0
        for p in parents.values():
            table = source_nodes(soup, p["metadata"]["source_locator"], ids)[0]
            headers = strict_json(p["metadata"]["headers_json"])
            grid = p["source_rows"]
            hrow = next(
                i
                for i, row in enumerate(grid)
                if all(h in [c["text"] for c in row["cells"]] for h in headers)
            )
            first = min(c["column"] for c in grid[hrow]["cells"] if c["text"] in headers)
            for row, saved in zip(table.find_all("tr")[hrow + 1 :], grid[hrow + 1 :], strict=True):
                for node, cell in zip(
                    row.find_all(["td", "th"], recursive=False), saved["cells"], strict=True
                ):
                    if cell["column"] >= first:
                        expected_cells += sum(
                            bool(clean_text(f)) for f in node.find_all("ix:nonfraction")
                        )
        require(len(package["cells"]) == expected_cells, "cell_coverage")
        ordered = [r["evidence_id"] for r in package["narratives"] + package["cells"]]
        require(len(ordered) == manifest["candidate_count"], "candidate_count")
        require(
            sha256(encoded(ordered)) == manifest["ordered_candidate_ids_sha256"],
            "candidate_order_hash",
        )
        chart = package["chart_sources"]
        require(len(chart) == 1, "chart_count")
        chart = chart[0]
        require(
            chart["accession"] == filing["accession"]
            and chart["html_url"] == filing["source_url"]
            and chart["pdf_url"] == spec["url"]
            and chart["source_asset_id"]
            == f"{filing['accession']}:chart:{spec['chart']['image_sha256']}",
            "chart_source_locator_identity",
        )
        for key, value in spec["chart"].items():
            require(chart[key] == value, "chart_locator_identity")
        require(len(soup.select(chart["html_selector"])) == 1, "chart_html_locator")
        require(chart["asset"] == spec["chart"]["image_sha256"] + ".jpg", "chart_asset_path")
        require(
            chart["html_sha256"] == filing["raw_sha256"] and chart["pdf_sha256"] == spec["sha256"],
            "chart_source_identity",
        )
        reader = PdfReader(within(root, spec["path"]))
        image = next(
            im for im in reader.pages[chart["page"] - 1].images if im.name == chart["pdf_image"]
        )
        require(sha256(image.data) == chart["image_sha256"], "original_chart_bytes")
        # A second PDF text extractor checks the selected displayed rows. Docling
        # coordinates remain provenance supplied by the builder, not new labels.
        by_id = {r["evidence_id"]: r for r in package["cells"]}
        checked = set()
        independent_anchors = {}
        for check in package["pdf_corroboration"]:
            m = by_id[check["canonical_id"]]["metadata"]
            require(check["canonical_id"] not in checked, "duplicate_pdf_check")
            checked.add(check["canonical_id"])
            page = next(p for p in spec["statement_pages"] if p["page"] == check["page"])
            require(
                check["title"] == m["table_title"] == page["title"]
                and check["row_label"] == m["row_label"] in page["checked_rows"]
                and check["column_header"] == m["column_header"]
                and check["pdf_sha256"] == spec["sha256"],
                "pdf_check_identity",
            )
            text = reader.pages[check["page"] - 1].extract_text()
            require(
                m["row_label"] in text
                and re.sub(r"\s", "", check["raw_value"]) in re.sub(r"\s", "", text),
                "pdf_display_text",
            )
            require(
                amount(check["raw_value"], m["scale_power10"])
                == Decimal(m["normalized_value_decimal"]),
                "pdf_amount",
            )
            pdf_page = reader.pages[check["page"] - 1]
            if check["page"] not in independent_anchors:
                independent_anchors[check["page"]] = pdf_text_anchors(pdf_page)
            audit_pdf_spans(check, pdf_page, strict_json(m["headers_json"]),
                            independent_anchors[check["page"]])
        expected_checks = {
            r["evidence_id"]
            for r in package["cells"]
            for p in spec["statement_pages"]
            if r["metadata"]["table_title"] == p["title"]
            and r["metadata"]["row_label"] in p["checked_rows"]
        }
        require(checked == expected_checks, "pdf_check_coverage")
        result.update(
            record_count=len(records),
            counts={
                k: len(package[k])
                for k in (
                    "narratives",
                    "parent_tables",
                    "cells",
                    "pdf_corroboration",
                    "chart_sources",
                )
            },
            candidate_count=len(ordered),
            ordered_candidate_ids_sha256=sha256(encoded(ordered)),
            files_sha256=manifest["files_sha256"],
            record_schema_sha256=schema_hash,
            source_sha256=sha256(raw),
            pdf_sha256=pdf["sha256"],
            pdf_position_verification="independent text anchors, rows and year columns; exact glyph rectangle extents not certified",
            accepted_profile="bounded Apple 2021 source package; wider corpus remains unmet",
        )
    except FileNotFoundError:
        result["status"] = "blocked"
        failures.append({"reason": "missing_package_or_source"})
    except (
        AuditError,
        OSError,
        KeyError,
        ValueError,
        TypeError,
        AttributeError,
        IndexError,
        StopIteration,
    ) as exc:
        reason = str(exc) if isinstance(exc, AuditError) else "package_integrity_or_shape"
        failures.append({"reason": reason})
    if result["status"] != "blocked":
        result["status"] = "passed" if not failures else "failed"
    return result


def candidate_sidecars(directory: Path):
    """Construct input row identities, without claiming vectors or a FAISS index."""
    package = strict_json((directory / "evidence.json").read_text(encoding="utf-8"))
    records = package["narratives"] + package["cells"]
    ordered = [r["evidence_id"] for r in records]
    metadata = [
        {"row": i, "evidence_id": r["evidence_id"], "metadata": r["metadata"]}
        for i, r in enumerate(records)
    ]
    return {
        "candidate_ids.json": encoded(ordered),
        "candidate_metadata.json": encoded(metadata),
        "parent_tables.json": encoded(package["parent_tables"]),
    }


def verify_sidecars(directory: Path, sidecars: Path):
    for name, payload in candidate_sidecars(directory).items():
        require(within(sidecars, name).read_bytes() == payload, f"sidecar_mismatch:{name}")
    return {"status": "passed", "scope": "candidate inputs only; no vector rows yet"}
