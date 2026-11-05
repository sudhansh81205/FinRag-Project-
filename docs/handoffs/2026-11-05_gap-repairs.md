# November 5 repair handoff: work through Ujjwal's environment task

Requested by Shanay and implemented with Codex assistance. This is an explicit
prerequisite repair, not claimed work or hours by Ujjwal or an off-day teammate.
The seven-member, one-owner-per-date schedule remains unchanged.

Starting merged revision: `e26805e23a4801aa01e0f8b3f11b91a475dd6f72` (PR 5).
The prior source reviews dated October 30 through November 4 identified F1-F10.
F1/F2/F6 were already repaired by provider PR 3; this repair addresses the
remaining existing-code findings F3/F4/F5/F7/F8/F9/F10. It does not implement
Likhit's pending cells/PDF/chart extraction or BGE/FAISS build.

## What changed

- Retriever retains index-provided IDs and rejects incomplete row mappings.
  Zero-budget streams make zero backend calls, including numerical queries.
- Engine selects whole evidence records inside a declared intermediate character
  budget, deduplicates identities, exposes exclusions and renders citation IDs
  alongside source content. Prompt formatting no longer silently cuts tables.
  The final common tokenizer/five-passage A-G budget is still Pavan's work.
- Existing arithmetic helper reports absolute change for negative-prior ordinary
  growth and no misleading percentage; suffix K/M/B amounts scale into base units.
  A typed, cited multi-step operation tree remains Rushil's future requirement.
- A lossless id/evidence_id adapter and executed schema/hash/count/identity checks
  reject empty, duplicate, corrupt or malformed existing parser packages.
  Future cell/chart schemas define interfaces; they do not create their data.
- Environment diagnostics use the actual Python interpreter, save blocked/failed
  outcomes, and retain DVC/MLflow artifacts. MLflow uses local persistent SQLite
  and verifies readback. DVC restores a synthetic fixture, not the final corpus.
- Corrected obsolete Ujjwal/MiniLM/Chroma handoff directions and added CI parser
  and environment smoke checks with artifact retention.

## Verification and course connection

See [environment instructions](../ENVIRONMENT.md) for executable commands.
The real existing parser reproduced 316 narratives and three parent tables;
source hash `8d9e6dbb6acd1f24dbc4345f74240b255ceaaf5beadb5874b143c7f67032e9d2`.
The extractor implementation itself is unchanged. Existing provider/mock/failure
regressions remain in the suite; there was no live paid generation call.

R2/R3/R13, common A-G identity controls and C/G contract prerequisites: valid
existing package passes; empty/duplicate/hash-corrupt input fails. This is typed
representation and integrity checking, not a completed financial inference layer.
R3/R10/R12 common context controls: a complete fitting record is cited; oversized
records are excluded with reasons and no partial-source citation.
R5 common arithmetic control: 120 versus 100 yields 20%; -50 versus -100 yields
absolute change 50 with percentage withheld. R4 safety: missing/failed/mock
providers still cannot yield successful financial answers.

## Next: Shanay on November 5 (8 estimated hours)

Use this repair revision and the unified PRD; do not repeat Ujjwal's tiny smoke
check as if it completed the independent data audit. Inspect any submitted
Likhit November 4 package at its exact revision. It was not present at the repair
inventory. Independently verify representative original-source values, periods,
units, parent/grid relationships and canonical IDs. Restore the real package in
a clean destination and compare hashes/counts/IDs. Keep rejection evidence.
If cells/PDF/chart inputs remain missing, record the validated available subset
and leave the full dependency blocked. Do not fabricate missing facts or assign
an off-day member work. R2/R3/R13 acceptance remains pending this audit.

## Then: Likhit on November 6 (10 estimated hours)

Consume Shanay's actual validated package and immutable manifest; a failed input
gate blocks real final indexing. The November 4 extraction work remains his
separate missing prerequisite, untouched by this repair. Use BGE
`BAAI/bge-base-en-v1.5`, normalized 768-D vectors and exact `IndexFlatIP` for all
A-G variants. Follow the ordered row/ID/sidecar contract and retain full parents.
Test rebuild/reload, duplicates, mismatches, replacement isolation and coverage.
No new MiniLM/Chroma final baseline; no assumption that schemas build an index.

## Still open

Final source/corpus coverage, typed cell/PDF/chart implementation, independent
validation/real-data restore, BGE/FAISS, BM25/RRF/cross-encoder/routing, real
Gemma/Ollama, typed cited arithmetic, connected answer UI and full evaluation.
Gemini remains the current prototype configuration; no verified cloud notebook
was identified and no credentials were copied. Full capacity is blocked pending
actual models/hardware/timings and case counts. Preserve all A-G metrics, named
benchmarks, 50 chart questions, separate independent 50-output audit, 1% tolerance,
latency and confidence intervals. R9 remains unscheduled Phase 2.

Viva: Why does a schema-and-hash pass not prove a financial answer? It establishes
data shape/identity, not semantic correctness, independent source interpretation,
comparability of operands, retrieval quality or model faithfulness.
