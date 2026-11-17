# FinRAG - Rushil completion handoff

Prepared 17 November 2026 (India time). Read this first, then give `RUSHIL_CODEX_PROMPT.md` to GPT/Codex **inside this repository on Rushil's computer**. This is a user-requested technical handoff; it does not rewrite historical contributions, certify human hours, merge a PR or submit coursework. Preserve the existing single-owner calendar. Obtain an explicit schedule decision before assigning additional people off-day work.

## 1. Where the project actually stands

Repository: https://github.com/sudhansh81205/FinRag-Project-

PR16: https://github.com/sudhansh81205/FinRag-Project-/pull/16

Inspection base: `87fd8210b6dafd1b3ed7bc14ef94ec75e1c75ac1`; PR16 was OPEN, mergeable and unmerged when checked. Use its current head, including this handoff, rather than assuming main contains the frontend. Previous CI at this base passed491Python tests and10gateway tests. Re-run current checks after further changes; test counts are not a completion percentage.

The monochrome frontend is deployed on Vercel Hobby at https://finrag-research.vercel.app. It has Vercel login protection. Supabase Free project `inygweteeaaozryxvmeh` is healthy; private saved-question schema/RLS is applied and tested. Email activation remains gated. This machine has no working Ollama endpoint, BGE weights/index or generator tokenizer. The new preflight recorded those blockers; no local-model answer was fabricated.

Three distinct finish lines:

1. **Runtime working:** real pinned model + accepted BGE/exact FAISS + tokenizer + a source-grounded success and meaningful failure.
2. **Presentation ready:** working real demonstration, checked six-slide deck, evidence-backed report, recorded backup and rehearsed viva. Missing full-study work must still be labelled partial.
3. **Full proposal complete:** all mandatory corpus, A-G, authentic benchmarks, RAGAS, separate Llama comparison and independent audits also pass. A polished website or a successful Apple example alone cannot establish this.

## 2. Remaining work, who can do it, and proof of done

| Priority / requirement | Remaining work and method | GPT/Codex can do | Human/machine dependency and finish evidence |
| --- | --- | --- | --- |
| 1 - R4/R13, common A-G | Open exact branch; start local Ollama; verify pinned Gemma digest/quantization; run live smoke | Inspect/install dependencies, execute and diagnose on Rushil's machine | Rushil supplies computer access, power/network and any installation/login interaction. Save current model fingerprint and real success/failure traces |
| 2 - R1/R2/R3 | Recover accepted source packages; acquire missing declared filings; parse, audit and build BGE IndexFlatIP | Download permitted public sources, implement supported parsing, produce lossless cells/parents and checked indexes | Broader independent acceptance cannot be fabricated. Five Apple + five Microsoft + ten companies must reconcile to accepted/indexed packages, not inventory counts |
| 3 - R10/R12, A-G | Complete actual stage adapters and shared token controls | Implement/test A/B representation loading, real E cross-encoder, F routing and G accepted captions | Current web builder supports C/D only. Prove enabled-stage execution, disabled-stage zero calls and common source eligibility; save real traces |
| 4 - R7/R12 | Import authentic official FinQA/TAT-QA/FinanceBench open150 and bind each case's source-equivalent corpus to retrieval | Write import/context adapters, CLI engine factory, unit/failure tests and provenance ledgers | Current candidate files are smoke fixtures. Current benchmark CLI injects NO engine; current runner reports contexts UNBOUND. These are coding tasks, not flags to flip |
| 5 - R7/R11 | Independently check fifty chart questions/captions; predeclare separate fifty-output sample | Build review sheets with original images, sources, hashes and authors; calculate shortfalls | An eligible independent person must inspect and record substantive decisions. Rushil/Codex cannot impersonate another reviewer or approve Rushil-authored labels independently |
| 6 - R7/R12 | Measure capacity, freeze controls, run full Gemma A-G, pinned RAGAS and separate Llama comparison | Measure actual cold/warm/evaluator timings; checkpoint; compute metrics and paired95%intervals | Intended machine must stay available. Use actual case counts and deadline; report insufficient capacity and exact unfinished scope immediately |
| 7 - R6/R13 | Connect the real Python backend to local frontend and then Vercel; verify source/math/error flows | Run services, add authenticated hosting configuration, browser/session tests and restart checks | Rushil keeps laptop awake. Cloud cannot reach his127.0.0.1. A chosen authenticated HTTPS route needs owner approval/setup; never expose raw Ollama |
| 8 - Web persistence | Configure Supabase Auth Site URL/redirects and verify two real users | Explain/apply available project settings, test own/cross-user isolation | Account owner performs login/OTP and any email-provider setup. Activate `SUPABASE_AUTH_READY` only after real delivery and redirect tests. No paid SMTP assumed |
| 9 - R8/R13 | Final report, exactly six slides, real backup demo, archive and restore | Generate result tables, revise report/deck from real evidence, check files and hashes | Humans verify claims, contributions, rehearse viva and approve final submission. Actual official route/cutoff and receipt must be observed |

R9 restatement comparison stays unscheduled Phase2. Supabase holds personal saved questions; it does not replace the required exact FAISS index with pgvector. Primary A-G stays on one pinned Gemma setup; Gemini remains an optional separately labelled demo provider.

## 3. First setup on Rushil's computer

Use a **new checkout** so existing local work is safe. Terminal commands below use macOS/Linux syntax, matching the historical Mac trace. Windows equivalents follow. Read `AGENTS.md`, `docs/plan/PRD.md`, `TASK_REQUIREMENTS.md`, `COURSE_ALIGNMENT.md`, `EVIDENCE_CONTRACT.md` and `schedule.json` before changing controls.

```bash
git clone --branch maintenance/verified-finrag-web --single-branch https://github.com/sudhansh81205/FinRag-Project-.git FinRAG-completion
cd FinRAG-completion
git rev-parse HEAD
git status --short
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt -r requirements-index.txt
python scripts/preflight_handoff.py --probe-ollama
```

If `python3.12` is absent, install a supported Python3.12 from its official source, or explicitly test another interpreter rather than assuming compatibility. Native FAISS/PyTorch wheels must match the platform. The index requirements download several GB of packages; model weights are separate. On an8GB Mac avoid running Gemma, Llama and a large evaluator simultaneously.

Windows PowerShell environment setup:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -r requirements-index.txt
python scripts/preflight_handoff.py --probe-ollama
```

If PowerShell blocks activation, invoke `.\.venv\Scripts\python.exe` directly; no execution-policy/security weakening is required. Preflight exit2 means prerequisites remain blocked. It does not install models, start daemons, generate answers or create approvals by default.

## 4. Activate the existing local model

Gemma3 is pretrained; no training job is required. First inspect the existing installation and preserve the pinned profile.

```bash
ollama --version
ollama list
curl -fsS http://127.0.0.1:11434/api/tags
```

If the endpoint is unavailable: on Mac open the installed Ollama app with `open -a Ollama`; on Windows start Ollama from Start. If no app/service manages it, run `ollama serve` in its own terminal. An address-in-use message usually means it is already serving; check `/api/tags` before starting a second instance. Leave the bind address on loopback. Install Ollama from https://ollama.com/download only if absent.

Expected profile in `configs/gemma3-4b.json`:

- Tag `gemma3:4b`, quantization `Q4_K_M`, vision capability.
- Digest `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7`.
- Temperature0, seed42, context4096, output768; current provider timeout180seconds.

If weights are absent, `ollama pull gemma3:4b` downloads the current tag. **A tag can change:** run the preflight afterward. If its digest differs, recover the original verified artifact or deliberately version a replacement, then re-freeze controls and rerun the affected comparisons. Do not simply overwrite the digest to make a check green or mix old/new outputs.

```bash
python scripts/preflight_handoff.py --probe-ollama
python scripts/preflight_handoff.py --generate-smoke
ollama ps
```

The second command explicitly runs one real, nonfinancial connectivity prompt. It is not retrieval or benchmark validation. Missing-model/digest failures must remain errors, with empty financial answers. Official API references: https://docs.ollama.com/api/tags and https://docs.ollama.com/api/generate.

## 5. Prepare real sources, exact index and tokenizer

These existing commands reproduce the bounded Apple package; they do not create broader acceptance automatically:

```bash
python scripts/parse_filing.py
python scripts/prepare_evidence.py
python scripts/verify_day05_environment.py
python scripts/verify_canonical_data.py
python scripts/build_index.py --download-model
python scripts/verify_index.py
python scripts/run_rushil_checks.py --output output/rushil-current-runtime
```

Use `--download-model` only for the first permitted public BGE download; later runs use cache. BGE is `BAAI/bge-base-en-v1.5`, pinned revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`, normalized768dimensions with exact IndexFlatIP. A copied old audit must not authorize changed inputs. `run_rushil_checks.py` is a source-selected generation/math/vision smoke, not a full BGE search experiment.

Obtain the exact Gemma3 generator tokenizer in a local directory. The official Hugging Face model may require Rushil to accept its licence and authenticate personally. Do not put access tokens in this handoff, repository or browser bundle. Pin tokenizer revision/files and verify that it matches the generator/template; a directory's existence alone is insufficient. Pass the actual directory:

```bash
python scripts/preflight_handoff.py --probe-ollama --tokenizer-dir /absolute/path/to/gemma3-tokenizer
python scripts/run_benchmarks.py --gate-report
```

All seven acceptance gates were closed on this handoff machine because there is no current accepted-artifact ledger. A valid gate needs real artifacts, exact hashes and legitimate acceptance. Never fabricate `accepted_by`, reviewer marks or timestamps. A ready local model does not open corpus/chart/reranker gates.

For broader inputs inspect `scripts/acquire_corpus.py`, `build_corpus_candidates.py` and `audit_corpus_candidates.py` with `--help`. Repair supported layouts and create candidate packages; keep original source/period/unit/cell identities and unsupported cases. Preserve the canonical Apple package. New candidates need appropriate independent checks before production/final evaluation.

## 6. Make the actual application work

After the required C/D resources and acceptance gates genuinely pass, configure the root `.env` with the pinned Ollama values from `.env.example`. Generate a separate private backend token; keep it out of logs and Git. Start on the same machine:

```bash
export FINRAG_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python scripts/serve_web_api.py --enable-engine --variant D --tokenizer-dir /absolute/path/to/gemma3-tokenizer
```

PowerShell token equivalent: `$env:FINRAG_API_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"`.

In a second terminal, create **local** `web/.env` (ignored by Git), using the SAME token:

```text
FINRAG_BACKEND_URL=http://127.0.0.1:8000
FINRAG_BACKEND_TOKEN=<same private FINRAG_API_TOKEN>
FINRAG_ALLOW_LOOPBACK_HTTP=true
FINRAG_BACKEND_TIMEOUT_MS=240000
```

```bash
cd web
npm run dev
```

Open http://127.0.0.1:4173. Node22+ loads `web/.env`; HTTP loopback works only with the explicit development opt-in. Production rejects HTTP and LAN addresses even if that flag is set. This local path avoids a tunnel during the first real demonstration.

For Vercel, the architecture is: **browser -> Vercel API -> authenticated HTTPS Python backend on Rushil's machine -> local Ollama + BGE/FAISS**. Keep Ollama11434 private. Use an owner-approved HTTPS reverse proxy/tunnel exposing the authenticated Python8000 service, not the raw model. Laptop sleep, power loss or a stopped tunnel makes the site unavailable. Configure only server-side `FINRAG_BACKEND_URL=https://...` and matching `FINRAG_BACKEND_TOKEN` in Vercel, then redeploy and test401without the token. Do not turn off Vercel protection or publish a new tunnel without the owner's explicit approval.

The patched gateway allows up to240seconds for an answer,250seconds in the browser,300seconds for the Vercel function; health checks use5seconds. These are deadlines, not measured model latency. Two180-second model calls can still exceed the overall deadline: measure actual planner+generation time. If it cannot fit reliably, implement an authenticated bounded job/poll flow on the backend rather than silently changing experimental model/output controls. Hobby Fluid Compute currently supports300seconds: https://vercel.com/docs/functions/configuring-functions/duration.

For Supabase, the account owner sets the exact deployed origin as Auth Site URL and allowed redirect, verifies email delivery and two real users, then enables `SUPABASE_AUTH_READY=true` and redeploys. Keep service-role keys out of browser/server gateway. No paid plan or new database is required.

## 7. Complete research execution - real coding still required

Opening Ollama is not enough for the following. Rushil's Codex should implement them, verify failures and update the report before launching final runs:

1. **Benchmark engine factory:** `scripts/run_benchmarks.py` currently creates `BenchmarkRunner` without an engine. Supply an explicit prepared engine for the requested variant and reject mismatches. Do not claim the current CLI runs a financial experiment.
2. **Context binding:** `src/benchmark/runner.py` currently queries the engine's own index and marks benchmark context UNBOUND. Build source-equivalent per-suite candidate indexes from the official text/tables, preserve stable IDs/periods/units and derive actual included context. Exclude gold/program/answer labels from prompts and retrieval. Test that unrelated report facts cannot answer another benchmark case. Keep the blocked status until this is genuinely implemented.
3. **A/B/E/F/G execution:** connect matched flattened/section/cell representations, load the real pinned bge-reranker-base, freeze F thresholds using development only, and add independently approved source-linked chart captions for G. Current web factory explicitly supports C/D only; new choices need real adapters, not renamed variants.
4. **Authentic data and evaluator:** replace smoke candidate files with legitimate versioned imports (without deleting original fixtures), exact provenance and exclusion ledgers. Pin and execute RAGAS; add the separate Llama run. A provenance string, placeholder evaluator or fake latency is not proof.
5. **Capacity before freeze:** measure actual cold/warm/planner/retrieval/evaluator times on representative development cases. Multiply full eligible counts by7variants and include caption/evaluator/retry time. Save estimates against actual remaining machine availability. If it cannot fit, state the exact shortfall; the deadline does not authorize a silent subset.
6. **Freeze, run, audit:** predeclare cases, chart15dev/35held-out image groups and the separate seeded fifty-output audit sample before scores are inspected. Run immutable jobs and retain failures/timeouts/exclusions. Independently inspect actual included passages and original evidence. Compute numerical/narrative/retrieval/RAGAS/latency measures with paired95%intervals.

The existing inventory/freeze/sample utilities are starting points; read their source and current command interface. Do not present them as a finished end-to-end evaluation orchestrator. No audit requires inventing additional same-day member duties: resolve reviewer eligibility/scheduling with the project owner.

## 8. Presentation and final acceptance checklist

Before saying **presentation ready**, save and actually open:

- A real narrative answer with source; a checked numerical answer (the known Apple FY2021 margin is a useful regression); an approved chart path when G is available.
- A wrong issuer/period or excluded-operand refusal and a stopped-service error, with no stale previous answer. Repeat from a second session and after restart.
- Current report and exactly six slides: (1)title/overview, (2)problem/motivation, (3)related work/theory, (4)architecture/A-G, (5)actual results and limitations, (6)actual contributions/course concepts/viva. Existing PPTX is a historical draft; rebuild and visually check after updating results.
- A real recorded demonstration plus offline source/result exports; a written procedure alone is not a backup recording. Rehearse from the release checkout.
- Complete/partial requirement ledger, AI-use disclosure, code/data/model/tokenizer manifests and one archive. Restore that archive in a fresh environment and verify it opens/runs. Submit only through the actual authorized course route and save the genuine acknowledgement.

Before saying **full proposal complete**, additionally require accepted broader coverage, authentic complete benchmark universes, actual A-G/RAGAS/Llama results, fifty independent chart decisions and fifty separately audited generated outputs. Failures/exclusions/undefined metrics must remain in the denominators. No completion guarantee can be based only on handing over these documents.

Viva: typed issuer/period/unit/source predicates license restricted Decimal arithmetic (KR&R); BGE, cross-encoder, Gemma and chart vision are transformer/DL components; A-G tests incremental changes under fixed controls. BM25/RRF and routing do not establish A*, minimax, game theory or multi-agent reasoning.

## 9. Work completed during this handoff

- Added `scripts/preflight_handoff.py` with installed identity, native exact-store and tokenizer checks; it never invents approvals and defaults to no generation/download.
- Added meaningful digest/quantization/host-isolation regression tests; recorded this machine's real blocked runtime inventory.
- Enabled an explicit development-only loopback backend path and `.env` loading, making a same-machine frontend demo practical without exposing Ollama.
- Increased bounded answer deadlines for local inference while keeping short health checks and production HTTPS requirements.
- Fixed stale result handling when a question, company, filing, period or example changes, and locked query controls while an answer is pending.
- Rechecked the deployed interface in a real browser: inventory/search/filing transfer, missing-engine refusal, email-disabled dialog and mobile layout. The new preview also verified query controls lock during an answer and restore afterward; filing changes clear the previous result. See PR16's latest checks for exact evidence.

These address R2/R4/R6/R12/R13, common A-G runtime/reproducibility and UI integrity. Success: same pinned model/source-bound output; failure: changed digest, missing assets, wrong request, unavailable service or production HTTP refuse. They do not implement the missing full research runner or independently approve labels.


## Superseding runtime evidence

Read [November17 runtime implementation](../../docs/handoffs/2026-11-17_runtime-completion.md). Pinned Gemma, BGE/exact FAISS,18candidate filing indexes and official150/1147/1663benchmark imports are now verified locally. Full combined517tests and13Node checks passed. The user confirmed no human independent review exists. Full A–G/evaluator/hosting/submission acceptance remains incomplete. This update does not establish completed human effort.
