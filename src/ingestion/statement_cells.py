"""Derive displayed financial facts from the three verified Apple statement grids."""

import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal

from src.ingestion.filing_parser import ParseError, clean_text, locator, sha256


def period_of(context):
    period = context.find("xbrli:period")
    if not period:
        raise ParseError("Missing XBRL period")
    instant = period.find("xbrli:instant")
    if instant:
        return {
            "period_kind": "instant",
            "period_start": None,
            "period_end": date.fromisoformat(instant.text).isoformat(),
        }
    start, end = period.find("xbrli:startdate"), period.find("xbrli:enddate")
    if not start or not end or date.fromisoformat(start.text) > date.fromisoformat(end.text):
        raise ParseError("Invalid duration context")
    return {"period_kind": "duration", "period_start": start.text, "period_end": end.text}


def displayed_amount(raw, scale):
    # Parentheses in the statement represent presentation sign. XBRL may instead
    # encode an outflow as a positive payments concept. Keep the two distinct.
    compact = raw.replace(" ", "").replace("$", "").replace(",", "")
    if compact in {"—", "–", "-", ""}:
        return None
    if not re.fullmatch(r"(?:\(\d+(?:\.\d+)?\)|-?\d+(?:\.\d+)?)", compact):
        raise ParseError(f"Unsupported displayed amount: {raw!r}")
    number = Decimal(compact.replace("(", "-").replace(")", ""))
    return format(number.scaleb(scale), "f")


def fact_attributes(fact, ids, raw):
    context = ids.get(fact.get("contextref"))
    unit = ids.get(fact.get("unitref"))
    if context is None or unit is None:
        raise ParseError("Unresolved XBRL context or unit")
    measures = [x.text for x in unit.find_all("xbrli:measure")]
    units = {
        ("iso4217:USD",): "USD",
        ("xbrli:shares",): "shares",
        ("iso4217:USD", "xbrli:shares"): "USD/share",
    }
    kind = units.get(tuple(measures))
    if not kind:
        raise ParseError(f"Unsupported unit {measures}")
    scale = int(fact.get("scale", 0))
    return {
        **period_of(context),
        "metric": fact["name"],
        "unit": kind,
        "currency": "USD" if "USD" in kind else None,
        "scale_power10": scale,
        "normalized_value": displayed_amount(raw, scale),
        "xbrl_sign": fact.get("sign"),
        "context_ref": context["id"],
        "unit_ref": unit["id"],
        "dimensions": {n["dimension"]: n.text for n in context.find_all("xbrldi:explicitmember")},
    }


def statement_cells(soup, parents):
    ids = {node["id"]: node for node in soup.find_all(id=True)}
    records = []
    for parent in parents:
        meta = parent["metadata"]
        table = soup.select_one(meta["source_locator"])
        headers = json.loads(meta["headers_json"])
        starts = []
        group_label = ""
        labels = Counter(row["cells"][0]["text"] for row in parent["source_rows"] if row["cells"])
        for row_no, (row, grid) in enumerate(
            zip(table.find_all("tr"), parent["source_rows"], strict=True)
        ):
            cells = row.find_all(["td", "th"], recursive=False)
            columns = [c["column"] for c in grid["cells"]]
            texts = [clean_text(c) for c in cells]
            if all(h in texts for h in headers):
                starts = [columns[texts.index(h)] for h in headers]
                continue
            if not starts:
                continue
            label = " ".join(t for col, t in zip(columns, texts) if col < starts[0] and t)
            if not any(t for col, t in zip(columns, texts) if col >= starts[0]):
                if label:
                    group_label = label
                continue
            if not label:
                raise ParseError(f"Unlabelled value row {row_no}")
            for i, start in enumerate(starts):
                end = starts[i + 1] if i + 1 < len(starts) else float("inf")
                parts = [c for col, c in zip(columns, cells) if start <= col < end]
                if not parts:
                    raise ParseError(f"Missing grid span for {label} / {headers[i]}")
                raw = " ".join(filter(None, (clean_text(c) for c in parts)))
                facts = [f for c in parts for f in c.find_all("ix:nonfraction")]
                if len(facts) > 1 or (not facts and any(ch.isdigit() for ch in raw)):
                    raise ParseError(
                        f"Ambiguous value or untagged numeric cell: {label} / {headers[i]}"
                    )
                if not facts:
                    raise ParseError(f"Missing typed context for {label} / {headers[i]}")
                attrs = fact_attributes(facts[0], ids, raw)
                node = facts[0].find_parent(["td", "th"]) if facts else parts[0]
                source = locator(node)
                footnotes = sorted(
                    {a["href"] for c in [cells[0], *parts] for a in c.select("a[href]")}
                )
                refs = sorted({ref for f in facts for ref in f.get("footnoterefs", "").split()})
                if any(ref not in ids for ref in refs):
                    raise ParseError("Unresolved inline footnote")
                title = meta["table_title"]
                # Repeated labels such as Products or Diluted need the preceding group.
                qualifier = group_label if labels[label] > 1 else ""
                units = {
                    "declared_text": json.loads(meta["units_json"])["declared_text"],
                    "unit": attrs.get("unit"),
                    "scale_power10": attrs.get("scale_power10"),
                }
                content = " | ".join(
                    filter(
                        None,
                        [
                            meta["company"],
                            title,
                            qualifier,
                            label,
                            headers[i],
                            raw or "[blank]",
                            units["declared_text"],
                            attrs.get("metric"),
                            f"{attrs['normalized_value']} {attrs['unit']}"
                            if attrs["normalized_value"] is not None
                            else "missing",
                        ],
                    )
                )
                records.append(
                    {
                        "evidence_id": f"{parent['id']}:r{row_no}:c{start}",
                        "content": content,
                        "metadata": {
                            **meta,
                            "type": "table_cell",
                            "record_schema_version": 1,
                            "source_locator": source,
                            "content_sha256": sha256(content.encode()),
                            "parser_version": "apple-2021-html-cells-v2",
                            "units_json": json.dumps(units),
                            **attrs,
                            "normalized_value_decimal": attrs["normalized_value"],
                            "normalized_value": json_number(attrs["normalized_value"]),
                            "raw_unit": units["declared_text"],
                            "normalized_unit": attrs["unit"],
                            "scale": 10 ** attrs["scale_power10"],
                            "scope": json.dumps(attrs["dimensions"], sort_keys=True)
                            if attrs["dimensions"]
                            else "consolidated",
                            "row_headers": [x for x in (qualifier, label) if x],
                            "column_headers": [headers[i]],
                            "row_index": row_no,
                            "column_index": start,
                            "row_label": label,
                            "row_group": qualifier,
                            "column_header": headers[i],
                            "raw_value": raw,
                            "footnote_links": footnotes + ["#" + ref for ref in refs],
                        },
                    }
                )
    if len({r["evidence_id"] for r in records}) != len(records):
        raise ParseError("Duplicate cell identity")
    return records


def json_number(value):
    """Satisfy the canonical number/null contract, retaining exact decimal text too."""
    if value is None:
        return None
    number = Decimal(value)
    if number == number.to_integral_value():
        return int(number)
    result = float(number)
    if not Decimal(str(result)).is_finite() or Decimal(str(result)) != number:
        raise ParseError("Amount cannot be represented by the canonical JSON number")
    return result
