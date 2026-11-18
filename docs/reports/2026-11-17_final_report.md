# FinRAG: Source-Grounded Financial Question Answering over SEC 10-K Filings

**CV ++ Team 6 | CS F407 Artificial Intelligence | Application Track**  
**Final Project Report | Submission Date: November 17, 2026**  
**Repository**: [github.com/sudhansh81205/FinRag-Project-](https://github.com/sudhansh81205/FinRag-Project-)  
**Sole Final-Day Release Owner**: Sudhansh Khandelwal  
**Release Status**: **Transparently Partial Reproducible Package** (Prepared; actual course submission is unverified)

---

For subsequent results, see the [application delivery report](2026-11-18_final-completion.md), [benchmark results](../validation/official-source/README.md), and [submission attribution](../../ATTRIBUTION.md).

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
- **Deterministic Request Binding**: Queries must specify the target company and requested value period. Issuer/accession eligibility is applied before retrieval; numeric value-period premises are independently checked on used facts/programs before displaying success.
- **Restricted Cited Calculator**: Arithmetic is executed by an authoritative Decimal tree (`src/llm/typed_calculator.py`). No arbitrary Python code execution or uncited constants are permitted. All operands must exist in the final `included_evidence_ids`.
- **Refusal Guarantees**: Any violation of issuer identity, period comparability, non-zero denominator, or context budget immediately aborts execution and returns an honest refusal (`insufficient_evidence` or `invalid_request`).

---

## 4. Results and Evaluation

### 4.1 Software and real local runtime

The previous 459-test figure is historical. PR16 at87fd821 passed491 Python and10 Node checks. The combined local suite passed517 Python tests and13Node checks;17affected regressions passed after the final margin-change guard. Ruff passed. Software tests are separate from research accuracy.

A fresh pinned Gemma3:4b call succeeded through Ollama. Pinned BGE-base-en-v1.5 generated real768-D embeddings and exact FAISS persisted/reopened535Apple records. All18filings across10companies have parsed candidate packages and matched A/B/C indexes with reload/order checks. Automated source/package reproduction passed18/18. The canonical Apple audit passed source/cell/sidecar checks, DVC restore and MLflow readback. Wider independent acceptance remains pending.

The local browser returned Apple FY2021 gross margin **41.78%**, using GrossProfit152,836million divided by Revenue365,817million. Live testing first exposed a financially wrong formula that nonetheless passed arithmetic checks. Source-driven gross-margin construction and a separate semantic validator now reject it at planning, engine and application boundaries. Instant versus duration periods are explicit and eligibility narrows both streams before top-k. These known-formula checks do not establish correct interpretation of every arbitrary financial metric.

A real narrative response succeeded through the Python API. A separate browser narrative attempt exceeded the old180-second gateway deadline. The latest PR16 configurable240-second backend/250-second browser deadline is integrated; development traces are retained, including failures. These timings are individual observations, not a final latency distribution. The hosted deployment has not been connected to this local engine.

### 4.2 Authentic benchmark inputs restored

Pinned publisher bytes were imported without replacing the synthetic smoke fixtures: **FinanceBench150**, **FinQA1,147**, **TAT-QA1,663** cases. FinQA/TAT-QA inputs contain raw contexts, with gold programs/mappings and supplied retriever outputs excluded from inference inputs. TAT-QA does not provide verified issuer/accession identity, so none is invented.

All84required FinanceBench full PDFs were restored and checked against publisher Git blob hashes. Extraction produced12,013pages, including65unreadable pages explicitly recorded. All150questions bind to every readable page in their source document. Annotator-selected support pages remain gold-only; no annotated support page is missing/unreadable in this extraction. Source-equivalent final engine adapters and independent dataset acceptance remain pending.

### 4.3 Final evaluation and review remain incomplete

The frozen A–G matrix still records **0/28completed run cells**. The development model calls above are outside that matrix. Full named-suite metrics, Recall@5/10, MRR, actual RAGAS, paired95%intervals and the separate Llama comparison are unavailable. No final accuracy is claimed.

The user explicitly confirmed that **nobody has completed the independent review**. A packet covers50candidatechartquestions and6captions, with hashes and an unreviewed template. It does not grant label approval. The separate predeclared50-generated-output audit remains **0/50**, a shortfall of50. Historical ledger files are unverified submitted claims, not new evidence of human certification.

## 5. Discussion and limitations

1. Correct arithmetic does not establish the correct financial formula. Current semantic coverage explicitly supports gross margin, while other interpretations need validation.
2. Restored datasets and candidate indexes do not complete matched A–G execution. A/B source adapters and real E/F/G stage integration remain unfinished. Current CLI does not yet supply a source-equivalent benchmark engine.
3. The8GiB Apple M3 machine supports the bounded local demo but has slow generation and experienced native CPU thread crashes before the single-thread default repair. A representative development capacity pilot is required before a final freeze. No GPU requirement or full-run completion estimate is inferred from one query.
4. Full cloud backend connectivity, verified email sign-in/two-real-user isolation and an observed course submission receipt remain open. Vercel connector access returned403 awaiting an owner grant; deployment protection remains enabled.
5. Human independent acceptance cannot be replaced by automated flags or assistant-authored signatures. The package remains a **verified partial release**.

---

## 6. Individual Contributions

The schedule assigns one owner per day. Actual commit timestamps, attribution and verified effort must be reported separately; planned hours do not prove human effort. The final November 17 release slot was assigned to Sudhansh Khandelwal at user request. Total planned effort: 140 hours across November 3–17.

| Member | Historical (Nov 3–11) | Planned (Nov 12–17) | Combined Hours | Key Responsibilities & Module Ownership |
|---|:---:|:---:|:---:|---|
| **Sudhansh Khandelwal** | 8h | 18h | **26h** | Integration controls, experiment scaffold (Nov 12); final release verification & submission (Nov 17) |
| **Agrawal Pavan Shailesh** | 10h | 10h | **20h** | Retrieval stages C–F (Nov 7); evidence audit, metrics, and report draft (Nov 16) |
| **Sri Sai Likhit Boddada** | 20h | 10h | **30h** | SEC filing parser (Nov 4); BGE/FAISS exact indexing (Nov 6); corpus expansion & A/B/C representations (Nov 13) |
| **Ujjwal Chandak** | 18h | 10h | **28h** | Environment contracts (Nov 5); independent chart reviews, gate freezing & run launch (Nov 15) |
| **Muppidi Gowtham Sai** | 8h | 10h | **18h** | UI setup and question interface (Nov 5); benchmark loaders and capacity measurement (Nov 14) |
| **B Rushil Mohan** | 10h | 0h | **10h** | Real model client and failure states (Nov 1); Decimal calculator and chart dataset (Nov 8); later HTML/CSS/JavaScript contributions to the research workspace, filing controls, evidence display and Saved Questions |
| **Shanay Ghodasara** | 8h | 0h | **8h** | Reproducible setup and early Gradio frontend with question, readiness and evidence controls (Oct 31); UI smoke checks and canonical data acceptance audit (Nov 5) |
| **Total** | **82h** | **58h** | **140h** | |

---

## 7. AI Usage Disclosure

AI coding assistants (Claude Code, Antigravity and Codex) were utilized for code generation, unit test authoring, lint repairs, and report drafting. Automated code and artifact checks are recorded separately from human review and individual understanding. No claim of independent human review is made. In strict accordance with course integrity rules:
- No human approval signatures, reviewer identities, or experimental metrics were fabricated.
- Development model calls are saved separately from unexecuted final experiments; missing results remain missing.

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
| **R1** | Corpus Coverage | Partial | Apple2021 bounded acceptance;18parsed/indexed candidatefilings, wider independent acceptance pending |
| **R2** | Persistent Index | Partial | Exact FAISS `IndexFlatIP` implemented; verified by `scripts/verify_index.py` |
| **R3** | Evidence Extraction | Partial | HTML/PDF parser with coordinate and cell extraction in `src/ingestion/` |
| **R4** | Real Generation | Local verified / final partial | Actual pinned Ollama Gemma3:4b generation and source-bound development answers |
| **R5** | Safe Calculation | Verified | Authoritative Decimal tree in `src/llm/typed_calculator.py`; verified by tests |
| **R6** | User Interface | Partial | Gradio plus local web/API workspace; live numeric result verified; cloud/auth incomplete |
| **R7** | Evaluation & Audit | Partial / Shortfall | Scaffold & metrics implemented; live runs blocked; 50-output audit shortfall is 50/50 |
| **R8** | Delivery Package | Partial / Prepared | Updated report, exactly6slides, backup walkthrough and release hashes; actual submission receipt absent |
| **R9** | Restatements | Out of Scope | Unscheduled Phase 2 per proposal agreement |
| **R10** | Advanced Retrieval | Partial | BM25, RRF (\(k=60\)), parent expansion, and routing in `src/retrieval/bm25.py` |
| **R11** | Grounded Charts | Partial | 50 candidate questions on 6 charts; candidate approval ledger exists; independent acceptance not certified here |
| **R12** | Experimental Controls | Partial / Blocked | Pinned controls and immutable A–G scaffold in `src/pipeline/experiment_scaffold.py` |
| **R13** | Reproducibility | Partial | CI passing on GitHub Actions; release verified by `scripts/verify_release_package.py` |

---

## 10. Viva Defense Questions and Concrete Answers

1. **Why does pre-top-k eligibility matter in financial RAG?**  
   *Answer*: Post-retrieval filtering on a global top-k can drop all candidates for a specific company or comparative period if another entity has higher dense similarity scores. Pre-top-k filtering enforces the typed KR premise that only facts belonging to the requested issuer and period can participate in inference.

2. **Why must the calculator refuse when an operand is excluded by the context token budget?**  
   *Answer*: A grounded financial system cannot rely on uninspected facts or hallucinated constants. If an operand is dropped to fit the token budget, the conclusion is ungrounded and must be refused.

3. **What distinguishes a bi-encoder from a cross-encoder?**  
   *Answer*: A bi-encoder embeds queries and passages independently into a shared vector space for fast vector search; this project uses exact FAISS search. A cross-encoder performs full cross-attention over concatenated query-passage tokens, capturing nuanced interactions at higher computational cost.

4. **Why is this release classified as transparently partial?**  
   *Answer*: Real local generation, exact indexes and official dataset imports are verified. Source-equivalent final adapters, E/F/G integration, independent acceptance and the full A–G runs remain incomplete. Reporting unmeasured results would violate academic integrity; a partial package must still identify unmet course requirements; it is not evidence of full acceptance.


## November17 implementation evidence
See `START_HERE.txt` and `docs/reports/2026-11-17_runtime-verification.json` for current checks, exact hashes and reproducible commands. The refreshed six-slide binary has been rendered and visually inspected as recorded there. The backup walkthrough remains a written procedure, not a recorded video. The acknowledgement remains PREPARED_NOT_SUBMITTED. Historical files remain in Git history.


## Primary bibliography checked17November2026

[RAG, Lewis et al.](https://arxiv.org/abs/2005.11401), [FinanceBench, Islam et al.](https://arxiv.org/abs/2311.11944), [FinQA, Chen et al.](https://aclanthology.org/2021.emnlp-main.300/), [TAT-QA, Zhu et al.](https://aclanthology.org/2021.acl-long.254/), [C-Pack/BGE, Xiao et al.](https://arxiv.org/abs/2309.07597), [RAGAS, Es et al.](https://arxiv.org/abs/2309.15217). The paper citations describe prior work, not completed local RAGAS or cross-encoder evaluation.
