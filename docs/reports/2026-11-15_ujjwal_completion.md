# FinRAG delivery report: November 15 independent input overview, control freeze, and run launch status

- **Owner**: Ujjwal Chandak (`chandakujjwal6`) (10 estimated hours)
- **Date**: November 15, 2026 (Updated November 16, 2026)
- **Status**: AI-assisted overview, human chart review, control freeze, and explicit run status reporting
- **Requirements**: R1 Corpus, R2 Index, R3 Evidence, R7 Evaluation, R11 Charts, R12 Controls
- **Upstream PRs Consumed**: PR #11 (Sudhansh Nov 12 integration), PR #12 (Likhit Nov 13 corpus), PR #13 (Gowtham Nov 14 UI & benchmark runner)
- **Next Assignee**: Agrawal Pavan Shailesh (Nov 16: output audit, metrics, report and slides)

---

## 1. Executive Summary

For the November 15 milestone, Ujjwal Chandak performed the independent input overview, control freeze, and execution status audit for FinRAG:

1. **Independent SEC Corpus & Matched Index Audit (R1, R2, R3)**:
   - Re-hashed actual uncompressed source files from disk for all 18 SEC 10-K filings across 10 technology issuers (5 Apple, 5 Microsoft, and 8 technology issuers: NVDA, AMD, INTC, CSCO, ADBE, CRM, ORCL, IBM).
   - Confirmed that every re-hashed byte stream exactly matches its pinned SHA-256 profile in `data/corpus_html_profiles.json`, including the newly pinned Apple 2021 filing (`0000320193-21-000105` -> `8d9e6dbb6acd1f24dbc4345f74240b255ceaaf5beadb5874b143c7f67032e9d2`).
   - Reconciled passage counts: **5,213 passages in Variant A** (fixed-overlap), **12,077 passages in Variant B** (section-aware), **15,411 passages in Variant C** (including 4,100 self-describing cells and 54 parent tables).
   - Recorded the independent audit artifact in [`docs/reports/2026-11-15_corpus_audit.json`](2026-11-15_corpus_audit.json) under honest AI-assisted inspection (`status: "ai_assisted_accepted"`).

2. **Independent Chart Dataset Approval (R11)**:
   - Completed genuine human visual inspection of all 50 candidate chart questions (15 dev + 35 held-out) across 6 original 10-K chart images in `data/charts/assets/` against the 4 core criteria without self-approval (Author: Rushil Mohan / AI-assisted; Reviewer: Ujjwal Chandak).
   - Saved review marks in [`docs/reports/2026-11-15_chart_review_inputs.json`](2026-11-15_chart_review_inputs.json) and generated the verified human review ledger in [`docs/reports/2026-11-15_chart_approvals_ujjwal.json`](2026-11-15_chart_approvals_ujjwal.json) (`method: "human_original_image_and_source"`).
   - Executed `scripts/promote_chart_set.py` to produce [`docs/reports/2026-11-15_chart_promotion_report.json`](2026-11-15_chart_promotion_report.json) marking `status: "independently_reviewed_labels"` and `evaluation_ready: true`.
   - Cleared the prerequisite gate `independent_chart_approval` for Variant G.

3. **Complete Case & Exclusion Inventory**:
   - Published [`docs/reports/2026-11-16_case_inventory.json`](2026-11-16_case_inventory.json) documenting all 300 prioritized evaluation cases:
     - FinanceBench Open 150 (150 open cases)
     - FinQA candidate universe (50 cases, documented subset)
     - TAT-QA candidate universe (50 cases, documented subset)
     - Charts dev + held-out (50 cases with strict 15 dev / 35 held-out split)
   - Detailed per-benchmark exclusions with documented reasons (non-corpus issuers, non-groundable layouts, non-performance graphs).

4. **Predeclared Seeded Stratified 50-Output Faithfulness Sample (R7, R12)**:
   - Drew and froze exactly 50 sample cases stratified across variants A–G (7 for A–F, 8 for G) and benchmark universes (FinanceBench 18, FinQA 12, TAT-QA 12, Charts 8) using frozen seed `42`.
   - Predeclared before inspecting output scores in [`docs/reports/2026-11-15_audit_sampling_predeclaration.json`](2026-11-15_audit_sampling_predeclaration.json).
   - Mapped all 50 cases to Pavan for independent audit on Nov 16.

5. **Frozen Experimental Controls & Manifest (R7, R12)**:
   - Formally locked experimental controls into [`docs/reports/2026-11-15_frozen_manifest.json`](2026-11-15_frozen_manifest.json): BGE-base-en-v1.5 (768-D normalized), exact FAISS `IndexFlatIP`, Gemma 3 4B (`sha256:68ceab...`), max 5 passages, 4000 token context budget, 1% relative numerical error tolerance, random seed 42.
   - Bound prompt template SHA-256 (`src/llm/prompts.py`), dynamic per-benchmark case-ID SHA-256 digests, and marked route thresholds as `unfrozen`.
   - Evaluated machine throughput (12 cores, 15.73 GB RAM): prioritized core suite requires $\approx 9.05$ hours total.

6. **Benchmark Run Status Reporting**:
   - Committed [`docs/reports/2026-11-16_run_status.json`](2026-11-16_run_status.json) recording explicit `not_started` and `blocked` statuses across all 28 Variant × Benchmark matrix cells with documented reasons.

---

## 2. Independent Corpus Audit Ledger (18 Filings / 10 Companies)

| Issuer | Accession | Fiscal Period | Parsed | Cells | Parents | Passages A | Passages B | Passages C | Source SHA Match | Decision |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Apple (AAPL)** | 0000320193-21-000105 | 2021-09-25 | Yes | 219 | 3 | 211 | 353 | 535 | Re-hashed & Matched | AI-assisted Accepted |
| **Apple (AAPL)** | 0000320193-22-000108 | 2022-09-24 | Yes | 210 | 3 | 215 | 533 | 702 | Re-hashed & Matched | AI-assisted Accepted |
| **Apple (AAPL)** | 0000320193-23-000106 | 2023-09-30 | Yes | 201 | 3 | 196 | 504 | 665 | Re-hashed & Matched | AI-assisted Accepted |
| **Apple (AAPL)** | 0000320193-24-000123 | 2024-09-28 | Yes | 198 | 3 | 195 | 504 | 662 | Re-hashed & Matched | AI-assisted Accepted |
| **Apple (AAPL)** | 0000320193-25-000079 | 2025-09-27 | Yes | 198 | 3 | 198 | 510 | 668 | Re-hashed & Matched | AI-assisted Accepted |
| **Microsoft (MSFT)** | 0001564590-21-039151 | 2021-06-30 | Yes | 222 | 3 | 261 | 611 | 794 | Re-hashed & Matched | AI-assisted Accepted |
| **Microsoft (MSFT)** | 0001564590-22-026876 | 2022-06-30 | Yes | 222 | 3 | 259 | 600 | 783 | Re-hashed & Matched | AI-assisted Accepted |
| **Microsoft (MSFT)** | 0000950170-23-035122 | 2023-06-30 | Yes | 222 | 3 | 281 | 677 | 860 | Re-hashed & Matched | AI-assisted Accepted |
| **Microsoft (MSFT)** | 0000950170-24-087843 | 2024-06-30 | Yes | 227 | 3 | 289 | 712 | 900 | Re-hashed & Matched | AI-assisted Accepted |
| **Microsoft (MSFT)** | 0000950170-25-100235 | 2025-06-30 | Yes | 227 | 3 | 269 | 666 | 854 | Re-hashed & Matched | AI-assisted Accepted |
| **Adobe (ADBE)** | 0000796343-25-000004 | 2024-11-29 | Yes | 255 | 3 | 321 | 776 | 980 | Re-hashed & Matched | AI-assisted Accepted |
| **NVIDIA (NVDA)** | 0001045810-24-000029 | 2024-01-28 | Yes | 218 | 3 | 221 | 429 | 607 | Re-hashed & Matched | AI-assisted Accepted |
| **Salesforce (CRM)** | 0001108524-24-000005 | 2024-01-31 | Yes | 221 | 3 | 367 | 869 | 1045 | Re-hashed & Matched | AI-assisted Accepted |
| **AMD (AMD)** | 0000002488-25-000012 | 2024-12-28 | Yes | 238 | 3 | 338 | 704 | 898 | Re-hashed & Matched | AI-assisted Accepted |
| **Intel (INTC)** | 0000050863-25-000009 | 2024-12-28 | Yes | 245 | 3 | 412 | 877 | 1079 | Re-hashed & Matched | AI-assisted Accepted |
| **Cisco (CSCO)** | 0000858877-24-000017 | 2024-07-27 | Yes | 262 | 3 | 398 | 1034 | 1245 | Re-hashed & Matched | AI-assisted Accepted |
| **Oracle (ORCL)** | 0000950170-24-075605 | 2024-05-31 | Yes | 236 | 3 | 222 | 398 | 590 | Re-hashed & Matched | AI-assisted Accepted |
| **IBM (IBM)** | 0000051143-25-000015 | 2024-12-31 | Yes | 279 | 3 | 560 | 1320 | 1544 | Re-hashed & Matched | AI-assisted Accepted |
| **TOTALS** | **18 Filings** | — | — | **4,100** | **54** | **5,213** | **12,077** | **15,411** | **All 18 Re-hashed** | **AI-assisted Accepted** |

Audit artifact: [`docs/reports/2026-11-15_corpus_audit.json`](2026-11-15_corpus_audit.json).

---

## 3. Independent Chart Dataset Approval & Promotion Gate

- **Audited Files**: `data/charts/question-set.json`, `data/charts/apple-2021-candidate-questions.json` (15 dev), `data/charts/heldout-35-candidate-questions.json` (35 held-out).
- **Reviewer**: Ujjwal Chandak (`chandakujjwal6`).
- **Original Author**: B Rushil Mohan (`rmo29` / AI-assisted).
- **Audit Verification Results**:
  1. **Visual Fidelity & Integrity**: Verified each of the 50 candidate questions against original chart graphics across all 6 companies (Apple, NVIDIA, AMD, Intel, Cisco, Adobe) checking answerability, exact wording, and proper basis.
  2. **Unknown Value Handling**: Confirmed that unprinted curve coordinates remain marked as unknown rather than interpolated or hallucinated.
  3. **Split Isolation**: Confirmed Apple 2021 (15 questions) appears strictly in development, while the remaining 5 issuers (35 questions) are strictly held-out.
  4. **Approval Ledger**: Recorded per-case human inspection marks in [`docs/reports/2026-11-15_chart_review_inputs.json`](2026-11-15_chart_review_inputs.json) and generated the verified ledger in [`docs/reports/2026-11-15_chart_approvals_ujjwal.json`](2026-11-15_chart_approvals_ujjwal.json) (`method: "human_original_image_and_source"`).
  5. **Inventory Hash Reconciliation**: Preserved canonical LF pinned `inventory_sha256` in `data/charts/chart-sources.json` (`3532d851...`) with cross-platform CRLF/LF resilience in `scripts/verify_chart_set.py`.
  6. **Gate Promotion**: `scripts/promote_chart_set.py` executed successfully; generated [`docs/reports/2026-11-15_chart_promotion_report.json`](2026-11-15_chart_promotion_report.json) with `status: "independently_reviewed_labels"` and `evaluation_ready: true`. Variant G prerequisite cleared.

---

## 4. Predeclared Output Faithfulness Audit Sample

To eliminate post-hoc selection bias, exactly 50 evaluation cases were predeclared using fixed seed `42` across all 7 canonical variants:

| Variant | Total Sampled Cases | Benchmarks Represented | Focus Area |
| :---: | :---: | :--- | :--- |
| **A** | 7 | FinanceBench (3), FinQA (2), TAT-QA (2) | Fixed-overlap text + flattened markdown tables |
| **B** | 7 | FinanceBench (3), FinQA (2), TAT-QA (2) | Section-aware structure vs flattened tables |
| **C** | 7 | FinanceBench (3), FinQA (2), TAT-QA (2) | Matched parent tables & self-describing cells |
| **D** | 7 | FinanceBench (3), FinQA (2), TAT-QA (2) | Dense + BM25 hybrid reciprocal rank fusion |
| **E** | 7 | FinanceBench (3), FinQA (2), TAT-QA (2) | Cross-encoder reranking over fused candidates |
| **F** | 7 | FinanceBench (3), FinQA (2), TAT-QA (2) | Two-stage structured routing escalation |
| **G** | 8 | Charts Dev (4), Charts Held-Out (4) | Multimodal chart candidates & visual evidence |
| **Total** | **50** | **FB (18), FinQA (12), TAT-QA (12), Charts (8)** | **Seeded Predeclaration (`seed: 42`)** |

Audit sample artifact: [`docs/reports/2026-11-15_audit_sampling_predeclaration.json`](2026-11-15_audit_sampling_predeclaration.json).

---

## 5. Frozen Controls Manifest

Experiment controls, prompt templates, and case pools are serialized in [`docs/reports/2026-11-15_frozen_manifest.json`](2026-11-15_frozen_manifest.json):

```json
{
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "embedding_dim": 768,
  "vector_index": "exact_faiss_flat_ip",
  "generator_model": "gemma3:4b",
  "generator_digest": "sha256:68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7",
  "max_passages": 5,
  "context_token_budget": 4000,
  "calculator": "restricted_decimal_trees_fail_closed",
  "numerical_relative_tolerance": 0.01,
  "random_seed": 42,
  "route_thresholds": "unfrozen"
}
```

---

## 6. Execution Status & Gate Summary

- **Variants A, B, C, D**: Runner readiness verified and prerequisite input gates cleared. Benchmark evaluation runs are marked `not_started` due to absence of local GPU compute on the owner's machine.
- **Variant E**: Gated and marked `blocked` pending `bge-reranker-base` cross-encoder fitting.
- **Variant F**: Gated and marked `blocked` pending routing threshold calibration.
- **Variant G**: `independent_chart_approval` prerequisite cleared; marked `blocked` pending reranker/threshold calibration and dedicated compute.
- **Comparative Runs**: Llama 3.2 3B comparison and automated RAGAS faithfulness runs are marked `not_started`.

Full run status matrix is recorded in [`docs/reports/2026-11-16_run_status.json`](2026-11-16_run_status.json).

---

## 7. Not Done / Pending Scope

1. **Benchmark Model Output Generation**:
   - No model evaluation outputs currently exist in `output/eval_*`.
   - Runs could not be launched on the owner's development machine due to hardware/compute constraints.
2. **Model Prerequisites for E & F**:
   - Cross-encoder reranker weights (`bge-reranker-base`) remain unfitted.
   - Routing thresholds across narrative/tabular/chart tiers remain uncalibrated (`route_thresholds: "unfrozen"`).
3. **Comparative & Faithfulness Pipelines**:
   - Llama 3.2 3B comparison runs have not been executed.
   - RAGAS faithfulness scoring has not been executed (requires generated output files).
4. **Handoff to Pavan Agrawal (`pavanagrawal0809`)**:
   - Pavan receives the runner, frozen controls manifest, and predeclared 50-output sample in [`docs/handoffs/2026-11-15_ujjwal.md`](../handoffs/2026-11-15_ujjwal.md). Variants A–D can run directly once LLM model inference environment is configured on allocated compute.
