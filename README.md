# FinRAG

A financial research workspace over source-checked SEC annual reports, with cited narrative answers, restricted Decimal calculations and private Supabase Saved Questions.

Start with [START_HERE.txt](START_HERE.txt), the current plain-text startup and professor demonstration manual. The canonical scope is [the current PRD](docs/plan/PRD.md). [ATTRIBUTION.md](ATTRIBUTION.md) records contributions and the single current disclosure.

## Current application

- Eighteen processed/indexed filings across ten companies: Apple and Microsoft FY2021-FY2025; Adobe, NVIDIA, Salesforce, AMD, Intel, Cisco, Oracle and IBM FY2024.
- The source-checked runtime exposes every indexed filing. Both web and Gradio derive selections from the registry. Each question stays bound to the selected company, exact accession and value period.
- Research, Filings and Saved Questions; original source/citation inspector, checked calculations and JSON export. Selection edits clear prior answers.
- Email/password sign-in and private per-user save/read/delete. Records live in Supabase and survive page refresh; session expiry requires signing in again. No service-role key is used.
- Known numerical questions return the validated source-bound calculation without optional model-written prose. The result explicitly identifies the typed calculator; narrative questions and matched experiment defaults retain model generation.
- Hosted workspace: https://finrag-workspace.vercel.app/ (Vercel Authentication). The approved temporary HTTPS backend still depends on Rushil's laptop remaining awake.

## Start on the prepared laptop

```sh
.venv/bin/python scripts/run_local_workspace.py --status
# Only if stopped and required ports are free:
.venv/bin/python scripts/run_local_workspace.py --gradio-port 7860
```

Open http://127.0.0.1:4180/ or the shared-engine Gradio workspace at http://127.0.0.1:7860/. No npm install is needed. The launcher checks installed model bytes and uses existing pinned BGE/FAISS/Gemma assets; it never silently downloads or substitutes models. See the manual for another machine, environment configuration and rebuilding parsed/indexed packages.

## Submission materials

- [Project report](docs/reports/2026-11-17_final_report.md) and [verified six-slide deck](docs/reports/2026-11-17_verified_slides.pptx).
- [Latest benchmark results and reproduction steps](docs/validation/official-source/README.md).
- [Team contributions and commit provenance](ATTRIBUTION.md).

## Demonstration files

- [Question spreadsheet](outputs/finrag-final-20261118/FinRAG_Sample_Questions.xlsx):108 source-derived questions, per-filing coverage, exact expected results/source IDs and three explicitly manual cross-filing exercises.
- [Demonstration PDF](outputs/finrag-final-20261118/FinRAG_Demonstration_Questions.pdf):20 printable pages, including a page for every filing.
- [Machine-readable question bank](outputs/finrag-final-20261118/sample-questions.json).
- [Current verification and blockers](docs/reports/2026-11-18_final-completion.md).

## Official-source retrieval benchmarks

The new evaluation attempted all **2,960 questions** from the restored FinanceBench, FinQA and TAT-QA source pools. Retrieval used the complete declared corpus for each suite, original questions and source IDs. FinanceBench ranks pages, while FinQA and TAT-QA rank paragraphs and whole tables.

| Dataset | Questions attempted | BM25 Recall@10 | BGE dense Recall@10 | Hybrid Recall@10 |
| --- | ---: | ---: | ---: | ---: |
| FinanceBench | 150 | 14.33% | Incomplete | Incomplete |
| FinQA | 1,147 | 58.89% | 71.61% | 72.12% |
| TAT-QA | 1,663 | 72.23% | 71.82% | 76.54% |

Three TAT-QA questions have no mapped evidence labels, leaving 1,660 scored retrieval cases. Dense/hybrid nDCG@10 was **0.5593/0.5482** on FinQA and **0.5469/0.6010** on TAT-QA. The report retains the paired 95% document-cluster intervals and per-question rankings. FinanceBench dense execution stopped after checkpointing 2,304 of 25,950 chunks.

Three real Gemma generation pilots averaged **69.98 seconds**. Extrapolating to 2,960 questions across seven variants gives **approximately 403 machine-hours** of sequential answer generation. This preliminary estimate uses one question per dataset and excludes charts, RAGAS, Llama comparison, reruns and human review. The available evaluation time was used for the completed retrieval comparisons and generation pilots. Full cumulative A-G implementation, execution and independent acceptance remain outstanding.

[Official-source report and reproduction](docs/validation/official-source/README.md) · [Plain-text results and runtime analysis](docs/validation/official-source/BENCHMARK_RESULTS.txt)

## Development benchmark results

The development study ran **90 local application requests** across 18 SEC filings from 10 companies. Its separate retrieval comparison used **71 labelled questions** with fixed BGE embeddings, exact FAISS, filing filters and ranked depth. The hybrid run added BM25 and reciprocal rank fusion.

| Retrieval metric | Dense only | Dense + BM25/RRF |
| --- | ---: | ---: |
| Operand nDCG@10 | 0.6029 | 0.5893 |
| Required-operand recall@5 | 75.35% | 75.35% |
| Required-operand recall@10 | 90.14% | 88.73% |
| All required operands in the top 10 | 83.10% | 77.46% |
| MRR@10 | 0.5410 | 0.5308 |

The measured hybrid nDCG@10 difference was **−0.0136**, with a paired 95% filing-cluster interval of **[−0.0598, +0.0383]**. This comparison found no evidence of a hybrid improvement on the selected questions.

| Application check | Result |
| --- | ---: |
| Numerical source-reference agreement | 59/71 (83.10%) |
| Expected refusal for missing aggregate evidence | 1/1 |
| Strict adversarial checks | 7/12 (58.33%) |
| Narrative responses with matching citation IDs and filing | 6/6 |
| Median local latency, numerical / narrative | 0.028 s / 102.997 s |

Numerical agreement requires the PRD's 1% relative tolerance, the correct units and period, and the cited source operands. Narrative checks measured response and citation structure. Claim-level assessment is pending. The study uses development questions from the application's supported filings. The official A–G matrix remains **0/28 complete**, with RAGAS, independent review and the separate Llama comparison outstanding.

[Plain-text benchmark report](BENCHMARK_RESULTS.txt) · [Protocol, raw results and reproduction](docs/validation/README.md)

## Verify

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
node --check web/public/app.js
node --test web/tests/*.test.mjs
.venv/bin/python scripts/check_project_readiness.py --publish-web
.venv/bin/python scripts/verify_chart_set.py
.venv/bin/python scripts/verify_release_package.py
```

`scripts/check_experiment_acceptance.py` checks all28 required suite/variant prerequisites against the official imported files; exit2 means acceptance remains blocked, not a successful experiment. See its report and the manual before attempting full runs.

## Research acceptance and supported questions

Application processing/count coverage meets the five-Apple/five-Microsoft/ten-company scope. Independent wider source acceptance remains separate. Source-backed annual numerical and narrative questions are available; not every metric, question or comparison has sufficient evidence. Oracle's aggregate gross-margin operands are not supplied by the current typed package, so that question refuses. Within-filing adjacent-year comparisons are supported where both typed periods exist. Automatic aggregation across separate filings/companies is not supported; compare separate cited answers explicitly.

Original-chart answers remain gated on genuine independent question/caption review. The full A-G runner still needs validated official-context binding. RAGAS, the separate Llama comparison and the independent fifty-output audit are also incomplete. Tests and live application probes do not constitute these experiments. New-user confirmation-email delivery and permanent unattended hosting require separate verification/setup. Historical reports are dated snapshots; use the current report/manual for present status.
