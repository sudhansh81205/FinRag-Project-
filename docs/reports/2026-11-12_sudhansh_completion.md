# FinRAG completion report: November 12 integration controls and experiment scaffold

- **Owner**: Sudhansh Khandelwal (8 estimated hours)
- **Date**: November 12, 2026
- **Requirements**: R3 Evidence, R7 Evaluation, R10 Retrieval, R12 Controls, R5 Calculation
- **Integration Heads**: `cc2614f`, `34e12fb`, `85b5593`
- **Updated Assignments**: Sudhansh owns November 12 and November 17 (reassigned from Shanay at user request); Pavan owns November 16.

---

## 1. Executive summary

On November 12, Sudhansh completed the integration controls and experiment scaffold for FinRAG. The task validated the combined codebase integrating PR8 (Gemma generation and Decimal calculator) and PR9 (BM25 and hybrid retrieval), verified fixes for findings F13 through F18, confirmed shared pre-top-k eligibility, established strict complete-context and operand-inclusion contracts, and implemented the immutable canonical A–G experiment scaffold with prerequisite gate validation.

All planning documentation (`docs/plan/PRD.md`, `schedule.json`, `TASK_REQUIREMENTS.md`, `COURSE_ALIGNMENT.md`, `EVIDENCE_CONTRACT.md`, `DELIVERY_CHECKLIST.md`, `README.md`, `AGENTS.md`) was synchronized to reflect the user's reassignment of the final November 17 release day to Sudhansh, preserving historical hours through November 11 and total planned hours (140 hours for November 3–17).

---

## 2. Verified integration controls

| Gate / Component | Requirement | Implemented Behavior | Verification Result |
|---|---|---|---|
| F13 PDF Spans | R3 / R13 | Span bbox check for finite numbers, non-degeneracy, mediabox containment, origin conversion | Passed on Apple 2021 package (11 PDF checks) |
| F14 Guarded Output | R13 | Diagnostic report path creation inside guarded execution; exits nonzero if output unwritable | Verified on Windows and POSIX failure modes |
| F15 Pre-Top-K Scope | R3 / R10 / R12 | Pre-top-k filter on ticker, period and source before both FAISS and BM25; consecutive filter isolation | Verified: query for AAPL cannot return MSFT; consecutive queries do not leak state |
| F16 Failure Semantics | R4 / R10 / R12 | Component, provider or cross-encoder failure yields typed `service_error`; mock fallback forbidden | Verified: `RetrievalStageError` halts generation; non-finite cross-encoder scores rejected |
| F17 Byte Integrity | R11 / R13 | Canonical LF line endings pinned in `.gitattributes`; JSON digests identical on Windows | Verified with `scripts/verify_chart_set.py` (50 candidate questions, 6 images) |
| F18 Lint & Quality | R13 | Ruff lint compliance, native FAISS integration | Verified clean |
| Passage Selection | R10 / R12 | Max 5 passages, shortfall recorded, exact `included_evidence_ids` | Verified: passages > 5 excluded with `passage_limit` |
| Safe Calculator | R5 | Cited operands must be present in `included_evidence_ids`; out-of-budget operands trigger refusal | Verified: missing operand refuses generation; exact Decimal arithmetic preserved |
| Experiment Scaffold | R7 / R12 | Immutable A–G variant specifications, pinned controls, prerequisite gate checker | Verified in `src/pipeline/experiment_scaffold.py` and unit tests |

---

## 3. Canonical A–G experiment scaffold

The scaffold (`src/pipeline/experiment_scaffold.py`) formalizes the 7 canonical evaluation variants:

- **Variant A**: Fixed-overlap narrative chunks + flattened Markdown tables (dense only)
- **Variant B**: Section-aware narrative chunks + flattened Markdown tables (dense only)
- **Variant C**: Section-aware narratives + self-describing cells + parent expansion (dense only)
- **Variant D**: Section-aware narratives + self-describing cells + parent expansion + BM25/RRF60 fusion
- **Variant E**: Variant D + hierarchical candidate restriction + `bge-reranker-base` cross-encoder
- **Variant F**: Variant E + keyword/short-model routing + escalation across text/table tiers
- **Variant G**: Variant F + independently approved source-linked chart descriptions

Common controls locked across all variants:
- Embedding model: `BAAI/bge-base-en-v1.5` (768-D L2-normalized)
- Vector index: exact FAISS `IndexFlatIP`
- Generator: `gemma3:4b` (`sha256:751a0b6e9a781b0a5c43d99d10e0c90c74f76ca09fa496735e5a95b8719fb424`)
- Max passages: 5
- Numerical relative tolerance: 1% (0.01)
- Random seed: 42

---

## 4. Unresolved gates ledger (Handoff to downstream owners)

| Owner | Date | Scheduled Deliverable | Mandatory Unresolved Gate |
|---|---|---|---|
| Likhit | Nov 13 | Corpus expansion & matched representations | Ingest 5 Apple + 5 Microsoft + 10 technology companies; build distinct A (fixed-overlap), B (section-aware), and C (cells/parents) indexes |
| Gowtham | Nov 14 | UI, benchmark runner & capacity measurement | Wire Gradio per-session inputs; implement versioned FinQA/TAT-QA/FinanceBench loaders and A–G execution; measure generation/evaluator capacity |
| Ujjwal | Nov 15 | Independent approval, freeze & run launch | Independently audit source/cell/index and 50 chart decisions without self-approval; freeze code/data/manifests; launch A–G runs |
| Pavan | Nov 16 | Output audit, metrics & report draft | Audit 50 predeclared generated outputs against context; compute Recall@5/@10, MRR, RAGAS, latency with 95% bootstrap intervals; draft 6 slides |
| Sudhansh | Nov 17 | Final verification, exclusions & submission | Clean environment restore check; resolve independent exclusions; verify hashes; assemble final submission archive and capture receipt |

---

## 5. Viva and course concept connections

1. **Knowledge Representation (KR&R)**:
   - Evaluated expressions use typed facts with issuer, filing, metric, period, unit and scale metadata.
   - Operations require exact predicate validation: `period(a) == period(b)` for same-period arithmetic, nonzero denominator for percentage change.
2. **Deep Learning (DL)**:
   - Dense embeddings map text into continuous semantic space; cross-encoders jointly attend to question-passage tokens.
   - Stage failures must be reported faithfully; substituting mock data or dense-only scores in place of a cross-encoder invalidates the ablation.
3. **Reproducibility & Safety**:
   - Every claim in the final report must trace to an immutable evidence ID in the retrieved context.
   - Honest refusal on missing premises prevents hallucinated financial advice.
