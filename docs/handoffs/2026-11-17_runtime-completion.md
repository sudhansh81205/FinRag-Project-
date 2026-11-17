# November 17 runtime recovery and verification

This is authorized implementation work based on PR16 at `131efa257ca99e3f1264a64ef4f9b17b20c979f8`, incorporating its later runtime handoff. It is separate from the recurring read-only review. Scheduled final-day owner remains Sudhansh. No measured human effort, independent approval or official submission is asserted.

## Verified changes and their purpose

- **R4/R12, common generator control, pretrained transformer inference:** restored the pinned local Gemma3:4b model and exact installed GGUF tokenizer. Every complete planner/answer prompt is checked before calling the provider, reserving generation/template space. Empty evidence and failed provider/tokenizer/model checks return no answer. Tests include an oversized prompt with zero provider calls, a changed tokenizer/model service and a missing actual model.
- **R1/R2/R3/R13, A/B/C representations, transformer embeddings and exact retrieval:** restored all18source packages across10companies, parsed them and built/reopened matched A/B/C candidate indexes. Apple has535actual narrative/cell records in its canonical exact FAISS index. BGE defaults to one CPU thread because default native concurrent execution crashed on this8GiB Mac. A fresh query after a separate process restart passed without special OMP environment settings. These automated checks do not grant wider human corpus acceptance.
- **R5/R6, common inference, KR&R:** a real model produced a mathematically valid but financially wrong gross-margin formula. Added source-driven formula construction and an independent semantic validator at planner, engine and application boundaries. Only cited gross profit/revenue or (revenue minus cost)/revenue is permitted. No financial constants are hardcoded. Apple FY2021 correctly returns41.78%. Missing/foreign/duplicate operands and reversed subtraction refuse. A margin-change question cannot silently receive a single-period margin level. Other named financial formulas remain outside this bounded semantic rule.
- **R5/R6/R10, C/D request eligibility, typed temporal predicates:** explicit fiscal-year-total versus year-end-balance selection. Numeric premises restrict period kind/end and scope before top-k in both retrieval streams. Narrative mode explicitly requests text evidence, preventing unrelated comparative table cells from displacing narrative or failing the request binding.
- **R6/R13, web delivery:** local development permits only loopback HTTP. Production still requires HTTPS. Integrated PR16's configurable bounded240second backend deadline and250second browser deadline. Clear old answers/evidence on any query/filing/mode/period change, lock all query controls while running, preserve saved value-period type. Fresh HTTP and malformed/foreign-response failures remain visible.
- **R7/R11/R12, experimental evidence integrity:** official complete public splits are imported from pinned publisher bytes. FinQA raw text/tables and TAT-QA raw contexts are separated from gold programs/mappings and publisher retrieval outputs. All84FinanceBench PDFs are checked against Git blob hashes; all150cases bind to their complete readable source pages, never annotator-selected oracle contexts. PDF corruption, path traversal and context-byte edits refuse.
- **R7/R11, independent review integrity:** replaced scripts that inferred named human acceptance from checks. The source/package audit now explicitly reports automation. Chart approval requires externally supplied actual reviewer identity, timestamp, method and exact case fingerprints. The packet starts every decision as unreviewed. The user confirmed nobody has done the review, so no approval file was generated.

## Checks actually run

Full combined suite: **517 passed**, three FAISS/SWIG deprecation warnings,436.18seconds. After the final bounded margin-change guard, all17affected formula/web/token regressions passed. Full Ruff passed. Node syntax and **13/13gateway tests** passed. The earlier506-test run is historical, superseded by the combined run.

Canonical Apple verification passed source hashes, derived cells/sidecars, DVC restore and MLflow readback. Automated wider source/package reproduction passed18/18. Exact A/B/C persisted indexes cover18filings and reload/order verification passed. Chart candidate integrity is50cases,15development/35heldout grouped across6original images, with independent review pending.

Real provider smoke, an actual missing-model failure and source-bound API generation were executed. The browser showed the corrected Apple41.78% and its five included evidence objects. Narrative API generation succeeded in179.9seconds, but separate browser narrative attempts timed out at the old gateway or the pinned provider's180second limit. The latter remains a real capacity/reliability limitation despite the gateway repair. Chart mode visibly refuses while independent acceptance is missing. Mobile390px layout exposed its menu and no horizontal overflow; console inspection returned no captured errors/warnings. Desktop result and query-lock/stale-result flows were checked. Email sign-in, two-real-user isolation, full recorded video and hosted model connectivity remain unverified.

The refreshed exactly six-slide deck is `docs/reports/2026-11-17_verified_slides.pptx`. All six rendered slides were inspected. Package/layout/Calibri policy and first-party import checks passed. The original deck is retained as the historical source. Native PowerPoint execution is not claimed.

## Local artifacts and reproducible commands

The authoritative local checkout is the `maintenance/nov17-completion` worktree. Paths below are relative to its root. The credentials file `output/nov17/local-service.json` is private, mode0600, excluded from Git and release archives. Never print or copy its token into a report.

- `output/nov17/canonical_audit.json`, `output/nov17/canonical_artifacts/`: source audit and restore proof.
- `output/nov17/corpus/coverage.json`, `reproduction_audit.json`, `A/`, `B/`, `C/`: candidate coverage, source checks and exact indexes.
- `output/models-http/`: verified cached BGE revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`.
- `../ollama-models/`: reused Gemma assets; model digest `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7`.
- `output/benchmarks/official/`: normalized full public splits, raw context pools, all FinanceBench pages, binding and source manifests. Original course resources remain only under the canonical Clg Books AI/FinRAG/Benchmarks folder.
- `output/nov17/independent-review/index.html`: human review packet and unreviewed JSON template. Rebuild safely with `python scripts/prepare_independent_review.py --output output/nov17/independent-review`.
- `docs/reports/2026-11-17-runtime/`: committed small verification records, source/model hashes and real development response traces. No model weights or secrets are committed.

```bash
python -m pip install -r requirements-index.txt -r requirements-dev.txt
python scripts/import_official_benchmarks.py --source-dir '/Users/rushilmohan/Desktop/Clg Books/ai/FinRAG/Benchmarks' --financebench-pages output/benchmarks/official/financebench_full_pages.json
python scripts/restore_financebench_documents.py --directory '/Users/rushilmohan/Desktop/Clg Books/ai/FinRAG/Benchmarks/FinanceBench Documents' --prepare-contexts output/benchmarks/official
python scripts/preflight_handoff.py --probe-ollama
python scripts/verify_chart_set.py
python -m pytest -q
python -m ruff check .
npm --prefix web run check
python scripts/verify_release_package.py
```

The PDF restore command reuses/hash-checks existing canonical files; `--download` is an explicit missing-file recovery option. Imports refuse changed pinned bytes and changed output destinations. The preflight's HF tokenizer-directory probe remains “missing” when using the actual GGUF tokenizer service instead; the separate live GGUF checks are the proof for that development path. Final acceptance still remains false.

For the local real API, keep the existing loopback Ollama11434 and tokenizer11435 services running. Use `scripts/serve_web_api.py --source-audit output/nov17/canonical_audit.json --model-cache output/models-http --tokenizer-url http://127.0.0.1:11435 --gguf <existing-pinned-GGUF-path> --gguf-sha256 f06e91e18fc74295d0c781bf91622508c75655e2c18ed869d52447ffe1e667e1`. Supply the private API token through the environment. The explicit source-audit mode is a bounded development runtime, distinct from the human-gated final prepared engine. The gateway uses that same token server-side and `FINRAG_WEB_PORT=4180`; it does not expose it to browser code. The running local UI is http://127.0.0.1:4180/.

## Remaining mandatory work and blockers

1. **Human review:** no independently completed50question/sixcaption review exists. A genuinely eligible reviewer must inspect original sources and supply actual bound decisions. The separate50generated-output audit follows final frozen output generation. Do not assign another member off-day work or create signatures on their behalf.
2. **Research execution code:** the benchmark CLI still lacks a prepared source-equivalent engine factory. Official contexts must drive matched per-suite indexes with stable source/cell/period/unit identities, including TAT-QA's missing issuer limitations. Actual A/B representations, real cross-encoder E runtime, development-tuned F routing and approved G need integration across the evaluation engine. A–G is still0/28completed cells. `--data-path` selects normalized official inputs but does not fix engine binding.
3. **Evaluation and capacity:** actual pinned RAGAS and separate Llama comparison, representative development pilots, a genuine freeze and full checkpointed runs with failure denominators and paired95%intervals remain. The restored question count is150+1147+1663+50=3010, or21070primary queries across7variants before RAGAS/Llama/retries. Individual local timings do not justify a completed capacity forecast. The older capacity module's1668TAT-QA declaration differs from the actually imported1663labelled release; use verified manifests for scope.
4. **Hosting/account work:** current rmo29 credentials have pull-only access to the team repo; merging PR16 returned403. Vercel connector returned403 pending an owner team grant. Hosted backend and email redirects/delivery/two-user isolation are pending. No tunnel, new public endpoint, billing or weakened deployment protection was created.
5. **Submission:** no observed course upload or receipt. A local archive, PR, test pass or scheduled owner does not establish submission.

## Viva checks

**Why did a valid calculator result still need a formula check?** Units and Decimal arithmetic license operations on the supplied facts, but do not identify which metric the question asks for. Gross profit divided by revenue measures gross margin. Subtracting revenue from already reported gross profit measures something else.

**Why exclude gold annotations from context construction?** Letting an annotator's selected page define retrieval would answer the selection problem in advance and inflate measured retrieval performance. Restore the full report first and keep the selected page only in the scoring reference.

**Why are downloaded/indexed sources still “candidate”?** A hash proves byte identity and automated predicates prove specific invariants. Neither establishes independent source interpretation or label approval.

**Why do 517tests not prove A–G complete?** Regression tests validate bounded software behavior. Experimental completion requires the actual frozen variants, eligible source contexts, real generation/evaluation outputs and independent decisions, with failures included.


## Reproducible local startup

The temporary chat-owned services stopped between continuations. The new launcher starts detached, health-checked loopback processes from existing assets and preserves the existing owner-only token. It refuses an occupied port, an altered GGUF or insecure token file before taking over a service. Three launcher failure/security checks passed with the temporary listener explicitly permitted by the sandbox. Reuse the current services if they are already running.

```bash
.venv/bin/python scripts/run_local_workspace.py --ollama ../ollama/ollama --llama-server ../ollama/llama-server --models ../ollama-models --gguf ../ollama-models/blobs/sha256-f06e91e18fc74295d0c781bf91622508c75655e2c18ed869d52447ffe1e667e1 --source-audit output/nov17/canonical_audit.json --model-cache output/models-http
```

The launcher prints the local workspace URL, never its token. It writes component logs and a non-secret PID inventory under `output/nov17`. A stopped provider remains a visible failure. Do not kill an unrelated process or reuse an old PID inventory without checking actual process identity.

Restart verification: all four services remained healthy after launcher exit. A fresh browser request again returned the cited41.78%margin. Screenshot capture failed twice (browser timeout), so no screenshot file or complete recorded video is claimed.
