# Parse the supported Apple filing

This implements Likhit's November 2 assignment from the revised plan, executed
November 3, 2026. It prepares source-linked records for the unified dependency
sequence: Ujjwal environment/contracts, Likhit cells/PDF/charts, Shanay validation,
then Likhit BGE/exact FAISS. It performs no index or provider calls. MiniLM/Chroma
is historical only. This direction was corrected November 5; extraction is unchanged.

## Run from a fresh checkout

Use Python 3.12. Windows PowerShell, from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-parser.txt
.\.venv\Scripts\python.exe scripts\parse_filing.py
```

On macOS/Linux, use `python3.12 -m venv .venv`, then `.venv/bin/python` for the
Python executable in the same commands. No notebook, model download, API key or
network request is needed after dependencies are installed. Default data paths
resolve from the script's repository root, even when launched from another folder.
Explicit `--manifest` and `--output` paths resolve from the shell directory.

The command restores the pinned source snapshot if needed, verifies its checksum
and filing identity, parses the selected evidence and updates the manifest to
`parsed_not_indexed`. It emits:

| File under data/processed/apple-2021 | Purpose |
| --- | --- |
| narrative.jsonl | 316 narrative records: Item 1A 128, Item 7 50, Item 8 138 |
| tables.jsonl | Three complete parent statement records, with raw cell structure |
| parsing_summary.json | Counts, section boundaries, table periods/units, exclusions and output hashes |

Repeat the command to reproduce the same records. The summary is written last;
its output hashes can detect incomplete/mixed outputs. Validation happens before
output writes. Do not read an output directory while rebuilding it. Generated
outputs and expanded raw HTML are ignored by Git; the small pinned source archive,
manifest, parser, tests and saved verification summary belong in the PR.

## What the parser does

1. Read `data/filing_manifest.json`: exact company, accession, report fiscal year,
   source URL, local source path, snapshot checksum and capture method.
2. Validate the checksum and inline XBRL company/CIK, document type, fiscal-year
   focus and period end. A wrong report or error page fails before output writes.
3. Follow the table-of-contents links to real body anchors. Bound Item 1A at
   Item 1B, Item 7 at Item 7A, and Item 8 at Item 9. Verify the body headings.
4. Collect visible leaf paragraphs outside all tables. Drop short standalone
   blocks/headings under 80 characters and page footers. Split long paragraphs
   into at most 1,000 characters, with up to 200 characters of overlap at word
   boundaries. Preserve final tails and source character offsets.
5. Select exactly the three named Item 8 statements. Keep source column headers,
   comparative periods and declared units, including exceptions. Separate
   presentation cells such as dollar signs stay with their period. Blank cells
   remain blank; parentheses are not converted or discarded.
6. Emit stable IDs using accession, section, record type, source-location hash
   and content hash. Store a CSS source locator and checksum on every record.

The supported tables are operations (2021/2020/2019), balance sheets (2021/2020)
and cash flows (2021/2020/2019). The report's `fiscal_year=2021` is distinct from
each table's `periods_json`; it must not overwrite comparative value periods.

## Record contract and indexing handoff

Both JSONL files contain records with `id`, `content`, `metadata`, following
`docs/plan/EVIDENCE_CONTRACT.md`. Metadata values are scalar; lists/objects such
as `periods_json`, `headers_json` and `units_json` are JSON-encoded strings for
Chroma compatibility. Tables also have a top-level `source_rows` array containing
source row locators, cell text, start-column offsets and colspans. Keep it as a
source artifact. `src.contracts.canonical_record` maps `id` to `evidence_id`
without changing identity and retains `source_rows`; preserve the full parent
separately from future vector metadata. Do not build a new Chroma baseline.

Example consumer (does not ingest by itself):

```python
records = [json.loads(line) for name in ("narrative.jsonl", "tables.jsonl")
           for line in (output_dir / name).read_text(encoding="utf-8").splitlines()]
ids = [r["id"] for r in records]
documents = [r["content"] for r in records]
metadatas = [r["metadata"] for r in records]
```

Tables use `financial_table`, which the existing retriever accepts. Their
`parent_table_id` points to themselves; normalized child row records and
typed `table_cell` records remain Likhit's November 4 prerequisite. The existing engine/UI
remain not ready until the scheduled index and retrieval integration is done.
Full parent tables can exceed an embedder/context limit: retain them as parent
evidence, and do not claim that embedding an automatically truncated table has
completed row-level table retrieval.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe app.py --check
```

`app.py --check` should still report `index_not_ready`; parsing does not create
a Chroma index or grant generation readiness. Parser tests cover the real source,
traceability, table periods and sample amounts, blank cells/signs, deterministic
reruns, clean archive restore, invalid source/sections/layouts and failure without
overwriting previous output. Fixture checks are parser regressions, not held-out
answer evaluation or evidence of improved retrieval accuracy.

## Limits to explain

This supports one checked layout. It excludes other tables, chart images and
short standalone blocks. It preserves raw values and unit declarations but does
not normalize numeric operands. It does not implement the later fair baseline,
index replacement/reopening, final citations, arithmetic or provider/UI integration.
Source acquisition and snapshot-byte provenance are explained in
`data/source/README.md`; the canonical SEC URL remains the original reference.
