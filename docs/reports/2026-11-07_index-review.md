# Proposal review and November 6 index evidence

On-demand review and late November 6 implementation requested by Likhit, executed
November 7, 2026. This is not the nightly review and does not advance its cutoff.
Input main: `c887b52bce7f2521261e1aeebb8fd4f1121c89d4`; the branch/PR records the
submitted revision. Prior PRs through #6 are merged. Shanay's latest accepted
package is used without changing his audit implementation or canonical schemas.
The unified November 3 PRD controls this review; earlier technology screenshots
do not override its exact-FAISS, Docling and full-evaluation decisions.

## Findings and repairs

| Finding | Repair / observed evidence | Requirement and course connection |
| --- | --- | --- |
| No production BGE/exact FAISS implementation on inspected main | Added real pinned CPU encoder, immutable exact-index generations, query and verification commands. Actual 535-record build, restart and independent cosine comparison pass; malformed vectors/model mismatch fail. | R2, common embedding/index control for A-G; DL transformer embeddings. Why normalize both sides? |
| Default config still selected MiniLM/Chroma and four final passages | Default path/model now BGE/FAISS and five passages; setup remains explicitly unavailable for final answering. Legacy prototype artifacts remain separate. | R2/R10/R12 experimental consistency; configuration alone does not implement matched A-G. Why must A use the same embedder as C? |
| Engine discarded `table_cell` candidates | Accept whole canonical cell content and retain ID through prompt/citation boundaries; regression verifies this. Existing excluded/oversized-context and mock/provider failures still pass. | R3/R10, C onward; KR facts and truthful context. Which unit and period qualify the number? |
| No index replacement/corruption boundary | Exclusive writer lock and validated atomic catalog switch; duplicate/row/model/hash failures reject. Replacement removes only the target filing's stale active records. | R2/R13, common A-G provenance; supporting engineering and identity integrity. Why is the row map necessary? |
| Corpus inventory only had the initial ten filings | Added eight exact technology-company filings, acquisition/identity checks and pinned verified hashes. Wrong issuer/period, non-PDF and checksum mismatch fail. Explicitly report two failed renditions and only one accepted indexed filing. | R1, common corpus; source provenance. Why is acquisition not ingestion? |
| Legacy evaluation docstring still implied a 14-question final task | Corrected the description to the unified benchmark/chart A-G requirement; runner remains explicitly disabled. | R7/R12, honest experimental scope; no evaluation completion claim. |

## Verification evidence

The final full local run passed 171 tests in 163.16 seconds; one subsequently added
atomic-publication failure/retry regression also passed (172 verified cases total).
The final PR CI provides the full-suite result on the submitted revision. Ruff and dependency
consistency checks pass. FAISS emits three SWIG deprecation warnings; no test is
skipped to hide them. Native FAISS was executed outside the restricted Windows
sandbox. An initial sandbox temporary-directory failure was environmental; the
workspace-temp rerun passed.

`2026-11-07_index-verification.json` records the **real model**, package versions,
source-code fingerprints, manifest, actual results and rebuild/restart outcome.
`2026-11-07_corpus-coverage.json` records per-filing counts, hashes and failures.
No model weights, generated index, credentials or bulk downloaded PDFs are committed.
Reproduction commands download the pinned weights explicitly and regenerate the
index from the checked-in source fixture; extra PDFs use pinned external URLs.

Observed index: 535 candidates, three parents, 768 dimensions; generation
`304e6b85ad4804d0d240852e84e83ada33831b76c5cf20635561345074ec4a88`.
Two independent real embedding builds produced that same generation. The verifier
also republished identical vectors twice and into a separate store, then loaded
the saved index/model in a fresh process. Apple 2021 total net sales ranks first
in the filtered cell query at USD 365,817,000,000; an Item 1A narrative query returns
risk passages. NumPy dot products agree with FAISS scores. A valid MSFT filter
returns no evidence; 602-token input is rejected before transformer inference.
These are development smoke checks, not evidence-recall or answer-accuracy metrics.

Unit regressions cover exact ties, eligibility before top-k, restart, idempotence,
target-only replacement, duplicate IDs, invalid dimensions/shapes, nonfinite/zero
vectors, wrong model revision, every artifact's corruption, lock contention,
failed atomic publication with unchanged active data and a successful retry,
disabled streams, incomplete/stale source handoffs and acquisition failures.
The existing source predicate, provider-error, arithmetic and context-integrity
tests remain in the suite. The source/sidecar/DVC/MLflow acceptance was rerun and
passed before this build; model readiness is proved separately, not inferred from
that earlier gate.

## Proposal status after this change

| Requirement | Evidence / remaining gate |
| --- | --- |
| R1 corpus | Partial. 18 exact filings/10 companies inventoried; 16 verified local PDF renditions/9 companies; only Apple 2021 has accepted canonical/indexed records. New layouts, complete financial sections, charts and benchmark sources remain. |
| R2 index | Checked bounded implementation delivered. Real BGE/exact FAISS and integrity/restart/replacement pass. BM25 ID alignment awaits Pavan's implementation, full-corpus scale and clean-machine index restore remain later gates. |
| R3 evidence | Merged bounded HTML cells/parents, Docling PDF corroboration and independent fact audit retained. Not a general multi-company PDF/table parser. |
| R4 generation | Existing explicit Gemini/Ollama provider boundary and prior Gemini success evidence retained. Required real pinned Gemma 3 run and separate Llama comparison remain Rushil's gate. No model call was fabricated in this task. |
| R5 calculations | Existing restricted checked arithmetic retained; full typed multi-step operation trees, benchmark operations and rule traces remain pending. |
| R6 UI | Launchable setup UI explicitly reports not ready. Final dense/hybrid/chart/calculation answer wiring and measured deployment remain scheduled. |
| R7 evaluation | Full FinQA/TAT-QA/FinanceBench, chart split, metrics, bootstrap intervals and 50-output audit not implemented by this task. Old 14 cases are smoke-only. |
| R8 report/course deliverables | Plans and handoffs exist; final evidence-based results/report/six slides/viva remain scheduled. |
| R9 | Unscheduled Phase 2; unchanged. |
| R10 retrieval | New dense adapter and canonical-cell compatibility. Existing two-stream heuristic class is not BM25/RRF; cumulative fusion, parent expansion, real reranking and final tokenizer budget remain Pavan's gate. |
| R11 charts | One original source asset and locator, no accepted generated captions or 50 checked chart questions. Corpus chart availability remains unaudited. |
| R12 matched A-G | Common BGE/exact-index component available; A/B representations, full A-G isolation, routing and fixed generation/evaluation configuration still required. Current cell-index smoke is not A-G completion. |
| R13 reproducibility | Existing CI plus real source-package DVC/MLflow gate retained; new index manifests, checksums and rebuild/restart evidence added. Full release index archival/restore and complete experiment tracking remain scheduled. |

The project follows the PRD's dependency direction, but it is **not yet complete
against the proposal**. Full corpus ingestion is the largest unresolved input
gap. This PR enables Pavan's bounded integration without bypassing that release
gate. No teammate is given a second same-day assignment and no schedule is
silently marked complete. Use later scheduled independent reviews to verify new
source packages and final experiment controls.

Microsoft 2022's chosen annual-report PDF lacks the qualifying issuer/form/period
cover. Oracle 2024's extracted issuer text is damaged and fails the strict check.
Those failures remain visible; a different verified rendition or independently
checked extraction is needed. IBM's short 10-K incorporates statements by reference,
so a passing cover check does not establish complete financial coverage. Download
success never certifies values, periods, chart captions or benchmark eligibility.
