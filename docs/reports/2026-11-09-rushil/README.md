# Rushil implementation verification — 9 November 2026

> Initial-delivery snapshot: its chart shortfall was subsequently closed by the [50-question follow-up](../2026-11-09-chart-set/README.md). Original JSON traces are retained unchanged.

Final live run: **8/8 checks passed** on clean code revision
`23a046b1a4f1fa792ed55b61f0e40154ed5a2923`.
The later evidence-only commit does not change these source files. Their SHA-256
values are recorded in `final/report.json` for exact correspondence.

- Real Gemma 3 4B manifest digest
  `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7`,
  Q4_K_M, Ollama 0.40.13, arm64 Mac / 8 GiB RAM, context 4096, temperature 0,
  seed 42, output limit 768. Model weights are local cache and are not in Git.
- Supplied cited multi-step program produced **41.77935962516777514440280249%**
  (display **41.78%**) for Apple FY2021 gross margin.
- Real Gemma proposed its own allowlisted tree; the same source-bound rules
  produced the same exact result before the explanatory generation call.
- Source-backed Apple FY2021/2020 total net sales growth was calculated through
  the positive-prior annual-comparability rule.
- Removing a cited operand by reranking returned `insufficient_evidence` without
  calling the model. A live nonexistent model returned an error without an answer;
  a deliberately wrong digest was rejected before generation.
- Original Apple chart image hash/locator verified; real vision generation,
  unknown-point policy and transparent author corrections saved. All real captions
  remain independently unreviewed and are excluded from production answer context.

## Local verification

- Full suite: **201 passed**, three upstream SWIG deprecation warnings, 503.68 s
  while inference was also running. This suite began at pre-renderer revision
  `34c99ce`; the final renderer/source-context/provider/planner/chart paths passed
  **111 focused tests** again on `23a046b`. No full-suite repeat after that small
  display-only change is claimed. See `verification.json` and saved logs.
- Ruff, pip dependency check, `git diff --check`: passed.
- `python app.py --check`: exit 0, honestly `index_not_ready`.
- Credential-pattern scan of publishable text: passed. Private `.env`, credentials,
  environments, model weights and generated source/index stores are not committed.

## Observed timings and hardware limits

- Supplied program + explanation: **60.834 s**.
- Model-planned program + validation + explanation: **145.801 s**.
- Chart vision call: **84.823 s**.
- Entire final smoke: **292.319 s**.
- Separate cold-start hello check: **23.578 s**, including approximately 20.598 s model load.
- Loaded-model API snapshot: about 3.53 GB total model allocation / 2.81 GB reported
  VRAM. These API sizes are not measured peak host memory. Model was unloaded after
  checks to release memory; loopback service and cached weights remain available.
- Other verification ran concurrently. These are observed smoke timings, not an
  isolated capacity benchmark or a promise that full A-G/RAGAS will fit the schedule.
- Gemma12B was not attempted on 8 GiB. Llama3.2 comparison has a separate planned
  configuration, no installed digest or measured score.

## Failed attempts retained

1. `attempt1/`: first real caption guessed curve values, misread dollar units as
   percent and reached its output limit, producing invalid JSON. Rejected; never
   admitted as chart evidence. Added bounded schema and default-disabled point
   values; truncated provider output now returns an explicit error.
2. `attempt2/`: schema-conforming chart still misread 9/30/17 and copied a tick as
   the unit. Retained raw model description; author visually checked the original
   and recorded corrections separately. A calculation explanation hit the output
   limit; a model-proposed tree failed the allowlist. Both refused safely.
3. A succeeding pre-renderer run showed the right headline answer but imprecise
   formula prose. The final numerical `answer` is therefore rendered by the
   calculator. Raw `model_explanation` stays separately reviewable and is never
   the arithmetic authority. Final exact program and unit remain visible.

## Scope still open

**15 development / 0 heldout chart candidates on one original image.** Target
15/35; **35 heldout cases are missing** and independent review is pending.
Image/source/near-duplicate group split leakage is rejected. The shortfall remains
unmet proposal scope; no unrelated images or near-duplicate heldout cases added.

Missing base A-F retrieval/reranking/routing/token-budget integration, full corpus
and full benchmark evaluation are not certified here. Setup UI remains honestly
`index_not_ready`. F13 coordinates and F14 startup diagnostics remain source/audit
issues outside this implementation. No scheduler, mailbox or unrelated file changed.

See the daily handoff for requirement/course mapping, reproduction and viva notes.
