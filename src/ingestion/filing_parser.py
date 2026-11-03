"""Parse the declared Apple 2021 HTML filing, without embeddings or index writes.

This is a deliberately bounded parser, not a generic SEC/XBRL implementation.
The notebook's BeautifulSoup extraction is split into explicit section/table
selection and source-linked records. Unsupported layouts fail visibly.
"""

import hashlib
import json
import re
from collections import Counter
from datetime import datetime

from bs4 import BeautifulSoup, Tag

PARSER_VERSION = "apple-2021-html-v1"
ACCESSION = "0000320193-21-000105"
SECTION_ENDS = {"Item 1A": "Item 1B", "Item 7": "Item 7A", "Item 8": "Item 9"}
TABLE_TITLES = (
    "Consolidated Statements of Operations",
    "Consolidated Balance Sheets",
    "Consolidated Statements of Cash Flows",
)
BLOCKS = ("div", "p", "h1", "h2", "h3", "h4", "li")


class ParseError(ValueError):
    """The input cannot be interpreted under the declared source contract."""


def clean_text(node):
    visible = [str(text).strip() for text in node.find_all(string=True)
               if not is_hidden(text.parent)]
    return re.sub(r"\s+", " ", " ".join(visible)).strip()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def locator(node):
    """CSS locator in the saved HTML/normal browser DOM; no fabricated page IDs."""
    parts = []
    while isinstance(node, Tag) and node.name != "[document]":
        if node.get("id") and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", node["id"]):
            parts.append("#" + node["id"])
            break
        index = 1 + len(node.find_previous_siblings(node.name))
        parts.append(f"{node.name}:nth-of-type({index})")
        node = node.parent
    return " > ".join(reversed(parts))


def is_hidden(node):
    for parent in [node, *node.parents]:
        if not isinstance(parent, Tag):
            continue
        style = re.sub(r"\s+", "", parent.get("style", "")).lower()
        if (parent.name in {"script", "style", "ix:header", "ix:hidden"}
                or parent.has_attr("hidden") or "display:none" in style
                or "visibility:hidden" in style):
            return True
    return False


def validate_source(raw, manifest):
    if (manifest.get("accession") != ACCESSION or manifest.get("fiscal_year") != 2021
            or manifest.get("ticker") != "AAPL" or manifest.get("form") != "10-K"
            or manifest.get("company") != "Apple Inc."
            or manifest.get("cik") != "0000320193"
            or manifest.get("period_end") != "2021-09-25"
            or manifest.get("filed_date") != "2021-10-29"):
        raise ParseError("Only the declared Apple fiscal 2021 10-K is supported.")
    if (manifest.get("selected_sections") != list(SECTION_ENDS)
            or manifest.get("proposed_tables") != list(TABLE_TITLES)):
        raise ParseError("Manifest scope differs from this bounded parser's supported sections/tables.")
    expected_url = (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019321000105/aapl-20210925.htm"
    )
    if manifest.get("source_url") != expected_url:
        raise ParseError("Source URL does not identify the declared accession.")
    if manifest.get("raw_sha256") and sha256(raw) != manifest["raw_sha256"]:
        raise ParseError("Source checksum mismatch; do not silently replace the declared filing.")
    try:
        soup = BeautifulSoup(raw.decode("utf-8"), "lxml")
    except UnicodeDecodeError as exc:
        raise ParseError("Expected UTF-8 HTML for this filing.") from exc
    expected = {
        "dei:EntityCentralIndexKey": "0000320193",
        "dei:DocumentFiscalYearFocus": "2021",
        "dei:DocumentType": "10-K",
        "dei:DocumentPeriodEndDate": "2021-09-25",
        "dei:EntityRegistrantName": "Apple Inc.",
    }
    for name, value in expected.items():
        # DEI facts may intentionally live in ix:hidden; identity checks still read them.
        values = {re.sub(r"\s+", " ", n.get_text(" ", strip=True)).strip()
                  for n in soup.find_all(attrs={"name": name})}
        if name == "dei:DocumentPeriodEndDate":
            try:
                values = {v if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v)
                          else datetime.strptime(re.sub(r"\s+,", ",", v), "%B %d, %Y").date().isoformat()
                          for v in values}
            except ValueError as exc:
                raise ParseError("Unsupported filing period-end format.") from exc
        if values != {value}:
            raise ParseError(f"Filing identity check failed: {name}.")
    return soup


def section_anchor(soup, section):
    # Use the TOC ONLY to follow its link to the real section body.
    links = [a for a in soup.find_all("a", href=True)
             if clean_text(a).rstrip(".").casefold() == section.casefold()]
    targets = {a["href"][1:] for a in links if a["href"].startswith("#")}
    if len(targets) != 1:
        raise ParseError(f"Missing/ambiguous body anchor for {section}.")
    matches = soup.find_all(id=targets.pop())
    if len(matches) != 1 or matches[0].find_parent("table") or is_hidden(matches[0]):
        raise ParseError(f"Invalid body anchor for {section}.")
    return matches[0]


def slices(text, size=1000, overlap=200):
    if size < 80 or not 0 <= overlap < size:
        raise ParseError("Require chunk size >= 80 and 0 <= overlap < size.")
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + overlap + 1, end + 1)
            if boundary > start:
                end = boundary
        yield start, end, text[start:end]
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
        while start < end and start > 0 and not text[start - 1].isspace():
            start += 1


def make_record(manifest, section, node, content, kind, extra=None):
    source_locator = locator(node)
    digest = sha256(content.encode("utf-8"))
    location_hash = sha256(source_locator.encode("utf-8"))[:12]
    record_id = f"{ACCESSION}:{section.replace(' ', '').lower()}:{kind}:{location_hash}:{digest[:16]}"
    metadata = {
        "accession": ACCESSION, "filing_id": ACCESSION, "ticker": "AAPL",
        "company": manifest["company"], "fiscal_year": 2021,
        "section": section, "source_url": manifest["source_url"],
        "source_locator": source_locator, "source_file": manifest["raw_path"],
        "source_sha256": manifest["raw_sha256"], "content_sha256": digest,
        "type": kind, "record_schema_version": 1, "parser_version": PARSER_VERSION,
        **(extra or {}),
    }
    return {"id": record_id, "content": content, "metadata": metadata}


def table_rows(table):
    result = []
    for tr in table.find_all("tr"):
        if tr.find_parent("table") is not table:
            raise ParseError("Nested tables are not supported in the selected statements.")
        cells, column = [], 0
        for cell in tr.find_all(["td", "th"], recursive=False):
            try:
                span = int(cell.get("colspan", 1))
                rowspan = int(cell.get("rowspan", 1))
            except ValueError as exc:
                raise ParseError("Invalid table span.") from exc
            if span < 1 or span > 100 or rowspan != 1:
                raise ParseError("Unsupported table span; review this table explicitly.")
            cells.append({"column": column, "colspan": span, "text": clean_text(cell)})
            column += span
        result.append({"source_locator": locator(tr), "cells": cells})
    return result


def parse_table(table, heading, units, manifest):
    rows = table_rows(table)
    # Source headers, not all years mentioned anywhere in the table's body.
    header_matches = [(i, [c for c in row["cells"]
                          if re.fullmatch(r"September \d{1,2},? 20\d{2}", c["text"])])
                      for i, row in enumerate(rows)]
    header_matches = [(i, cells) for i, cells in header_matches if len(cells) >= 2]
    if len(header_matches) != 1:
        raise ParseError(f"Cannot identify comparative column headers: {heading}.")
    header_index, headers = header_matches[0]
    periods = [int(re.search(r"20\d{2}$", c["text"])[0]) for c in headers]
    wanted = [2021, 2020] if heading == TABLE_TITLES[1] else [2021, 2020, 2019]
    if periods != wanted:
        raise ParseError(f"Unexpected comparative periods: {heading}.")
    starts = [c["column"] for c in headers]
    lines = [" | ".join(["Row label", *[c["text"] for c in headers]])]
    for row in rows[header_index + 1:]:
        groups = [[] for _ in range(len(headers) + 1)]
        for cell in row["cells"]:
            group = sum(cell["column"] >= start for start in starts)
            if cell["text"]:
                groups[group].append(cell["text"])
        if any(groups):
            lines.append(" | ".join(" ".join(g) for g in groups))
    content = f"{heading}\nDeclared units: {units}\n" + "\n".join(lines)
    record = make_record(manifest, "Item 8", table, content, "financial_table", {
        "table_title": heading, "periods_json": json.dumps(periods),
        "headers_json": json.dumps([c["text"] for c in headers]),
        "units_json": json.dumps({"declared_text": units, "normalization": "not_performed"}),
    })
    record["metadata"]["parent_table_id"] = record["id"]
    # Keep unmodified cell text and spans for the Nov 6 row-normalization work.
    record["source_rows"] = rows
    return record


def parse_filing(raw, manifest, *, chunk_size=1000, overlap=200):
    """Return narrative records, full table records and an accounted summary."""
    # Validate settings even if the source happens to contain no long paragraphs.
    list(slices("", chunk_size, overlap))
    soup = validate_source(raw, manifest)
    manifest = {**manifest, "raw_sha256": sha256(raw)}
    elements = list(soup.find_all(True))
    order = {id(tag): i for i, tag in enumerate(elements)}
    bounds, sections = {}, {}
    for section, following in SECTION_ENDS.items():
        start, end = section_anchor(soup, section), section_anchor(soup, following)
        if order[id(start)] >= order[id(end)]:
            raise ParseError(f"Invalid section order: {section}.")
        first_blocks = [n for n in elements[order[id(start)] + 1:order[id(end)]]
                        if n.name in BLOCKS and not n.find(BLOCKS)
                        and not n.find_parent("table") and not is_hidden(n) and clean_text(n)][:5]
        if not any(re.match(re.escape(section) + r"\.\s", clean_text(n)) for n in first_blocks):
            raise ParseError(f"Body heading does not match {section}.")
        bounds[section] = (order[id(start)], order[id(end)])
        sections[section] = {"start": locator(start), "end_exclusive": locator(end)}

    narrative, tables = [], []
    excluded = Counter()
    for section, (start, end) in bounds.items():
        eligible = elements[start + 1:end]
        candidates = [n for n in eligible if n.name in BLOCKS and not n.find(BLOCKS)]
        for node in candidates:
            if node.find_parent("table") or is_hidden(node):
                excluded["table_or_hidden_blocks"] += 1
                continue
            text = clean_text(node)
            if len(text) < 80 or re.fullmatch(r"Apple Inc\. \| 2021 Form 10-K \| \d+", text):
                excluded["short_or_footer_blocks"] += 1
                continue
            for begin, finish, passage in slices(text, chunk_size, overlap):
                narrative.append(make_record(manifest, section, node, passage, "narrative_text", {
                    "char_start": begin, "char_end": finish,
                }))
        if not any(r["metadata"]["section"] == section for r in narrative):
            raise ParseError(f"No narrative evidence extracted from {section}.")

    start, end = bounds["Item 8"]
    for title in TABLE_TITLES:
        headings = [n for n in elements[start + 1:end] if n.name in BLOCKS
                    and not n.find(BLOCKS) and not n.find_parent("table")
                    and not is_hidden(n) and clean_text(n).casefold() == title.casefold()]
        if len(headings) != 1:
            raise ParseError(f"Missing/ambiguous statement heading: {title}.")
        heading = headings[0]
        table = heading.find_next("table")
        if table is None or not start < order[id(table)] < end or is_hidden(table):
            raise ParseError(f"Missing table inside Item 8: {title}.")
        between = elements[order[id(heading)] + 1:order[id(table)]]
        unit_notes = [clean_text(n) for n in between if n.name in BLOCKS
                      and not n.find(BLOCKS) and "in millions" in clean_text(n).casefold()]
        if len(unit_notes) != 1:
            raise ParseError(f"Missing/ambiguous declared units: {title}.")
        tables.append(parse_table(table, title, unit_notes[0], manifest))

    records = narrative + tables
    if len({r["id"] for r in records}) != len(records):
        raise ParseError("Duplicate evidence IDs; inspect source locations and chunks.")
    for record in records:
        if len(soup.select(record["metadata"]["source_locator"])) != 1:
            raise ParseError("Evidence source locator does not resolve uniquely.")
    summary = {
        "parser_version": PARSER_VERSION, "accession": ACCESSION,
        "source_sha256": manifest["raw_sha256"], "source_bytes": len(raw),
        "chunk_size": chunk_size, "chunk_overlap": overlap,
        "sections": sections, "narrative_records": len(narrative), "table_records": len(tables),
        "total_records": len(records),
        "narrative_by_section": dict(Counter(r["metadata"]["section"] for r in narrative)),
        "excluded_blocks": dict(excluded),
        "all_source_tables": len(soup.find_all("table")),
        "selected_statement_tables": [
            {"id": t["id"], "title": t["metadata"]["table_title"],
             "periods": json.loads(t["metadata"]["periods_json"]),
             "units": json.loads(t["metadata"]["units_json"]),
             "source_locator": t["metadata"]["source_locator"],
             "source_rows": len(t["source_rows"])} for t in tables
        ],
        "limitations": ["Only the declared Apple 2021 layout is supported.",
                        "Only the three selected statements are table evidence; other tables are excluded.",
                        "Short headings/blocks under 80 characters are not standalone narrative evidence.",
                        "Full tables are parent records; numeric row normalization is Nov 6 work.",
                        "No embedding, index readiness, retrieval quality or financial answer is established."],
    }
    return narrative, tables, summary
