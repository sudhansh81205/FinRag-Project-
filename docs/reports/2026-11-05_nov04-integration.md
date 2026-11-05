# November 4 extraction integration, checked November 5

Reviewed main e273b22 and merged it into likhit/nov04-evidence without textual
conflicts. This includes Ujjwal PR #5 (merge e26805e), the canonical schema
repairs and later retrieval/context/arithmetic repairs (d4b0c1c and 19457fe).
Those repairs remain intact. The PR is limited to Likhit's R1/R3/R11 extraction
handoff and its verification, with a CI command for the new offline package.

The provisional local cell schema was incompatible with the merged contract.
It now emits evidence_id, type table_cell, schema version 1 and all mandatory
metadata. All 538 records pass that schema. Normalized JSON numbers retain a
separate exact decimal representation. Narratives and full parent grids use the
merged lossless identity adapter. Chart sources are separate from future model
caption records. See the [handoff](../handoffs/2026-11-04_likhit.md).

## Executed checks

- Full suite passed, 131 tests in 85.28 seconds on Python 3.12.
- Ruff and pip dependency consistency passed. Git whitespace/unmerged-file checks passed.
- Two fresh prepare_evidence.py runs produced identical bytes for all four outputs.
- Preserved 316 narratives and three full grids, added 219 typed cells, corroborated
  11 values on PDF pages 32/34/36 and extracted the original chart on page 22.
- All 219 cell source selectors resolve to the declared row/table and XBRL fact.
- Negative tests reject changed PDF/HTML values, ambiguous chart locators, invalid
  numeric text, schema mismatches, absent periods, corrupt content and duplicate IDs.
- Existing parse_filing.py still reproduces 319 records. The merged parser-contract,
  synthetic DVC restore and persistent MLflow readback checks all passed.
- app.py --check reports index_not_ready, as expected for the current app.

The first pytest attempt was blocked by the sandbox temporary directory. The
successful run used a fresh workspace temporary path. DVC/MLflow initially failed
inside the sandbox and passed with normal local cache/temp access. No source or
application fix was needed for those environment restrictions. No live generation,
model download, benchmark evaluation or index build was performed.

Runnable commands after installing requirements-dev.txt

```powershell
python -m pytest -q
python -m ruff check .
python -m pip check
python scripts/parse_filing.py
python scripts/prepare_evidence.py
python scripts/prepare_evidence.py --output output/nov04-rebuild-check
python scripts/verify_day05_environment.py
python app.py --check
```

The [machine-readable record](2026-11-05_nov04-integration.json) contains exact
code file fingerprints, source/output/schema hashes and smoke statuses. Output
hashes refer to this local checkout, including its schema file bytes. CI results
must be read from the PR; this report records local checks only.

## Acceptance and remaining boundaries

This completes the bounded November 4 source extraction handoff for checked Apple
fixtures. Ten filing identities are inventoried but only Apple 2021 is processed.
The Docling backend checks selected programmatic PDF rows, not arbitrary PDF
layout/OCR. Full corpus coverage, generated chart descriptions, independent data
validation and real-data DVC restore remain later work. The Nov 3 environment
report's missing-deliverable list describes its older parent-only validation
profile; it does not inspect this new package.

Shanay must independently validate source semantics and restore this real package
before the November 6 BGE/FAISS work consumes it. R3/C is typed representation
and source traceability; R11/G is original image provenance. Neither constitutes
implemented financial inference or a vision caption model. Viva example: trace
repurchases (85,971) million to -85,971,000,000 USD, its duration and parent grid,
then explain why the PDF corroboration is not another searchable fact.

AI assistance was used for implementation and verification. Human contribution
time was not inferred from test duration or commits.
