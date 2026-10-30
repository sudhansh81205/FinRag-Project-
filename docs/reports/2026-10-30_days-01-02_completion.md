# FinRAG completion report: first two assignments

Date: **October 30, 2026, Asia/Kolkata**. This is an implementation completion
report, not the scheduled 23:59 nightly review. It follows the PRD and review-kit
structure. The user explicitly approved completing both initial tasks today and
confirmed November 17 is the internal team target, not a hard course cutoff.

## Reviewed revision and contribution evidence

Implementation revision:
[`9943b746238446c7be59ee3956a89de32c50d890`](https://github.com/sudhansh81205/FinRag-Project-/commit/9943b746238446c7be59ee3956a89de32c50d890).
It is a history-preserving merge with parents `88ad70b` (shared PRD/review kit) and
`c4b1a76` (backend). The former includes original main `b3bb02f`.
Merge commit time: October 30, 22:23:52 IST / 16:53:52 UTC.

| Planned owner | Original date / budget | Work performed for that assignment | Attribution |
| --- | --- | --- | --- |
| Sudhansh Khandelwal | Oct 30 / 2 hours | Scope, filing, integration route, evidence/status examples, acceptance/delivery checklist | AI-assisted completion at user's request; no claim Sudhansh authored this commit |
| Shanay Ghodasara | Oct 31 / 3 hours | Combined source, configuration, dependencies, setup UI, tests and launch verification | AI-assisted in Shanay's workspace; Git author is Shanay Ghodasara |

Budgets are planned allocations, not measured human hours. Exact human work time
was not tracked. No work is attributed to other teammates. Future ownership and
the six-hour planned allocation per member remain unchanged.

## Completed work and branch integration

Sudhansh's acceptance artifacts are in the [integration checklist](../plan/INTEGRATION_CHECKLIST.md),
[filing manifest](../../data/filing_manifest.json), [record/status contract](../plan/EVIDENCE_CONTRACT.md),
[record examples](../plan/record_examples.json) and [delivery checklist](../plan/DELIVERY_CHECKLIST.md).
The selected corpus is one Apple 2021 10-K, with Items 1A/7/8 and three proposed
financial statements. The source was checked on the [SEC filing page](https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm).
It has not been downloaded/parsed into a validated index in this task.

Shanay's setup is implemented in [`app.py`](../../app.py),
[`src/config.py`](../../src/config.py), [`src/application.py`](../../src/application.py),
the requirements files, CI, and [setup tests](../../tests/test_setup.py).
One YAML configuration and optional private environment overrides replace
contradictory startup settings. The application imports Gradio only when launching
and never downloads embedding models or calls a provider at startup. It reports
`not_ready` instead of fabricating answers when prerequisites are missing.

There were **no Git text conflicts**. The behavioral conflicts were resolved as follows:

| Difference between branches | Resolution |
| --- | --- |
| Standalone UI versus modular backend | One root `app.py`; explicit backend assembly in `src/application.py`; original UI retained in `prototypes/` |
| Unused BGE configuration versus existing MiniLM | Canonical configuration selects MiniLM and the existing cross encoder |
| Missing Gradio and unpinned setup | Gradio added; direct dependencies and resolved setup/dev constraints pinned |
| Model/data loading before a usable screen | Setup UI starts without model/data and describes missing prerequisites |
| Hidden `.env` loading on module import | Removed; the central loader reads values without changing process credentials |
| Container claims app startup but runs absent tests | Preserved as historical `prototypes/Dockerfile.experimental`; native launch documented |
| Generated certificate and private local state | Certificate removed from tracked runtime files; local caches, reports and keys ignored |

Original code is retained in merge history. The archived UI only has trailing
whitespace normalized. The notebook was preserved. None of these merge decisions
claims completion of later provider, ingestion, citation or calculator tasks.

## Verification performed

The code tested is the implementation in `9943b74`; later report edits do not alter
that code. A new isolated Python 3.12.14 environment was used on Windows.

| Check | Result | Meaning / limit |
| --- | --- | --- |
| `python -m pip install -r requirements-dev.txt` | Passed | Fresh setup/UI/test installation; no model weights |
| `python -m pip check` | Passed | No broken installed requirements |
| `python -m pytest -q` | **21 passed in 0.43 seconds** | Original 7 plus 14 setup cases; includes explicit legacy mock tests, not accuracy proof |
| `python -m ruff check .` | Passed | Active source checks; archived prototype files excluded |
| `python app.py --check` | Passed | Explicit missing filing/index/model and `not_ready` |
| `python app.py` | Passed | Actual server launched at localhost port 7860 |
| `python scripts/check_setup_ui.py` | Passed | HTTP 200; actual Gradio callback returned `not_ready`, empty answer/evidence; blank input returned `invalid_input` |
| Git whitespace and targeted private-data scan | Passed | No conflict markers, whitespace failures, known credential patterns or private recipient in proposed tracked files |
| Schedule consistency | Passed | 19 dates, 7 members, 42 planned hours, 6 per member |
| Real provider, Chroma retrieval, financial accuracy | **Not run** | No verified model/index in this milestone |

The first UI attempt happened before installation finished and failed to import
Gradio. After installation completed, the real server and callback checks passed.
No paid provider call was made. Local detailed logs are in ignored
`output/verification/`; the portable evidence and commands are recorded here.

Setup versions actually installed: Gradio 6.31.0, python-dotenv 1.2.4, PyYAML 6.0.3,
pytest 9.2.0 and Ruff 0.17.3. All resolved setup/dev versions are in
[`constraints-setup.txt`](../../constraints-setup.txt). Dependencies were checked
against [PyPI](https://pypi.org/project/gradio/6.31.0/); environment loading follows
the [python-dotenv documented non-mutating API](https://bbc2.github.io/python-dotenv/).

## Where the project has reached

| PRD milestone | Current status | Remaining proof |
| --- | --- | --- |
| Day 1 scope/interfaces/checklists | Complete | Official course rubric/cutoff still not supplied |
| Day 2 reproducible setup and not-ready launch | Complete | Final full-machine release check remains Nov 16 |
| Real model and honest failure statuses | Not complete | Live success, invalid-key and no-evidence behavior |
| One-report ingestion and stable persistent index | Not complete | Hash, selectors, record counts, repeatable rebuild |
| Source-linked retrieval and UI | Not complete | Metadata preserved into included answer citations |
| Typed financial calculation | Not complete | Wired calculation with cited operands and unit/period checks |
| Matched baseline and held-out evaluation | Not complete | Frozen 7/7 split, all 14 outputs and actual scores |
| Report/slides/demo/final package | Not complete | Later scheduled deliverables |

Two scheduled setup assignments are complete; an overall project completion
percentage is not defensible from these tasks. A launchable screen is not proof
of a correct financial answering system.

## Remaining review findings

All locations below refer to reviewed revision `9943b74`. Findings are confirmed
by code inspection; severity concerns enabling the preserved prototype for real
answers. The new setup UI does not expose these legacy generation paths.

1. **P1 — false success in the legacy provider.**
   [`client.py:53`](https://github.com/sudhansh81205/FinRag-Project-/blob/9943b746238446c7be59ee3956a89de32c50d890/src/llm/client.py#L53)
   automatically falls back to a fixed successful mock. The Gemini path also tries
   unverified fallback model IDs. Minimal repair: explicit verified provider/model,
   test-only mock mode, and typed service failure. Prove invalid credentials cannot
   return the fixed revenue answer. Owner: Rushil, Nov 1.
2. **P1 — empty evidence and provider errors lack a safe answer contract.**
   [`finrag_engine.py:80`](https://github.com/sudhansh81205/FinRag-Project-/blob/9943b746238446c7be59ee3956a89de32c50d890/src/pipeline/finrag_engine.py#L80)
   generates without enforcing sufficient evidence and does not propagate a failed
   provider result into a clear status. Add early abstention and `service_error`;
   verify no generation call occurs with empty evidence. Owner: Rushil, Nov 1.
3. **P1 — source identity is not preserved into answers.**
   [`finrag_engine.py:63`](https://github.com/sudhansh81205/FinRag-Project-/blob/9943b746238446c7be59ee3956a89de32c50d890/src/pipeline/finrag_engine.py#L63)
   reduces records to strings. Retain IDs/metadata through retrieval, reranking and
   context; verify every citation maps to included evidence. Contract is now defined;
   ingestion/index/retrieval owners implement it on Nov 2–5 and Nov 8.
4. **P2 — zero table budget still reaches collection query.**
   [`retriever.py:87`](https://github.com/sudhansh81205/FinRag-Project-/blob/9943b746238446c7be59ee3956a89de32c50d890/src/retrieval/retriever.py#L87)
   can receive `n_results=0`, then catches the failure. Skip zero-budget queries;
   test baseline retrieval with a collection spy. Pavan's retrieval/baseline task.
5. **P2 — historical evaluation/calculator are not delivery evidence.**
   The three-case runner has no matched scored protocol and the math helper is not
   wired into generated answers. Retain as reference; complete typed arithmetic and
   the frozen two-mode evaluation in their assigned slots. Do not publish mock
   benchmark outputs as measured financial performance.

## Tomorrow and the next unfinished assignment

**Tomorrow, October 31: Shanay's first task is already completed early.** No extra
same-day worker, meeting or new task is assigned. The next unfinished scheduled
work is **November 1 — Rushil — two planned hours**.

1. Read the [master prompt](../review/MASTER_PROMPT.md), this report, the
   [handoff](../handoffs/2026-10-30_days-01-02.md) and the current main revision.
2. Verify one real provider/model on the demo machine; configure privately through
   the existing loader. Do not assume old hardcoded model names work.
3. Remove automatic mock/model fallback and map service failures to `service_error`.
4. Return `insufficient_evidence` before generation when no usable source is present.
5. Save one real-call record and deliberate failure checks, without secrets. Keep
   the UI not ready until its real evidence/provider prerequisites are validated.

Stack: existing Python 3.12, config/YAML/dotenv, `UnifiedLLMClient`, `FinRAGEngine`
and the application status boundary. Proposed provider dependency is
`google-genai==2.34.0`, or the existing requests client for a verified local Ollama
model. The real provider/model is **unverified**; install/verify it in that task.
No new framework or vector store is needed. Chroma 1.5.9 and sentence-transformers
6.2.0 are pinned in the full requirements but are not claimed runtime-tested here.

### Copy-ready implementation prompt

> I am Rushil, working on the November 1 FinRAG task with a two-hour budget. Read
> the current main PRD, MASTER_PROMPT.md and this October 30 completion report.
> Fix findings 1 and 2 in the preserved model client/engine using the central
> settings and response contract. Verify one real provider/model, remove hidden
> mock and model fallback, return service_error on provider failure, and abstain
> before generation for empty evidence. Use a clearly identified small source
> fixture if the future index is not ready. Do not enable unverified UI answering
> or implement other members' ingestion/index tasks. Save a real-call record,
> failure checks and a concise handoff without keys or fabricated results.

### Copy-ready verification/handoff prompt

> Review my November 1 changes against the exact main revision and the PRD.
> Run pytest, Ruff and the setup smoke check, then verify real success, bad
> credentials, empty evidence, unknown provider and explicitly selected test mocks.
> Confirm no fixed mock answer or unverified model fallback can look like live
> analysis. Record actual model/version, commands, results, missing proof and the
> dependency handed to Likhit for November 2. Keep unavailable checks unverified.

## Improvement bridge and delivery

| Current gap | Next task's change | Expected behavior / acceptance |
| --- | --- | --- |
| Provider errors can become mock success | Explicit provider plus failure status | Bad key never yields the fixed financial answer |
| Empty evidence can reach generation | Early evidence gate | Abstention without a provider call |
| Setup screen intentionally cannot answer | Connect only validated application behavior | Readiness remains honest until data/model exist |
| Missing ingestion/provenance/calculation | Preserve the new interface for later owners | Later work fits the same application without another branch split |

Optional chart/BM25/cloud work remains deferred. Official course requirements,
real model access and the final dataset/evaluation remain open information or
implementation items. This report is intentionally shared in GitHub at the user's
request. No WhatsApp delivery or mobile push is claimed.

Publication status is recorded below after remote verification.
