"""Extract review candidates from checksum-pinned SEC inline-XBRL documents."""

import json
import re
import warnings
from collections import Counter
from datetime import date, datetime
from decimal import Decimal

from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning

from src.contracts import sha256
from src.ingestion.filing_parser import (
    BLOCKS,
    SECTION_ENDS,
    ParseError,
    clean_text,
    is_hidden,
    locator,
    table_rows,
)
from src.ingestion.statement_cells import displayed_amount, fact_attributes, json_number

PROFILE = "sec-ixbrl-corpus-v1"
SECTION_LABELS = {
    "Item 1A": "riskfactors",
    "Item 1B": "unresolvedstaff",
    "Item 7": "management",
    "Item 7A": "quantitative",
    "Item 8": "financialstatements",
    "Item 9": "changesin",
}
STATEMENT_FACTS = (
    {"NetIncomeLoss", "OperatingIncomeLoss", "Revenues", "ProfitLoss"},
    {"Assets", "LiabilitiesAndStockholdersEquity"},
    {"NetCashProvidedByUsedInOperatingActivities"},
)


def require(condition, message):
    if not condition:
        raise ParseError(message)


def name_key(value):
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def parse_date(value):
    value = re.sub(r"\s*,\s*", ", ", value.strip())
    for style in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, style).date()
        except ValueError:
            pass
    raise ParseError(f"Unsupported date: {value}")


def open_html(raw, digest):
    require(sha256(raw) == digest, "Pinned SEC HTML checksum mismatch")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        return BeautifulSoup(raw.decode("utf-8"), "lxml")


def validate_identity(soup, filing):
    def values(name, transform):
        return {
            transform(n.get_text(" ", strip=True))
            for n in soup.find_all(attrs={"name": "dei:" + name})
        }

    issuer = name_key(filing["issuer"])
    # SEC DEI uses the registered short name for this issuer.
    if filing["cik"] == "0001045810":
        issuer = "nvidiacorp"
    checks = {
        "issuer": (values("EntityRegistrantName", name_key), {issuer}),
        "CIK": (values("EntityCentralIndexKey", int), {int(filing["cik"])}),
        "form": (values("DocumentType", str.upper), {"10-K"}),
        "period": (
            values("DocumentPeriodEndDate", parse_date),
            {date.fromisoformat(filing["period_end"])},
        ),
        "fiscal year": (values("DocumentFiscalYearFocus", int), {int(filing["period_end"][:4])}),
    }
    for label, (actual, expected) in checks.items():
        require(actual == expected, f"SEC filing {label} mismatch")


def body_blocks(soup):
    return [
        n
        for n in soup.find_all(BLOCKS)
        if not n.find(BLOCKS) and not n.find_parent("table") and not is_hidden(n)
    ]


def section_bounds(blocks, profile, *, absent=()):
    bounds = {}
    for section, end in SECTION_ENDS.items():
        if section in absent:
            continue
        anchors = []
        for item in (section, end):
            if item in profile.get("headings", {}):
                matches = [
                    i for i, n in enumerate(blocks) if clean_text(n) == profile["headings"][item]
                ]
            else:
                label = SECTION_LABELS[item]
                matches = [
                    i
                    for i, n in enumerate(blocks)
                    if name_key(clean_text(n)).startswith(name_key(item) + label)
                    and len(clean_text(n)) <= 175
                ]
            require(
                len(matches) == 1, f"Expected one body heading for {item}, found {len(matches)}"
            )
            anchors.extend(matches)
        require(anchors[0] < anchors[1], f"Invalid body order for {section}")
        bounds[section] = tuple(anchors)
    return bounds


def record(base, kind, node, content, **metadata):
    source = locator(node)
    digest = sha256(content.encode())
    meta = {
        **base,
        **metadata,
        "type": kind,
        "content_sha256": digest,
        "source_locator": source,
        "source_anchor": node.get("id"),
    }
    identity = f"{base['accession']}:{kind}:{sha256((base['source_sha256'] + source).encode())[:16]}:{digest[:16]}"
    return {"evidence_id": identity, "metadata": meta, "content": content}


def narrative_blocks(blocks, start, end, base):
    result = []
    for node in blocks[start:end]:
        content = clean_text(node)
        if not content or content.casefold() == "table of contents" or content.isdigit():
            continue
        if node.find("table") or re.fullmatch(r"(?:PART [IVX]+|Item \d+[A-Z]?)", content, re.I):
            continue
        # Preserve source blocks before applying the experiment's chunking policy.
        result.append(
            record(base, "narrative_text", node, content, char_start=0, char_end=len(content))
        )
    require(bool(result), f"No narrative for {base['section']}")
    return result


def comparative_header(grid, period_end):
    choices = []
    for i, row in enumerate(grid):
        cols = row["cells"]
        dates = [c for c in cols if re.fullmatch(r"[A-Za-z]+ \d{1,2},? \d{4}", c["text"])]
        years = [c for c in cols if re.fullmatch(r"20\d\d", c["text"]) and c["column"] > 0]
        if len(dates) >= 2:
            choices.append((i, dates, [parse_date(c["text"]) for c in dates]))
        elif len(years) >= 2:
            # Microsoft, Oracle, Salesforce and IBM can put the month/day above
            # or beside the year cells. Require an explicit unique date label.
            head = " ".join(c["text"] for r in grid[max(0, i - 1) : i + 1] for c in r["cells"])
            labels = set(re.findall(r"\b([A-Za-z]+ \d{1,2})(?:,|:)", head))
            if len(labels) == 1:
                label = labels.pop()
                choices.append((i, years, [parse_date(f"{label}, {c['text']}") for c in years]))
        if choices:
            break
    require(bool(choices), "Unsupported comparative column headers")
    i, cols, dates = choices[0]
    require(
        dates[0].isoformat() == period_end and dates == sorted(set(dates), reverse=True),
        "Statement column dates do not match the filing period",
    )
    return i, cols, dates


def typed_fact(fact, ids, raw, column_date, label, cik):
    attrs = fact_attributes(fact, ids, raw)
    context = ids[fact["contextref"]]
    identifiers = context.find_all("xbrli:identifier")
    require(
        len(identifiers) == 1 and int(identifiers[0].get_text(strip=True)) == int(cik),
        "Fact issuer differs",
    )
    require(not context.find("xbrldi:typedmember"), "Unsupported typed dimension")
    actual_end = date.fromisoformat(attrs["period_end"])
    if actual_end != column_date:
        require(
            attrs["period_kind"] == "instant"
            and re.search(r"beginning|opening|at January 1\b", label, re.I)
            and 350 <= (column_date - actual_end).days <= 380,
            "Fact period does not match displayed column",
        )
    require(-12 <= attrs["scale_power10"] <= 12, "Unsupported XBRL scale")
    exact = attrs["normalized_value"]
    if exact is not None:
        tag_value = displayed_amount(clean_text(fact), attrs["scale_power10"])
        require(
            tag_value is not None and abs(Decimal(tag_value)) == abs(Decimal(exact)),
            "Displayed/tagged values differ",
        )
    return attrs


def statement(table, base, title, expected_facts, ids, period_end):
    grid = table_rows(table)
    tagged = {n.get("name", "").split(":")[-1] for n in table.find_all("ix:nonfraction")}
    require(tagged & expected_facts and len(tagged) >= 8, f"Incorrect pinned statement for {title}")
    header_i, headers, dates = comparative_header(grid, period_end)
    units_re = re.compile(r"\([^()]*\bin millions\b[^()]*\)", re.I)
    header_text = " ".join(c["text"] for r in grid[: header_i + 2] for c in r["cells"])
    units = units_re.findall(header_text)
    if not units:
        for adjacent in (table.find_previous_sibling(), table.find_next_sibling()):
            if (
                isinstance(adjacent, Tag)
                and not adjacent.find("table")
                and adjacent.name != "table"
            ):
                units = units_re.findall(clean_text(adjacent)[:170])
                if units:
                    break
    if not units:
        for node in table.find_all_previous(BLOCKS, limit=28):
            if not node.find(BLOCKS) and not node.find_parent("table"):
                units = units_re.findall(clean_text(node)[:170])
                if units:
                    break
    require(len(set(units)) == 1, f"Missing/ambiguous unit declaration for {title}")
    unit_text = units[0]
    starts = [c["column"] for c in headers]
    date_labels = [d.isoformat() for d in dates]
    lines = [title, unit_text, " | ".join(["Line item", *date_labels])]
    pending, omissions = [], Counter()
    group = ""
    for row_no, tr in enumerate(table.find_all("tr")):
        if row_no <= header_i:
            continue
        row = grid[row_no]
        nodes = tr.find_all(["td", "th"], recursive=False)
        pieces = list(zip(row["cells"], nodes, strict=True))
        left = [(c, n) for c, n in pieces if c["column"] < starts[0]]
        label = " ".join(c["text"] for c, _ in left if c["text"])
        values = []
        for i, start in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else float("inf")
            parts = [(c, n) for c, n in pieces if start <= c["column"] < end]
            raw = " ".join(c["text"] for c, _ in parts if c["text"])
            values.append(raw)
            if not raw or not label:
                continue
            facts = [
                (c, n, f)
                for c, n in parts
                for f in n.find_all("ix:nonfraction")
                if not is_hidden(f)
            ]
            if not facts and not any(ch.isdigit() for ch in raw):
                continue  # retain displayed blank/dash in the parent grid
            try:
                require(len(facts) == 1, "Mixed or untagged numeric cell")
                c, node, fact = facts[0]
                attrs = typed_fact(fact, ids, raw, dates[i], label, base["cik"])
                exact = attrs["normalized_value"]
                refs = fact.get("footnoterefs", "").split()
                require(all(ref in ids for ref in refs), "Unresolved inline footnote")
                links = sorted(
                    {a["href"] for _, n in left + parts for a in n.select("a[href]")}
                    | {"#" + ref for ref in refs}
                )
                dimensions = attrs["dimensions"]
                content = " | ".join(
                    filter(
                        None,
                        (
                            base["company"],
                            title,
                            group,
                            label,
                            date_labels[i],
                            raw,
                            unit_text,
                            attrs["metric"],
                            f"{exact} {attrs['unit']}" if exact is not None else "missing",
                        ),
                    )
                )
                pending.append(
                    record(
                        base,
                        "table_cell",
                        node,
                        content,
                        **{
                            **attrs,
                            "table_title": title,
                            "column_header": date_labels[i],
                            "periods_json": json.dumps([d.year for d in dates]),
                            "headers_json": json.dumps(date_labels),
                            "normalized_value_decimal": exact,
                            "normalized_value": json_number(exact),
                            "raw_unit": unit_text,
                            "normalized_unit": attrs["unit"],
                            "scale": 10 ** attrs["scale_power10"],
                            "scope": json.dumps(dimensions, sort_keys=True)
                            if dimensions
                            else "consolidated",
                            "row_label": label,
                            "row_headers": list(filter(None, (group, label))),
                            "row_group": group,
                            "column_headers": [date_labels[i]],
                            "row_index": row_no,
                            "column_index": c["column"],
                            "raw_value": raw,
                            "footnote_links": links,
                        },
                    )
                )
            except (ValueError, KeyError, ArithmeticError) as exc:
                omissions[str(exc).split(":")[0]] += 1
        if any(values) and label:
            lines.append(" | ".join([label, *values]))
        elif label:
            group = label
            lines.append(label)
    require(bool(pending), f"No source-typed facts in {title}")
    parent = record(
        base,
        "financial_table",
        table,
        "\n".join(lines),
        table_title=title,
        periods_json=json.dumps([d.year for d in dates]),
        headers_json=json.dumps(date_labels),
        units_json=json.dumps({"declared_text": unit_text}),
    )
    parent["source_rows"] = grid
    parent["metadata"]["parent_table_id"] = parent["evidence_id"]
    for cell in pending:
        cell["metadata"]["parent_table_id"] = parent["evidence_id"]
        cell["metadata"]["units_json"] = parent["metadata"]["units_json"]
    return parent, pending, dict(omissions)


def parse_corpus_filing(raw, filing, profile, exhibit_raw=None):
    soup = open_html(raw, profile["sha256"])
    validate_identity(soup, filing)
    blocks = body_blocks(soup)
    exhibit = profile.get("exhibit")
    if "block_ranges" in profile:
        require(
            all(clean_text(blocks[i]) == expected for i, expected in profile["block_anchors"]),
            "Pinned body headings differ",
        )
        bounds = profile["block_ranges"]
    else:
        bounds = section_bounds(blocks, profile, absent={"Item 7", "Item 8"} if exhibit else ())
    base = {key: filing[key] for key in ("accession", "ticker", "cik", "source_url")}
    base.update(
        filing_id=filing["accession"],
        company=filing["issuer"],
        fiscal_year=int(filing["period_end"][:4]),
        filing_period_end=filing["period_end"],
        source_sha256=profile["sha256"],
        source_file=filing["accession"] + ".html",
        record_schema_version=1,
        parser_version=PROFILE,
    )

    def section_records(source_blocks, ranges, meta):
        return [
            r
            for section, (start, end) in ranges.items()
            for r in narrative_blocks(source_blocks, start + 1, end, {**meta, "section": section})
        ]

    narratives = section_records(blocks, bounds, base)
    ids = {
        n["id"]: n
        for n in soup.find_all(id=True)
        if n.name in {"xbrli:context", "xbrli:unit", "ix:footnote"}
    }
    require(
        len(ids)
        == len(
            soup.find_all(
                lambda n: (
                    n.has_attr("id") and n.name in {"xbrli:context", "xbrli:unit", "ix:footnote"}
                )
            )
        ),
        "Duplicate XBRL context/unit",
    )
    if exhibit:
        filename = exhibit["filename"]
        require(soup.find("a", href=filename) is not None, "10-K exhibit link missing")
        require(exhibit_raw is not None, "Incorporated exhibit unavailable")
        soup = open_html(exhibit_raw, exhibit["sha256"])
        base = {
            **base,
            "source_url": filing["source_url"].rsplit("/", 1)[0] + "/" + filename,
            "source_file": filename,
            "source_sha256": exhibit["sha256"],
            "context_source_url": filing["source_url"],
            "context_source_sha256": profile["sha256"],
        }
        exhibit_blocks = body_blocks(soup)
        require(
            all(clean_text(exhibit_blocks[i]) == expected for i, expected in exhibit["anchors"]),
            "Exhibit sections no longer match their declared locations",
        )
        narratives += section_records(exhibit_blocks, exhibit["ranges"], base)

    tables = soup.find_all("table")
    titles = ("Income statement", "Balance sheet", "Cash flow statement")
    parents, cells, rejected = [], [], {}
    for i, title, expected in zip(profile["tables"], titles, STATEMENT_FACTS, strict=True):
        table = tables[i]
        require(not is_hidden(table), "Selected statement is hidden")
        parent, facts, omitted = statement(
            table, {**base, "section": "Item 8"}, title, expected, ids, filing["period_end"]
        )
        parents.append(parent)
        cells.extend(facts)
        rejected[title] = omitted
    return {
        "narrative_blocks": narratives,
        "parents": parents,
        "cells": cells,
        "omitted_cells": rejected,
    }
