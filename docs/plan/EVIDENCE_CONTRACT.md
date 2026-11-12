# FinRAG evidence and answer contract

Document revision November 12, 2026. This defines final acceptance interfaces alongside the current PRD; it does not assert every field/path is already implemented. The canonical record JSON Schema remains the executable shape authority at its recorded version. Historical example records are synthetic design examples, not indexed facts or gold labels.

## Identity and source records

A canonical record has evidence_id, content and metadata. Physical adapters may expose id, but it maps losslessly to the same logical evidence_id; do not generate a second identity. Stable IDs distinguish accession, section, source locator, record type and content identity. Identical inputs reproduce IDs; a numeric position alone is insufficient.

Required metadata binds accession, issuer/ticker, filing and value periods where applicable, section/type, source URL/locator/file, source and content hashes, record schema and parser version. Preserve source snapshots and licence/rendition provenance. A browser snapshot checksum is not an issuer-published checksum. A PDF mirror is explicitly a rendition and must resolve to the exact issuer/form/period identity.

Keep raw, parsed, independently accepted and indexed coverage separate. Inventory and download counts, isolated chart images and schema passes cannot establish full corpus acceptance. Additional source layouts require supported fixtures, failure checks and original-source interpretation; missing assets or layouts remain visible.

## Typed cells parents and PDF positions

A cell binds original parent grid, table title, row/column headers and coordinates, raw display amount, metric/statement/scope, exact value-period kind/start/end, raw and normalized currency/unit/scale/value, footnotes and source identity. Keep original grids and source rows independent of embedding limits. Blank/missing is not zero. Parentheses, shares/per-share units, comparative years and dimensions must remain explicit.

Reject unresolved or ambiguous period/unit/parent identity; a shape-valid changed fact must fail its source-derived predicates. Do not derive a legal operand from an untyped PDF number by guessing its year or unit. Renditions corroborate existing facts rather than duplicating them.

A claimed PDF position needs the exact original PDF/page/hash, declared coordinate origin, valid finite nondegenerate in-page bounds and independently resolvable word/row/year binding. Text somewhere on a page or a rectangle inside its bounds is insufficient. Unsupported exact-position guarantees must be withheld honestly.

Generations are immutable: identical re-ingestion is idempotent; changed/foreign destinations are rejected or use a new generation. A replacement affects only its declared filing and never erases unrelated packages.

## Index and retrieval

Index manifests bind code/schema/data/source hashes, pinned BGE revision and preprocessing/query instruction, 768 normalized dimensions, exact FAISS IndexFlatIP and ordered row-to-ID/metadata sidecars. BM25 shares canonical IDs and explicit eligibility. Reject duplicate IDs, row swaps, dimension/model/preprocessing mismatch, corrupt sidecars and incompatible reloads.

Every request applies the same explicit issuer/company/value-period/source policy before dense and lexical top-k. Reject unsupported filters and state leakage. The E-only hierarchy is distinct from common explicit eligibility. Preserve dense/BM25 ranks, RRF60 score, candidate restriction, reranker score type/model and validation, route/escalation attempts/threshold/stop reason, candidates, selections/exclusions, parent expansion and budget. Disabled streams issue no query.

Missing, raising, wrong-length or nonfinite cross-encoder output cannot silently yield successful E/F/G status. An explicitly labelled diagnostic/degraded path must not be miscounted as the requested final variant.

## Context and answer states

The actual prompt uses complete selected evidence objects under one pinned tokenizer/input budget and fixed five-final-passage control, reserving instructions/output capacity. Use fewer valid passages with recorded shortfall; do not pad unsupported records. Parent/chart expansion shares the same budget. Actual included IDs, rendered citations, prompt objects and permitted operands must agree exactly. Retrieved-but-excluded IDs remain separate; no truncation after claiming inclusion.

Answers retain status, question, answer, message, evidence, calculations, provider/model/configuration and timings, with actual included IDs and source citations. Financial success requires real accepted provider output and valid evidence; exact numerical rendering remains authoritative over raw model explanation.

| Status | Meaning | Output rule |
| --- | --- | --- |
| ok | Real accepted execution from included support | Preserve actual citations, result/rules and model provenance. |
| invalid_request | Empty/malformed/unsupported request | Explain correction; no financial answer. |
| index_not_ready | Required index/application integration unavailable | Name missing prerequisite; no invented evidence. |
| insufficient_evidence | Valid execution found inadequate support or failed a financial premise | Abstain and preserve reasons. |
| service_error | Retrieval/model/runtime stage failed | No successful-looking fallback or stale financial answer. |

Internal typed errors may be more detailed, but public mapping must preserve failure meaning. Historical not_ready/invalid_input aliases are not the current public contract. Explicit mock mode remains test-only and cannot become a financial ok response.

## Restricted calculation

Only approved bounded arithmetic operations may execute. Leaves resolve to actual included canonical cells; no uncited numeric constants, arbitrary Python, imports, file/network calls or unbounded expressions. Bind caller-supplied issuer/scope/requested periods, validate source/content and raw/normalized value consistency, comparability, supported dimensions and nonzero denominators.

Retain operation tree, expression, raw/normalized operands, evidence IDs, exact result/unit, rule premises/outcomes and policy notes. Ordinary growth with positive prior permits percentage change; zero prior refuses; negative prior yields absolute change plus explanation unless a documented benchmark policy specifies otherwise. A model may propose an untrusted bounded tree and explain a validated conclusion; it cannot override failed rules or authoritative request constraints.

## Charts and independent promotion

A chart record binds original image bytes/path/hash, exact filing/page or HTML locator, source hash, generated description, model/digest/quantization/configuration/prompt/schema fingerprint and unknown-value markers. Retain raw model captions and author corrections separately; generated captions must not be presented as issuer-authored text.

Candidate questions/captions stay pending until independent decisions bind exact image, label and caption identities and an eligible reviewer different from their author. Preserve authorship/reviewer evidence, accept/reject reasons and immutable split mapping. Do not approve by flipping frozen flags or changing expected hashes to hide edits. Alternate crops/renditions of one image stay in one split; retain fifteen development/thirty-five held-out questions. Unprinted or ambiguous values remain unknown.

A validated approved-loader/promotion path must reject tampering, missing approvals, self-review and mismatched splits. Exact implementation/reproduction commands belong in the verified handoff. Fifty candidates are not fifty approvals or fifty independent images.

## Experiment and audit records

Bind code/data/source/index/model/configuration hashes, canonical A-G, query/document preprocessing, prompt, calculator, tokenizer/budget/five-passage controls, route thresholds, random settings, eligible case/split IDs, outputs/statuses, raw metric inputs, hardware, timestamp and observed duration. Retain checkpoints, failures/timeouts/exclusions and denominators; missing timing is unknown, not zero.

A-G uses one pinned Gemma configuration; separate Llama outputs remain separately labelled. Freeze complete FinQA/TAT-QA/FinanceBench and chart universes without label leakage. Fourteen local cases and injected tests remain smoke only.

Score unit-normalized numerical answers at 1 percent relative tolerance for nonzero gold; declare zero-gold absolute tolerance from display precision. Preserve narrative measures, Recall@5/@10, MRR,RAGAS,latency and paired 95 percent confidence intervals. The independently reviewed fifty generated outputs are distinct from fifty chart questions; retain author/reviewer conflicts and exact included context/original source evidence.

Likhit on November 13 supplies supported corpus and representations; Gowtham on November 14 supplies the UI/loaders/runner and measured real capacity. Ujjwal on November 15 independently checks inputs, freezes accepted controls and launches full jobs. Pavan on November 16 computes/reconciles metrics and audits non-self-authored outputs; Sudhansh on November 17 completes remaining independent exclusions and release. No same-day extra reviewer is assigned. Missing mandatory evidence prevents complete acceptance even when software tests pass.
