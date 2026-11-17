# FinRAG web workspace

Black/white, self-hosted Geist typography, keyboard navigation, responsive filing library,
evidence/calculation inspector, JSON export, clear failure states and optional private Supabase saved questions.
The DoTA design reference informed hairlines, spacing and restrained motion. No analytics or external asset requests.

## Local
For the prepared real-model workspace, run from the repository root:
```bash
.venv/bin/python scripts/run_local_workspace.py --status
# If stopped, start the existing verified assets (no download):
.venv/bin/python scripts/run_local_workspace.py --gradio-port 7860
```
Open http://127.0.0.1:4180/. Defaults point to this checkout's existing sibling Ollama/GGUF assets,
canonical source audit and BGE cache. Other machines must supply actual installed asset paths;
use `--help`. The launcher refuses occupied ports and changed assets. Reuse a healthy running
workspace; do not kill unrelated listeners. A partial startup needs inspection of `output/nov17/*.log`.

The optional shared-engine Gradio UI opens http://127.0.0.1:7860/. It uses the same engine/lock,
keeps session state separate and clears prior output on edits. See the current
[manual handoff](../docs/handoffs/2026-11-18_manual-workspace.md) and
[requirement ledger](../completion_status.md). The redesigned web workspace has three primary
navigation items, an evidence inspector, original chart review, exact JSON export and explicit
unavailable-feature reasons. It does not substitute browser-only storage for private user accounts.

The frontend alone can run without those assets:
Node22+; no npm dependencies or installation:
```
cd web
npm run dev
npm test
```
That frontend-only command opens http://127.0.0.1:4173/ and cannot answer financial questions
until its authenticated Python backend is configured.

## Long answers
The Python service advertises `jobs_supported`. The browser submits `/api/jobs` and polls
`/api/jobs/poll`, each using a short HTTP call. The prepared backend persists private SQLite
job status, runs one job at a time and accepts at most two pending jobs. A random 256-bit
job reference acts as a bearer capability; do not share it. Completed results must match the
exact original question, filing, period type and included evidence. Job access expires after
15 minutes; startup marks interrupted work failed and never silently repeats generation.
Transient polling transport failures are retried with bounded backoff, at most five consecutive attempts. Submission is never retried automatically, and completed model failures are final.
The model's own pinned timeout still applies. This queue is single-process: run one Python
service against a job store. Vercel is the stateless gateway; SQLite stays on the backend machine.

Cloudflare Quick Tunnels may bridge this authenticated API for an explicitly approved temporary
demonstration. They are not permanent hosting: laptop sleep or a stopped tunnel disconnects the
site, and a new tunnel needs the Vercel backend URL updated. Keep raw Ollama private.

## Current hosted demonstration
Open https://finrag-workspace.vercel.app/ in the signed-in Brave session. Vercel Authentication protects all deployments. Numerical and narrative answers were verified through the real hosted flow; chart acceptance and saved-query authentication remain pending. The initial deployment was bound to commit43ba054; the current aa52b98 receipt is linked below and uses the separately approved temporary laptop HTTPS API. This is a file/API deployment; a Git push alone does not redeploy it. See `../docs/reports/2026-11-18_deployment-receipt.json`.

## Vercel Hobby
Deploy this `web` directory as the project root. `vercel.json` serves `public` and the standard Node Function API.
Use default Hobby compute, no build-machine overrides, no paid model/Gateway calls.
The Node gateway never bundles local model weights or invents answers.

Configure server-only `FINRAG_BACKEND_URL` (HTTPS) and `FINRAG_BACKEND_TOKEN` to the authenticated prepared Python service.
The token must match that service's `FINRAG_API_TOKEN`. Missing runtime returns `index_not_ready` with empty answer.
Run `python scripts/serve_web_api.py --help` from the repository for the prepared-machine route.
Enable the engine only with current independent acceptance gates, a matching BGE/FAISS store, actual local weights,
the pinned provider and a real local generator tokenizer. No download or silent fallback occurs on startup.

## Supabase
Use the explicitly selected free FinRAG project. Inspect its existing schema first, apply `../supabase/schema.sql`,
then run `../supabase/verify_rls.sql` and advisors. Add `SUPABASE_URL` and a publishable key as
`SUPABASE_PUBLISHABLE_KEY` to Vercel. Legacy `SUPABASE_ANON_KEY` is supported; service-role keys are not used.
Configure the exact production origin as the Auth site URL/allowed redirect. The application requests a magic link
only when the visitor explicitly submits the sign-in form. Auth tokens are session-only; the server verifies `/auth/v1/user`
on every private request. RLS limits select/insert/delete to the owner; updates are not granted. Saved questions
are not accepted source records, benchmark gold or verified outputs.

Database provisioning, auth email delivery and two-real-user isolation require the actual account/runtime.
The committed SQL is not a claim that a database was created or those checks passed.

Provisioned project: `inygweteeaaozryxvmeh` (ap-south-1, free). Migration `20261116194117_finrag_private_saved_queries` is applied; transaction-based owner/cross-owner/anonymous checks passed and both advisors returned no findings.

Email activation is a separate release gate: set the Supabase Auth Site URL and redirect allowlist to the exact Vercel origin, configure permitted test recipients or SMTP and verify a complete sign-in. Then set `SUPABASE_AUTH_READY=true` in Vercel and redeploy. The default UI explicitly disables sign-in until this is verified. Database connection alone does not certify email delivery.

## Rushil runtime handoff
Read `../docs/handoffs/RUSHIL_START_HERE.md`. Local Node22 dev loads `web/.env`. An HTTP loopback backend is permitted only with `FINRAG_ALLOW_LOOPBACK_HTTP=true` outside production. Production still requires HTTPS. Answers have a bounded240-second gateway budget with250-second browser and300-second Vercel function limits; health probes use5seconds. Measure total planner+generation time before the live demo.

## Current 18 November workspace deployment

The redesigned implementation `aa52b98` is READY at https://finrag-workspace.vercel.app/ with existing Vercel Authentication. A real hosted gross-margin answer and focused source citation were verified. See the [current deployment receipt](../docs/reports/2026-11-18_workspace-deployment.json). The owner merged earlier PR18; current changes are in [PR19](https://github.com/sudhansh81205/FinRag-Project-/pull/19) for owner merge. Four current reports are in `../docs/reports/2026-11-18-completion-pack/`. The laptop API and temporary tunnel must stay running; full-study and Supabase gates remain open.
