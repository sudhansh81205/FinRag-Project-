# FinRAG completion report: November 15 independent input approval, freeze, and execution launch

- **Owner**: Ujjwal Chandak (`chandakujjwal6`) (10 estimated hours)
- **Date**: November 15, 2026
- **Requirements**: R1 Corpus, R2 Index, R3 Evidence, R7 Evaluation, R11 Charts, R12 Controls
- **Upstream PRs Consumed**: PR #11 (Sudhansh Nov 12 integration), PR #12 (Likhit Nov 13 corpus), PR #13 (Gowtham Nov 14 UI & benchmark runner)
- **Next Assignee**: Agrawal Pavan Shailesh (Nov 16: output audit, metrics, report and slides)

---

## 1. Executive Summary

On November 15, 2026, Ujjwal Chandak completed the independent input approval, control freeze, and run launch gate for FinRAG. Acting as the team's independent auditor under strict anti-self-approval guidelines:

1. **Independent SEC Corpus & Matched Index Audit (R1, R2, R3)**:
   - Independently audited all 18 SEC 10-K filings across 10 technology issuers (5 Apple, 5 Microsoft, and 8 technology issuers: NVDA, AMD, INTC, CSCO, ADBE, CRM, ORCL, IBM).
   - Verified that uncompressed byte streams match pinned profiles in `data/corpus_html_profiles.json`.
   - Reconciled passage counts: **5,213 passages in Variant A** (fixed-overlap), **12,077 passages in Variant B** (section-aware), **15,411 passages in Variant C** (including 4,100 self-describing cells and 54 parent tables).
   - Formally accepted all 18 candidate filings in `docs/reports/2026-11-15_corpus_audit.json`.

2. **Independent Chart Dataset & Caption Approval (R11)**:
   - Independently audited all 50 candidate chart questions (15 dev + 35 held-out) across 6 original 10-K chart images in `data/charts/assets/` without self-approval (Author: Rushil Mohan / AI-assisted; Reviewer: Ujjwal Chandak).
   - Reconciled the canonical LF `inventory_sha256` in `data/charts/chart-sources.json` against `data/application_filings.json` (`3532d851...`).
   - Verified `scripts/verify_chart_set.py` (exit code 0) and promoted the set to `independently_reviewed_labels` (`evaluation_ready: true`) via `scripts/promote_chart_set.py`.
   - Satisfied the prerequisite gate `independent_chart_approval` for Variant G.

3. **Predeclared Seeded Stratified 50-Output Faithfulness Sample (R7, R12)**:
   - Drew and froze exactly 50 sample cases stratified across variants A–G (7 for A–F, 8 for G) and benchmarks (FinanceBench 18, FinQA 12, TAT-QA 12, Charts 8) using frozen seed `42`.
   - Predeclared *before* score inspection in `docs/reports/2026-11-15_audit_sampling_predeclaration.json`.
   - Assigned all 50 cases to Pavan for independent audit on Nov 16 with zero authorship conflicts.

4. **Frozen Experimental Controls & Capacity Gate (R7, R12)**:
   - Locked frozen controls: BGE-base-en-v1.5 (768-D normalized), exact FAISS `IndexFlatIP`, Gemma 3 4B (`sha256:68ceab...`), max 5 passages, 1% relative numerical error tolerance, random seed 42.
   - Evaluated machine throughput (12 cores, 15.73 GB RAM): full 3,015 unbatched CPU cases across 7 variants (21,105 evaluations = 90.87 hours) exceeds the 72-hour window before Nov 17.
   - Formally approved the prioritized core suite: FinanceBench open 150 + FinQA candidate + TAT-QA candidate + Charts dev/heldout ($\approx 9.05$ hours total).
   - Verified runner execution on Variant A using `scripts/run_benchmarks.py`.

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

## 3. Independent Chart Dataset Approval Ledger (50 Questions / 6 Images)

- **Audited Files**: `data/charts/question-set.json`, `data/charts/apple-2021-candidate-questions.json` (15 dev), `data/charts/heldout-35-candidate-questions.json` (35 held-out).
- **Reviewer**: Ujjwal Chandak (`chandakujjwal6`).
- **Original Author**: B Rushil Mohan (`rmo29` / AI-assisted).
- **Audit Verification Results**:
  1. **Visual Fidelity**: Verified each of the 50 questions against original embedded/rendered chart graphics in `data/charts/assets/`.
  2. **Unknown Value Handling**: Confirmed that unprinted curve coordinates remain marked as unknown rather than interpolated or hallucinated.
  3. **Split Isolation**: Confirmed Apple 2021 (15 questions) appears strictly in development, while the remaining 5 issuers (35 questions) are strictly held-out.
  4. **Inventory Hash Reconciliation**: Preserved canonical LF pinned `inventory_sha256` in `data/charts/chart-sources.json` (`3532d851...`) with cross-platform CRLF/LF resilience in `scripts/verify_chart_set.py`.
  5. **Promotion Result**: `scripts/promote_chart_set.py` executed successfully; generated [`docs/reports/2026-11-15_chart_promotion_report.json`](2026-11-15_chart_promotion_report.json) with `status: independently_reviewed_labels` and `evaluation_ready: true`.

---

## 4. Predeclared Output Faithfulness Audit Sample

To eliminate post-hoc selection bias, exactly 50 evaluation cases were predeclared using fixed seed `42` across all 7 canonical variants:

- **Stratification**:
  - Variant A: 7 cases (3 FinanceBench, 2 FinQA, 2 TAT-QA)
  - Variant B: 7 cases (3 FinanceBench, 2 FinQA, 2 TAT-QA)
  - Variant C: 7 cases (3 FinanceBench, 2 FinQA, 2 TAT-QA)
  - Variant D: 7 cases (3 FinanceBench, 2 FinQA, 2 TAT-QA)
  - Variant E: 7 cases (3 FinanceBench, 2 FinQA, 2 TAT-QA)
  - Variant F: 7 cases (3 FinanceBench, 2 FinQA, 2 TAT-QA)
  - Variant G: 8 cases (8 Chart Multimodal questions)
- **Reviewer Assignment**: All 50 cases assigned to **Agrawal Pavan Shailesh** for November 16 audit.
- **Authorship Conflicts**: 0 conflicts. Pavan did not author any of the candidate labels, guaranteeing full independence.

Artifact: [`docs/reports/2026-11-15_audit_sampling_predeclaration.json`](2026-11-15_audit_sampling_predeclaration.json).

---

## 5. Prerequisite Gate Status & Capacity Decision

| Prerequisite Gate | Target Variant | Verification Evidence | Status |
| :--- | :---: | :--- | :---: |
| `fixed_overlap_index_representation` | A | Reconciled 5,213 passages in `docs/reports/2026-11-15_corpus_audit.json` | **Cleared** |
| `section_aware_index_representation` | B | Reconciled 12,077 passages in `docs/reports/2026-11-15_corpus_audit.json` | **Cleared** |
| `canonical_cells_and_parents` | C, D, E, F, G | Reconciled 4,100 cells and 54 parent tables | **Cleared** |
| `bm25_index` | D, E, F, G | In-memory BM25 index over canonical text/table representations | **Cleared** |
| `independent_chart_approval` | G | Promoted chart set with independent human review (`Ujjwal Chandak`) | **Cleared** |
| `bge_reranker_base` | E, F, G | Pending live cross-encoder download/cache on execution machine | **Gated** |
| `frozen_routing_thresholds` | F, G | Tuned route thresholds from dev-only runs | **Gated** |

### Capacity Profiling Verdict
Hardware profiled: Intel 12-core CPU, 15.73 GB RAM.
$$\text{Full unbatched CPU runtime} = \frac{3,015 \text{ cases} \times 7 \text{ variants} \times 15.5 \text{ sec}}{3600} = 90.87 \text{ hours}$$
Since $90.87 \text{ hours} > 72 \text{ hours}$ (time to November 17 deadline), Ujjwal formally approves the **prioritized benchmark execution plan**:
- Full FinanceBench open 150: 1,050 evaluations across A–G ($\approx 4.52$ hours)
- FinQA candidate universe: 350 evaluations ($\approx 1.51$ hours)
- TAT-QA candidate universe: 350 evaluations ($\approx 1.51$ hours)
- Charts dev + heldout: 350 evaluations ($\approx 1.51$ hours)
- **Total Prioritized Runtime**: $\approx 9.05$ hours (fully feasible before deadline).

---

## 6. Viva and Course Concept Connections

1. **Independent Verification vs. Self-Approval**:
   - In safety-critical and financial AI, candidate gold answers authored with LLM assistance cannot be verified by the prompt author. An independent auditor checks each assertion against ground-truth images and primary SEC documents.
2. **Predeclared Stratified Sampling**:
   - Sampling generated outputs *after* observing metric scores introduces severe confirmation bias. Freezing the 50 case IDs prior to evaluation ensures that failure cases and hallucinations are faithfully captured.
3. **Representation Hierarchy**:
   - Fixed chunking (Variant A) destroys financial tables by severing cells from column headers. Section-aware chunking (Variant B) protects topical boundaries. Self-describing cell tuples (Variant C) bind explicit XBRL period, unit, and parent metadata directly to the fact.
