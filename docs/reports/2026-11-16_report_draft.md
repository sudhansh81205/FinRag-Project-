# FinRAG: source-grounded financial question answering over SEC 10-K filings

**PARTIAL DRAFT, 2026-11-16 (Pavan, sole owner).** Every claim below is tied to a saved artifact. Where evidence does not exist the text says so; nothing here is a measured experimental result. Base revision `cec33f2` (main with merged PR14) plus the uncommitted November 16 changes listed in `docs/handoffs/2026-11-16_pavan.md`.

## 1. Introduction

FinRAG answers annual-report questions from inspectable narrative, table and chart evidence and executes only cited, restricted Decimal arithmetic. Its research question is: with corpus, embedder, answer model, prompt, calculator and five final passages fixed, how do section-aware chunks, self-describing cells, hybrid retrieval, hierarchical reranking, routing and chart descriptions change recall, answer quality, faithfulness and latency compared with standard dense RAG? The expected improvements are hypotheses; **none has been tested** because no benchmark outputs exist (Section 4).

## 2. Background and related work

Retrieval-augmented generation (Lewis et al., 2020); financial QA benchmarks FinanceBench (Islam et al., 2023), FinQA (Chen et al., 2021) and TAT-QA (Zhu et al., 2021); BGE embeddings and the bge-reranker-base cross-encoder (Xiao et al., 2023); BM25 (Robertson and Zaragoza, 2009) with reciprocal rank fusion (Cormack et al., 2009); RAGAS faithfulness (Es et al., 2023). *Bibliographic details were written from memory and must be re-verified against the originals before submission.*

## 3. Method

* **Variants A-G (cumulative):** A fixed overlapping chunks and flattened tables, dense only; B section-aware chunks; C self-describing cells and parent expansion; D dense/BM25 fusion with RRF k=60; E hierarchical candidates and cross-encoder; F bounded routing; G independently approved chart descriptions. Common controls: BAAI/bge-base-en-v1.5 (768-D, normalized) with exact FAISS, Gemma 3 4B via Ollama, one prompt, five passages, one token budget, fixed seed (`src/pipeline/experiment_scaffold.py`).
* **KR&R:** typed facts (issuer, accession, metric, scope, period, raw value, unit/scale, source) and deterministic predicates license a bounded cited expression tree (`src/llm/typed_calculator.py`). November 16 adds request binding: included records must match the requested issuer, exact filing, value period and scope before the calculator runs (`src/application.py`).
* **Deep learning:** pretrained BGE embeddings, a cross-encoder, Gemma generation and a vision-language chart pipeline. No training or fine-tuning is claimed.
* **Evaluation design:** 1 percent relative tolerance after unit normalization with a declared zero-gold tolerance, exact match / all-spans rubric / token F1 reported separately, Recall@5/@10, MRR, RAGAS, median latency, paired bootstrap (10,000 resamples, seed 42), a predeclared stratified 50-output independent audit separate from the 50 chart questions.

## 4. Results and evaluation

**Not available:** no A-G benchmark output was produced. PR14's run status records 28 matrix cells with 0 completed, 16 not started and 12 blocked. Therefore no accuracy, Recall@5/@10, MRR, RAGAS score, latency or confidence interval is reported, and the 50-output audit has a shortfall of 50 of 50.

**Established by software checks (not experimental results):** the full suite passes (459 tests, up from 378) and Ruff is clean. New regression tests demonstrate: wrong issuer/filing/period/scope, empty evidence, excluded operands and default facts refuse; 100 million = 0.1 billion passes while 100 billion fails; a multi-span gold needs every span; contradictory or unsupported-number sentences score 0 on the (renamed, non-RAGAS) lexical diagnostic; nested gold fields are refused; resume refuses changed code, revoked approvals, changed model-config content and edited controls; gates open only from bound artifacts plus an acceptance record.

**Benchmark data:** the 150/50/50 files are generated smoke fixtures (FinanceBench-labelled file: 150 records, one unique context; FinQA-labelled: 20 unique questions in 50; TAT-QA-labelled: one shared table). They are classified `synthetic_smoke_fixture`; full evaluation is BLOCKED until authentic, versioned, source-bound records are imported.

**PR14 audit (`docs/reports/2026-11-16_pavan_evidence_audit.json`):** 10 PASS (mechanically re-derived facts, e.g. 15/35 split with no shared image group, frozen file hashes), 10 FAIL (e.g. frozen manifest labels the FinanceBench fixture `is_subset=false`; run status marks A-D "unlocked" although no gate can open; routing thresholds unfrozen; capacity numbers copied rather than measured; promotion-report approval hash differs from the ledger on disk; label authors hard-coded), 3 UNVERIFIED (human chart review authenticity, IBM exhibit identity, `ai_assisted_accepted` corpus status), 2 BLOCKED (source re-hash, generated outputs).

**Capacity:** this machine (Windows, 16 logical cores, 15.29 GB RAM) has no running Ollama and no models, so cold/warm/retrieval/evaluator timings and full-run feasibility are unknown, not estimated.

## 5. Discussion and limitations

Correct arithmetic can still be an invalid answer: Apple FY2021 margin 41.78 percent is licensed only for a matching Apple FY2021 consolidated request. Tests demonstrate software boundaries, not experimental validity. Unmeasured and absent: authentic benchmarks, live retrieval/generation, RAGAS, cross-encoder execution, chart-caption approval, 18-source restore, benchmark-context-bound retrieval (the runner reports `context_binding: UNBOUND`), period binding in numerical scoring. The November 17 deadline is user-requested; the official cutoff and submission route are unconfirmed. Full repairs plus real generation, RAGAS and audits by then are not demonstrated feasible. If they cannot fit, the submission must be explicitly partial.

## 6. Individual contributions (estimates, not measured effort)

Scheduled sole owners: Sudhansh (Oct 30 task, Nov 12 scaffold), Shanay (Oct 31 setup, historical review), Rushil (Nov 1 provider, calculator, charts), Likhit (parsing, BGE/FAISS, corpus), Ujjwal (Nov 3 environment, Nov 15 inputs/freeze; PR14 submitted after the cutoff), Gowtham (Nov 14 UI/loaders/runner/capacity, PR13), Pavan (Nov 7 retrieval stages, Nov 16 audit/repairs/report). The final-day owner conflicts between the repository documents (Sudhansh) and the review PDFs (Shanay); the team must confirm. Commit authorship is not evidence of hours or understanding. Planned hours: Sudhansh 26, Shanay 8, Rushil 10, Likhit 30, Ujjwal 28, Pavan 20, Gowtham 18 (schedule.json estimates).

## 7. AI usage

AI coding assistants were used to write and review code, tests and these drafts, including the November 16 repairs (Claude Code). Chart candidate labels include AI-assisted authorship (`ai-assisted`). AI assistance does not replace the human review gates: no human approval, reviewer identity, output or metric was synthesized in this draft.

## 8. Connection to course concepts

* **KR&R (typed facts, predicates, inference):** cited operands are licensed only if issuer, filing, period, scope and unit agree with the request. Success: Apple FY2021 sales 365,817 and cost 212,981 (USD millions) give 41.78 percent. Failure: the same result refuses a Microsoft 2022 request.
* **Deep learning for NLP:** BGE bi-encoder ranking versus cross-encoder pair scoring versus generation; a missing or unrecorded cross-encoder stage means the E/F/G variant did not run (runner marks it failed).
* **Computer vision:** pretrained vision-language chart description with original-image grounding and unknown values; approval requires an independent human review, not a flag.
* **Ethics and safety:** AI-use disclosure, explicit refusals instead of default facts, uncertainty and no investment advice. BM25/RRF are information retrieval and routing is control logic; no A*, minimax, game-theory or multi-agent claim is made.

## 9. Requirement ledger (complete / partial / blocked)

| Requirement | Status at 2026-11-16 |
| --- | --- |
| R1 corpus | Partial: one accepted Apple filing; 17 further filings are candidates, sources not re-verifiable here |
| R2 index | Partial: BGE/exact FAISS baseline; no index in this checkout |
| R3 evidence | Partial: typed parser/cells/parents; request/filing binding repaired in code |
| R4 generation | Blocked: Ollama/Gemma not running here |
| R5 calculation | Partial: typed evaluator; helper validation now strict |
| R6 interface | Partial: exact filing tuples, request binding, demo-only; no live engine or two-browser test |
| R7 evaluation | Blocked: no authentic cases, no outputs, RAGAS not run, audit shortfall 50 |
| R8 delivery | Partial: this draft and six slides; no backup demo, no submission |
| R9 | Unscheduled Phase 2 |
| R10 retrieval | Partial: components exist; no live cross-encoder execution |
| R11 charts | Unverified: submitted human review claims; captions/G not executed |
| R12 controls | Partial: artifact-bound resume and gates repaired; thresholds unfrozen |
| R13 reproduction | Partial: CI green; capacity unknown; clean restore not performed |
