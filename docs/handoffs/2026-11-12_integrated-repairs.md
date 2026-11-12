# Integrated repair handoff on November 12

This handoff covers AI-assisted repairs requested by the project owner after reviewing the reports through November 8 and the later submissions for those assignments. It does not assign human hours or certify the full project. The code repair commit is `cc2614f329c06be7a371b75d2cd038173b96db2c`. The current PRD and schedule control remaining dates, including Shanay's November 17 submission slot.

## What is combined

The starting main was `10e715cb6edb234028e5641f77ccf2e399021a07`. Both submitted heads are ancestors of the repair branch: Rushil's PR8 `211e563b2e2a49341e51ec701bbf32c7436eb08d` and Pavan's PR9 `aa8d46fa02123cbb5474d8a3bee98209fc0877d9`. They were published after the November 8 cutoff; earlier dated reviews remain unchanged. Remote publication and hosted checks are recorded by the integration PR and subsequent main history.

## How the corrected answer path works

1. A caller supplies an already opened `ExactStore`, matching BGE encoder, explicit real-provider client and, for E/F, an actual cross-encoder. `src.application.assemble_exact_engine` connects these contracts directly. The old Chroma collection adapter remains a labelled legacy route; the setup UI is still disabled until its full workflow is implemented and validated.
2. `src.retrieval.eligibility` validates request filters and intersects them with the configured scope. The same company, filing, period and other supported predicates apply before each dense and BM25 top-k. A request cannot widen the constructor's scope or leave state behind for the next request.
3. `DenseRetriever` uses the matching encoder and exact FAISS store. `BM25Retriever` ranks the same eligible canonical identities. RRF combines independent ranks with k=60 and retains component score types and ranks. Conflicting source identities fail.
4. Canonical D is fusion; E adds a distinct section-group hierarchy and cross-encoder; F adds bounded routing with recorded attempts and stop reasons. A/B need real representation-specific indexes; G needs independently approved captions and its adapter. An unavailable variant is an explicit error, never another variant relabelled as success. Routing thresholds are configuration until tuned on development data and frozen.
5. The adapter returns ranked/candidate IDs. `FinRAGEngine` preserves the already computed cross-stream ranking, selects at most five complete objects, and alone assigns actual included IDs. It records rejected objects and passage shortfall. An explicitly supplied tokenizer and identity enable a measured token budget; the legacy character policy remains labelled intermediate. Neither policy by itself establishes a frozen A-G experiment.
6. Restricted calculations resolve only cells actually included in the final prompt. The Decimal operation tree checks source/content identity, issuer, scope, period, metric, units, scale and division premises. The exact calculator result is authoritative. Raw model explanation is retained separately. The explanation prompt now retains included chart objects as well as narrative and table objects, so its included-ID claim remains truthful.
7. Any component failure, invalid cross-encoder output, missing stage or provider error prevents an ordinary successful answer. Errors retain sanitized typed stage codes and traces. No mock or heuristic fallback is counted as a successful required transformer stage.

## Source and chart safety

`src.evidence_audit` now reads independent pypdf text baselines from the original PDF. It checks declared coordinate origin, valid bounds, the actual value anchor, its row label and comparative year column. Supported TOPLEFT coordinates are converted to BOTTOMLEFT. Unsupported page transforms fail. This verifies a bounded baseline/row/year association; it does not certify exact glyph-outline rectangle extents or arbitrary PDF/OCR layouts.

The accepted Apple package still contains 316 narrative records, 219 cells and three parent tables, with eleven PDF corroborations. The actual source audit passed after the repair. This remains one accepted filing, not eighteen accepted filings. Inventory, acquisition, parsing, source acceptance and indexing are distinct counts.

`.gitattributes` pins byte-sensitive JSON and other text to LF. Frozen chart/inventory bytes reproduce on a Windows archive with `core.autocrlf=true`; expected hashes and the held-out split were not rewritten. Intentional tampering still fails.

`load_reviewed_set` and `scripts/promote_chart_set.py` accept a separate completed human approval ledger. The caller supplies trusted reviewer identities and known label authors; every decision must bind the unchanged image/source/question hashes, state a review basis and pass independence checks. This validates recorded approval provenance, not the human's identity or visual judgement. Real candidate labels and captions remain pending. Label promotion alone does not approve captions or establish G readiness.

## Verification and reproduction

Use the declared development environment. The repair was checked on Python 3.14.3, pytest 9.2.0, Ruff 0.17.3, NumPy 2.5.4 and native FAISS 1.13.2. Hosted CI uses its declared Python version. Development requirements now include the native FAISS dependency so its storage tests actually run without downloading model weights.

```text
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q
python scripts/verify_chart_set.py
python app.py --check
```

The chart command should report 50 candidates, 15 development and 35 held-out, six images, and `evaluation_ready: false` until real independent approval exists. `app.py --check` still reports `index_not_ready` on this repair machine: no local accepted index catalog is connected to the setup application. Configured Gemma 3 4B has a digest, but the current Ollama readiness request failed with ConnectionError. No new real model inference or paid evaluator call was run here.

To reproduce the bounded source package when source prerequisites are present, use the existing `scripts/parse_filing.py`, `scripts/prepare_evidence.py` and `scripts/verify_canonical_data.py` entry points. The last command performs actual restore/tracking checks. An existing-file artifact destination must save a structured failure to a separately writable report path. If the report destination itself is unwritable, stdout explicitly reports that no report was saved and the command exits nonzero.

The independent approval command is documented in `data/charts/README.md`. Never create a pretend human ledger to make it pass. Missing/stale/self-authored approvals must remain blocked. Never use held-out answers to tune prompts, routing or thresholds.

## Remaining work and handoff

Follow the current schedule: Pavan November 12 controls/scaffold; Likhit November 13 broader supported corpus and matched representations; Gowtham November 14 full UI, benchmark runner and measured capacity; Ujjwal November 15 independent approvals/freeze/full runs; Sudhansh November 16 metrics, output audit, report and six slides; Shanay November 17 clean release, remaining independent exclusions and submission. Each owner reads this handoff inside their own assigned block.

Mandatory gaps still include broad accepted corpus, real A/B index representations, actual pinned cross-encoding and tuned F thresholds, independently approved captions/G integration, full source-linked UI, named benchmark loaders/runner, complete Gemma/Llama/RAGAS execution, the separate independent 50-output audit, confidence intervals and the final reproducible package. Keep all failures and exact shortfalls visible. Fourteen local smoke cases and passing component tests replace none of these deliverables.

## Course explanation and exercises

R3/R10/R12 and common A-G eligibility are KR predicates: a requested issuer and period define which facts may participate before ranking. Success is an AAPL request recovering AAPL even when MSFT has the globally strongest vector; failure is an unknown filter or incompatible source identity. Viva: why does post-top-k filtering lose an eligible answer?

R4/R10 E/F use a pretrained transformer cross-encoder to jointly score question/passage pairs. Success requires one finite real scalar per candidate; an exception, short vector, boolean, string or NaN cannot certify that stage. Viva: what experiment did you measure if the required transformer failed but the output was labelled successful?

R3/R13 source checks establish a citation premise independently of the parser. A valid original-source row/year association passes; a number elsewhere on the same page fails. Viva: which positional claim remains deliberately uncertified?

R5 reasoning licenses a conclusion only after typed cited premises pass. Trace the Apple margin example `(365817 - 212981) / 365817 * 100 = 41.78%` and then change the issuer, unit or denominator to explain refusal. Chart vision and safety retain unknown values and require real independent source/image review. Hash equality certifies identity, not semantic truth. No A star, minimax, game theory or multi-agent reasoning claim follows from BM25, RRF or routing.

Exercise: draw the exact-source to eligible-rankings to actual-context to calculator to provider flow. Mark where a wrong-company request, excluded operand, failed cross-encoder and pending chart must stop. Then compare the same immutable request across two sessions without sharing mutable filters or answers.
