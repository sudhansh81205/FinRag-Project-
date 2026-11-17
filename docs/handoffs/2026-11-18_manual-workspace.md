# FinRAG manual workspace handoff

The bounded real-model workspace is ready for manual checks. The complete research study remains partial; see `../../completion_status.md` and the dated code review. The17November scheduled release owner remains Sudhansh; no18November recovery assignment or human hours are implied.

## Current prepared host

```bash
cd "/Users/rushilmohan/Documents/Codex/2026-11-02/go-th/work/finrag-nov17-completion"
.venv/bin/python scripts/run_local_workspace.py --status
```

Web: http://127.0.0.1:4180/. Gradio: http://127.0.0.1:7860/. Protected hosting: https://finrag-workspace.vercel.app/. Existing services are already running. Keep this laptop awake with API/model/tunnel alive for hosted answers. No interactive chat or per-question approval is needed.

If all corresponding ports are free and services are stopped:

```bash
.venv/bin/python scripts/run_local_workspace.py --gradio-port 7860
```

The launcher reuses the existing sibling Ollama/GGUF assets, canonical source audit and BGE cache. It refuses changed assets or occupied ports. Do not kill a reused PID or run a second copy over existing listeners. On another machine, use `--help` and supply actual existing assets; this is not a fresh-machine model installer.

## Manual sequence

1. Select Apple FY2021, value-period end2021-09-25, fiscal-year total. Ask the gross-margin example; expect41.78%, checked original operands and actual source IDs.
2. Open a citation with the keyboard; its original evidence panel should open and retain focus. Inspect original-source links, units, source values and the exact calculation.
3. Export JSON; included IDs and displayed result should agree. Edit the question/company/filing/period; the old answer/evidence must disappear.
4. Ask the supply-chain narrative question and the total-revenue example. Revenue should use Total net sales and return365817000000USD.
5. Inspect an inventory-only filing. Its unavailable research action must state why. Chart answering remains disabled; How it works shows all six original charts, candidate descriptions/labels and unknown values for review.
6. Try360px, tablet and desktop sizes. Use the mobile drawer, Tab/Shift+Tab/Escape, reduced motion, source panels and wide table scrolling.
7. Open Saved Questions. Unavailable sign-in should explain the setup and allow basic research. Do not treat a local Gradio session as a Supabase account.
8. In Gradio, use Narrative/Table QA for real source questions. Clear All must clear query and primary answer. A second client’s invalid request must not expose another session’s result.

The actual stopped-service/recovery rehearsal and real Gradio session checks were executed in this continuation. Repeating the rehearsal later requires checking idle jobs and exact process identity before stopping only the managed API.

## Repeatable checks

```bash
.venv/bin/python scripts/check_handoff.py --output output/nov18/checks
.venv/bin/python scripts/prepare_reranker.py
.venv/bin/python scripts/build_web_review_assets.py
.venv/bin/python scripts/run_benchmarks.py --gate-report
```

`prepare_reranker.py` verifies existing official pinned assets. Add `--download` only for the explicit missing-model recovery; it does not download at app startup. The check runner continues after failures and records actual outcomes. `all_commands_passed=true` with closed acceptance gates still produces an overall nonzero exit and does not certify the project.

The prepared host uses the actual GGUF tokenizer service. To reproduce the explicit live check, add `--live-runtime --model-cache output/models-http --tokenizer-url http://127.0.0.1:11435 --gguf ACTUAL_GGUF --gguf-sha256 f06e91e18fc74295d0c781bf91622508c75655e2c18ed869d52447ffe1e667e1`. An alternative HF tokenizer must be the actual matching generator tokenizer, not a BGE substitute. Do not put private tokens in commands, Git or reports.

## Conditional stages and deployment

A/B require an explicitly selected matching representation index. E/F/G require the verified local cross-encoder directory; F/G additionally require an actual accepted policy, and G requires separate independent caption decisions. These options do not open independent gates or bind benchmark contexts. Official contexts remain UNBOUND and final experiments unrun.

The protected Vercel project retains Node22 and all-deployment authentication. Production credentials stay server-side. This is a file/API deployment; Git pushes alone do not redeploy it. The temporary authenticated HTTPS backend is separately approved; raw Ollama, tokenizer and Gradio remain local. No billing or new database project is set up. The user chose PR19 for owner merge; no main merge is claimed.
