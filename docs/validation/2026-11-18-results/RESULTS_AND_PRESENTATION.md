# FinRAG validation results and presentation defence

## What this study establishes

This is a **PRD-aligned development validation subset** of the current application and a controlled retrieval-only comparison. It is not an official benchmark result, a held-out test or completion of the promised full A-G study. Case selection, expected outcomes, reference values, original-source checks and scoring controls were frozen before the new execution. The original PRD remains unchanged.

We evaluated 90 requests: 72 numerical requests across 18 filings / 10 companies, 12 adversarial requests and 6 narrative requests. Of the 72 numerical requests, 71 had numeric reference values;one known Oracle aggregate-margin case was predeclared unanswerable and retained separately. References were developer-derived from the existing question bank; 71 unique original inline operands were corroborated against their original displayed values, scales, context dates and exact locators. They are not independently human-approved labels. Question development and metric interpretation share application parsing assumptions.

## Results suitable for the validation slide

| Measurement | Actual result | Meaning |
| --- | --- | --- |
| Numerical source-reference agreement | **59/71 (83.10%)** | PRD 1% relative tolerance plus unit, period, source accession and required cited operands. |
| Numerical agreement, 95% filing-cluster interval | 83.10% [66.67%, 95.83%] | 10,000 bootstrap resamples with seed 42 of filings; uncertainty within this selected development set. |
| Correct expected missing-evidence refusal | **1/1 (100.00%)** | Oracle gross margin; included in 72 requests and not counted as a numeric success. |
| Strict adversarial contract score | **7/12 (58.33%)** | Exact predeclared response/completeness/semantic expectations; all failures retained. |
| Safe scope rejection, ignoring refusal-status subtype | **8/8** | Supplemental view of the 8 guard cases. An insufficient-evidence refusal is safe but may still fail the exact invalid-request contract. |
| Citation identity/accession on successful numeric responses | **59/59** | Structural identity check only; it cannot establish that the question intent or financial interpretation is correct. |
| Incorrect returned values on the labelled consolidated numerical set | **0/59** | Also report false refusals; a high conditional result must not hide unanswered questions. This excludes the separately reported adversarial questions. |
| Numeric local HTTP median/p95 | **0.028s / 0.050s** | Known typed-calculator application route, not LLM accuracy or generation latency. |
| Narrative responses with an OK status | **6/6** | Actual configured-model outputs. Semantic quality remains unreviewed. |
| Narrative citation identity/accession | **6/6** | Includes failed/missing responses in denominator; not a claim-level faithfulness score. |
| Narrative local HTTP median/p95 | **102.997s / 157.759s** | Prepared-machine observations. Model residency/cold state was not controlled. |

The latency runner's term “warm prepared runtime” means services were already started. It does **not** establish controlled model residency, a warm GPU/cache, cold-start speed or a production load test. Do not compare numerical calculator time with narrative LLM time as if only retrieval differed.

## Controlled retrieval-only comparison

There are 71 labelled numerical questions. Both methods use the same original question, same pinned BGE query vector, same canonical C cells, exact FAISS, per-filing/consolidated filters and depth 10. Hybrid adds BM25 and RRF k=60. All comparative periods remain eligible. No answer model, query expansion, exact metric lookup, cross-encoder, routing, chart caption or parent injection is used. This isolates a retrieval component corresponding to part of the PRD's C-to-D transition.

Values below are point estimates with 95% filing-cluster bootstrap intervals. The paired difference is hybrid minus dense on the same case and sampled filing groups. MRR is also shown as a percentage-scaled score for compactness.

| Metric | Dense only | Dense+BM25/RRF60 | Paired difference |
| --- | --- | --- | --- |
| Operand Recall@5 | 75.35% [69.01%, 80.99%] | 75.35% [64.58%, 84.03%] | +0.00 pp [-9.15, +9.03] |
| Operand Recall@10 | 90.14% [84.51%, 95.00%] | 88.73% [85.42%, 92.25%] | -1.41 pp [-5.63, +3.47] |
| Complete operands@5 | 61.97% [54.29%, 69.01%] | 61.97% [50.70%, 71.83%] | +0.00 pp [-8.45, +8.57] |
| Complete operands@10 | 83.10% [75.00%, 90.28%] | 77.46% [70.83%, 84.51%] | -5.63 pp [-11.59, +0.00] |
| MRR@10 | 54.10% [45.94%, 63.09%] | 53.08% [43.19%, 63.51%] | -1.02 pp [-7.46, +5.85] |

Query embedding batch time:1.507s for 71 queries. Median exact dense-search time:9.239ms; median added BM25/RRF time:5.142ms. These exclude model loading and answer generation. They are not per-user total latency estimates.

Do not claim a positive retrieval effect when its measured difference is zero/negative or when the paired interval crosses zero. A component result cannot prove the full system, reranker, routing or captions improve answer accuracy.

## Why the failures matter

Every failed case is in `summary.json` and the full output ledger. False company-name rejections, component-versus-total substitutions, relative-percent versus percentage-point ambiguity and incomplete compound questions must remain visible if observed. Report the exact count and examples below; do not replace failed full-name questions with easier ticker wording inside the primary results. A wording repair or semantic fix needs a new code revision and a separate rerun, retaining this baseline.

- **CRM-2024-074** — What was Salesforce, Inc.'s net income in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **CRM-2024-075** — What was Salesforce, Inc.'s gross margin in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **CRM-2024-076** — What was Salesforce, Inc.'s revenue growth from FY2023 to FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **AMD-2024-080** — What was Advanced Micro Devices, Inc.'s net income in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **AMD-2024-081** — What was Advanced Micro Devices, Inc.'s gross margin in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **AMD-2024-082** — What was Advanced Micro Devices, Inc.'s revenue growth from FY2023 to FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **CSCO-2024-092** — What was Cisco Systems, Inc.'s net income in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **CSCO-2024-093** — What was Cisco Systems, Inc.'s gross margin in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **CSCO-2024-094** — What was Cisco Systems, Inc.'s revenue growth from FY2023 to FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **IBM-2024-104** — What was International Business Machines Corporation's net income in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **IBM-2024-105** — What was International Business Machines Corporation's gross margin in FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **IBM-2024-106** — What was International Business Machines Corporation's revenue growth from FY2023 to FY2024? Status: `invalid_request`. The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.
- **non-adjacent** — What was Apple's revenue growth from FY2021 to FY2025? Status: `insufficient_evidence`. Annual comparisons require two adjacent fiscal years.
- **component-azure** — How much revenue did Microsoft report from Azure in FY2025? Status: `ok`. Calculated from cited source values with checked financial rules.
- **component-iphone** — How much revenue did Apple report from iPhone in FY2025? Status: `ok`. Calculated from cited source values with checked financial rules.
- **margin-relative-percent** — By what percentage did Apple's gross margin increase from FY2020 to FY2021? Status: `ok`. Calculated from cited source values with checked financial rules.
- **compound-metrics** — What were Apple's revenue and net income in FY2025? Status: `ok`. Calculated from cited source values with checked financial rules.

## Recorded runner correction

The original pre-execution manifest and all 90 HTTP outputs are preserved. The first retrieval attempt stopped before producing any rankings because the BM25 stream API rejects an explicit `type` filter. The adapter was corrected to select table cells through `top_k_text=0, top_k_tables=10`, while the dense store retains its explicit table-cell filter. Candidate scope, case selection, reference answers, all HTTP outputs, scoring, query vectors, depth and fusion constant were unchanged. The second analysis manifest records both code identities and inherited-ledger hashes. This is a disclosed API-binding correction, not post-result tuning. See `analysis-amendment.json` and `original-pre-execution-manifest.json`.

## How to present it

Use the existing results slide in the six-slide deck rather than adding slides beyond the PRD's six-slide requirement. Replace stale illustrative/test-count-only result claims with the actual table above, a compact dense/hybrid retrieval comparison and a short limitations line. Use a separate backup handout for the full methods and case ledger.

Suggested 90-second script:

“Our original research question asks whether structured financial evidence and improved retrieval help grounded financial QA. We have a working 18-filing application. For this development validation, we froze 90 questions covering numerical answers, adversarial inputs and narrative answers. We scored financial numbers using the PRD's 1% tolerance together with period, unit and source requirements. We also compared dense retrieval with BM25/RRF fusion using exactly the same questions, BGE vectors, cell corpus and filing filters. The displayed results are the actual measured counts and paired intervals. Our failures show that correct arithmetic and valid citations alone cannot guarantee that a question's intent was understood. This is a development subset, not a held-out benchmark or completion of A-G. We have not claimed RAGAS or independent human audit scores that were not measured.”

Say the observed numbers from the results table; do not memorise a claim that all metrics improved. If retrieval did not improve, state that directly and explain what the unchanged controls let us conclude.

## Likely examiner questions and defensible answers

**Does this satisfy the entire original proposal?**
No. It implements and measures a meaningful subset with the proposal's source, tolerance, retrieval and uncertainty controls. Full accepted A–G across the promised corpora, independent review, RAGAS, separate Llama and final audits remain incomplete. We cannot unilaterally claim that a smaller study fulfils the original commitment; a formal scope reduction needs professor agreement.

**Why not use the original full benchmark immediately?**
The existing runner's official contexts are not yet bound to a verified source-equivalent canonical retrieval universe. Running questions against unrelated application filings would give misleading scores. We therefore measured the actual supported application separately and kept the missing official binding explicit.

**Are these independent or unseen test questions?**
No. They are frozen development questions, some already used during implementation. References were recomputed from original inline facts, but financial interpretation and case design are developer-derived. This measures regression behaviour and supports failure analysis; it does not estimate unseen-user generalisation.

**Did you validate the LLM's arithmetic?**
Known numerical questions use restricted source-bound Decimal operations and explicitly report no model-generated explanation. These results validate the typed calculation/application path. The narrative cases use the real pinned model; their semantic correctness requires a separate actual review.

**Do correct citations prove faithfulness?**
No. Citation identity says the displayed citations match the included context and selected filing. It does not prove that every generated claim follows from that context. We provide exact narrative outputs/context and blank reviewer fields rather than inventing a faithfulness score.

**Does numerical reference agreement prove that hybrid RAG improved answers?**
No. For recognised numerical questions, the interactive application uses a typed source lookup and checked calculator. We do not attribute those answer scores or timings to lexical fusion. The separate retrieval experiment disables query expansion and typed lookup and measures the actual original-question ranking. Narrative answers use retrieval and the model, but their semantic quality remains pending review. These are separate measurements, not a causal end-to-end comparison.

**Why use complete-operand coverage as well as MRR?**
A margin or growth calculation needs several premises. Retrieving revenue at rank 1 can give a good MRR while missing cost or the prior-year value. Complete-operand coverage checks whether the entire calculation can be supported.

**Why bootstrap by filing?**
Several questions reuse one report, so treating them as fully independent understates uncertainty. We resample whole filings with a fixed seed and 10,000 resamples; dense/hybrid use paired questions. This still does not remove development-selection bias or prove external validity.

**Why is no RAGAS score shown?**
No pinned RAGAS evaluator was executed on these outputs. A lexical-overlap check or citation hash is not RAGAS faithfulness. We can show actual structural checks and leave the six narratives for genuine claim-level review without relabelling them.

**What important limitations did evaluation find?**
Use the actual failures in this report. Explain whether the failure is a false refusal, wrong question interpretation, incomplete answer or service failure. Do not say the app can answer any filing question.

## Claim boundaries

- Defensible: source-derived development answer agreement, observed failures/refusals, per-case source/citation checks, actual local timings and this controlled retrieval-only comparison.
- Not established: official FinanceBench / FinQA / TAT-QA scores; full A–G generation results; chart / G acceptance; Llama superiority; RAGAS; independent50-outputaudit; cold-start/load capacity; unseen-question accuracy or universal filing coverage.
- Manual next step: an eligible person reviews all six actual narrative outputs and their exact included source contexts using the blank packet. This six-case review must not be called the PRD's independent stratified fifty-output audit.

Artifacts: `manifest.json`, `cases.json`, `reference-source-checks.json`, `http-results.jsonl`, `retrieval-results.json`, `summary.json`, and `narrative-review.html/json`. The manifest/reference/output checksums are in `artifact-hashes.json`. No credentials or authorization headers are included.
