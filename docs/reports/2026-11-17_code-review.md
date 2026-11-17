# FinRAG code review and deployment check

Observed 17 November 2026. This is the user-authorized implementation and review session, not a recurring read-only nightly review. Sole scheduled final-day owner: Sudhansh; hours remain estimates. No new assignment, human approval or course submission is created by these changes.

## Verdict and reviewed revisions

The prepared Apple FY2021 application produces real cited narrative and numerical answers. This is a functioning bounded demonstration and a partial research project. It is not a completed A–G evaluation or a completed course submission.

Reviewed remote main: `c6ebf57f99b8998677a0aad3302eba079968180e` (PR16 merged). PR17's runtime repair head `d41130f0c6cecea33055754b0725293cbf6f5a31` was merged into `maintenance/verified-finrag-web`, not main. This branch `maintenance/nov17-deployment-review` merges main at `9129d4f` and adds the reviewed repairs below. The publication record/PR identifies its final published head; publication is not a claim of main integration.

## Findings repaired

### F35 High — unsupported experimental freeze and capacity attribution

`scripts/freeze_controls_manifest.py` inserted a person's name as frozen_by and hardcoded hardware, run hours and an approved subset. These are not observations or human acceptance. Replaced this with an actual-input draft manifest: no frozen person/date, no measured capacity, no approved reduction, and explicit missing freeze evidence. The old `docs/reports/2026-11-15_frozen_manifest.json` is retained as a superseded, unverified draft with withdrawn approval and gate claims. It must not certify a final experiment.

Related repair: `scripts/generate_case_inventory.py` now requires an explicitly selected input directory, reloads actual cases, hashes bytes and IDs, verifies any import manifest and records provenance. Counts or a manifest cannot promote synthetic smoke fixtures to authentic inputs. Capacity can consume those exact selected counts. Current selected official files plus authored chart candidates contain 150 + 1,147 + 1,663 + 50 = 3,010 cases, or 21,070 primary variant queries before evaluators/comparison/retries.

R7/R12/R13; common A–G controls; experiment validity and accountable AI. Positive check: selected counts/hashes round-trip. Failure checks: changed imported bytes, inconsistent totals and fixture-only provenance fail or stay explicitly limited. Viva: a file count or an assistant-authored approval field cannot establish independent label validity, actual throughput or a controlled freeze.

### F36 High — synchronous long model calls break the website path

Real narrative execution approached the previous gateway deadline. Added a bounded authenticated answer queue in `src/web_jobs.py`, connected through `scripts/serve_web_api.py`, `web/lib/api.mjs` and `web/public/app.js`. Vercel can submit and poll using short HTTP calls while the Python worker owns generation. SQLite state is private mode0600, references are random256-bit capabilities, access expires after15minutes, one model worker runs, at most two pending jobs and100 total records are allowed. Restart marks unfinished jobs failed rather than repeating calls. Errors are sanitized and completed payloads are cleared. An initial HTTPS probe exposed a transient poll failure while the job kept running; the browser now retries only polling transport failures up to five consecutive attempts, with bounded backoff. Submission is never automatically repeated, and completed model failures are final.

Successful results must match the exact original question/company/filing/value period/period kind/scope/mode and the actual included evidence IDs. The legacy synchronous route and queued work share a nonblocking application lock to prevent concurrent model execution. This transport does not alter the pinned model's own timeout or research controls. It is a single-process demonstration queue, not a horizontally scalable cloud queue.

R4/R6/R13; common A–G serving; supporting distributed-systems engineering and failure transparency. Positive checks: real browser numerical41.78% with five evidence objects, and a real cited supply-chain narrative. Failure checks: wrong question/period/citations, full queue, expiry, restart, provider exception and concurrent entry all return empty financial answers. Viva: polling changes HTTP lifetime; it does not make a failed or over-time provider invocation successful.

### F37 Medium — saved questions lose period semantics and can display a stale private response

The save API omitted period_kind, so reloading an instant balance could switch interpretation to a duration. It now retains the selected type. Saved-list responses are discarded if the sign-in token or render revision changed while the request was in flight. Starting new research clears result/export/save state through the same invalidation function used for changed requests.

R5/R6/R13; common A–G request boundary; typed financial premises and privacy. Positive check: an instant request is persisted with its type. Failure check: expired/anonymous access remains denied and responses bound to another period are rejected. Live two-user email-login isolation is still unverified; injected Node tests do not establish it.

### F38 Medium — CLI never supplies a real engine

The benchmark CLI previously constructed a runner without an engine. An explicit `--enable-engine` route now builds the prepared C/D engine only, with the real digest-pinned Gemma profile, accepted assets and tokenizer requirements. Missing acceptance fails before model loading; unsupported A/B/E/F/G do not silently alias C/D. This closes only factory wiring for the existing prepared runtime. The runner still refuses UNBOUND official contexts; a prepared application filing index is not a source-equivalent benchmark corpus.

R4/R7/R12; C/D runtime and common controls; pretrained transformer embeddings/generation and controlled experiment interfaces. Positive unit check: the selected variant/settings reach the factory. Failure checks: unsupported variant/provider or closed acceptance refuse. No full real benchmark execution is claimed from these injected tests.

## What is actually available

- Application inventory:18filings/10companies, all parsed into candidate A/B/C indexes with previous reproduction evidence. Only one independently accepted application filing is reported; wider candidates are not silently accepted.
- Real local assets: pinned Gemma3:4b, BGE-base-en-v1.5 at768dimensions, exact FAISS, BM25/RRF60, source-bound Apple records, installed GGUF tokenizer and restricted Decimal calculator. Numerical semantic coverage is bounded; gross margin correctness does not prove arbitrary financial interpretation.
- Authentic source imports:150FinanceBench,1,147FinQA,1,663TAT-QA and all84FinanceBench full PDFs.65unreadable pages remain declared. No annotated support-page shortfall was found in the previous extraction. Candidate provenance/coverage is separate from independent acceptance.
- Real interface: filing selection, period type, narrative/numeric answers, evidence/calculation inspection, export, honest chart refusal, and optional private saved questions when configured.
- Existing partial report, exactly six visually checked slides and prior restored archive. The earlier archive is bound to5b065a4 and does not include this review's changes.

## Current verification

`docs/reports/2026-11-17-deployment/pytest.txt`:530passed,3FAISS/SWIG deprecation warnings,127.73seconds. A prior sandbox-only attempt failed its socket bind; the permission-enabled suite passed. `node.txt`:17passed. `ruff.txt`:all checks passed. `git diff --check` passed.41focused tests cover the new queue, concurrency, real-inventory capacity, factory gates and occupied-port safety.

Real browser results are development observations, not final accuracy/latency statistics. Numerical41.78% and a source-cited narrative completed; selecting an unapproved chart cleared the old answer and returned not-ready. The approved temporary HTTPS route rejects requests without credentials with401 and returns ready/jobs_supported with authenticated200. No token is stored in this report, public bundle or screenshots. The repaired production gateway handler subsequently completed the real HTTPS queued numerical request in13.814seconds, returning41.78% and five matching evidence objects; `https-gateway.json` preserves the bounded observation and `https-gateway-initial-failure.json` retains the first failure. This is local handler execution over HTTPS, not a Vercel deployment or a representative throughput pilot.

## Hosting and account state

Vercel team access was successfully granted in Brave and the connector now works. The earlier finrag-research project/deployment is absent from this authorized team. The initial attempt to create protected finrag-workspace was rejected by automatic approval review. The user subsequently explicitly approved it; creation and protected production deployment succeeded. This supersedes the earlier pending status. The separate temporary authenticated HTTPS connection was explicitly approved and is running. Only API8000 is tunneled; Ollama/tokenizer remain loopback.

The Supabase account is now signed in as the existing GitHub account. Both accessible organizations were inspected at project-list level; none contains the repo's recorded FinRAG project. Its historical SQL/advisor receipt is retained as earlier evidence, not a fresh account-access claim. Do not attach unrelated databases or enable email auth without verifying the right project, exact deployed redirect and delivery. No new billing or paid compute was configured.

A Quick Tunnel depends on the laptop, local model/API and tunnel remaining alive. It is an approved temporary demonstration connection. Permanent unattended hosting and the two-real-user sign-in test remain open.

## Mandatory open work in dependency order

1. Integrate the main-targeted repair PR and verify CI at its actual main head. Fork publication alone is not main integration; current team permissions cannot merge it.
2. Build source-equivalent official benchmark retrieval corpora/adapters with stable case/evidence identity. Keep gold answers/programs/support selections out of inference. Declare TAT-QA issuer/accession mapping limits and65unreadable FinanceBench pages.
3. Connect A/B representations to real benchmark execution; provision and trace real E cross-encoder assets; complete bounded short-model F routing and development-only threshold calibration; connect G only after genuine input approval. Keep common BGE/exactFAISS/Gemma/prompt/calculator/five-passages/token/seed controls matched.
4. Obtain genuine independent input acceptance, including all50chartquestions/sixcaptions and wider source/cell/index checks. The prepared packet remains unreviewed; the user confirms no independent review exists.
5. Measure representative development throughput including planner/generator/evaluator/cold start/failures and memory; resolve scope/capacity before a genuine freeze. Do not substitute guessed hours or an invented approved subset.
6. Freeze accepted identities, development thresholds, exact denominator/exclusions and a predeclared independent output sample. Run all seven variants on all four suites: currently0/28finalcells completed. Record full failures/timeouts/shortfalls.
7. Execute real RAGAS, separate Llama3.2 comparison, numerical tolerance/zero-gold policy, Recall@5/10, MRR, narrative metrics, latency and paired95%intervals. Produce an independent50-generated-output audit, currently0/50, distinct from chart-label review.
8. Protected Vercel production is now deployed; the hosted numerical flow and chart refusal were verified after midnight18November IST. Resolve correct Supabase project access and complete the remaining deployed browser/model flows. Test two real signed-in users, expiry/logout and owner isolation before enabling sign-in. Verify mobile/keyboard/reduced-motion and provider/tokenizer/tunnel outages. A permanent backend needs an explicit host.
9. Validate financial formula semantics beyond gross margin. Preserve source/type checks and explicit refusal for unsupported operations; do not count a numerically correct but financially wrong formula as success.
10. Update report and exactly six slides with actual research results, contributions/AI-use/source records, record a real backup demonstration, rebuild and restore the final package, and obtain the actual course upload receipt. No verified receipt currently exists. R9 restatement comparison remains unscheduledPhase2.

## Requirement acceptance ledger

| Requirement | Actual current evidence | Missing acceptance or execution |
| --- | --- | --- |
| R1 corpus |18candidatefilings,10companies; one accepted Apple filing | Independent wider source coverage |
| R2 index | Real pinned BGE/exactFAISS and candidate A/B/C reloads | Wider independent acceptance and matched final adapters |
| R3 evidence | Typed source/cell/parent checks and reproduction | Broader source semantics/locators acceptance |
| R4 generation | Real pinned local Gemma answers | Representative capacity, final runs and separate Llama comparison |
| R5 calculation | Restricted cited Decimal programs and gross-margin semantic checks | Other required financial interpretations and benchmark operations |
| R6 interface | Working queued web narrative/numerical flow and existing Gradio path | Accepted charts, complete two-client/real-auth and hosted verification |
| R7 evaluation | Loaders, immutable runner gates, inventory and draft tooling |0/28finalcells; genuine freeze/metrics and independent50-outputaudit |
| R8 delivery | Partial report/sixslides/priorarchive | Actual final results/demo/package and submission receipt |
| R9 Phase2 | Unscheduled by current PRD | Not a prerequisite |
| R10 retrieval | Common eligibility, C/D and tested stage contracts | Actual matched A/B and real E/F/G end-to-end execution |
| R11 charts | Siximages,50questions,6captions and review packet | Genuine independent acceptance and G loading |
| R12 controls | Guarded identities/five-passages/token/calculator and honest draft | Accepted matched final freeze and development-only F calibration |
| R13 reproduction |530Python/17Node/Ruff; prior prepared restore | Fresh-machine final model restore and remaining hosted/auth checks |

No percentage completion is inferred from this mixed acceptance ledger.

## Sole-owner handoff and viva

Sudhansh remains the17November release owner. No later recovery date or extra named same-day reviewer is invented. Human independent decisions cannot be created by automation or by self-approval.

Copy-ready next-work instruction: Read the canonical PRD, this review and the exact main-targeted PR. Verify main/PR/asset hashes first. Close official-context source equivalence and the actual A–G runtime stages without changing common controls, then obtain eligible independent acceptance. Measure capacity, freeze and run the declared scope; preserve every failure/denominator. Finish the independent50-output audit and genuine deployment/submission evidence. If an input or approval is missing, keep the result partial and identify the precise missing artifact.

Viva explanation: typed facts and predicates license cited arithmetic only for the correct issuer, scope, period and unit. BGE/Gemma are pretrained transformer applications; actual E requires a joint query/passage cross-encoder. BM25/RRF and queue scheduling are retrieval/control and supporting engineering, not A*, minimax, game theory or multi-agent inference. Independent chart review establishes label validity; a SHA only establishes unchanged bytes.

## Post-publication deployment update

The user approved protected finrag-workspace and deployment after the initial rejection. Production https://finrag-workspace.vercel.app/ is READY, deployed from app commit43ba054; project protection remains all-deployments Vercel Authentication and backend credentials are server-only sensitive variables. Node22 is pinned. PR18 targets main, and GitHub run44147510311 passed at43ba054. Later documentation commits update this receipt without changing the deployed web source. Hosted numerical41.78% and unapproved-chart refusal were observed on18November IST. Source/evaluation/human-review/course-receipt gaps above remain open. This update does not backdate completion to the17November cutoff.

Final hosted verification: both numerical41.78% and source-cited narrative succeeded, each with five complete evidence objects. An unapproved-chart request cleared the previous answer and returned index_not_ready. A separate anonymous probe reached Vercel login. See `2026-11-18_deployment-receipt.json` for the deployment identity, actual observation time and screenshot hashes. Correct Supabase access, two-real-user email checks and permanent hosting remain open.
