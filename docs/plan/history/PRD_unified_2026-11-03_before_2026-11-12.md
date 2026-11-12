# FinRAG unified product requirements

CV ++ Team 6 | CS F407 Artificial Intelligence | Application track | Consolidated 3 November 2026

Build the financial question answering system described in the submitted proposal, repair the gaps identified by the professor, and make every contribution verifiable in code, evaluation and the viva. This revision replaces the reduced one-report product scope and 14-question evaluation as the definition of the final submission.

The consolidation adopts the friend dependency gates and updated parser checkpoint while retaining full proposal scope, professor feedback and course alignment. Exactly one member is assigned per date. November 17 remains the internal release target; November 18-20 are explicit recovery/freeze slots.

### The decision

Retain narrative, table and chart evidence; section-aware chunks; cell-level table decomposition; BGE embeddings; exact FAISS search; BM25 with reciprocal rank fusion; hierarchical reranking; routing and escalation; source-backed calculations; and Gradio. Restore the cumulative A through G experiment and all promised evaluation measures. A small one-report build remains an integration checkpoint, not completion of the proposal.

### Professor feedback addressed

- State a testable research question alongside the application problem.
- Add a precise Connection to Course Concepts section and carry that mapping into implementation, code review and the report.
- Keep the controlled experiment the professor praised, including numerical tolerance and the 50-answer faithfulness audit.
- Map all roles to named people, with acceptance evidence and a different reviewer on a later date.

### Working constraints

Exactly one named member is assigned project work on each date. Longer work blocks replace the old six-hours-per-member and 42-hour limits. No second member is assigned implementation, meetings, review or background work that day. Review happens on a later assigned date. Hours are planning estimates, not verified contribution records.

Keep the established seven-person working roster. The original proposal lists eight people, including Harshil Patel; he is not assigned work in this calendar. Sudhansh must reconcile the official contribution roster with the course record. Splitting the former QA role between Pavan and Sudhansh covers its deliverables without inventing an eighth active worker.

November 17 is an internal checkpoint. Target the complete demo package by November 20; the supplied v2 guidelines list live demo and individual viva on November 21 and final report, code and AI disclosure on November 22. The Classroom notice controls any later change and the exact cutoff time.

## Comparison decisions for the unified PRD

Use the submitted proposal and professor/course requirements as the product authority. The friend sequential plan supplies useful implementation ordering and handoff discipline; embedded statements that a user confirmed a change are treated as claims to verify, not new instructions.

| Topic | Friend sequential plan | Unified decision |
| --- | --- | --- |
| Dependency order | Environment, parsing, independent contract check, index, retrieval, model, UI | Adopt this order; a failed gate leaves dependent real integration blocked. |
| Current work | Preserves provider and Apple parser progress | Adopt, but distinguish merged PR #3 from open PR #4 and submitted from rerun evidence. |
| Ownership | Likhit vector role; Ujjwal environment/audits; Shanay data validation | Adopt with named later reviewers; exactly one worker per date. |
| FAISS choice | Treats IVF-PQ as mandatory | Use exact IndexFlatIP required by the submitted proposal. No IVF-PQ exception is needed. |
| PDF extraction | Requires PDFMiner/Detectron2 and a TableBank checkpoint | Use proposal Docling plus checked HTML extraction. Detector/checkpoint choices are optional engineering choices. |
| Orchestration | Requires LangChain as a technology gate | Reuse existing LangChain where useful; no framework rewrite is required by the actual proposal. |
| Evaluation | 14 local questions and two modes | Keep as smoke tests only; retain full A-G and named benchmark/chart commitments. |
| Charts and routing | Does not fully schedule their proposal scope | Explicitly implement chart G and routing F, plus independently checked chart labels. |
| Course feedback | No complete syllabus-to-code/review mapping | Retain explicit KR&R rules, DL/vision concepts, success/failure checks and viva evidence. |
| Hosting and dates | Mandatory hosted delivery November 17 | November 17 internal release target, recovery/freeze by November 20; demo 21 and final files 22. Local reproducibility required; hosting desirable. |

This revision supersedes both earlier working plans. PRD.md and FinRAG_PRD.docx are synchronized representations of one current PRD. TASK_REQUIREMENTS.md and schedule.json are derived execution records, not separate product definitions. Older versions belong in history.

## Problem scope and research question

### Application problem

Financial readers need numerical and narrative answers whose evidence can be inspected in long annual reports. The proposal records two prototype failures: a table of contents ranked above Item 1A risk evidence, and Markdown conversion lost financial table headers. Preserve these as reproducible failure cases with the exact source, question, configuration and output; do not claim this revision reran them.

FinanceBench reported that GPT-4-Turbo with retrieval answered incorrectly or refused 81% of its evaluated questions [E1]. This is a historical result for that tested configuration, not a measurement of FinRAG or every current model. It motivates testing evidence representation and retrieval rather than promising a hallucination-free system.

### Testable question

With the corpus, embedder, answer model, prompt, calculator and final passage count held fixed, how does adding section-aware chunking, cell-level tables, hybrid retrieval, hierarchical reranking, routing and chart descriptions change evidence recall, answer accuracy, faithfulness and median latency compared with standard dense RAG?

Expected direction: structure-preserving table units and hybrid retrieval improve evidence coverage and numerical answer accuracy; reranking improves the final ordering; chart descriptions improve chart-only answerability. Treat these as hypotheses. Report negative or uncertain effects and latency costs. The cumulative experiment measures the incremental effect in this order, not every interaction or universal causal contribution.

### Corpus commitment

Application documents remain SEC Form 10-K annual reports. Focus on Item 7 MD&A, Item 8 financial statements, their footnotes and embedded charts; support Item 1A as the original risk-factor failure case. Start with five exact Apple and five exact Microsoft filings, then expand to ten technology-sector companies. Use at least one declared 10-K for each additional company; the proposal does not specify five filings for every company. Validate the claimed downloads rather than assuming they are parsed or indexed.

Benchmark contexts are separate reproducible evaluation corpora containing the documents or contexts the named benchmarks reference. Audit filing types and available provenance. A benchmark context is not evidence of support for that document type in the application. Publish incompatible or inaccessible cases and coverage counts; an eligible subset must be labelled as a subset and does not satisfy a full-suite claim.

### Scope boundary

Exclude live market data, investment advice, fine-tuning and unrelated agent or game features. Preserve the Application track. Course justification does not change an approved track or topic; any actual change of approved topic or track requires the IC sign-off specified in the v2 guidelines.

## Data indexing and model requirements

| ID and owner | Required behavior | Acceptance evidence |
| --- | --- | --- |
| R1 Corpus \| Likhit | Manifest exact application filings, benchmark sources and chart images. Store issuer, accession, filing date, fiscal period, type, URL, checksum, parser version and counts. | Five Apple plus five Microsoft filings and ten companies accounted for; failures and supported sections listed. |
| R2 Index \| Likhit | Use bge-base-en-v1.5, 768-dimensional L2-normalized embeddings and FAISS IndexFlatIP; keep BM25 and FAISS evidence IDs aligned. | Repeat ingest and restart preserve IDs, counts, source mapping and retrieval; changed models force a rebuild. |
| R3 Evidence \| Likhit | Parse EDGAR HTML with BeautifulSoup/pandas and PDFs with Docling. Preserve title, multirow headers, fiscal period, units and footnotes at cell level. Keep the original grid. | Hand-checked fixtures show parent links, negative values, scales, missing cells and comparative years; locators resolve. |
| R4 Generation \| Rushil | Use Gemma 3 through Ollama, initially 4B; use 12B only after memory/timing validation. Pin one choice for A-G; separate Llama 3.2 comparison. | Actual provider/model identifier, digest/quantization, hardware and success/failure traces saved; no automatic mock fallback. |
| R5 Calculation \| Rushil | Translate evidence-backed arithmetic into a restricted typed expression or operation tree, validate rules, execute in code and display the program. | Source-backed operands and multi-step benchmark operations pass reviewed fixtures; arbitrary Python cannot execute. |

### Migration rule

The existing MiniLM/Chroma prototype is a recovery aid and historical reference. It cannot be the final baseline if the enhanced system uses BGE/FAISS: that would change multiple factors. Rebuild A and B-G with the same pinned BGE model and index implementation. Do not reinterpret the proposal as an IVF-PQ requirement; its exact-search choice is explicit.

### Numerical execution

Allow only approved arithmetic operations required by the frozen task inventory, such as addition, subtraction, multiplication, division, sums and composed ratio or percentage calculations. Reject imports, function calls outside the allowlist, file/network access, unbounded expressions and uncited constants. Set expression size/depth limits. This tightens the proposal Python-expression step without changing its purpose: arithmetic runs in code and produces an inspectable trace.

## Retrieval charts and application requirements

### R10 Retrieval and routing

Pavan owns the orchestration, section-aware chunks, BM25 orchestration, fusion, reranking, routing and complete context selection; Likhit owns the index adapters and rank-to-ID contract; Ujjwal independently checks integrity. Dense and BM25 candidates share one eligibility policy. Fuse with reciprocal rank fusion using k=60 and deterministic tie-breaking. Preserve the component ranks and final score trace.

Hierarchical selection first restricts candidates by company, requested value period and supported Item, then applies bge-reranker-base and selects five evidence passages. A request without a known filter must not receive an invented one. Apply comparable explicit query filters in A-G; reserve the hierarchical candidate stage and cross-encoder change for E. Log candidate counts and discarded records.

Routing uses keyword rules plus a short model prompt to choose narrative, numerical or chart-based evidence. Escalate through the declared text, table and chart tiers when development-tuned relevance or requested metric/period coverage is inadequate. Cap attempts and record the route, threshold, missing facts and stopping reason. Scores are model-dependent relevance signals, not probabilities or admissible search heuristics.

Select complete evidence objects inside a fixed input budget. Derive prompt content and reported included IDs from exactly that selection. Parent expansion, deduplication and chart descriptions must obey the same budget; do not slice away a source after reporting it as included. Disabled streams issue no retrieval query.

### R11 Chart evidence

Rushil owns Gemma 3 chart captioning; Likhit owns image extraction and independently checked chart labels. Describe each chart title, axes, legend, series, periods, units and only legible values. Save image hash, report/page or HTML locator, model configuration and description. Mark unclear values as unknown. Link every description to the original image; never present a generated caption as issuer-authored text.

Create about 50 chart-only questions from eligible filings and cross-check every answer visually. Target 50, with 15 development and 35 held-out cases; record actual counts and distinct images. Avoid near-duplicate images crossing the split. If the corpus contains too few usable charts, record the shortfall as unmet proposal scope rather than substituting unrelated images.

### R6 Interface

Gowtham owns the Gradio workflow: supported company/report/period, question, answer status, source passages, table headers and cells, original chart, calculation, route trace and timings. Keep user inputs session-specific. Show invalid_request, index_not_ready, insufficient_evidence and service_error distinctly. A local reproducible demo is essential; a public host is an enhancement subject to measured readiness.

## Connection to course concepts

The strongest course connection is Knowledge Representation and Reasoning combined with Applications of Deep Learning. The course handout names predicate logic, ontology/categories, word embeddings, transformers and computer vision. Implement and explain the connection below instead of merely listing retrieval packages.

| Course topic | Concrete project behavior | Proof and viva question |
| --- | --- | --- |
| KR&R ontology and predicates \| T1 chapters 7-10 | Represent issuer, filing, period, statement, metric, unit, value, table cell and source as typed facts. Explicit rules check comparability and whether an operation is justified. | Show facts and a rule trace. Why is a 2023 consolidated USD-million value incompatible with a 2024 segment value? |
| KR&R inference | Infer that a requested calculation is allowed only when all required operands are cited, comparable and valid. Record rule failures and abstain. | A missing operand or zero denominator blocks the result. Which premises established the displayed result? |
| DL for NLP \| T1 chapter 25 | BGE embeds question and evidence; the cross-encoder jointly scores pairs; Gemma generates a grounded explanation. Use pretrained transformer models without fine-tuning. | Explain cosine retrieval versus cross-encoding, normalization and context limits. Save measured A-G outcomes. |
| Computer vision \| T1 chapter 27 | Use a pretrained vision-language model to convert report images into cited chart descriptions. | Compare the image with its caption and explain an unreadable-value failure. No claim of training a vision model. |
| Ethics and safety \| T1 chapter 28 | Disclose AI help, retain source provenance, expose uncertainty and provider failures, and avoid unsupported financial claims. | Show an abstention, an AI-use entry and source verification. |

Search and Problem Solving is a limited supporting analogy: evidence candidates, constrained selection and tier escalation define a search process, but BM25/RRF/nearest-neighbour retrieval are information-retrieval methods, not implementations of A*, CSP, minimax or a syllabus state-space algorithm. Agents and Game Theory is not a claimed implemented contribution; bounded routing alone is not multi-agent planning or equilibrium reasoning. No extra game or planner is added merely to name all four areas.

In the report, include the explicit section title Connection to Course Concepts. In every meaningful code review, name the applicable concept, point to its implementation, inspect one successful and one failing case, and record what the member must explain in the viva. An ordinary packaging change may say supporting engineering rather than forcing a false algorithm connection.

## Knowledge rules and evidence contracts

### Minimal executable reasoning

Implement the rules as deterministic typed Python predicates with recorded premises and outcomes. This is a small rule-based reasoning layer; do not claim a general theorem prover, resolution engine, knowledge graph database or probabilistic inference system.

- Value facts bind issuer, metric, period boundaries, statement, scope, currency, scale, normalized value and evidence ID.
- Comparable requires matching issuer, metric meaning, scope, currency and appropriate periods for the requested operation. A year-over-year comparison deliberately allows two specified periods; a same-period comparison requires the same one.
- Allowed division requires valid, cited operands and a nonzero denominator. Missing, ambiguous or incompatible facts cause an explicit rule failure.
- For ordinary growth, a positive prior value permits (current - prior) / prior times 100. A zero prior is undefined. For a negative prior, display absolute change and an explanation unless a separately documented benchmark operation explicitly defines another calculation.
- Conclusions retain operand IDs, rule IDs, normalized values, units, expression and result. The language model may explain a validated result but cannot override a failed rule.

| Record | Mandatory contents |
| --- | --- |
| Evidence | Stable ID; issuer and filing identity; type; section/page/HTML locator; source URL; content hash; parser version; readable content; parent ID. |
| Cell | Table title; row and column headers; raw value; metric; period boundaries; raw and normalized unit/currency/scale; footnote links; parent grid coordinates. |
| Retrieval trace | Eligible corpus/filter; dense and BM25 ranks; RRF and reranker scores with type; route/escalation; candidate IDs; selected IDs; expansions; budget. |
| Answer | Status; answer text; actual included IDs; resolvable citations; provider/model/configuration; operation tree and rule trace; warnings; timing. |
| Run | Code SHA; data/model/configuration hashes; variant A-G; question/split IDs; output; scores; failure code; hardware; timestamp; duration. |

### Reliability

Reject missing indexes, invalid requests and unusable evidence before financial generation. Provider errors cannot turn into successful mock answers. Separate test fixtures from real outputs; never log secrets. Data replacement must not delete unrelated filings. Preserve cited context exactly; list retrieved-but-excluded IDs separately.

## Controlled evaluation and ablation

R7 is co-owned by Sudhansh for experiment design and reproducible runs and Pavan for independent audits and interpretation. One person owns each dated deliverable. The old 14-case local set may be retained as a smoke test; it cannot replace the promised experiment.

| Variant | One cumulative change | Required isolation |
| --- | --- | --- |
| A | Fixed-size overlapping narrative chunks, flattened Markdown tables, dense retrieval only | Use common BGE, FAISS, answer model, prompt, calculator and passage count. |
| B | A plus section-aware narrative chunking | Keep table representation and retrieval stages otherwise as A. |
| C | B plus self-describing table cells and parent expansion | Same underlying source facts; no chart descriptions. |
| D | C plus BM25/dense fusion with RRF k=60 | Save independent rankings; do not change generator or final budget. |
| E | D plus hierarchical filtering and cross-encoder reranking | Record candidate restriction separately from explicit request filters. |
| F | E plus query routing and bounded tier escalation | Freeze thresholds on development data; chart tier unavailable until G. |
| G | F plus chart descriptions linked to original images | Chart-only failures in A-F remain in the measured results. |

### Matched conditions

Recompute accuracy, retrieval Recall@5 and @10, MRR, RAGAS faithfulness and median latency for every row. Generate from five final passages under one fixed token limit; retrieval @10 uses the pre-context ranked list. When fewer than five valid passages exist, use only those available and record the shortfall. No padding with unsupported evidence. Keep model, prompt, calculator, corpus version and random settings identical within the comparison.

A-G is the primary Gemma 3 comparison. A Llama 3.2 comparison is a separately labelled secondary experiment using the same frozen inputs and selected baseline/final configuration. Do not combine its outputs with A-G. Pin the actual model sizes, revisions and quantization only after the hardware check.

### Benchmark protocol

Create versioned loaders for FinQA, TAT-QA and the FinanceBench open sample of 150 questions. FinQA evaluation pools the declared test contexts into one retrieval index, without answer/program leakage. For TAT-QA and FinanceBench, declare the candidate universe and source mapping. Separate benchmark splits from local development questions; use public labels only where permitted. Do not train or tune on final answers.

Freeze complete eligible case IDs, exclusions, splits, source hashes and scoring before final runs. Where official labels or original locators are unavailable, report that limitation and use a clearly named accessible split; never claim an inaccessible official test was evaluated.

## Scoring faithfulness and runtime gates

### Answer and retrieval scoring

After currency/scale normalization, numerical answers with nonzero gold value pass when absolute(predicted - gold) / absolute(gold) is at most 0.01. For a zero gold value, use a separately declared absolute tolerance derived from source display precision; do not divide by zero or silently replace 1% with a broad epsilon. State percentage versus percentage-point conventions and sign rules. Incorrect periods, units or unsupported answers fail even if the number happens to match.

Use reviewed narrative rubrics or official exact match/F1 where appropriate and report them separately from numerical accuracy. Map every gold span, cell or chart to stable source identities. Evidence Recall@k is recovered required gold evidence divided by required gold evidence; also report complete-evidence success for multi-operand questions. MRR uses the first relevant evidence unit. Publish the mapping and deduplication policy so cell and chunk variants remain comparable.

### Faithfulness audit

Run RAGAS with pinned evaluator, prompt and settings. Treat it as an automated estimate, not financial truth. Before reading final scores, fix a seed and a stratified sample of 50 answer outputs covering A-G and narrative, table, numerical and chart questions. Record variant and question IDs; these 50 answers are separate from the 50 chart-only questions.

Likhit begins the non-self-authored-label portion on November 15 against exact included context and original sources. Pavan completes any self-authored-label exclusions and remaining cases on November 19, then reviews disagreements and high-risk numerical cases. No person independently validates their own labels. The combined audit contains 50 outputs; the schedule makes these reviews sequential. Save human labels, automated scores, unsupported claims, abstentions and disagreements; count failed calls separately rather than dropping them.

### Uncertainty and failures

Report 95% bootstrap confidence intervals for accuracy, recall, MRR, faithfulness and median latency, plus paired A-to-G or adjacent-row differences. Resample the same questions for every variant. Use a fixed seed and 10000 resamples; cluster by shared document or chart where feasible and state the unit. Give per-dataset counts, exclusions and denominators. Small or related samples support limited conclusions. Retain failures and timeouts; undefined metrics show the reason and count.

### Capacity gate before full evaluation

On November 3, record a preliminary resource check; by November 10, time a representative pilot on the intended hardware and estimate model and RAGAS work separately. Expected machine hours are the sum of case count times variants times observed seconds per case divided by 3600, plus extraction, captioning and evaluator overhead. Compare this with actual available machine hours through November 20, not human work hours. Save costs, memory, restart/checkpoint behavior and the uncertainty margin.

If the full promised runs or chart coverage will not fit, record unmet scope immediately. Use batching, cached immutable embeddings/captions and resumable execution without changing experimental conditions. A sampled interim table must remain labelled interim. Reducing the final commitment requires an explicit team scope decision and any required instructor approval; do not quietly replace the full plan with 14 local questions.

## Named ownership and stack decisions

Each module has one primary owner. A reviewer checks it on the reviewer own later scheduled workday. Ownership does not require two people to work together or prove actual effort. A handoff contains code revision, verified behavior, unresolved gaps, inputs and restart instructions.

| Member and student ID | Primary accountability | Later reviewer |
| --- | --- | --- |
| Sudhansh Khandelwal<br>2024AAPS0255H | Coordination, integration, experiment design, report and submission | Pavan |
| Agrawal Pavan Shailesh<br>2024A3PS0399H | Retrieval orchestration, BM25/RRF, reranking, routing and QA audit | Ujjwal |
| B Rushil Mohan<br>2024AAPS0235H | Ollama generation, safe calculations, chart captions and regressions | Pavan |
| Sri Sai Likhit Boddada<br>2024A1PS0838H | Parsing, cell/chart sources, BGE/FAISS, methods and manual output audit | Shanay and Ujjwal |
| Ujjwal Chandak<br>2024A3PS0379H | Environment/data contracts, label/index audits, evaluation integrity and slides | Shanay |
| Shanay Ghodasara<br>2024AAPS0244H | CI, DVC, MLflow, packaging, environment and clean-machine verification | Sudhansh |
| Muppidi Gowtham Sai<br>2024AAPS0207H | Gradio, evidence and image display, demonstration and usability checks | Shanay |

### How the friend advice is used

Adopt Rushil for Ollama, Likhit for PDF/table extraction, Shanay for reproducibility and operations, Gowtham for Gradio, and Sudhansh for coordination. Pavan leads retrieval and QA review; Sudhansh leads release accountability. Adopt Likhit as primary BGE/FAISS owner alongside parsing, as clarified in the sequential plan. Ujjwal owns environment/data contracts and independent label/index audits. Pavan retains retrieval orchestration, fusion, reranking and routing.

### Tools are means to the proposal deliverables

Use Python, BeautifulSoup/pandas, Docling, BGE, FAISS IndexFlatIP, BM25/RRF, bge-reranker-base, Ollama/Gemma 3 and Gradio. Retain the current test/lint workflow where sound. Restore DVC data/index manifests and MLflow run tracking as promised; local tracking is enough if reproducible. GitHub Actions checks reviewed code. Hosting is desirable for the demo, but does not replace a clean local release.

Do not add Detectron2, IVF-PQ, a new orchestration framework, fine-tuning or cloud complexity just because the strategy document names them. Record actual installed versions and APIs during implementation; planning is not evidence that model files, hardware or services are available.

## Daily schedule with one assigned member

The historical October 30 through November 2 assignments and evidence remain unchanged. The replacement execution calendar starts November 3. These blocks include reading, implementation, checks and handoff. They are demanding estimates; each owner records actual effort and unfinished work rather than claiming the scheduled hours were completed.

| Date | Sole owner | Hours | Deliverable |
| --- | --- | --- | --- |
| 11-03 | Ujjwal | 8 | Verify environment resources and handoff contracts |
| 11-04 | Likhit | 10 | Extend verified parsing to cells PDFs and chart sources |
| 11-05 | Shanay | 8 | Independently validate canonical data and restore behavior |
| 11-06 | Likhit | 10 | Build BGE exact FAISS and corpus coverage |
| 11-07 | Pavan | 10 | Implement cumulative retrieval stages and routing |
| 11-08 | Rushil | 10 | Integrate real models calculations and chart descriptions |
| 11-09 | Gowtham | 8 | Connect the full interface and measure real throughput |
| 11-10 | Sudhansh | 8 | Define full evaluation research question and capacity gate |
| 11-11 | Ujjwal | 10 | Independently check labels and development runs |
| 11-12 | Pavan | 8 | Fix development defects and freeze A through G |
| 11-13 | Gowtham | 10 | Run full evaluation and capture the demo |
| 11-14 | Shanay | 10 | Verify clean setup tracking and deployment readiness |
| 11-15 | Likhit | 8 | Write methods and begin the fifty-output audit |
| 11-16 | Ujjwal | 8 | Audit results and prepare the six-slide release candidate |
| 11-17 | Sudhansh | 8 | Review the internal proposal release target |
| 11-18 | Rushil | 8 | Use the recovery slot for numerical and chart defects |
| 11-19 | Pavan | 8 | Finish the independent audit and release review |
| 11-20 | Sudhansh | 8 | Freeze the single final package |

Total planned execution capacity from November 3 through 20 is 158 person-hours across 18 dates. Planned totals: Gowtham 18 hours; Likhit 28 hours; Pavan 26 hours; Rushil 18 hours; Shanay 18 hours; Sudhansh 24 hours; Ujjwal 26 hours. These totals intentionally replace the earlier equal six-hour allocations; they are not a claim of equal actual contributions.

Detailed steps, dependencies, requirement IDs, completion checks and course concepts are in TASK_REQUIREMENTS.md. Only the sole owner handles bounded prerequisite repairs or hands an unresolved dependency to a later dated slot.

## Next steps and feasibility decisions

### Start with the actual handoff

GitHub was inspected for this consolidation. Main at 6f9f236 contains Rushil provider/failure-boundary work from PR #3. Parser PR #4 at 384beea remains open and unmerged; its handoff reports 316 narrative records and three parent statements for Apple 2021, with 79 local tests. Those are submitted implementation/verification records, not independently rerun results here. Preserve the parser contribution and review the exact PR revision before reuse; parsing does not establish indexing, normalized cells, charts or final app readiness.

- November 3-6: validate environment and completed parser input, add source-checked cells/PDFs, independently freeze canonical records, then build BGE/FAISS.
- November 7-9: integrate A-G retrieval, safe typed calculations, real model/chart descriptions and the source-linked interface.
- November 10-12: quantify complete evaluation time, independently verify labels, resolve development defects and freeze every experimental control.
- November 13-16: execute/checkpoint the full experiment, verify clean setup, audit outputs, draft results and prepare the six required slides.
- November 17: inspect the full requirement ledger and freeze a release candidate only if its gates pass. Use November 18-20 recovery slots for recorded defects/audit completion and final package freeze.

### Risk decisions

Unattended deterministic jobs may continue on a reserved machine across dates; only the member assigned to the current date actively monitors, changes or validates them. Automated completion alone does not establish correctness.

The full proposal is materially larger than the former 42-hour build. The execution estimate is a provisional planning envelope, not proof that every full benchmark and model comparison fits. Reserve November 18-20 for recovery and final freeze; aim for an internal release candidate November 17. Ten-hour blocks are difficult alongside coursework. Track remaining tasks and time after every handoff; do not add unrelated features or treat a capacity warning as authorization to omit the proposal.

If a source, model, parser layout or benchmark label is unavailable, save the specific failure and affected counts. Keep the working narrative/table path demonstrable while the missing proposal feature stays open. If demo-critical work is late, the team must explicitly choose a recovery change; removing charts, BM25, full evaluation or the faithfulness audit is a scope change, not routine cleanup.

### R9 remains a separate extension

Preserve the existing Phase 2 cross-report restatement specification. It compares the same issuer/metric/period/scope across two exact filings, keeps raw and normalized values, and distinguishes unchanged, potential_revision, confirmed_restatement, disclosed_reclassification, disclosed_recast, incomparable and insufficient_evidence. A confirmed label requires a cited issuer disclosure; a number mismatch alone cannot establish a restatement or fraud.

Retain versioned filings, both operand citations, precision-based tolerances and at least eight independently checked cases, including one real disclosed restatement. No R9 work is assigned before the original proposal release. Its separate estimate, owners and dates must be recorded before implementation. The previous detailed R9 text is preserved in R9_PHASE2.md.

## Delivery course rubric and review rules

### R8 Required final package

Deliver the written report with Introduction, Background/Related Work, Method, Results/Evaluation, Discussion and Limitations, Individual Contributions and AI Usage. Include the explicit course connection and testable question, architecture, frozen A-G settings, actual metric tables, confidence intervals, manual audit, errors and limits. The repository must include run/rebuild instructions, data manifests, dependency versions, tests, result artifacts and steady contribution history.

Prepare exactly six presentation slides: 1 Title with team name/number, project name, repository, track and relevant area; 2 Problem Statement; 3 Related Work; 4 Methods; 5 Results; 6 Project management and work division. Include a live narrative, numerical and chart example, one evidence inspection and a clear failure case in the demonstration. Save a backup video and reproducible outputs.

| Course milestone | Project action | Scheduling rule |
| --- | --- | --- |
| November 17 internal checkpoint | Record requirement and experiment status | Sudhansh is sole assigned worker; this is not the official cutoff. |
| November 20 package freeze | Finish complete demo/report/results archive | Sudhansh is sole assigned worker. |
| November 21 live demo and viva | Gowtham handles demo setup and delivery | Every member must answer their own official viva. Assessment attendance is unavoidable and is not a second development assignment. |
| November 22 final files | Sudhansh submits/checks final report, code and AI disclosure | Verify Classroom cutoff and save receipt; no new feature work. |

The one-worker rule governs assigned project work; it cannot waive the course requirement for individual viva attendance on the scheduled assessment date. Module handoffs include viva explanations ahead of time; no additional same-day team rehearsal is assigned.

### R12 and R13 Review and accountability

Final rubric: report technical correctness 5, track-specific quality 5, live demo 15, Q&A 5, GitHub code 5 and process/accountability 5 marks. Align review priorities with a working, defensible application, not only lint or test counts. Retain dated code/evidence, actual contribution records, AI tools/purpose/verification and licence/source acknowledgments.

Every review identifies requirement and A-G variant, exact reviewed revision, observed issue and consequence, applicable syllabus concept, success/failure evidence, smallest repair and a viva question. Distinguish merged, PR-only, local-only and unverified work. A reviewer must not infer understanding or effort from commit counts. Preserve source integrity, arithmetic and experimental controls as release checks.

AGENTS.md, task requirements, schedule, evidence contract, review template and implementation prompt use this unified revision. GitHub publication has a dedicated planning commit; implementation PRs remain separate. Historical reviews and state are retained. Editing these files does not reconfigure the external review scheduler.

## Daily requirements 2026-11-03 to 2026-11-05

### 2026-11-03 Ujjwal 8 planned hours

Verify environment resources and handoff contracts. Requirements R2 R4 R13.

Read current main and parser PR #4 at its exact revision; preserve completed setup/provider/parser work. Check BGE, exact FAISS, Docling, Ollama/Gemma, memory and machine access. Pin the canonical record/parent-table and index-sidecar contracts. Set up local DVC and MLflow with one restore/log smoke check and retain existing Ruff/pytest CI. Estimate full evaluation machine time from a small representative pilot or explicitly mark missing inputs.

Completion gate: Environment/resource inventory, input revision, canonical schema, successful DVC restore and MLflow smoke run exist. No model, parser or full-data readiness is inferred from installation alone.

Course connection: Reproducible AI and typed evidence contracts. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-04 Likhit 10 planned hours

Extend verified parsing to cells PDFs and chart sources. Requirements R1 R3 R11.

Consume the tested Apple 2021 HTML parser rather than rebuilding its completed work. Add self-describing table cells and parent grids with raw/normalized units, periods, footnotes and source coordinates. Add Docling PDF extraction on checked fixtures and original chart image locators. Expand the initial Apple/Microsoft manifest and record unsupported layouts and chart availability. Distinguish HTML/PDF renditions and avoid duplicate fact ingestion.

Completion gate: Checked HTML/PDF cell fixtures, full parent tables, image/source manifests and deterministic records have resolvable provenance. Existing 316 narratives and three parent tables remain a preserved starting artifact, not final corpus coverage.

Course connection: KR ontology and grounded chart evidence. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-05 Shanay 8 planned hours

Independently validate canonical data and restore behavior. Requirements R2 R3 R13.

Check representative source facts, periods, scales, parent links and deterministic IDs from the prior package. Validate row-to-ID mappings, metadata sidecars and a clean DVC restore with equal hashes. Retain any existing Chroma/MiniLM regression artifacts separately. Pin environment/configuration and validate storage replacement rules before the BGE/FAISS build.

Completion gate: One canonical data package and restore log reproduce the same IDs, hashes and counts; malformed or mismatched metadata fails. This is input validation, not a claim that FAISS is complete.

Course connection: Knowledge representation integrity and reproducibility. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

## Daily requirements 2026-11-06 to 2026-11-08

### 2026-11-06 Likhit 10 planned hours

Build BGE exact FAISS and corpus coverage. Requirements R1 R2.

Use bge-base-en-v1.5 with pinned preprocessing/revision and normalized 768-dimensional vectors. Build exact IndexFlatIP with stable evidence/metadata mapping, separate parent-table storage and compatible manifests. Verify duplicate IDs, dimensions, filtered results, stale-record cleanup, rebuild and reload. Continue corpus expansion toward five Apple/five Microsoft filings and ten technology companies; show actual parsed/indexed counts and failures.

Completion gate: Checked narrative and cell retrieval survive restart and identical reruns. Source/index hashes and required company/filing coverage reconcile. IVF-PQ is not a release requirement.

Course connection: Transformer embeddings and source identity. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-07 Pavan 10 planned hours

Implement cumulative retrieval stages and routing. Requirements R3 R10 R12.

Use the frozen record/index interfaces. Implement A-F flags for section chunks, table cells/parent expansion, BM25 and RRF k=60, eligibility and bge-reranker-base, and bounded narrative/numerical/chart routing. Keep the chart tier unavailable until descriptions exist. Preserve component ranks, IDs and complete evidence under the common budget. Use existing LangChain where it participates usefully; do not require a framework rewrite.

Completion gate: A-F traces isolate each stage; exact-term, semantic, TOC, no-result, missing-metric and context-budget cases pass with preserved IDs. Disabled streams issue no query.

Course connection: DL cross-encoding with explicit reasoning preconditions. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-08 Rushil 10 planned hours

Integrate real models calculations and chart descriptions. Requirements R4 R5 R11 R12.

Reuse merged provider boundaries and pin a real Gemma 3/Ollama configuration. Implement restricted multi-step arithmetic with cited operands and typed period/unit/comparability rules. Produce source-linked chart descriptions, unknown-value handling and a candidate 50-question chart set with 15 development and 35 held-out items grouped by image. Record the separate Llama comparison configuration and remaining hardware limits.

Completion gate: Real model and failure traces, safe calculation/rule fixtures, linked chart captions and candidate chart questions exist. No arbitrary generated Python executes, and unreadable chart values stay unknown.

Course connection: KR predicates and inference plus NLP and vision transformers. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

## Daily requirements 2026-11-09 to 2026-11-11

### 2026-11-09 Gowtham 8 planned hours

Connect the full interface and measure real throughput. Requirements R4 R6 R11.

Connect Gradio to real narrative/cell/chart retrieval, calculations, route traces and source links. Check session isolation and explicit invalid/not-ready/no-evidence/service-error states. Run separate development smoke cases. Measure actual model, extraction/caption and evaluator throughput on intended hardware; pass the measurements to Sudhansh for the full-run estimate.

Completion gate: A notebook-free question-to-source walkthrough works for narrative, numerical and chart evidence with honest failures; real timing and memory evidence are saved.

Course connection: Explainable application behavior and measurement. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-10 Sudhansh 8 planned hours

Define full evaluation research question and capacity gate. Requirements R7 R8 R12.

Build versioned FinQA, TAT-QA and FinanceBench loaders and A-G runner with source-equivalent evidence mappings, no label leakage and all promised metrics. Freeze dataset eligibility and proposed splits; preserve 14 local cases only as smoke tests. Consolidate chart labels, research question, report/course sections and role records. Estimate full machine hours using actual case counts and measured generation/RAGAS throughput.

Completion gate: Case inventory, scoring/split protocol, audit sampling rule, report outline and quantified full-run capacity decision exist. Slow or inaccessible suites remain explicit scope risks rather than being replaced silently.

Course connection: Experimental controls and course-linked hypotheses. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-11 Ujjwal 10 planned hours

Independently check labels and development runs. Requirements R1 R2 R7 R11.

Verify chart questions and labels against images, benchmark evidence mappings, units/periods and duplicate-source split leakage. Check Likhit index integrity and source coverage. Run development cases only, log outputs and identify parser/retrieval/model/math defects. Require 50 checked chart cases or declare the exact shortfall before freeze.

Completion gate: Independently checked gold/source manifests, unchanged splits, development results and concrete defect reproductions exist. No held-out answer is used for tuning.

Course connection: Label validity and representation checks. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

## Daily requirements 2026-11-12 to 2026-11-14

### 2026-11-12 Pavan 8 planned hours

Fix development defects and freeze A through G. Requirements R3 R7 R10 R12.

Repair bounded development defects and finalize route thresholds using development data only. Verify chart G integration, complete-context IDs and calculator rule failures. Lock A-G and shared BGE/model/prompt/calculator/five-passage/token settings; freeze the full evaluation list and stratified 50-output manual audit selection rule. Save integration and course review evidence.

Completion gate: One frozen experiment manifest, reviewed rule/context behavior and reproducible run commands exist. An unresolved mandatory gate stays open; no fake dependency artifact is substituted.

Course connection: Controlled ablation and reasoning verification. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-13 Gowtham 10 planned hours

Run full evaluation and capture the demo. Requirements R6 R7 R11 R13.

Execute or checkpoint all frozen A-G runs over the named benchmark corpora and chart split, plus the separate Llama comparison. Save rankings, selected context, statuses, answers, score inputs, timings and failures. Capture a real source-linked backup demo. Keep the legacy 14-case smoke output separate from the final experiment.

Completion gate: The full case-variant ledger accounts for completed, failed and running cases, with resumable artifacts and measured outputs. No short interim run is called the completed proposal experiment.

Course connection: Reproducible AI evaluation. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-14 Shanay 10 planned hours

Verify clean setup tracking and deployment readiness. Requirements R2 R6 R8 R13.

Restore the frozen data/index, rebuild or reopen on a clean environment, verify CI and DVC/MLflow records, and check real model/network access. Prepare a Docker/hosting route only if resources permit, using smoke cases separate from held-out data. Save hosting success or failure honestly; the reproducible local demo remains required. Continue immutable evaluation jobs if needed without changing their settings.

Completion gate: Clean-machine logs, pinned environment, source/model/index/run identities and a usable local release route exist. Any hosted URL has actual pipeline checks; a Dockerfile alone is not deployment proof.

Course connection: Supporting engineering for reproducible AI. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

## Daily requirements 2026-11-15 to 2026-11-17

### 2026-11-15 Likhit 8 planned hours

Write methods and begin the fifty-output audit. Requirements R3 R7 R8 R11.

Write source, parsing, indexing, chart and method sections from saved evidence. Audit the preselected 50 outputs against included context and original sources using gold labels you did not author; defer any self-authored-label cases to Pavan November 19. Compare with RAGAS and classify unsupported claims, numerical errors and abstentions. Keep incomplete benchmark runs explicit.

Completion gate: Evidence-based method draft, independently audited output records, unresolved case IDs and disagreement log exist; authored labels are not self-certified.

Course connection: Source-grounded reasoning and faithfulness. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-16 Ujjwal 8 planned hours

Audit results and prepare the six-slide release candidate. Requirements R7 R8 R12 R13.

Recompute sampled scores and paired bootstrap intervals from the frozen outputs; verify failure denominators, source coverage and configuration equality. Review data/index evidence and report claims. Prepare exactly six slides in guideline order, contribution/viva notes and a release inventory with archive hashes. Record any incomplete audit or evaluation for the checkpoint.

Completion gate: Independent metric checks, results draft, six slides and release-candidate inventory agree with actual evidence; unfinished requirements remain visible.

Course connection: Measurement uncertainty and defensible AI results. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-17 Sudhansh 8 planned hours

Review the internal proposal release target. Requirements R7 R8 R12 R13.

Compare every requirement with implementation, full-run/audit status and the course rubric. Review reproducibility and the report, source references, seven-member contributions and AI disclosure. Freeze a release candidate if all gates pass; otherwise record remaining work and use only the dated recovery slots. The official demo/submission dates remain November 21/22.

Completion gate: Internal checkpoint states complete/partial/unmet requirements, exact revision, remaining machine hours and release risks. November 17 is a target, not permission to label incomplete work complete.

Course connection: Hypothesis assessment and accountability. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

## Daily requirements 2026-11-18 to 2026-11-20

### 2026-11-18 Rushil 8 planned hours

Use the recovery slot for numerical and chart defects. Requirements R4 R5 R7 R11.

Resolve reproducible critical defects from the checkpoint within this slot, or verify final provider, calculator and chart regressions if none remain. Preserve the frozen experiment when possible. Any output-affecting change gets a new version and affected A-G reruns, with held-out reuse disclosed; no new feature scope is added.

Completion gate: Critical fixes have reproductions and regression evidence, or a verified unchanged release trace exists. Updated outputs are versioned honestly.

Course connection: Reasoning and model failure analysis. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-19 Pavan 8 planned hours

Finish the independent audit and release review. Requirements R7 R8 R10 R12.

Complete any remaining manual audit cases whose labels Likhit authored so the combined independent audit reaches 50 outputs. Review high-risk disagreements and sampled metrics, retrieval/context regressions and report/course claims. Check Rushil recovery changes on this later date and reconcile all result versions.

Completion gate: Fifty independent audit outputs, disagreement analysis and final course/release review exist, with any unmet commitments explicitly recorded.

Course connection: Independent reasoning and experimental review. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

### 2026-11-20 Sudhansh 8 planned hours

Freeze the single final package. Requirements R6 R8 R13.

Finalize the unified report, exact six slides, results/audit files, contribution and AI-use sections, run instructions and backup demonstration. Verify source/code/configuration/archive hashes and submission access. Freeze the complete demo package and name any unmet requirement; do not assign another member same-day work.

Completion gate: One frozen runnable archive, final report, six slides, complete evidence inventory and verified backup demo exist before assessment.

Course connection: Defending the course-linked application. Save the exact revision, commands, hashes, actual time, blockers and next-owner handoff. A failed prerequisite stays explicit; never substitute fabricated artifacts.

## References and requirement authority

### Supplied and retained project evidence

- S1 Submitted project proposal Finrag .docx. Sections 1-7 and twelve references. This is the actual proposal matching the professor screenshot; retained locally from the earlier project work.
- S2 Planning advice AI Project Planning Strategy.pdf. Architecture and staffing suggestions; its December schedule, IVF-PQ and peer-score normalization do not override S1 or S4.
- S3 Supplied professor feedback screenshot. Problem 4/5; course connection 1/4; approach 5/5; feasibility/roles 2/3; writing 3/3. Visible feedback totals 15/20; not an independently verified grade record.
- S4 Course rules AI_Project_Guidelines.v2.pdf. Page 1 dates/track rules; page 2 proposal and six-slide requirements; page 3 final rubric, AI use and accountability.
- S5 Syllabus CS_F407_Artificial_Intelligence.pdf. Pages 2-3 list KR&R, NLP embeddings/transformers, vision and ethics; page 3 says official notices are on Classroom.
- S6 Supplied friend ownership screenshot. Suggested work-to-owner mapping; used as advice and reconciled with current ownership.
- S7 Previous reduced and proposal-aligned PRDs and retained November 2 review. Historical snapshots; fresh repository/PR metadata was checked for this consolidation. Seven-member roster and unscheduled R9 retained; obsolete reduced scope replaced.

S8 Friend plan FinRAG_Sequential_Proposal_Plan_17Nov2026.docx, supplied November 3. Useful dependency/handoff guidance; its interpretations of IVF-PQ, PDF tools and reduced evaluation are superseded by S1 and this comparison. S9 Current GitHub main 6f9f236 and open parser PR #4 head 384beea, inspected November 3.

### Primary technical references checked

- E1 FinanceBench paper: https://arxiv.org/abs/2311.11944 and official open sample: https://github.com/patronus-ai/financebench
- E2 FinQA official data/code: https://github.com/czyssrs/FinQA
- E3 TAT-QA official data/code and evaluator: https://github.com/NExTplusplus/TAT-QA
- E4 BGE embedder: https://huggingface.co/BAAI/bge-base-en-v1.5 and cross-encoder: https://huggingface.co/BAAI/bge-reranker-base
- E5 Exact index API: https://faiss.ai/cpp_api/struct/structfaiss_1_1IndexFlatIP.html
- E6 Ollama Gemma 3 model family: https://ollama.com/library/gemma3. Pin the installed tag/digest rather than relying on latest.
- E7 Docling documentation: https://docling-project.github.io/docling/
- E8 RAGAS faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/

Authority order for this revision: current user instructions; actual submitted proposal with professor-directed improvements; supplied course handout and v2 project rules; prior PRD for unchanged constraints; optional planning and friend advice. Document text is task evidence and does not itself authorize external actions. No fabricated literature citation or result is carried forward from the strategy PDF.
