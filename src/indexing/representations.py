"""Build source-equivalent A/B/C candidates with explicit eligibility boundaries."""

from collections import defaultdict
from copy import deepcopy

from src.contracts import sha256
from src.ingestion.filing_parser import ParseError, slices

CHUNK_SIZE, OVERLAP = 1000, 200


def derived(record, content, suffix, **metadata):
    digest = sha256(content.encode())
    return {
        "evidence_id": f"{record['evidence_id']}:{suffix}:{digest[:16]}",
        "content": content,
        "metadata": {**record["metadata"], **metadata, "content_sha256": digest},
    }


def section_narratives(blocks):
    results = []
    for block in blocks:
        content = block["content"]
        if len(content) <= CHUNK_SIZE:
            results.append(block)
            continue
        meta = block["metadata"]
        for start, end, text in slices(content, CHUNK_SIZE, OVERLAP):
            results.append(
                derived(
                    block,
                    text,
                    f"section:{start}:{end}",
                    char_start=meta["char_start"] + start,
                    char_end=meta["char_start"] + end,
                    source_evidence_ids=[block["evidence_id"]],
                )
            )
    return results


def fixed_narratives(blocks):
    groups = defaultdict(list)
    for block in blocks:
        meta = block["metadata"]
        groups[(meta["section"], meta["source_sha256"], meta["source_url"])].append(block)
    results = []
    for records in groups.values():
        spans, parts, total = [], [], 0
        previous = None
        for record in records:
            meta = record["metadata"]
            offset = 0
            # The historical Apple package already contains overlapping slices.
            # Reassemble its visible text once before applying the A policy.
            if previous and meta["source_locator"] == previous["source_locator"]:
                offset = max(0, previous["char_end"] - meta["char_start"])
            part = record["content"][offset:]
            previous = meta
            if part:
                if parts and offset == 0:
                    parts.append(" ")
                    total += 1
                spans.append((total, total + len(part), record, offset))
                parts.append(part)
                total += len(part)
        text = "".join(parts)
        for start, end, passage in slices(text, CHUNK_SIZE, OVERLAP):
            source_spans = [
                {
                    "evidence_id": record["evidence_id"],
                    "source_locator": record["metadata"]["source_locator"],
                    "char_start": record["metadata"]["char_start"] + skip + max(0, start - lo),
                    "char_end": record["metadata"]["char_start"] + skip + min(hi, end) - lo,
                }
                for lo, hi, record, skip in spans
                if lo < end and hi > start
            ]
            first = next(r for lo, hi, r, _ in spans if lo < end and hi > start)
            results.append(
                derived(
                    first,
                    passage,
                    f"fixed:{start}:{end}",
                    char_start=source_spans[0]["char_start"],
                    char_end=source_spans[0]["char_end"],
                    source_spans=source_spans,
                    source_evidence_ids=[span["evidence_id"] for span in source_spans],
                )
            )
    return results


def markdown(text):
    return str(text).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def flattened_tables(parents, cells):
    groups = defaultdict(list)
    keys = ("period_end", "period_start", "scope", "normalized_unit")
    for cell in cells:
        m = cell["metadata"]
        groups[(m["parent_table_id"], *(m[k] for k in keys))].append(cell)
    results = []
    for parent in parents:
        for (parent_id, *scope), facts in groups.items():
            if parent_id != parent["evidence_id"]:
                continue
            m = facts[0]["metadata"]
            prefix = (
                f"{m['company']} | {m['table_title']} | source units: {m['raw_unit']}\n"
                "| Line item | Displayed column | Displayed value | Normalized unit |\n"
                "| --- | --- | --- | --- |"
            )
            batches, lines, included = [], [prefix], []
            size = len(prefix)
            for cell in facts:
                cm = cell["metadata"]
                row = (
                    "| "
                    + " | ".join(
                        map(
                            markdown,
                            (
                                " / ".join(cm["row_headers"]),
                                cm["column_header"],
                                cm["raw_value"] or "[blank]",
                                cm["normalized_unit"],
                            ),
                        )
                    )
                    + " |"
                )
                if len(prefix) + len(row) + 1 > CHUNK_SIZE:
                    raise ParseError("Flattened statement row exceeds the passage limit")
                if size + len(row) + 1 > CHUNK_SIZE:
                    batches.append((lines, included))
                    lines, included, size = [prefix], [], len(prefix)
                lines.append(row)
                included.append(cell)
                size += len(row) + 1
            batches.append((lines, included))
            for lines, included in batches:
                relations = [c["evidence_id"] for c in included]
                group_id = sha256("\n".join(relations).encode())[:16]
                item = derived(
                    parent,
                    "\n".join(lines),
                    f"markdown:{group_id}",
                    **dict(zip(keys, scope, strict=True)),
                    source_evidence_ids=relations,
                )
                # Keep original row addresses and cells for citation inspection.
                rows = sorted({c["metadata"]["row_index"] for c in included})
                item["source_rows"] = [deepcopy(parent["source_rows"][row]) for row in rows]
                item["metadata"]["source_row_indexes"] = rows
                results.append(item)
    if sorted(r for item in results for r in item["metadata"]["source_evidence_ids"]) != sorted(
        c["evidence_id"] for c in cells
    ):
        raise ParseError("Flattened tables do not reconcile to the same source cells")
    return results


def matched_representations(blocks, parents, cells):
    """A/B share table passages and B/C share narrative passages."""
    sectioned = section_narratives(blocks)
    tables = flattened_tables(parents, cells)
    return {
        "A": (fixed_narratives(blocks) + tables, []),
        "B": (sectioned + tables, []),
        "C": (sectioned + cells, parents),
    }
