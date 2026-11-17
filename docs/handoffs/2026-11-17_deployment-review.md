# FinRAG run and deployment handoff

This checkout contains the reviewed bounded real-model application plus the main-targeted integration branch. Read `../reports/2026-11-17_code-review.md` for fixed findings, verification and mandatory remaining research/account work. Final experiment readiness remains false.

## Open the prepared site

```bash
cd "/Users/rushilmohan/Documents/Codex/2026-11-02/go-th/work/finrag-nov17-completion"
.venv/bin/python scripts/run_local_workspace.py --status
```

Open http://127.0.0.1:4180/. If status says unavailable and the four service ports are free, start with:

```bash
.venv/bin/python scripts/run_local_workspace.py
```

The command reuses installed sibling Ollama/GGUF assets and this checkout's BGE/source audit. On another computer pass actual asset paths via `--help`; no downloads or guessed models are performed. Existing occupied listeners are not taken over. If startup partly fails inspect `output/nov17/*.log` and verify the process identity before cleanup. Frontend-only `cd web` then `npm run dev` opens4173 but has no financial engine unless configured.

## What to try

Select Apple FY2021, requested value end2021-09-25 and a fiscal-year duration. Use the numerical gross-margin example: expected41.78% with cited cells and inspectable checked calculation. The supply-chain example uses real narrative evidence and can take minutes on this machine. The chart example must refuse until independent labels and G are accepted; this is an expected incomplete feature.

Answers now use authenticated jobs/polling when the backend supports it. Do not share random job references. The queue is single-process, two pending jobs, private SQLite status and15minute access expiry. A restart does not replay unfinished work. The model's pinned timeout remains unchanged.

## Hosted route

Production is live at https://finrag-workspace.vercel.app/ with Vercel Authentication protecting all deployments. Open it in the existing signed-in Brave session. The user explicitly approved the replacement project after the initial automatic-review rejection. Deployment dpl_AMF3Aavw6tit36aY6B8uSE5sv6ik serves reviewed app commit43ba054ad832d8615f855b71fd7dcf0725d7f2f3, using Node22 and server-only sensitive backend credentials. This is an API/file deployment; Git pushes do not automatically redeploy it.

The user approved a temporary HTTPS tunnel to the authenticated Python API. Its changing URL and process record are in local ignored `output/nov17/tunnel.json`; keep the matching token private. The raw model endpoints stay on loopback. The laptop/model/API/tunnel must stay alive. A recreated tunnel requires a server-only Vercel backend URL update and redeployment. Do not put credentials in frontend files or Git.

The signed-in Supabase account currently has no FinRAG project in either accessible organization. Reuse the correct existing project only after access is resolved. Keep SUPABASE_AUTH_READY false until exact redirects, email delivery and two-real-user private-query checks pass.

## Research commands and limits

```bash
.venv/bin/python scripts/generate_case_inventory.py --benchmark-dir output/benchmarks/official
.venv/bin/python scripts/freeze_controls_manifest.py --benchmark-dir output/benchmarks/official
.venv/bin/python scripts/run_benchmarks.py --gate-report
.venv/bin/python scripts/run_benchmarks.py --profile-capacity --benchmark-dir output/benchmarks/official
```

The first inventories3010selectedcases, not accepted cases. The second creates a draft only, never a named human freeze. Capacity timings remain unknown without a recorded representative pilot. `run_benchmarks.py --enable-engine` can explicitly prepare accepted C/D with actual tokenizer/cache paths, but official benchmark contexts remain UNBOUND; no final run is implied. A/B/E/F/G adapters and independent approval remain mandatory.

## Verification

530Python tests passed,17Node tests passed, Ruff and diff checks passed. See `../reports/2026-11-17-deployment/`. Real browser narrative and numerical success were observed separately from those injected regressions. Authenticated HTTPS health passed200 and unauthenticated401. Final frozen experiments0/28, independent generated-output audit0/50 and course receipt unverified.

## Publication and actual observation date

[PR18](https://github.com/sudhansh81205/FinRag-Project-/pull/18) targets main. [CI run44147510311](https://github.com/sudhansh81205/FinRag-Project-/actions/runs/44147510311) passed for43ba054. Main integration still requires maintainer access. Deployment was built before midnight17November IST; hosted numerical/chart verification continued on18November IST and is not credited as a completed17November course submission. See the dated deployment receipt for final browser results.
