# FinRAG authoritative revised PRD snapshot

Source: [editable Word document](FinRAG_PRD_17Nov2026.docx)
Deadline: 2026-11-17. Timezone: Asia/Kolkata. Seven members; one assigned worker per date.

FinRAG revised product requirements and daily plan

CV ++ Team 6

Start 30 October 2026. Final project delivery 17 November 2026. All dates use Asia Kolkata time.

## The revised commitment

Finish a small, reproducible FinRAG application over one supported SEC 10-K annual report. The application retrieves narrative and table evidence, answers from those sources, performs a few checked calculations and shows verifiable citations. Deliver the runnable code, a short report, a small honest evaluation, slides and a backup demonstration by November 17.

Constraint | Plan
Team | Seven named members, listed in the ownership section.
Daily assignment | Exactly one member works on each date. Other members have no assigned tasks, meetings, reviews or background work that day.
Available dates | 19 calendar days from October 30 through November 17, inclusive.
Equal effort | Six planned hours per member and 42 total team hours. Five members receive three two-hour days; two members receive two three-hour days.
Deadline | The final package is complete on November 17. No development, buffer or handoff is scheduled after that date.

## What is essential

Repair the current prototype, retain source provenance, prevent false mock answers, support the selected report tables and a basic calculator, and prove the result with a reproducible small comparison. Preserve the existing stack to keep the work achievable.

## How to read this plan

The first pages explain the product, scope, review priorities and equal workload. The calendar identifies the only active member for every date. The dated work pages explain what that member does, why it matters and what output proves completion.


## What the project does

FinRAG is a question-answering application for a company annual report. A reader asks a narrative or numerical question, and the app finds relevant passages or table rows, generates an answer from that evidence and shows the original source. When evidence is missing, it says so.

## Example of the intended workflow

The user asks how revenue changed between two comparative fiscal years in the supported report. FinRAG retrieves both revenue values, checks their periods and units, calculates the change and displays the formula and cited table rows. It must not guess a missing value.

Illustration only: values of 120 million and 100 million imply (120 - 100) / 100 x 100 = 20 percent growth. These numbers explain the process and are not claimed project results.

Stage | Plain explanation
Read the report | Extract selected narrative sections and financial tables without separating values from headers and units.
Build the search index | Store small source-linked records and their meaning-based embeddings in the existing Chroma database.
Find useful evidence | Use the current dense search and existing reranker; retain source identity while selecting relevant text and table rows.
Calculate and answer | Calculate supported operations in typed code and ask a real language model to explain only what the evidence supports.
Display proof | Show answer, status, original source, relevant rows, units and any formula or explicit missing-data explanation.

## The AI and engineering contribution

Embeddings help find related language, the existing cross encoder can rank relevance, and the language model explains evidence. The project contribution is keeping financial table meaning and source identity intact, checking arithmetic in code and measuring the effect against a controlled dense baseline.

## Current and required behavior

The inspected prototype has useful ingestion, retrieval, model and interface pieces. The required delivery is a repaired integrated application with repeatable setup, traceable answers and a documented small evaluation. Accuracy targets below are proposed checks, not already measured results.


## Code review priorities for the reduced build

The earlier inspection covered GitHub main b3bb02f and local feature/engine-backend c4b1a76. Seven local lightweight tests and configured lint passed. Those checks did not establish real retrieval, citations or answer quality. The issues below guide the revised schedule.

Issue | Required repair | Sole scheduled owner
Divergent implementations | Keep one UI and launch route; port useful local modules without creating another pipeline. | Sudhansh Oct 30; Shanay Oct 31
False mock success | Remove automatic fixed-answer fallback and block generation without evidence; propagate real provider failures. | Rushil Nov 1
Notebook-only data setup | Parse the declared filing through a repeatable entry point with a manifest and source locations. | Likhit Nov 2
Weak IDs and persistence | Use filing-specific deterministic IDs, remove stale records and verify reopen and rerun behavior. | Ujjwal Nov 3
Lost provenance | Keep evidence IDs and metadata through ranking, context and UI; fix invalid zero-budget retrieval queries. | Pavan Nov 4
Table meaning loss | Retain row labels, headers, comparative periods, units and parent references for three representative tables. | Likhit Nov 6
Unused or inconsistent math | Wire helpers into answers, normalize supported units and handle zero or negative prior values explicitly. | Rushil Nov 7
Context truncation | Replace the 4000-character slice with complete evidence selection inside a configured input budget. | Pavan Nov 8
Unproven evaluation | Use checked questions, independent label review and saved matched-mode outputs rather than LLM self-grading alone. | Sudhansh Nov 9; Ujjwal Nov 10; Gowtham Nov 12
Incomplete package | Repair dependencies and launch instructions; verify the final archive in a clean environment. | Shanay Oct 31; Shanay Nov 16

Dates listed together identify separate sequential workdays, not shared work on the same date. Fixes remain proposed work until their dated completion checks pass.


## Product requirements and scope

Requirement | Required November behavior | Completion evidence
R1 Corpus | One exact Apple 10-K with comparative fiscal-year values; selected narrative from Items 1A, 7 and 8 and three representative financial tables. | Manifest, original URL, checksum, supported periods and accounted record counts.
R2 Reproducible data | A documented parse and ingestion route builds the index and reopens it after restart. | Stable IDs and counts after two runs; no stale records for the filing.
R3 Evidence | Preserve source identity, narrative section, table title, row, value period, original value and unit. | Cited evidence can be checked against the original report.
R4 Grounded answers | Use the same real model configuration for both modes. Explicitly distinguish ok, insufficient_evidence, index_not_ready, invalid_request and service_error. | A real answer and deliberately triggered failure paths; no hidden mock result.
R5 Calculations | Support sum, difference and percentage change over cited operands with matching periods and units. | Formula and values match the code result; missing data and zero denominators are handled.
R6 Interface | Show the supported filing, question, status, answer, evidence, source links and calculation. | A simple demo runs without notebook execution.
R7 Comparison | Compare dense baseline and table-aware retrieval on 14 checked local questions, with seven reserved for final evaluation. | Fixed settings, saved outputs, actual scores and independent review.
R8 Delivery | Deliver code, setup guide, report, slides, results, contribution record and backup demo by November 17. | Clean-machine evidence, archive checksum and delivery or submission record.

## What this deadline excludes

Defer chart image understanding, BM25 and rank fusion, FAISS or BGE migration, corpus expansion, full external benchmarks, extra LLM comparisons, fine-tuning, cloud hosting, new Docker work, MLflow and DVC. These features must not appear as implemented contributions in the report.

The existing narrative-and-table search is not BM25 hybrid search. Describe the delivered mode as table-aware retrieval. Keep financial evidence quality and honest failures ahead of new features.


## Architecture and quality rules

## Offline preparation

Declared filing -> narrative and table parsing -> evidence records -> supported value normalization -> existing MiniLM embeddings -> Chroma persistence and a record-count summary. Baseline records contain the same source facts, with tables flattened into text. Enhanced records retain table rows and headers.

## Online question answering

Question and supported period -> readiness check -> dense search -> existing reranker where used -> complete evidence selection -> validated calculation and real model call -> answer, sources and timing, or an explicit failure state.

Data contract | Required fields
Evidence | evidence_id, filing_id, evidence type, source URL or file, section or table locator, readable content and parser version.
Financial row | Parent-table ID, table title, row label, column label, value fiscal period, raw value, normalized value, currency and scale.
Answer | Status, answer text, provider and model, included evidence IDs, citations, calculation, warnings and elapsed time.
Calculation | Approved operation, cited operand IDs, raw and normalized values, periods, units, formula and result.

## Calculation policy

Use fixed typed operations rather than executing generated Python. Percentage change for a positive prior value is (current - prior) / prior x 100. If the prior value is zero, return undefined. For a negative prior value, show absolute change and explain that ordinary growth percentage is not supported in this small build. Normalize scale before arithmetic and round only the final display value.

## Required reliability

All citations must resolve to included evidence and a source location. Empty data or failed model calls must not produce a financial answer. Store no credentials in Git or logs, and do not mutate a shared environment variable from a user request. Use one configured embedder compatible with the stored index and rebuild if it changes.

## Performance and recovery

Record observed warm response times and cold setup separately; do not promise a latency threshold without measurements. The native local app is the required demo path. A backup video and saved evaluation outputs may demonstrate prior measured behavior if the real service fails, with that fact clearly stated.


## Small evaluation and scoring plan

Use 14 manually checked local questions from the supported filing: six narrative, four table, two calculation and two unanswerable. Reserve seven development and seven held-out cases, each with three narrative, two table, one calculation and one unanswerable question. Keep related question templates together when selecting cases; use distinct facts to avoid near duplicates across splits.

Date | Sole owner | Evaluation responsibility
Nov 9 | Sudhansh | Author 14 cases, preassign the split and write expected answers and source locations.
Nov 10 | Ujjwal | Independently verify labels and source mappings; lock the split and use development cases only for checks.
Nov 11 | Rushil | Freeze code, model, prompt, calculator and context budget before final test use.
Nov 12 | Gowtham | Run seven test cases in both modes and score all 14 saved outputs.
Nov 14 | Pavan | Independently audit results, recompute scores and explain limitations.

## Fair comparison

Mode A uses dense retrieval over fixed chunks with table facts flattened into readable text. Mode B uses section and table-row records preserving headers and context. Keep the same source report, model, generation prompt, calculator, total context budget and reranker setting. If either path uses the existing reranker, both must use the same setting. Only representation and retrieval of that representation differ.

## Measures and proposed checks

Report answer correctness out of six answerable test cases per mode, table and calculation correctness out of three, and correct abstention out of one. A useful target is at least five of six answerable cases correct with all three numeric cases and the one abstention correct; report actual results even if the target is missed.

Check source support for every answer and operand, and report the fraction of gold evidence included within the top five results using common source-location mappings. For numbers, require matching period and unit, then use a predeclared 1 percent relative tolerance for nonzero amounts and 0.1 percentage point for percentage results. Define absolute tolerance separately for zero or near-zero values before testing.

## Honest interpretation

Retain failures in the outputs. Report counts beside percentages and state that the test is tiny and specific to one report. No published benchmark or unseen-company claim follows from it. If a real blocker is fixed after test use, version the change, rerun both modes and label the reused-test regression result. Do not tune features against the reserved answers.


## Seven member ownership and equal workload

Member and ID | Main contribution | Days | Total hours
Sudhansh Khandelwal; 2024AAPS0255H | Integration, evaluation design and submission | 3 | 6
Agrawal Pavan Shailesh; 2024A3PS0399H | Retrieval, context and independent result review | 3 | 6
B Rushil Mohan; 2024AAPS0235H | Real model calls, calculations and failure handling | 3 | 6
Sri Sai Likhit Boddada; 2024A1PS0838H | One filing, parsing, source verification and report draft | 3 | 6
Ujjwal Chandak; 2024A3PS0379H | Index persistence, gold-label verification and data package | 3 | 6
Shanay Ghodasara; 2024AAPS0244H | Setup, packaging and clean-machine verification | 2 | 6
Muppidi Gowtham Sai; 2024AAPS0207H | Interface, fixed evaluation run and demonstration | 2 | 6

## How equality works

There are 19 available dates and seven members, so everyone cannot receive the same number of whole dates. Equal planned hours solve this: Sudhansh, Pavan, Rushil, Likhit and Ujjwal each receive three two-hour days; Shanay and Gowtham each receive two three-hour days. Every member receives six hours, and total scheduled effort is 42 hours.

Hours include reading the previous handoff, doing the bounded task, running its checks and leaving the next handoff. They are planning estimates; actual effort should be recorded. If a task overruns, narrow its nonessential part instead of silently assigning work to another person that day.

## Exactly one active member per date

Only the listed owner has work assigned on a given day. There are no shared standups, same-day code reviewers, background dataset assignments or extra tasks for other members. The next scheduled owner reviews the previous change during their own workday. Specific independent label and result checks are placed on different dates.

## Daily handoff record

Before stopping, save the changed files or revision, the result of the daily completion check, exact run instructions, source or configuration changes, actual time used and any unresolved defect. The next owner should be able to start from this record without a meeting.

## Scope control for this capacity

Equal hours do not guarantee equal technical difficulty. Use existing modules and one tested example before expanding. Cut polish, extra questions or optional features before weakening citations, numerical correctness, honest failure states or the verified launch path. No recovery work is assigned after November 17.


## Complete calendar with one owner per day

The owner shown is the only assigned worker that date. All times are focused work estimates including checks and handoff.

Date | Member | Hours | Daily outcome
30 Oct | Sudhansh | 2 | Choose one runnable implementation
31 Oct | Shanay | 3 | Make setup and launch reproducible
01 Nov | Rushil | 2 | Connect a real model and remove false success
02 Nov | Likhit | 2 | Parse one supported annual report
03 Nov | Ujjwal | 2 | Build and reopen the persistent index
04 Nov | Pavan | 2 | Preserve source records through retrieval
05 Nov | Gowtham | 3 | Finish the source linked question interface
06 Nov | Likhit | 2 | Repair the tables needed for the demonstration
07 Nov | Rushil | 2 | Add a small source checked calculator
08 Nov | Pavan | 2 | Keep complete evidence in the model context
09 Nov | Sudhansh | 2 | Prepare the small evaluation and report outline
10 Nov | Ujjwal | 2 | Independently verify labels and freeze the split
11 Nov | Rushil | 2 | Verify final answers and freeze evaluation settings
12 Nov | Gowtham | 3 | Run the reserved evaluation and capture the demo
13 Nov | Likhit | 2 | Write the evidence based final report draft
14 Nov | Pavan | 2 | Audit results and review the report
15 Nov | Ujjwal | 2 | Package data and prepare the final presentation
16 Nov | Shanay | 3 | Run the final clean machine and release check
17 Nov | Sudhansh | 2 | Complete final verification and deliver the project

Totals: 19 daily assignments, seven members, six hours each and 42 team hours. November 17 is the final delivery date; no additional workday or buffer follows it.


## Daily work plan 1 and 2

## Day 1 30 October 2026

Sudhansh is the only assigned member. Planned work 2 hours.

Choose one runnable implementation

Why this matters: The remote prototype has a UI, while the local branch has reusable modules. Select one integration route before changing either version.

Start with: The two inspected revisions, supplied proposal and current course requirements.

1. Keep the existing Chroma, MiniLM and Gradio route. Select one Apple 10-K with comparative years; record a minimal scope and launch path.

2. Define the evidence record and answer status fields. Record which UI functions and local modules will be reused in the integration branch.

3. Create the acceptance checklist and a shared handoff file. Record the official delivery requirements, model-access assumption and November 17 cutoff.

Completion check: One integration checklist, one proposed filing, shared record examples and a fixed delivery checklist are saved.

What we learn: The goal is to repair a small existing prototype and prove its answers, rather than start another implementation.



## Day 2 31 October 2026

Shanay is the only assigned member. Planned work 3 hours.

Make setup and launch reproducible

Why this matters: The next owners need a working environment and a single application entry point. Repair setup before spending time on model or retrieval changes.

Start with: The Day 1 integration checklist and evidence examples.

1. Review the previous handoff. Create the integration branch and port the chosen UI and module wiring without deleting the useful source versions.

2. Fix dependencies, including Gradio, and add one configuration loader and environment example. Keep credentials out of files and logs.

3. Run the existing lightweight tests and launch the UI in an explicit not-ready state. Document installation, data location and launch commands.

Completion check: The application starts from documented commands, reports missing data clearly and has a saved setup and test log.

What we learn: A launchable application needs its dependencies, configuration and entry point to agree.


## Daily work plan 3 and 4

## Day 3 01 November 2026

Rushil is the only assigned member. Planned work 2 hours.

Connect a real model and remove false success

Why this matters: A fixed mock answer must never appear as financial analysis when the actual provider fails.

Start with: The configured application and status contract from Days 1 and 2.

1. Verify one real provider and model on the demo machine. Put the confirmed model identifier in configuration and construct an explicit API client.

2. Remove automatic mock fallback and process-wide credential mutation. Keep mock mode available only through an explicit test setting.

3. Return service_error for provider failures and insufficient_evidence when context is absent. Save one real-call check and one deliberate failure check.

Completion check: A real model call works; invalid credentials and empty evidence cannot return the fixed mock financial answer.

What we learn: Model access failure and missing source evidence are different outcomes and must remain visible.



## Day 4 02 November 2026

Likhit is the only assigned member. Planned work 2 hours.

Parse one supported annual report

Why this matters: One fully checked filing is a feasible foundation for the reduced schedule. Downloaded files alone are not searchable evidence.

Start with: The filing choice, evidence schema and data path already recorded.

1. Record the exact accession, company, report fiscal year, original URL, local path and checksum for one Apple 10-K.

2. Move the required parsing cells into a repeatable function. Extract bounded sections from Items 1A, 7 and 8 and relevant statement tables.

3. Emit narrative and table records separately, preserving source locations, table titles, comparative periods and declared units. Save a parsing summary.

Completion check: One command parses the declared filing into traceable narrative and table records; the table of contents is not treated as risk-factor evidence.

What we learn: The filing year and the comparative year of a table value are separate pieces of metadata.


## Daily work plan 5 and 6

## Day 5 03 November 2026

Ujjwal is the only assigned member. Planned work 2 hours.

Build and reopen the persistent index

Why this matters: Search must use the intended parsed report and return the same records after restart or repeated ingestion.

Start with: The Day 4 parsed records and original source manifest.

1. Index the supported records with the existing MiniLM embedder and Chroma. Use deterministic IDs containing filing identity, evidence type and location.

2. Preserve source metadata, parent-table links and embedding identity. Replace that filing cleanly so shortened reruns do not leave stale records.

3. Re-ingest twice, restart the application and compare IDs and counts. Save one retrieved narrative record and one table record with their sources.

Completion check: Repeated ingestion is stable, reopening the index preserves search and every returned record resolves to the supported report.

What we learn: Persistent search is reproducible only when IDs, stored embeddings and source metadata remain consistent.



## Day 6 04 November 2026

Pavan is the only assigned member. Planned work 2 hours.

Preserve source records through retrieval

Why this matters: Returning passage text alone loses the information needed to verify the company, period and cited source.

Start with: The Day 5 populated index and evidence contract.

1. Return complete evidence records through retrieval and the existing reranker. Validate supported filing and value-period filters.

2. Define dense baseline and table-aware modes with the same generator, calculator and context limit. Baseline chunks retain flattened table facts.

3. Skip disabled retrieval streams instead of issuing zero-result queries. Handle empty collections and no eligible evidence before generation.

Completion check: A retrieved source ID survives ranking; baseline and table-aware modes return structured evidence and fail clearly when no eligible record exists.

What we learn: The baseline measures retrieval changes fairly only when generation and available source facts are matched.


## Daily work plan 7 and 8

## Day 7 05 November 2026

Gowtham is the only assigned member. Planned work 3 hours.

Finish the source linked question interface

Why this matters: A user should see the answer and the actual evidence without inspecting the notebook or developer logs.

Start with: The real provider, persistent index and structured retrieval output.

1. Connect the UI to the selected backend. Show the supported report, question input, retrieval mode and an understandable loading state.

2. Display answer status, retrieved passages, table title, comparative period, units and original source links. Add the calculation area for later integration.

3. Check a narrative question, table question, empty input and missing-evidence case. Verify invalid credentials give a service error and inputs stay session-specific.

Completion check: The integrated UI shows real evidence and source links and handles the four checked cases without notebook execution.

What we learn: Showing an answer is not enough; the interface must let the reader verify the source and recognize a failure.



## Day 8 06 November 2026

Likhit is the only assigned member. Planned work 2 hours.

Repair the tables needed for the demonstration

Why this matters: Financial values are useful only when their row labels, comparative periods and scale survive parsing.

Start with: The Day 7 evidence display and original annual report.

1. Select three representative financial tables from the supported report. Check their headers, units, parentheses, blank values and comparative-year columns.

2. Create self-describing row records with parent-table links. Keep raw values and normalized numeric values and exclude duplicate narrative table copies.

3. Save small hand-checked fixtures and refresh the index using the existing command. Verify the displayed source locations against the original report.

Completion check: The three selected tables have source-checked values, labels, years and units; row records expand back to their original table.

What we learn: Table-aware retrieval preserves relationships that disappear when a grid is flattened into unrelated text.


## Daily work plan 9 and 10

## Day 9 07 November 2026

Rushil is the only assigned member. Planned work 2 hours.

Add a small source checked calculator

Why this matters: The model can explain a calculation, but arithmetic should run in predictable code using values actually retrieved.

Start with: The normalized values and parent references from Day 8.

1. Connect the existing math helpers to the answer path for sum, difference and percentage change. Use typed operations and evidence-linked operands.

2. Normalize the supported currency scale, preserve the requested periods and reject absent or incompatible operands. Do not execute arbitrary generated code.

3. Show the formula, substituted values, result and unit. Check positive-year growth, a negative amount, missing evidence and a zero denominator.

Completion check: A demonstrated calculation uses cited operands and checked arithmetic; zero-base or insufficient-data cases explain why no growth result is available.

What we learn: A calculated answer needs correct inputs, units and periods as well as correct arithmetic.



## Day 10 08 November 2026

Pavan is the only assigned member. Planned work 2 hours.

Keep complete evidence in the model context

Why this matters: A relevant table may be retrieved but still lose its important rows when a character slice cuts the model input.

Start with: The row records, source-linked calculator and two retrieval modes.

1. Replace the 4000-character table slice with complete record selection under the configured input budget. Retain headers, units and required operand rows.

2. Preserve the included evidence IDs in the answer contract. Reject references or calculations that cannot be matched to included records.

3. Check a long-table fixture and an unsupported-period question. Keep baseline and enhanced generation settings and total context budget the same.

Completion check: The required rows reach final context, every citation maps to included evidence and unsupported periods produce clear abstention.

What we learn: Retrieval quality is lost if context assembly removes the information needed to answer the question.


## Daily work plan 11 and 12

## Day 11 09 November 2026

Sudhansh is the only assigned member. Planned work 2 hours.

Prepare the small evaluation and report outline

Why this matters: The submission needs a modest, honest test rather than a broad accuracy claim that the schedule cannot substantiate.

Start with: The working integrated app, original report and matched retrieval modes.

1. Create 14 questions with source locations and checked answers: six narrative, four table, two calculation and two unanswerable cases.

2. Reserve seven development and seven held-out IDs before tuning: each split has three narrative, two table, one calculation and one unanswerable case.

3. Freeze a scoring checklist for answers, units, source support, evidence recall and timing. Create the report outline and an evaluation-results template.

Completion check: A versioned 14-case question file, fixed seven plus seven split, scoring rubric and report outline exist. No test answers are used to tune retrieval.

What we learn: A small source-checked test supports a precise claim about this report; it does not establish broad financial accuracy.



## Day 12 10 November 2026

Ujjwal is the only assigned member. Planned work 2 hours.

Independently verify labels and freeze the split

Why this matters: The answers used to score the app need an independent source check so a mistaken gold label does not reward a wrong result.

Start with: The Day 11 question file, split and original source records.

1. Independently verify all 14 answers and supporting locations against the original report. Correct labels without moving difficult test questions into development.

2. Map baseline and table-aware records to the same source locations. Confirm repeatable record counts and the intended embedding version.

3. Run only the seven development questions to check the scoring process. Correct a blocking index or metadata defect and record the resulting version.

Completion check: Every gold case has an independent verification record and the split is locked. Only development examples have been used to guide corrections.

What we learn: Citation identity and scoring must stay fair when baseline and enhanced chunk boundaries differ.


## Daily work plan 13 and 14

## Day 13 11 November 2026

Rushil is the only assigned member. Planned work 2 hours.

Verify final answers and freeze evaluation settings

Why this matters: The final model, calculation path and failure states must be fixed before the reserved questions are run.

Start with: The checked labels, development results and real generation provider.

1. Recheck model-unavailable, no-evidence, incompatible-unit and zero-denominator paths using development cases or dedicated fixtures.

2. Confirm mock mode is rejected by the real evaluation path. Keep the same model, prompt, calculator and context budget for both retrieval modes.

3. Freeze the code revision and run settings. Save a generation and calculation handoff explaining how to run the reserved cases and record failures.

Completion check: A frozen evaluation revision and configuration exist, with explicit failure checks and no hidden mock fallback.

What we learn: Freezing settings before test evaluation prevents favorable-looking results from being selected through repeated tuning.



## Day 14 12 November 2026

Gowtham is the only assigned member. Planned work 3 hours.

Run the reserved evaluation and capture the demo

Why this matters: Today measures the frozen app on the seven questions that were kept out of tuning and records what actually works.

Start with: The Day 13 frozen revision, two modes, held-out IDs and scoring rubric.

1. Run all seven held-out questions in both modes and retain all 14 outputs, included evidence IDs, status, model settings and timing.

2. Score the six answerable and one unanswerable case per mode. Check sources, numerical periods and units, and compare evidence coverage fairly.

3. Save the metric table and error notes. Capture a short demo showing a real answer, source, calculation and abstention; label saved results and recordings clearly.

Completion check: Fourteen held-out outputs, a scored result table, source audits and a playable backup demo are saved, including failures.

What we learn: Measured results may favor either mode. Reporting failures and denominators matters more than promising improvement.


## Daily work plan 15 and 16

## Day 15 13 November 2026

Likhit is the only assigned member. Planned work 2 hours.

Write the evidence based final report draft

Why this matters: The report must explain the delivered system and actual measurements, with a clear boundary around the reduced scope.

Start with: The report outline, source manifest and Day 14 results.

1. Draft the problem, one-report corpus, parsing method, table representation and implemented architecture using the saved handoff notes.

2. Insert the actual results with counts and explain source examples, limitations and unsupported layouts. Mark chart analysis and broad benchmarks as future work.

3. Include the seven-member contribution log, source references and AI-assistance disclosure draft. Add setup and calculator sections from the existing handoffs.

Completion check: A complete short report draft explains methods, actual results, limitations and all seven contributions; no unimplemented feature is claimed.

What we learn: The report should describe the submitted software and evidence, including its limitations, rather than repeat an earlier ambitious proposal.



## Day 16 14 November 2026

Pavan is the only assigned member. Planned work 2 hours.

Audit results and review the report

Why this matters: A separate review checks that the saved outputs justify the reported conclusions and that retrieval behavior is explained correctly.

Start with: The Day 15 report draft and all evaluation artifacts.

1. Independently review the 14 saved outputs and recompute the reported counts. Check that incorrect periods, units and unsupported answers are scored as failures.

2. Classify remaining errors as parsing, retrieval, context, calculation or provider failures. Correct the report and add an annotated question-to-source walkthrough.

3. Fix only a reproducible release blocker. If a fix affects outputs, version it, rerun both modes and label the results as reused-test regression results.

Completion check: The report and result table have an independent review record. Every change has an explained effect on the saved evidence.

What we learn: After the test run, investigate and report errors instead of treating the test answers as another tuning set.


## Daily work plan 17 and 18

## Day 17 15 November 2026

Ujjwal is the only assigned member. Planned work 2 hours.

Package data and prepare the final presentation

Why this matters: The evaluator needs a clear source inventory and a short explanation of how the project works, alongside the runnable code.

Start with: The reviewed report, final source revision and ingestion instructions.

1. Package the filing manifest, small fixtures, record-count summary and deterministic index rebuild instructions. Verify every original source link.

2. Assemble a short presentation from the report: problem, workflow, table treatment, calculated answer, actual comparison and limitations.

3. Create the release checklist and archive inventory. Check that the report, results, presentation, demo and contribution log refer to the intended versions.

Completion check: The data package, short presentation and release inventory are ready for a clean-machine check.

What we learn: Data identity and source instructions are part of reproducibility, even when large raw files are not committed to Git.



## Day 18 16 November 2026

Shanay is the only assigned member. Planned work 3 hours.

Run the final clean machine and release check

Why this matters: The last full technical check protects delivery from hidden local dependencies and missing files.

Start with: The Day 17 release inventory, runnable source and both saved retrieval modes.

1. Build or restore the index on a fresh environment using the included instructions. Run a known question and confirm its cited source and calculation.

2. Check credentials, runtime requirements and the app launch command. Keep the verified native launch path; add no cloud deployment or new container dependency.

3. Recheck critical failure paths, open the report, slides and demo, then freeze and back up the archive. Save its checksum, exact revision and launch evidence.

Completion check: The final archive launches from documented inputs, all delivery files open and a backup plus verification log are ready.

What we learn: The release check proves the project can leave the original developer machine without losing its data or setup knowledge.


## Daily work plan 19

## Day 19 17 November 2026

Sudhansh is the only assigned member. Planned work 2 hours.

Complete final verification and deliver the project

Why this matters: November 17 is the final project delivery deadline. Use the verified package and retain proof of what was delivered.

Start with: The Day 18 frozen archive, report, presentation, demo and verification log.

1. Check the exact package against the official delivery checklist. Verify seven correct names, final links, report results and contribution records.

2. Perform a short final demo using the frozen build or transparently labeled backup video. Make only necessary document corrections.

3. Deliver or submit before the confirmed November 17 cutoff and retain the receipt and exact archive. If the official portal opens later, retain this frozen ready-to-submit release.

Completion check: The project is complete by November 17, with its final package and verification record delivered. If submission is open, the receipt is retained; otherwise the frozen release is ready.

What we learn: Finishing by the internal deadline means the code, evidence and documents are complete together, without relying on later development.


## Release risks and final checklist

Risk | Response inside the assigned day
Scope exceeds available hours | Keep one filing and the required three tables; drop new features and cosmetic work. The named owner records what was cut.
A scheduled day is missed | Reduce scope or move a future whole task within the remaining dates. Never assign two owners to the same date or assume work after November 17.
Model access fails | Use another real provider only after a check and consistent settings. If all services fail, show the labeled backup video and saved outputs; never use hidden mock answers.
Parser cannot handle a table | Choose a representative supported table from the same filing and document the excluded layout. Keep all question sources within the declared supported scope.
Test result is weak | Report it with the actual denominator and failure analysis. Keep the distinction between the original test run and any regression rerun.
A mandatory feature conflicts with scope | Verify course requirements on October 30 and replace optional scope early. Do not claim charts or broad benchmark coverage without implementing and checking them.
Official upload is unavailable | Finish and retain the frozen release by November 17. If the portal opens later, submit the already-completed package when allowed.

## Final package on November 17

Include the frozen source revision, tested dependency setup, environment example without keys, one-filing manifest and source references, repeatable ingestion and launch guide, index rebuild or restore instructions, short report, question and split files, all evaluation outputs, scoring and audit notes, presentation, backup demo and seven-member contribution record with AI-use disclosure.

## Final demonstration

Show one supported narrative answer, one table answer, one checked calculation with periods and units, one verifiable original source and one abstention. Open the same verified build from the final archive. Keep the saved video ready and label it clearly if used.

## Completion record

Keep the archive checksum, exact code revision, clean-machine verification log and delivery acknowledgment together. If the portal is open, retain the submission receipt. The deadline is November 17 and no later development is assumed.


## Plain language terms and source references

Term | Meaning for this project
RAG | Find relevant source evidence first, then ask a language model to answer using that evidence.
Chunk | A smaller passage or table row stored as a searchable record.
Embedding | A numeric representation of meaning used to find related questions and evidence.
Reranking | Score retrieved candidates again to put more useful evidence first.
Provenance | The identity and original location of the report evidence behind an answer.
Baseline | A simpler comparison system with the same underlying source facts and generation settings.
Gold question | A question whose answer and required evidence were checked against the original source.
Held out case | A reserved question used for final reporting instead of guiding feature tuning.
Abstention | An explicit statement that the available evidence is not enough to answer reliably.
Mock | A fake output for tests; it must never silently replace a failed real financial answer.

## Project references

The supplied proposal Finrag .docx provides the project intent and member names. The membership and schedule in this revised plan follow the latest team instructions. AI Project Planning Strategy1.pdf supplies earlier architectural ideas, and FinRAG_Team_Code_Review.pdf documents review findings on main b3bb02f. ideas.pdf is background on the original project alternatives.

GitHub main reviewed: b3bb02fb54c68ff7fc3bda9c0959df3d61b0acbf. The notebook and app.py contain the earlier ingestion, retrieval and UI prototype. https://github.com/sudhansh81205/FinRag-Project-/tree/b3bb02fb54c68ff7fc3bda9c0959df3d61b0acbf

Local modular branch reviewed: feature/engine-backend at c4b1a7636b59890f8bf7ae73a20b309038ed6501. Relevant modules are src/retrieval, src/llm, src/pipeline, scripts/run_eval.py, tests, configuration and Dockerfile.

Repository observations and lightweight checks are from the planning review on October 29, 2026. The dated repairs and performance checks in this document are planned work. Course delivery requirements and the exact cutoff time are checked on the first assigned day.
