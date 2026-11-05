# Environment boundary and reproducibility checks

This supports Ujjwal's November 3 assignment and the authorized November 5 gap
repair. It does not complete Likhit's missing parser/index assignments or
Shanay's independent audit. Keep the schedule in docs/plan/schedule.json.

## Local setup

Use an isolated Python environment. CI uses Python 3.12; the repair was tested
on Windows Python 3.14.3. Installation success is not model compatibility proof.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/parse_filing.py
.venv/Scripts/python.exe scripts/verify_day05_environment.py
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe app.py --check
```

On Linux use `.venv/bin/python`. No service login is required for local DVC or
MLflow. Do not put keys in Git or an environment report. Full dependencies,
weights, data assets and future model calls are separate steps, not silently
installed or invoked by this checker.

## What a successful check means

The parser prepares 316 narrative records and three complete table parents from
the pinned Apple browser snapshot. The environment command validates their
structural contract and source/output/content hashes. It does not independently
certify financial values or comparative periods; Shanay still performs that
audit after Likhit's actual cell/PDF/chart package is available.

DVC restores one synthetic fixture in a new local directory and compares
SHA-256 before/after. The actual canonical-package clean restore remains Shanay's
task. MLflow logs contract parameters, record count and the contract JSON to a
persistent local SQLite store, reopens the run and checks the saved artifact.
It is a tracking smoke check, not a generation/evaluation run.

Default report: `output/environment/report.json`. Persistent artifacts:
`output/environment/runs/<unique-run>/dvc` and `mlflow`. Keep these while reviewing
the result. The JSON stores the exact interpreter, revision, dirty-worktree flag,
versions, hashes, MLflow run ID and tracking URI. A later checkout gets a new local
run; the original author's temporary URI is historical and is not a shared server.

Each check records passed/blocked/failed independently. Missing executables or
malformed input must still produce a report before exit code 1. Exit 0 means
only the declared environment smoke checks passed; `full_pipeline_ready` stays
false. Missing model assets and capacity inputs are explicit separate blockers.
CI runs these same checks and uploads the diagnostic/artifacts even on failure.

## Runtime and capacity decision

Keep the already configured Gemini route for the current prototype. The earlier
handoff recorded a live Gemini `gemini-3.5-flash-lite` check; this repair makes no
paid model call and does not prove present credentials/quota. Do not automatically
switch to mock, another provider or another model. No verified cloud notebook
URL is available; the user requested reuse of the existing route.

The final proposal still requires measured Gemma 3/Ollama and a separate Llama
comparison. Record intended machine, real model tag/digest, memory and pilot
timings before accepting that gate. The checker queries only local Ollama tags;
it never starts a server, pulls weights or generates. Windows adapter memory is
not a reliable statement of usable dedicated VRAM.

Capacity remains blocked until eligible benchmark counts, seven A-G variants,
generation/retrieval and RAGAS timings, extraction/caption overhead and machine
availability exist. A formula, import check or planned human hours cannot replace
those measurements. Keep the 50 chart questions and independent 50-output audit
separate; 14 local cases remain smoke only.

## Troubleshooting and handoff

- Wrong interpreter: inspect `python.executable` in the report and use the venv
  explicitly, not whichever `python` or `dvc` happens to be on PATH.
- Missing parser output: run the existing parser; do not create empty JSONL to
  make the checker pass. Hash mismatch: retain the rejected package and source;
  investigate the change instead of overwriting the expected hash.
- DVC failed: inspect the saved command/status. No remote account is needed for
  this local cache check. A missing cache is not a successful restore.
- MLflow failed: the report records the exception type without leaking raw
  private diagnostics. Check declared packages and local SQLite/file permissions.
  The run artifact and database must remain on disk for readback.
- Schema passed but cells/PDF/charts absent: the full dependency is still blocked.
  Do not mark Shanay's validation or Likhit's final index task complete.

Course: typed evidence representation and integrity predicates support KR&R;
this checker is not a general inference engine. DVC/MLflow are supporting
reproducibility engineering. Viva: Why can a successful hash/schema check still
accept a faithfully copied but incorrectly interpreted financial fact? Because
integrity preserves bytes and shapes, while independent source/semantic checks
establish meaning, units and periods.

References: [DVC checkout](https://doc.dvc.org/command-reference/checkout),
[MLflow client](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.client.html),
[JSON Schema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/).
