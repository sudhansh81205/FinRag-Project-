# FinRAG gap repair review

November 5, 2026 | Supplement to the nightly reviews | Work through Ujjwal's environment assignment

## Decision and reviewed scope

Seven existing review findings have bounded repairs: F3, F4, F5, F7, F8, F9 and F10. The prior provider fixes F1, F2 and F6 remain protected by regressions. All 123 local tests pass, Ruff passes, declared dependencies are consistent, the existing parser reproduces 319 records, and real local DVC/MLflow checks pass. This is a safer prerequisite baseline. The full FinRAG answer pipeline is still not ready.

Reviewed application commit: [19457fe40ec95080da52c9b24f30304f744ba383](https://github.com/sudhansh81205/FinRag-Project-/commit/19457fe40ec95080da52c9b24f30304f744ba383), now published on main by an ordinary fast-forward. Starting main: [e26805e23a4801aa01e0f8b3f11b91a475dd6f72](https://github.com/sudhansh81205/FinRag-Project-/commit/e26805e23a4801aa01e0f8b3f11b91a475dd6f72). Current code was reviewed and tested; documentation/report additions after this commit do not imply new application features. Hosted verification for the code commit: [success](https://github.com/sudhansh81205/FinRag-Project-/actions/runs/42018291691). The report JSON preserves the observed run state; later status must be checked on GitHub.

This is an explicitly requested daytime repair on November 5, not the November 5 23:59 review. It does not advance the nightly cutoff, overwrite the November 4 report, or claim later work has happened. Generation timestamp UTC: 2026-11-05T11:23:49.599730+00:00. Current review model: gpt-6.1-sol, exposed by this session's runtime instructions. Earlier review model versions were not reliably exposed and remain unknown. This is separate from the application's configured Gemini model.

The user requested repair of prior gaps through Ujjwal's November 3 assignment, expressly excluding Likhit's pending tasks. Likhit's extraction implementation is unchanged. Only outdated forward directions in the parser CLI/manifest and handoff docs were corrected. No typed-cell/PDF/chart extractor, BGE/FAISS index, final model integration or evaluation was implemented here. The November 3 unified PRD and unchanged one-owner schedule remain authoritative.

## Previous work, fallback history and attribution

| Work/review date | Verified history and gap carried forward |
| --- | --- |
| October 30 | Integration/setup first tasks completed, including Shanay's authorized early October 31 task. Initial review found unsafe mock fallback, evidence loss, disabled-stream calls and arithmetic gaps. |
| October 31 | No new remote implementation evidence; existing findings remained open. Early setup was not assigned or counted twice. |
| November 1 | Rushil's provider task lacked submitted completion at the cutoff. No-change review retained defects rather than inventing work. |
| November 2 | Provider PR 3 was submitted and independently inspected, still separate from merged main at that cutoff. F1/F2/F6 fixed in the PR; complete-context defect F7 found. |
| November 3 | PR 3 merged just after midnight IST, PR 4 parser merged later that day, and unified planning revision published. Provider rewritten head had the same tree: no duplicate implementation credit. Ujjwal's task still had no submitted evidence at the original cutoff. |
| November 4 | No new submitted code at 23:59. Delayed review separately inspected PR 5, published/merged November 5 but claiming the November 3 assignment. It found F9/F10; missing November 4 extraction stayed missing. |
| November 5 repair | AI-assisted gap repair requested by Shanay; Git author is Shanay Ghodasara, associated GitHub login shanayghodasara-boop. This is not claimed human work/hours by Ujjwal or Likhit and is not Shanay's independent audit. |

At the pre-repair inventory, PRs 1-5 were merged and no open PR existed. The remaining parser/environment branches were ancestors of main, not independent unmerged implementation. The original local prototype c4b1a76 was also an ancestor of current main. Existing edits in the earlier shared-plan checkout were preserved and were not counted as delivered features. Coverage is the base repository and observed local checkouts; unpublished teammate forks/work cannot be inferred.

Fallback review: provider failure must remain service_error; mock is test-only. An empty or corrupt dataset cannot become a successful environment check. An oversized source cannot be partially sliced and still cited as complete. MiniLM/Chroma remains historical recovery code; it cannot substitute for BGE/exact FAISS in final A-G. No automatic provider/model substitution or fabricated evidence was added.

## Findings repaired and residual limits

### F3 P1 - evidence identity lost in the retrieval adapter

The old adapter returned content/metadata without the backend ID. [src/retrieval/retriever.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/retrieval/retriever.py#L37) now keeps the index-provided ID and fails a stream if its ID/document/metadata rows are missing or misaligned. A collection spy returns source-1 and the result retains it; malformed/missing ID lists return an error and no evidence. R2/R3/R10, common A-G provenance control. Confidence high. This repairs the existing adapter, not the still-missing FAISS row mapping or independent locator audit.

### F4 P2 - disabled retrieval stream still queried

Zero limits now skip the stream before calling the backend; numerical intent caps the text request at the caller's budget rather than forcing two records. Text-only/table-only/fully-disabled spies prove actual call counts. [src/retrieval/retriever.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/retrieval/retriever.py#L72). R10/R12, fair common retrieval controls. This does not implement BM25/RRF or final routing.

### F5 P2 - misleading negative-prior growth and suffix parsing

[src/llm/financial_reasoning.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/llm/financial_reasoning.py#L18) now reports ordinary growth only with a positive prior. For -50 versus -100 it reports absolute change 50, no percentage, and the matching subtraction formula. Prior zero is rejected; 120 versus 100 yields 20%. Explicit K/M/B suffixes scale into base units once; malformed grouping and non-finite strings are rejected. R5/common calculator safety. This legacy helper still lacks cited typed operands, period/scope comparability and a restricted multi-step operation tree; those remain Rushil's November 8 work.

### F7 P1 - claimed citations differed from actual prompt content

[src/pipeline/finrag_engine.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/pipeline/finrag_engine.py#L64) selects whole records within an 8,000-character intermediate evidence budget, rejects missing/conflicting IDs, deduplicates identities and records exclusions. [src/llm/prompts.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/llm/prompts.py#L8) no longer slices the joined table text. Included IDs are derived from the same records actually rendered, with an ID header per block. The regression proves a later unique marker is present when cited, an oversized record is excluded entirely, and zero usable records cause no provider call. R3/R10/R12; safety and faithful source attribution. The final model-token budget, five final passages, parent expansion and A-G fairness controls are still pending.

### F8 P2 - obsolete ownership and stack directions

The active parser CLI, manifest, parsing instructions, setup warning and handoff now point to the unified sequence: Ujjwal environment, Likhit cells/PDF/charts, Shanay validation, then Likhit BGE/exact FAISS. [scripts/parse_filing.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/scripts/parse_filing.py#L55) and [docs/PARSING.md](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/docs/PARSING.md). Historical completion reports are retained as historical evidence; their obsolete dates/stack are not new assignments. Parser extraction logic and existing record hashes are preserved. R1/R2/R13 supporting engineering, not a feature completion claim.

### F9 P1 - empty/duplicate/corrupt parser package passed validation

[src/contracts.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/contracts.py#L42) runs JSON Schema and verifies nonempty files, unique deterministic IDs, source/archive/content/output hashes, summary/manifest counts and self-parent identity. The lossless adapter maps id to evidence_id and retains source_rows. Actual existing 319-record package passes. Adversarial cases fail even when test fixture file hashes/counts are updated: empty input, duplicate IDs, wrong source/content hash, wrong accession/ID/parent, missing grid and malformed records. Missing files are blocked. R2/R3/R13 common identity and C/G contract prerequisites. Confidence high for this declared legacy profile. Future canonical cells/charts still require Shanay's cross-record semantic/source checks; a schema pass never certifies their truth.

### F10 P2 - missing tools prevented a saved diagnostic

[scripts/verify_day05_environment.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/scripts/verify_day05_environment.py#L23) guards command failures/timeouts; package checks use the current interpreter, and each check is isolated. [scripts/verify_day05_environment.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/scripts/verify_day05_environment.py#L189) writes the report before returning failure. Missing tools produce exit 1 and saved blocked statuses; MLflow skips invalid parser prerequisites. Raw exception text is not exposed. Persistent MLflow SQLite/artifact readback replaces the deleted temporary store. R13 common reproducibility control, supporting engineering. Actual MLflow run ID: 31615ebb6dfe40dca2c11d78cc6d448a. This is local smoke evidence, not a cloud tracking server or model evaluation.

## Verification evidence and boundaries

| Check | Observed result |
| --- | --- |
| Full final pytest on code SHA | 123 passed in 41.44 seconds; no paid generation or model downloads |
| Ruff and dependency consistency | Pass; pip check reports no broken requirements |
| Existing offline parser | 316 narratives plus 3 parent tables, 319 total; extraction source unchanged |
| Executable package contract | Passed for all 319 current records; full_canonical_package_ready remains false |
| Real DVC smoke | Local synthetic fixture restored with matching SHA-256; final-data restore not performed |
| Real MLflow smoke | Persistent local SQLite run reopened and saved JSON artifact byte-checked |
| Missing/corrupt-data checks | Rejected with reason and saved diagnostic; no false green status |
| Setup app | index_not_ready as expected; current repair checkout has no private Gemini key |
| Hosted CI | success; https://github.com/sudhansh81205/FinRag-Project-/actions/runs/42018291691 |
| Not run | BGE/FAISS, Docling/PDF/chart pipeline, live Gemini/Gemma, benchmark evaluation, independent fact audit |

The first expanded local run had two failures solely from old setup-message assertions after the warning was corrected. Those assertions were updated to the intended warning; the complete 118-test run passed at d4b0c1c. Final arithmetic review then found that finite operands could overflow to infinity. The follow-up code commit rejects non-finite intermediate/results and unrepresentably large integers, with five JSON-safe failure regressions. The final complete 123-test suite passed at 19457fe. DVC/MLflow/parser evidence is from unchanged environment code at d4b0c1c; it is not relabeled as a new run at 19457fe.

Immutable source hash: 8d9e6dbb6acd1f24dbc4345f74240b255ceaaf5beadb5874b143c7f67032e9d2. Narrative JSONL SHA-256: d0dfc2eb9760e9074e2860fcb8111ae38ca4a91350b25e8e3f95012f06cbbc98. Parent-table JSONL SHA-256: 85cb7569ef3d260f9771507a1deb2618c0fb7e3f588b10e3f2d1b144e232a834. Sorted newline ID-set hash: 515781949cf725684a60d1d79401a7d4b8b3b7dfcb599b771dc1ba13b723ee1e. This last hash is NOT the future ordered vector-row hash. Schema hash and exact local smoke evidence remain in the accompanying JSON/environment report.

Actual repair environment: Python 3.14.3; BeautifulSoup 4.15.0, lxml 6.1.3, jsonschema 4.26.0, DVC 3.67.1, MLflow 3.17.2, pytest 9.2.0, Ruff 0.17.3. CI declares Python 3.12; its result is separate evidence. FAISS, Docling, sentence-transformers and torch are absent in this isolated repair venv. Laptop memory is about 16 GB with Intel Arc integrated graphics; OS adapter memory is not validated model VRAM. Local Ollama is unavailable. Current prototype config remains Gemini gemini-3.5-flash-lite based on the earlier real check, not a new availability claim. No verified cloud notebook URL was identified; user requested reuse of the current route.

## Cumulative PRD acceptance

| Requirement | Current acceptance position |
| --- | --- |
| R1 Corpus | Partial: one pinned Apple 2021 layout; five Apple/five Microsoft filings and ten companies not proven |
| R2 Index | Contracts strengthened; final BGE/exact FAISS and rebuild/reload/replacement evidence absent |
| R3 Evidence | 316 narratives and 3 parents verified mechanically; typed cells/PDF/chart sources and independent audit pending |
| R4 Generation | Provider boundaries and earlier Gemini live evidence exist; final measured Gemma/Ollama pin absent |
| R5 Arithmetic | Legacy defect repaired; typed cited restricted multi-step reasoning not implemented |
| R6 Interface | Launchable setup, honest not-ready state; real end-to-end answer flow pending |
| R7 Evaluation | Full named benchmark/chart experiment, metrics and independent audits pending |
| R8 Report/course | Unified plan and handoffs exist; final evidence-based report/six slides/demo pending |
| R9 Restatements | Unscheduled Phase 2; unchanged |
| R10 Retrieval | Existing safety gaps repaired; BM25/RRF/cross-encoder/bounded routing pending |
| R11 Charts | Contract target only; real image sources/descriptions and independently checked 50 questions absent |
| R12 A-G controls | Scope retained; full matched implementation and results absent |
| R13 Reproducibility | Existing-package contract and durable local tool smoke pass; clean full-package/index/model/deployment validation pending |

No overall completion percentage is defensible from these mixed acceptance gates. Ujjwal's environment checkpoint now has executable evidence and explicit unavailable-resource/capacity status. This does not turn all of R13 or later tasks green.

## Prioritized remaining gaps and next-owner bridge

P1 dependency: missing Likhit November 4 cells/PDF/chart package blocks full Shanay validation and therefore the final index gate. Evidence: current [data/filing_manifest.json](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/data/filing_manifest.json) and unchanged [src/ingestion/filing_parser.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/ingestion/filing_parser.py#L281) limitation/accounting. Do not invent records to unblock a calendar.

P1 semantic validation: field/schema/hash checks do not prove values, period interpretation, scales, footnotes, parent coordinates or labels. Shanay independently checks actual sources and creates the real-data restore/rejection ledger. That closes the meaning gap left by F9, rather than repeating its mechanical checks.

P1 index/readiness: no BGE/FAISS adapter or actual ordered row/metadata proof. Likhit consumes the validated package and tests mismatches/reload/replacement. Reusing the repaired ID boundary prevents F3 from reappearing.

P1 final model/reasoning/evaluation: Gemma hardware/timings, typed arithmetic rules and complete A-G runs remain later scheduled work. F5/F7 repairs reduce present risk but do not satisfy those features. Do not call the 14 local cases final evaluation.

P2 context limitation: intermediate character selection preserves whole records but can omit an oversized relevant parent. Pavan later implements bounded parent expansion and a common tokenizer/five-passage budget, with excluded IDs and insufficient-evidence behavior retained. A real answer's citations and claims still need independent verification.

## Shanay - November 5, 8 estimated hours, sole owner

1. Fetch/read the repair SHA, current main and any new extraction PR at exact revisions. Do not treat this repair as independent validation of its own outputs.
2. Check whether the missing November 4 package exists. If absent, audit the available narrative/parent subset only and record the full dependency block.
3. Compare representative original-source facts, headers, comparative periods, scales/per-share exceptions, negative values and blank cells; verify parent coordinates/locators, IDs and hashes. Generated labels cannot self-certify truth.
4. Validate the actual canonical representation and ordered ID sidecars. Restore the REAL package into a clean destination and compare bytes, counts and IDs. The tiny DVC fixture is not that acceptance test.
5. Save reject cases, exact code/data/schema versions, installed environment and next-owner artifacts. Do not manufacture an index or schedule another person on the same date.

Use Python/JSON, the declared BeautifulSoup/lxml parser, jsonschema, DVC and MLflow. No new login is required for these local checks. Private model credentials are unnecessary for this audit. Verified commands from repo root, using the intended venv: `python scripts/parse_filing.py`; `python scripts/verify_day05_environment.py`; `python -m pytest -q`; `python -m ruff check .`; `python -m pip check`; `python app.py --check`. Parser regeneration writes its local generated outputs/manifest; retain the supplied package before independently comparing it. No new full-canonical-data audit CLI is claimed to exist.

## Likhit - November 6, 10 estimated hours, next sole owner

Use Shanay's actual accepted package and immutable manifests. The missing November 4 extraction remains an explicit prerequisite; this repair did not do it. If prerequisites fail, document the block and handle only a bounded repair within the scheduled owner slot or record a later recovery need. Do not assign same-day background work to someone else.

Pin BAAI/bge-base-en-v1.5 and preprocessing; normalize 768-D vectors; use exact FAISS IndexFlatIP consistently for all A-G variants. Bind row i to ordered evidence ID i and metadata row i; preserve full parents separately. Test duplicates, wrong dimensions/models/hashes, repeated ingest, reload, stale-record replacement and unrelated-filing preservation. Record actual corpus counts and failures. Libraries/model assets for this future work are not installed or downloaded by this repair; verify suitable versions on the intended machine before use.

## Copy-ready implementation prompt

Act as the implementation partner for the sole scheduled owner. Read AGENTS.md, docs/plan/PRD.md, TASK_REQUIREMENTS.md, COURSE_ALIGNMENT.md, EVIDENCE_CONTRACT.md, schedule.json, docs/review/MASTER_PROMPT.md and this November 5 repair review. Start from code 19457fe40ec95080da52c9b24f30304f744ba383 or explicitly reviewed newer main. Preserve F1-F10 repairs and the distinction between a mechanical environment smoke and independent data validation. For Shanay November 5, verify original-source semantics and a real clean data restore; missing Likhit cells/PDF/charts must stay blocked. Do not implement or claim Likhit's tasks in Shanay's audit. For Likhit November 6, proceed to BGE/exact FAISS only when the real prerequisite package and Shanay's acceptance exist. Preserve IDs/parents/units/periods and all A-G controls. Save exact revision, commands, success/failure evidence and a viva explanation. No fake completion, inferred human hours, automatic mock fallback or extra off-day worker.

## Copy-ready verification prompt

Review the next owner's exact revision and its genuine inputs. Reproduce valid acceptance and a relevant failure: empty/duplicate/corrupted source, wrong parent/period/unit, missing tool, wrong model/dimension or mismatched row mapping as applicable. Recompute hashes and compare the actual included context with reported IDs. For Shanay, independently verify source facts and the real restored package; for Likhit, verify actual rebuild/reload/replacement only after the input gate passes. Keep stub tests, real-source checks, live model outputs and benchmark results separate. Map each finding to an R requirement and A-G/common control and explain typed facts/predicates versus implemented transformer stages. Preserve all failures and denominators and write a later-owner handoff.

## Course trace and viva

KR&R representation: accession/type/source/content identity are facts; checks such as source-hash equality and ID uniqueness are integrity predicates. Valid 319 records satisfy this boundary; corrupted source hash fails. This supports grounded reasoning but does not implement the final comparable(issuer,metric,scope,period,currency,scale) financial inference layer. Viva: why is matching a hash not enough to compare two profits? A hash identifies bytes, not matching economic scope, units or periods.

DL: future BGE embeds text/query; a cross-encoder jointly scores a pair; Gemma generates from evidence. None of those final model executions was performed here. The legacy adapter fix preserves identities needed by those stages. Safety trace: a fitting source reaches the prompt with its ID; an oversized source is excluded and zero remaining evidence prevents generation. Chart schema alone is not chart vision. No A*, minimax, game theory or multi-agent reasoning is claimed.

## Scope and deadline retained

Final evaluation remains FinQA, TAT-QA, FinanceBench open sample and chart questions under cumulative A-G controls with common corpus/BGE/index/model/prompt/calculator/five passages/token budget. Track Recall@5/@10, MRR, answer/narrative measures, 1% numerical tolerance after unit normalization with a declared zero-gold rule, RAGAS, median latency and paired 95% confidence intervals. Independently checked 50 chart questions (15 dev/35 held-out grouped by image) are separate from a stratified independent 50-output faithfulness audit. Retain exclusions, failures and denominators. Capacity needs measured case/variant timings plus extraction/caption/evaluator overhead and machine availability.

November 17 remains the internal release-candidate target; November 18-20 sole-owner recovery/freeze; November 21 demo and individual viva; November 22 final submission. Exact course cutoff is not confirmed. Dependency delay remains the major risk. This repair does not reschedule members or change the automation.

## Delivery and durable context

The repair handoff is published in the repository. The user additionally requested an immediate run of the everyday review/delivery workflow: its final on-demand PDFs and sending evidence are retained privately, separate from the 23:59 nightly cutoff. The regular nightly state remains intact and no duplicate November 4 report is sent. Existing Git authentication successfully published an ordinary fast-forward.
