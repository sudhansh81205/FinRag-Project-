# Install and launch the shared setup build

Use `main`. This build opens the interface and reports missing prerequisites. It
does not yet answer financial questions. No credentials, filing download, Chroma
index or model weights are required to run the setup UI.

## Windows PowerShell

Use Python **3.12** (the verified environment is 3.12.14). Run these commands from
the repository root. Using the environment's executable avoids activation-policy
problems. If `py -3.12` is unavailable, install Python 3.12 first.

```powershell
git switch main
git pull --ff-only origin main
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe app.py --check
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:7860`. Enter a question and choose **Check readiness**.
Expect `not_ready`, a missing-source/index/model explanation, and an empty answer.
An empty question returns `invalid_input`. Stop the server with Ctrl+C. The server
is local; no public share link is created.

For macOS/Linux use `python3.12 -m venv .venv` and `.venv/bin/python` instead of
the Windows executable. Windows is locally verified; CI checks Linux separately.

## Configuration and data locations

[`configs/config.yaml`](../configs/config.yaml) holds all non-secret defaults.
Optional `.env` values override YAML, and process environment overrides `.env`.
Copy `.env.example` only if you need overrides; never overwrite an existing `.env`.
The loader reads only the repository's `.env` and does not change process values.
Paths resolve from the repository root even when launched from another directory.

| Setting | Default / meaning |
| --- | --- |
| `FINRAG_RAW_DIR` | `data/raw`; selected filing goes here during ingestion |
| `FINRAG_INDEX_DIR` | `sec_vector_db`; persistent index built later |
| `FINRAG_COLLECTION` | `sec_10k_filings` |
| `FINRAG_PROVIDER` | `unconfigured`; later explicitly `gemini` or `ollama` |
| `FINRAG_MODEL` | Empty until a real model is verified |
| `GEMINI_API_KEY` | Private value only; never paste into code/report |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `FINRAG_HOST` / `FINRAG_PORT` | `127.0.0.1` / `7860`; change port if occupied |

Do not create empty data files to bypass readiness: a folder/key does not prove
that a collection, embedding model or provider works. Answering stays disabled in
this setup milestone until the next owner connects validated behavior.

## Dependencies and verification

`requirements-app.txt` contains the lightweight UI/configuration dependencies.
`requirements-dev.txt` adds the test/lint tools; this is today's verified install.
`constraints-setup.txt` records the exact resolved setup/dev versions from the
clean Python 3.12 environment. Both install files use these constraints.
`requirements.txt` adds the planned ingestion/retrieval/provider packages for the
later owners. Those packages and their model weights are not needed for today's UI.
Do not describe a successful setup install as a verified complete inference stack.

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

With the app running, use a second terminal for a real HTTP/callback smoke check:

```powershell
.\.venv\Scripts\python.exe scripts/check_setup_ui.py
```

The tests include the original explicit mock test plus setup/configuration
regressions. Passing them does not establish financial accuracy or live model
access. See the [completion report](reports/2026-10-30_days-01-02_completion.md)
for the exact checks actually run and remaining limitations.

Do not run historical `prototypes/` files or `scripts/run_eval.py` as the final
application/evaluation. The next owner starts from `app.py`, `src/application.py`
and the [handoff](handoffs/2026-10-30_days-01-02.md).
