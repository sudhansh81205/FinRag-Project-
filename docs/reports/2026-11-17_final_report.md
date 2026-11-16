# FinRAG: Source-Grounded Financial Question Answering over SEC 10-K Filings

**CV ++ Team 6 | CS F407 Artificial Intelligence | Application Track**  
**Final Project Report | Submission Date: November 17, 2026**  
**Repository**: [github.com/sudhansh81205/FinRag-Project-](https://github.com/sudhansh81205/FinRag-Project-)  
**Sole Final-Day Release Owner**: Sudhansh Khandelwal  
**Release Status**: **Transparently Partial Reproducible Package** (Submitted under strict adherence to course honesty controls)

---

## 1. Introduction

Financial decision-making demands high-precision information extraction from corporate disclosures. SEC Form 10-K annual reports contain intricate narrative disclosures (Item 1A Risk Factors, Item 7 Management’s Discussion and Analysis), multi-year comparative financial statements and footnotes (Item 8), and graphical performance charts. Standard Retrieval-Augmented Generation (RAG) models often suffer from three critical failure modes when applied to financial reports:
1. **Context Fragmentation**: Inflexible chunking splits financial tables across chunk boundaries, separating numeric values from their corresponding row headers, comparative fiscal years, and currency units.
2. **Hallucinated Arithmetic**: General-purpose Large Language Models (LLMs) perform unconstrained text generation that hallucinates arithmetic calculations or incorporates uncited external constants.
3. **Context Disregard & Silent Errors**: Plausible numeric conclusions are generated even when key premises (issuer, fiscal period, consolidation scope) are absent or belong to a different company.

### Research Question
*With corpus, embedder, answer model, prompt, calculator, and five final passages fixed, how do section-aware chunks, self-describing cells, hybrid retrieval, hierarchical reranking, routing, and chart descriptions change recall, answer quality, faithfulness, and latency compared with standard dense RAG?*

In this project, we designed and built **FinRAG**, a source-grounded financial question answering application that integrates inspectable narrative, table, and chart evidence, executes justified and cited Decimal arithmetic, and enforces deterministic refusal when premises are missing.

---

## 2. Background and Related Work

- **Retrieval-Augmented Generation (RAG)**: Lewis et al. (2020) established dense bi-encoder retrieval coupled with sequence-to-sequence generation. While effective for open-domain QA, financial domains require strict structural preservation.
- **Financial QA Benchmarks**: FinQA (Chen et al., 2021) and TAT-QA (Zhu et al., 2021) highlight the necessity of hybrid reasoning over text and tables. FinanceBench (Islam et al., 2023) established an open-domain benchmark evaluating hallucination and source faithfulness on SEC filings.
- **Dense Representation & Cross-Encoding**: Pretrained dense bi-encoders such as BAAI/bge-base-en-v1.5 (Xiao et al., 2023) map queries and passages to 768-dimensional normalized vector spaces, while cross-encoders (`bge-reranker-base`) perform joint token-level attention over query-document pairs.
- **Lexical Fusion**: Okapi BM25 (Robertson & Zaragoza, 2009) captures exact financial identifiers and accession numbers that dense embeddings miss. Reciprocal Rank Fusion (RRF, Cormack et al., 2009) with \(k=60\) merges heterogeneous ranked lists without requiring score calibration.
- **Faithfulness & Alignment**: RAGAS (Es et al., 2023) measures generation faithfulness against retrieved context. In FinRAG, lexical overlap diagnostics serve as local checks, while uncalibrated automated metrics are never conflated with financial truth.

---

## 3. System Architecture and Method

FinRAG implements a modular pipeline with cumulative, controlled variants (**A through G**), strict Knowledge Representation predicates, and an authoritative Decimal calculator.

### 3.1 Cumulative Experimental Variants (A–G)
All variants share identical baseline controls: embedder `BAAI/bge-base-en-v1.5` (768-D L2-normalized), vector store (exact FAISS `IndexFlatIP`), generator (`gemma3:4b`), context limit (5 complete passages), and random seed 42.

| Variant | Name | Retrieval Strategy | Document Representation |
|---|---|---|---|
| **A** | Dense Baseline | Dense FlatIP search | Fixed overlapping narrative chunks + flattened Markdown tables |
| **B** | Section-Aware | Dense FlatIP search | Section-aware narrative chunks (Item 1A, Item 7) + flattened tables |
| **C** | Cell & Parent | Dense FlatIP search | Section-aware narratives + self-describing cells with parent table expansion |
| **D** | Hybrid Fusion | Dense + BM25 with RRF (\(k=60\)) | Self-describing cells + parents + section-aware narratives |
| **E** | Cross-Encoder | Variant D + hierarchical candidates | Re-scored using `bge-reranker-base` cross-encoder |
| **F** | Routed Escalation | Variant E + keyword/short-model routing | Escalation across text/table tiers with bounded attempts |
| **G** | Chart Grounding | Variant F + chart descriptions | Independently approved source-linked chart descriptions |

### 3.2 Knowledge Representation & Safe Inference (KR&R)
- **Typed Evidence Records**: Financial facts are stored as strongly typed records binding `issuer`, `accession`, `form`, `metric`, `period`, `raw_value`, `unit`, `scale`, `normalized_value`, and `source_locator` (file, page, coordinates).
- **Deterministic Request Binding**: Queries must specify the target company and requested value period. Evidence eligibility is evaluated strictly **pre-top-k** before retrieval.
- **Restricted Cited Calculator**: Arithmetic is executed by an authoritative Decimal tree (`src/llm/typed_calculator.py`). No arbitrary Python code execution or uncited constants are permitted. All operands must exist in the final `included_evidence_ids`.
- **Refusal Guarantees**: Any violation of issuer identity, period comparability, non-zero denominator, or context budget immediately aborts execution and returns an honest refusal (`insufficient_evidence` or `invalid_request`).

---

## 4. Results and Evaluation

### 4.1 Software Verification (459 Passing Tests)
The full software implementation was rigorously validated using automated unit and integration tests:
- **Test Suite Status**: 459 passed, 0 failed, 0 regressions.
- **Code Quality**: Ruff linter passes with zero warnings (`All checks passed!`).
- **Verified Boundaries**:
  - Request-bound retrieval: Apple FY2021 facts refuse to answer Microsoft FY2022 queries.
  - Calculation safety: Valid Apple FY2021 margin (`(365,817 - 212,981) / 365,817 * 100 = 41.78%`) computes correctly; missing operands or zero denominators cleanly refuse.
  - Unit normalization: `100M == 0.1B` passes with relative error \(\le 0.01\); incompatible scales fail.
  - Diagnostic setup: `python app.py --check` reports honest `index_not_ready` without unhandled crashes.

### 4.2 Truthful Experimental Status (Honest Reporting)
In accordance with course guidelines, planning prose and test counts are not substituted for experimental benchmark outputs:
- **A–G Benchmark Runs**: **Not Executed**. The test environment lacked a running Ollama daemon, Gemma 3 4B model weights, and GPU hardware. The benchmark runner matrix records 28 cells: 0 completed, 16 not started, 12 blocked (`docs/reports/2026-11-16_run_status.json`).
- **Benchmark Corpus Provenance**: The 150/50/50 test files in `data/benchmarks/` were audited and classified as `synthetic_smoke_fixture` by Pavan's November 16 audit. Authentic, source-bound benchmark datasets were not imported.
- **50-Output Independent Audit**: Because zero live LLM outputs were generated, the independent 50-output audit is recorded as a **shortfall of 50/50**. In accordance with academic integrity rules, outputs were not synthesized or fabricated.

---

## 5. Discussion and Limitations

1. **Request Binding vs. Arithmetic Correctness**: An answer can be mathematically correct yet financially invalid if attributed to the wrong entity or period. FinRAG enforces this constraint deterministically.
2. **Synthetic vs. Official Benchmarks**: Passing smoke tests does not imply accuracy on official SEC benchmarking suites. Full benchmark evaluation remains gated on importing authentic datasets.
3. **Hardware & Model Availability**: Running local 4B/12B generative models alongside cross-encoders requires measured GPU memory and execution time. Without local model infrastructure, execution feasibility cannot be claimed.
4. **Transparent Partial Release**: Rather than presenting simulated metrics as real findings, the package discloses all unverified gates and unmet prerequisites openly.

---

## 6. Individual Contributions

The project adhered to a strict single-owner-per-day calendar. The final November 17 release slot was assigned to Sudhansh Khandelwal at user request. Total planned effort: 140 hours across November 3–17.

| Member | Historical (Nov 3–11) | Planned (Nov 12–17) | Combined Hours | Key Responsibilities & Module Ownership |
|---|:---:|:---:|:---:|---|
| **Sudhansh Khandelwal** | 8h | 18h | **26h** | Integration controls, experiment scaffold (Nov 12); final release verification & submission (Nov 17) |
| **Agrawal Pavan Shailesh** | 10h | 10h | **20h** | Retrieval stages C–F (Nov 7); evidence audit, metrics, and report draft (Nov 16) |
| **Sri Sai Likhit Boddada** | 20h | 10h | **30h** | SEC filing parser (Nov 4); BGE/FAISS exact indexing (Nov 6); corpus expansion & A/B/C representations (Nov 13) |
| **Ujjwal Chandak** | 18h | 10h | **28h** | Environment contracts (Nov 5); independent chart reviews, gate freezing & run launch (Nov 15) |
| **Muppidi Gowtham Sai** | 8h | 10h | **18h** | UI setup and question interface (Nov 5); benchmark loaders and capacity measurement (Nov 14) |
| **B Rushil Mohan** | 10h | 0h | **10h** | Real model client and failure states (Nov 1); Decimal calculator and chart dataset (Nov 8) |
| **Shanay Ghodasara** | 8h | 0h | **8h** | Reproducible setup & entry point (Oct 31); canonical data acceptance audit (Nov 5) |
| **Total** | **82h** | **58h** | **140h** | |

---

## 7. AI Usage Disclosure

AI coding assistants (Claude Code, Antigravity) were utilized for code generation, unit test authoring, lint repairs, and report drafting. All generated artifacts were reviewed and verified through deterministic software checks. In strict accordance with course integrity rules:
- No human approval signatures, reviewer identities, or experimental metrics were fabricated.
- Where live models were unavailable, outputs are reported honestly as missing or blocked.

---

## 8. Connection to Course Concepts

1. **Knowledge Representation and Reasoning (KR&R)**:
   - Financial statements are represented as ontology-backed typed predicates.
   - Grounded arithmetic licenses conclusions only when premises (entity, period, unit) match the user request.
2. **Deep Learning for NLP**:
   - Bi-encoder dense representation (`bge-base-en-v1.5`) embeds semantics into inner-product vector space.
   - Cross-encoder pair scoring (`bge-reranker-base`) jointly models token interactions for fine-grained ranking.
3. **Computer Vision**:
   - Original stock performance charts (Item 5) are anchored by SHA-256 digests and spatial locators, requiring independent human review before integration into Variant G.
4. **AI Safety and Explainability**:
   - Explicit refusal on ungrounded or ambiguous premises prevents financial misinformation.
   - Complete evidence citation links every operand to an inspectable source ID.

---

## 9. Requirement Ledger (Release Status)

| Requirement | Area | Status | Evidence / Artifact |
|---|---|:---:|---|
| **R1** | Corpus Coverage | Partial | Apple 2021 accepted; 18 filings inventoried in `data/application_filings.json` |
| **R2** | Persistent Index | Partial | Exact FAISS `IndexFlatIP` implemented; verified by `scripts/verify_index.py` |
| **R3** | Evidence Extraction | Verified | HTML/PDF parser with coordinate and cell extraction in `src/ingestion/` |
| **R4** | Real Generation | Blocked | Gemma 3 4B pinned in configs; Ollama daemon unavailable on test machine |
| **R5** | Safe Calculation | Verified | Authoritative Decimal tree in `src/llm/typed_calculator.py`; verified by tests |
| **R6** | User Interface | Partial | Gradio application in `app.py` with request binding and diagnostic checks |
| **R7** | Evaluation & Audit | Partial / Shortfall | Scaffold & metrics implemented; live runs blocked; 50-output audit shortfall is 50/50 |
| **R8** | Delivery Package | Complete | Final report, 6 slides, backup demo walkthrough, release manifest, submission receipt |
| **R9** | Restatements | Out of Scope | Unscheduled Phase 2 per proposal agreement |
| **R10** | Advanced Retrieval | Verified | BM25, RRF (\(k=60\)), parent expansion, and routing in `src/retrieval/bm25.py` |
| **R11** | Grounded Charts | Partial | 50 candidate questions on 6 charts; independent approval ledger verified |
| **R12** | Experimental Controls | Verified | Pinned controls and immutable A–G scaffold in `src/pipeline/experiment_scaffold.py` |
| **R13** | Reproducibility | Complete | CI passing on GitHub Actions; release verified by `scripts/verify_release_package.py` |

---

## 10. Viva Defense Questions and Concrete Answers

1. **Why does pre-top-k eligibility matter in financial RAG?**  
   *Answer*: Post-retrieval filtering on a global top-k can drop all candidates for a specific company or comparative period if another entity has higher dense similarity scores. Pre-top-k filtering enforces the typed KR premise that only facts belonging to the requested issuer and period can participate in inference.

2. **Why must the calculator refuse when an operand is excluded by the context token budget?**  
   *Answer*: A grounded financial system cannot rely on uninspected facts or hallucinated constants. If an operand is dropped to fit the token budget, the conclusion is ungrounded and must be refused.

3. **What distinguishes a bi-encoder from a cross-encoder?**  
   *Answer*: A bi-encoder embeds queries and passages independently into a shared vector space for fast approximate search. A cross-encoder performs full cross-attention over concatenated query-passage tokens, capturing nuanced interactions at higher computational cost.

4. **Why is this release classified as transparently partial?**  
   *Answer*: While the software architecture, safety boundaries, and unit tests (459 passing) are complete, live model weights and GPU hardware were unavailable to execute the final A–G benchmark runs. Reporting unmeasured results would violate academic integrity; an honest partial release fulfills course requirements.
