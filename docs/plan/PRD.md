# FinRAG completion requirements through November 17

CV ++ Team 6 | CS F407 Artificial Intelligence | Application track | Revised November 12 2026

Build a financial question answering application that answers annual report questions from inspectable narrative, table and chart evidence, executes justified cited arithmetic, and exposes failures. Complete and submit the reproducible package by November 17, 2026 under the user's current instruction. Shanay owns the final day's release and submission. The revised calendar preserves proposal scope and professor requirements; a planning edit is not implementation or evaluation evidence.

## Authority and working rules

November 17 is the operative user-requested submission deadline. Its exact cutoff and any changed official course notice are unconfirmed. The old November 17 internal checkpoint and November 20/21/22 freeze, assessment and submission dates are historical context, not automatic recovery after this deadline. Individual official viva attendance remains required when scheduled by the course.

Exactly one named member owns project work on each date, including implementation, reviews, meetings, monitoring and handoffs. No off-day background tasks are assigned. Frozen deterministic jobs may run unattended; only the current owner actively manages or validates them. Hours are estimates, not measured effort. Preserve the seven-member roster without Harshil, historical assignments through November 11, and authorized early completion of the first Sudhansh and Shanay tasks.

PRD.md and FinRAG_PRD.docx are the current canonical representations. TASK_REQUIREMENTS.md and schedule.json derive the execution plan; COURSE_ALIGNMENT.md and EVIDENCE_CONTRACT.md explain controls. Archive old plans and preserve dated reviews. Source documents do not themselves authorize publication, messages, spending or credential use.

## What the project does

A user chooses a supported company, filing and value period, then asks a narrative, numerical or chart question. FinRAG retrieves eligible evidence, preserves original source identities, selects complete evidence within a fixed budget, and asks a real pinned model for a grounded response. Numerical answers require restricted operation trees whose cited operands pass deterministic issuer, scope, period, unit and denominator rules. The interface shows sources, actual included evidence, calculation and rule trace, route, model and status. Missing premises or failed services yield an honest refusal or error.

Support SEC Form 10-K annual reports, focusing on Item 7 MD&A, Item 8 statements and footnotes, and Item 1A risks. Exclude live market data, investment advice, fine-tuning and unrelated agent/game features. Preserve the Application track; actual approved-topic/track changes follow course approval rules. Retain exact source/configuration/output regressions for table-of-contents retrieval and lost financial table headers.

## Research question and retained scope

With corpus, embedder, answer model, prompt, calculator and final passage count fixed, how do section-aware chunks, self-describing cells, hybrid retrieval, hierarchical reranking, routing and chart descriptions change recall, answer quality, faithfulness and latency compared with standard dense RAG?

Expected improvements are hypotheses. Report uncertain/negative effects and latency costs. Cumulative A-G measures incremental changes in its declared order, not every interaction or universal causality. Professor requirements remain: an explicit testable question, concrete course connection, controlled experiment, numerical tolerance, independent fifty-output audit, named contributions and defensible viva evidence. One report, fourteen smoke questions and the old 42-hour plan cannot stand in for proposal completion.

Application coverage requires five exact Apple and five exact Microsoft filings, then at least one declared filing from each additional technology company needed to reach ten companies. Benchmark contexts are separate versioned corpora for FinQA, TAT-QA and the FinanceBench open sample of 150 questions. Declare their candidate universes, document types, inaccessible cases and source-mapping limits. A subset must be labelled a subset; it does not satisfy a full-suite claim.

## Starting evidence and remaining gates

The pre-repair review baseline is main 10e715cb6edb234028e5641f77ccf2e399021a07. PR8 at 211e563b2e2a49341e51ec701bbf32c7436eb08d and PR9 at aa8d46fa02123cbb5474d8a3bee98209fc0877d9 were later publications for November 8 and November 7 assignments. Their actual merge state and the repair SHA belong in the integration report. Do not retroactively credit their publication to the November 8 cutoff. F1-F12 already had bounded fixes; current AI-assisted repairs address F13-F18 and candidate integration defects without claiming human member hours.

| Area | Evidence available before this repair | Acceptance still required |
| --- | --- | --- |
| Corpus | Eighteen filings inventoried, sixteen previously acquired across nine companies; one independently accepted/indexed Apple 2021 filing. Its package has 316 narratives, 219 cells, three parents, eleven bounded PDF corroborations and one original chart. | Supported broader parsing and source acceptance before November 15 independent audit. Downloads and six chart assets do not establish multi-filing narrative/cell coverage. |
| Index | Pinned BGE base, 768 normalized dimensions, exact FAISS IndexFlatIP for 535 candidates, immutable generations and row checks. | Broader accepted builds, matched A/B representations, combined restart/restore evidence. |
| Retrieval | PR9 adds BM25, RRF60, parent helpers and injected reranker, with filter/failure/stage defects. | Repaired canonical C-F gates, actual integration, executable A/B representations, real cross-encoder, common tokenizer and five-passage controls. A configured class is not execution proof. |
| Model and math | PR8 pins Gemma 3 4B and cited Decimal trees with deterministic numerical rendering; historical real Mac traces exist. | Current intended-machine assets/access, throughput, integration and benchmark operation coverage. Runtime assets are not presumed locally available. |
| Charts | Fifty author-checked candidates, fifteen development/thirty-five held-out, on six original stock-performance charts; raw captions and corrections retained. | Independent per-case/caption approval, immutable identities, unchanged image-group splits, approved loading and G integration. Narrow chart diversity remains a limitation. |
| Application and results | Setup UI, source/DVC/MLflow checks and component tests. | Full UI/session isolation, loaders, frozen A-G runs, metrics, output audit, report, six slides and clean release. |

No defensible overall completion percentage follows from test counts or this table. The integration report distinguishes merged, PR-only, local-only, executed and unverified work.

## Requirements and accountability

Ownership is module accountability, not a second same-day assignment. A later reviewer works on their own scheduled date.

| ID | Required behavior | Accountability and acceptance |
| --- | --- | --- |
| R1 Corpus | Exact issuer/accession/form/filing and value periods, source/rendition hashes, parser and raw/parsed/accepted/indexed counts. | Likhit. Required Apple/Microsoft and ten-company coverage reconciles to checked packages; unsupported layouts and duplicates remain visible. |
| R2 Index | Pinned BAAI/bge-base-en-v1.5, 768-D L2-normalized vectors, exact IndexFlatIP, canonical BM25/dense IDs. | Likhit. Deterministic build/reload, row identity, changed-model rejection and isolated per-filing replacement pass. |
| R3 Evidence | Checked HTML/Docling PDF extraction, original grids, headers/footnotes, cells, periods, raw/normalized units and source coordinates. | Likhit. Original facts pass; altered or ambiguous source/period/scale/unit/parent/position fails. Renditions do not duplicate facts. |
| R4 Generation | Real Ollama Gemma 3, initially 4B; digest, quantization and bounded settings fixed across A-G. Separate Llama 3.2 comparison. | Rushil. Current real success/failure and model identity evidence; no automatic mock/provider/model fallback. Use 12B only after measured readiness. |
| R5 Calculation | Restricted cited multi-step tree, typed predicates, bounded depth/size, exact result/rule trace; no generated Python or uncited constants. | Rushil. Valid operations succeed; wrong issuer/scope/period/unit, excluded operand, zero denominator and forbidden operations refuse. |
| R6 Interface | Gradio per-session filters/question/results, original sources/images, calculations, route/status/timings. | Gowtham. Two clients stay isolated; real accepted narrative/numerical/chart paths work; errors clear stale output. |
| R7 Evaluation | Full versioned loaders, eligible case inventory, frozen A-G runner/scoring, capacity gate and independent fifty-output audit. | Sudhansh design/runs, Pavan review accountability; one owner per dated artifact. Retain complete ledgers and independent evidence. |
| R8 Delivery | Written report, exactly six slides, contributions/AI-use/sources, real backup demo and single final archive. | Sudhansh report accountability; Shanay November 17 packaging/submission. Claims agree with saved evidence. |
| R10 Retrieval | Section orchestration, BM25/RRF60, hierarchy/cross-encoder, bounded routing, complete context and trace. | Pavan. Shared pre-top-k eligibility, enabled-stage success/failure evidence, zero queries for disabled streams. |
| R11 Charts | Original image/locator/hash, model description/unknowns, independently checked chart questions/captions. | Rushil captions, Likhit extraction; Ujjwal November 15 independent approval. Fifty candidates are neither fifty approved labels nor fifty images. |
| R12 Controls | Canonical A-G under common corpus/BGE/FAISS/model/prompt/calculator/random settings, five passages and one token budget. | Pavan. Frozen manifest and truthful included IDs; failed or missing stages cannot count as successful variants. |
| R13 Reproduction | CI, immutable manifests, real DVC restore, persisted MLflow records, restart and clean-machine checks. | Shanay, Ujjwal environment/contracts. Source/code/model identities and failures survive restart; Dockerfile alone is not deployment. |

R9 restatement comparison remains unscheduled Phase 2 in R9_PHASE2.md. A mismatch is not proof of restatement or fraud. No R9 work precedes this submission.

## Retrieval and complete context

Use identical explicit company, requested value period, source and supported-Item eligibility before both dense and BM25 top-k in every variant. Reject unsupported filters and isolate consecutive requests. Do not invent authoritative filters from an ambiguous question. Preserve component ranks, deterministic RRF k=60 ties, candidate restriction, reranker score type/model, route/stopping reason, selected/excluded IDs and budget.

E adds hierarchical restriction and real bge-reranker-base cross-encoding. F adds keyword plus bounded short-model routing and development-tuned escalation through declared text/table/chart tiers. Record maximum attempts, thresholds and missing facts; charts stay unavailable until G's independent acceptance. Missing/failed cross-encoder or invalid scores cannot become successful E/F/G answers.

Select complete evidence using one pinned tokenizer and fixed input budget, reserving prompt/instructions and output capacity. Generate from five valid passages, or fewer with recorded shortfall. Parent expansion, deduplication and charts obey the same controls. Derive actual prompt content, included IDs, citations and legal calculation operands from exactly that selection. An intermediate character cap is not final token-budget proof.

## Knowledge representation and safe inference

Typed facts bind issuer, filing, metric, statement, scope, period, raw value, currency/unit/scale, normalized value, parent and source. Deterministic predicates establish source/content integrity, comparability, actual included citations and admissible operations. Same-period operations require the same period; annual change requires the specified comparable annual periods and metric. Division requires nonzero denominator.

Positive prior permits ordinary percentage growth; zero prior refuses; negative prior yields absolute change and explanation unless a separately documented benchmark operation explicitly defines another policy. Retain premises, rule outcomes, expression, cited operands, exact result, units and rendering. The model may propose bounded expressions and explain validated results; it cannot insert authoritative request constraints, override failed rules or replace the exact numerical conclusion with prose.

## Controlled experiment

| Variant | Cumulative change | Isolation |
| --- | --- | --- |
| A | Fixed overlapping narrative chunks and flattened Markdown tables, dense only | Common accepted corpus, BGE/exact FAISS, generator, prompt, calculator and budget. |
| B | Section-aware narrative chunks | Same table representation and other controls as A. |
| C | Self-describing cells and parent expansion | Same underlying facts; no chart descriptions. |
| D | Dense/BM25 fusion with RRF60 | Save independent rankings; generator/budget unchanged. |
| E | Hierarchical candidates and cross-encoder | Distinct from explicit eligibility common to A-G. |
| F | Bounded routing and escalation | Tune on development only; chart tier unavailable. |
| G | Independently approved source-linked chart descriptions | Keep A-F chart-only failures in measured denominators. |

Freeze full case IDs, accessible splits, exclusions, source mappings and hashes before final runs. Pool declared FinQA test contexts into one retrieval index without answer/program leakage; declare TAT-QA/FinanceBench candidate universes. Public labels must follow access terms and cannot tune final answers. Alternate crops/renditions of one chart stay in one split. Fifteen development/thirty-five held-out chart questions are separate from fifty audited generated outputs.

Use one pinned Gemma configuration for primary A-G. A separately labelled Llama 3.2 secondary comparison uses the same frozen inputs and selected baseline/final configuration. Do not mix models within A-G or infer availability from a configuration file.

## Scoring audit and capacity

After currency/scale normalization, nonzero-gold numerical answers pass only at relative error at most 0.01 (1 percent). Wrong period/unit or unsupported answers fail even when numerically matching. Declare zero-gold absolute tolerance from source display precision and percentage versus percentage-point conventions. Report reviewed narrative rubrics or official exact match/F1 separately.

For every row report answer measures, Recall at 5 and 10, MRR, RAGAS faithfulness, median latency and 95 percent bootstrap intervals. Retrieval at 10 uses the pre-context ranking; multi-operand cases also report complete-evidence success. Save source-identity mappings and deduplication policy. Pin evaluator/model/prompt/settings; automated faithfulness is an estimate, not financial truth.

Predeclare a seeded stratified fifty-output sample across variants and question types before inspecting final scores. A reviewer cannot independently approve their own labels. Sudhansh audits non-self-authored cases November 16; Shanay handles remaining exclusions November 17. Record label authorship/reviewer, exact included context/original sources, unsupported claims, abstentions, disagreements and shortfalls.

Use paired question resampling, fixed seed and 10,000 bootstrap resamples; cluster shared documents/charts where feasible and state sampling unit. Preserve failures, timeouts, exclusions, undefined-metric reasons and per-dataset denominators. Fourteen smoke cases and component tests replace none of these commitments.

Capacity separates generation, extraction/captioning and RAGAS machine time. Multiply actual case/variant counts by measured seconds per case, include restart/error overhead, and compare with available machine hours through November 17. Human estimates are not machine capacity. Batch/cache/checkpoint without changing controls. If complete runs cannot fit, state exact unfinished scope immediately; no silent sample or omitted chart/audit may be called proposal completion.

## Remaining daily plan

TASK_REQUIREMENTS.md gives ordered steps and verification. Each block includes reading prior handoff, work, checks and a new handoff; failed dependencies stay explicit.

| Date | Sole owner | Estimate | Deliverable |
| --- | --- | --- | --- |
| November 12 | Pavan | 8 hours | Complete integration controls and experiment scaffold. |
| November 13 | Likhit | 10 hours | Expand supported corpus and build matched representations. |
| November 14 | Gowtham | 10 hours | Connect application benchmark runner and measured capacity. |
| November 15 | Ujjwal | 10 hours | Independently approve inputs freeze controls and launch full runs. |
| November 16 | Sudhansh | 10 hours | Audit outputs compute metrics and finalize report and slides. |
| November 17 | Shanay | 10 hours | Verify clean release finish independent exclusions and submit. |

Six remaining dates cannot give all seven members distinct future days. Rushil's earlier submitted model/math/chart work stays historical; no off-day duty is invented for apparent equality. These estimates are not equal actual effort. Earlier October 30 through November 2 hours remain separately preserved.

| Member | November 3 through 11 estimate | November 12 through 17 estimate | Combined estimate |
| --- | --- | --- | --- |
| Sudhansh Khandelwal | 8 hours | 10 hours | 18 hours |
| Agrawal Pavan Shailesh | 10 hours | 8 hours | 18 hours |
| B Rushil Mohan | 10 hours | 0 hours | 10 hours |
| Sri Sai Likhit Boddada | 20 hours | 10 hours | 30 hours |
| Ujjwal Chandak | 18 hours | 10 hours | 28 hours |
| Shanay Ghodasara | 8 hours | 10 hours | 18 hours |
| Muppidi Gowtham Sai | 8 hours | 10 hours | 18 hours |
| Total | 82 hours | 58 hours | 140 hours |

Likhit owns supported broader corpus and matched A/B/C representations on November 13. Gowtham owns full UI, benchmark loader/runner wiring, real model/cross-encoder access and measured capacity on November 14. Ujjwal owns independent input approval, freeze and complete run launch on November 15. Broader accepted corpus coverage must pass that audit or remain a mandatory shortfall. Preserve the accepted Apple package. Source/model assets, real cross-encoding, approved labels and benchmark outputs cannot be created by planning prose. November 17 packaging cannot substitute for unfinished jobs or missing independent outputs; no automatic post-deadline recovery is assigned.

## Final package and release decision

The report includes Introduction, Background and Related Work, Method, Results and Evaluation, Discussion and Limitations, Individual Contributions, AI Usage and the explicit Connection to Course Concepts. Include architecture, research question, frozen settings, actual tables/intervals, audit, errors, coverage and limitations.

Exactly six slides: title/team/repository/track/area; problem; related work; methods; results; management/work division. Demo narrative, numerical and chart paths, inspectable evidence and a meaningful failure; retain a real backup video/output route and reproducible commands. Verify files open, source/code/data/model/config/archive hashes agree, AI-use/contributions/sources are accurate, and submission acknowledgement is saved.

Call the release complete only when every mandatory gate has evidence. Otherwise submit an explicitly partial package naming unmet requirements and failed/unfinished cases. Passing tests do not prove universally error-free behavior. Hosting is optional and cannot replace a reproducible local application.

## Connection to Course Concepts

KR&R is typed facts, ontology, predicates and licensed inference, not metadata alone. Show why cited Apple 2021 sales 365,817 and cost 212,981 USD million permit margin 41.78 percent, and why wrong issuer/period/unit, excluded operand or zero denominator blocks a conclusion. DL uses pretrained BGE embeddings, cross-encoder pair scoring and Gemma; chart processing uses pretrained vision-language models with original-image grounding and unknown values. No training claim is made.

Safety means AI-use disclosure, source checking, explicit failures, uncertainty and no unsupported financial advice. BM25/RRF are information retrieval and routing is control logic; do not claim A star, minimax, game theory or multi-agent reasoning from them. Every meaningful change/review maps to an R requirement and A-G stage/control, names the accurate concept, verifies success/relevant failure, and leaves a concrete viva explanation.
