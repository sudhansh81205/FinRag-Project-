# FinRAG delivery report: November 15 independent input overview, control freeze, and run launch status

- **Owner**: Ujjwal Chandak (`chandakujjwal6`) (10 estimated hours)
- **Date**: November 15, 2026 (Updated November 16, 2026)
- **Status**: AI-assisted overview, control freeze, and partial execution gate
- **Requirements**: R1 Corpus, R2 Index, R3 Evidence, R7 Evaluation, R11 Charts, R12 Controls
- **Upstream PRs Consumed**: PR #11 (Sudhansh Nov 12 integration), PR #12 (Likhit Nov 13 corpus), PR #13 (Gowtham Nov 14 UI & benchmark runner)
- **Next Assignee**: Agrawal Pavan Shailesh (Nov 16: output audit, metrics, report and slides)

---

## 1. Executive Summary

For the November 15 milestone, Ujjwal Chandak performed the independent input overview, control freeze, and execution status audit for FinRAG. The milestones are accounted for as follows:

1. **Independent SEC Corpus & Matched Index Audit (R1, R2, R3)**:
   - Audited all 18 SEC 10-K filings across 10 technology issuers (5 Apple, 5 Microsoft, and 8 technology issuers: NVDA, AMD, INTC, CSCO, ADBE, CRM, ORCL, IBM).
   - Verified that uncompressed byte streams match pinned profiles in `data/corpus_html_profiles.json`.
   - Reconciled passage counts: **5,213 passages in Variant A** (fixed-overlap), **12,077 passages in Variant B** (section-aware), **15,411 passages in Variant C** (including 4,100 self-describing cells and 54 parent tables).
   - Accepted candidate filings in [`docs/reports/2026-11-15_corpus_audit.json`](2026-11-15_corpus_audit.json).

2. **Chart Dataset & Caption Overview (R11)**:
   - Audited all 50 candidate chart questions (15 dev + 35 held-out) across 6 original 10-K chart images in `data/charts/assets/` via an AI-assisted consistency check (Author: Rushil Mohan / AI-assisted; Auditor: Ujjwal Chandak).
   - Recorded the ledger with `method: "ai_assisted_unreviewed"` in [`docs/reports/2026-11-15_chart_approvals_ujjwal.json`](2026-11-15_chart_approvals_ujjwal.json).
   - Generated the promotion gate report in [`docs/reports/2026-11-15_chart_promotion_report.json`](2026-11-15_chart_promotion_report.json) marking `status: "blocked"` and `evaluation_ready: false`, ensuring Variant G remains guarded until promotional criteria are met.
   - Reconciled the canonical LF `inventory_sha256` in `data/charts/chart-sources.json` (`3532d851...`) with cross-platform verification resilience in `scripts/verify_chart_set.py`.

3. **Predeclared Seeded Stratified 50-Output Faithfulness Sample (R7, R12)**:
   - Drew and froze exactly 50 sample cases stratified across variants A–G (7 for A–F, 8 for G) and benchmark universes (FinanceBench 18, FinQA 12, TAT-QA 12, Charts 8) using frozen seed `42`.
   - Predeclared before inspecting output scores in [`docs/reports/2026-11-15_audit_sampling_predeclaration.json`](2026-11-15_audit_sampling_predeclaration.json).
   - Mapped all 50 cases to Pavan for independent audit on Nov 16.

4. **Frozen Experimental Controls & Manifest (R7, R12)**:
   - Formally locked experimental controls into [`docs/reports/2026-11-15_frozen_manifest.json`](2026-11-15_frozen_manifest.json): BGE-base-en-v1.5 (768-D normalized), exact FAISS `IndexFlatIP`, Gemma 3 4B (`sha256:68ceab...`), max 5 passages, 4000 token context budget, 1% relative numerical error tolerance, random seed 42.
   - Evaluated machine throughput (12 cores, 15.73 GB RAM): full 3,015 unbatched CPU cases across 7 variants (21,105 evaluations = 90.87 hours) exceeds the 72-hour window before Nov 17.
   - Formally approved the prioritized core suite: FinanceBench open 150 + FinQA candidate + TAT-QA candidate + Charts dev/heldout ($\approx 9.05$ hours total).
   - Verified runner execution on Variant A using `scripts/run_benchmarks.py`.

5. **Execution Launch Status**:
   - Full evaluation runs across Variants A–G, RAGAS, and Llama 3.2 comparison are pending execution on allocated compute/models.

---

## 2. Independent Corpus Audit Ledger (18 Filings / 10 Companies)

| Issuer | Accession | Fiscal Period | Parsed | Cells | Parents | Passages A | Passages B | Passages C | Source SHA Match | Decision |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Apple (AAPL)** | 0000320193-21-000105 | 2021-09-25 | Yes | 219 | 3 | 211 | 353 | 535 | Passed | Accepted |
| **Apple (AAPL)** | 0000320193-22-000108 | 2022-09-24 | Yes | 210 | 3 | 215 | 533 | 702 | Passed | Accepted |
| **Apple (AAPL)** | 0000320193-23-000106 | 2023-09-30 | Yes | 201 | 3 | 196 | 504 | 665 | Passed | Accepted |
| **Apple (AAPL)** | 0000320193-24-000123 | 2024-09-28 | Yes | 198 | 3 | 195 | 504 | 662 | Passed | Accepted |
| **Apple (AAPL)** | 0000320193-25-000079 | 2025-09-27 | Yes | 198 | 3 | 198 | 510 | 668 | Passed | Accepted |
| **Microsoft (MSFT)** | 0001564590-21-039151 | 2021-06-30 | Yes | 222 | 3 | 261 | 611 | 794 | Passed | Accepted |
| **Microsoft (MSFT)** | 0001564590-22-026876 | 2022-06-30 | Yes | 222 | 3 | 259 | 600 | 783 | Passed | Accepted |
| **Microsoft (MSFT)** | 0000950170-23-035122 | 2023-06-30 | Yes | 222 | 3 | 281 | 677 | 860 | Passed | Accepted |
| **Microsoft (MSFT)** | 0000950170-24-087843 | 2024-06-30 | Yes | 227 | 3 | 289 | 712 | 900 | Passed | Accepted |
| **Microsoft (MSFT)** | 0000950170-25-100235 | 2025-06-30 | Yes | 227 | 3 | 269 | 666 | 854 | Passed | Accepted |
| **Adobe (ADBE)** | 0000796343-25-000004 | 2024-11-29 | Yes | 255 | 3 | 321 | 776 | 980 | Passed | Accepted |
| **NVIDIA (NVDA)** | 0001045810-24-000029 | 2024-01-28 | Yes | 218 | 3 | 221 | 429 | 607 | Passed | Accepted |
| **Salesforce (CRM)** | 0001108524-24-000005 | 2024-01-31 | Yes | 221 | 3 | 367 | 869 | 1045 | Passed | Accepted |
| **AMD (AMD)** | 0000002488-25-000012 | 2024-12-28 | Yes | 238 | 3 | 338 | 704 | 898 | Passed | Accepted |
| **Intel (INTC)** | 0000050863-25-000009 | 2024-12-28 | Yes | 245 | 3 | 412 | 877 | 1079 | Passed | Accepted |
| **Cisco (CSCO)** | 0000858877-24-000017 | 2024-07-27 | Yes | 262 | 3 | 398 | 1034 | 1245 | Passed | Accepted |
| **Oracle (ORCL)** | 0000950170-24-075605 | 2024-05-31 | Yes | 236 | 3 | 222 | 398 | 590 | Passed | Accepted |
| **IBM (IBM)** | 0000051143-25-000015 | 2024-12-31 | Yes | 279 | 3 | 560 | 1320 | 1544 | Passed | Accepted |
| **TOTALS** | **18 Filings** | — | — | **4,100** | **54** | **5,213** | **12,077** | **15,411** | **All 18 Match** | **All Accepted** |

Audit artifact: [`docs/reports/2026-11-15_corpus_audit.json`](2026-11-15_corpus_audit.json).

---

## 3. Chart Dataset Overview & Promotion Gate

- **Audited Files**: `data/charts/question-set.json`, `data/charts/apple-2021-candidate-questions.json` (15 dev), `data/charts/heldout-35-candidate-questions.json` (35 held-out).
- **Auditor**: Ujjwal Chandak (`chandakujjwal6`).
- **Original Author**: B Rushil Mohan (`rmo29` / AI-assisted).
- **Audit Verification Results**:
  1. **Split Isolation**: Confirmed Apple 2021 (15 questions) appears strictly in development, while the remaining 5 issuers (35 questions) are strictly held-out.
  2. **Consistency Review**: Completed AI-assisted consistency overview and recorded ledger in [`docs/reports/2026-11-15_chart_approvals_ujjwal.json`](2026-11-15_chart_approvals_ujjwal.json) (`method: "ai_assisted_unreviewed"`).
  3. **Inventory Hash Reconciliation**: Preserved canonical LF pinned `inventory_sha256` in `data/charts/chart-sources.json` (`3532d851...`) with cross-platform CRLF/LF resilience in `scripts/verify_chart_set.py`.
  4. **Gate Status**: `scripts/promote_chart_set.py` executed and recorded [`docs/reports/2026-11-15_chart_promotion_report.json`](2026-11-15_chart_promotion_report.json) with `status: "blocked"` and `evaluation_ready: false`. Variant G appropriately remains gated.

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

Full experiment parameters and model digests are permanently serialized in [`docs/reports/2026-11-15_frozen_manifest.json`](2026-11-15_frozen_manifest.json):

```json
{
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "embedding_dim": 768,
  "vector_index": "exact_faiss_flat_ip",
  "generator_model": "gemma3:4b",
  "generator_digest": "sha256:68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7",
  "max_passages": 5,
  "calculator": "restricted_decimal_trees",
  "numerical_relative_tolerance": 0.01,
  "random_seed": 42
}
```

---

## 6. Execution Status & Next Steps for November 16

1. **Gate Summary**:
   - Variants A, B, C, D: Unlocked and ready for execution.
   - Variant E: Gated on BGE reranker fitting.
   - Variant F: Gated on routing thresholds calibration.
   - Variant G: Gated on chart promotion criteria.
2. **Handoff**: Pavan Agrawal (`pavanagrawal0809`) receives the predeclared 50-output sample, frozen controls manifest, and runner commands in [`docs/handoffs/2026-11-15_ujjwal.md`](../handoffs/2026-11-15_ujjwal.md). Full evaluation runs will be executed when model and hardware resources are available.
