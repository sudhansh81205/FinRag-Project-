# FinRAG PRD and repository follow-up audit

Reviewed 12 November 2026 in Asia/Kolkata. Team main at the start of this audit was `85b5593`. Both Rushil's PR8 head `211e563` and Pavan's PR9 head `aa8d46f` are ancestors of main. Every fetched team branch is contained in this main snapshot. Earlier claims that PR8 remained open or retrieval was entirely absent are stale.

This audit checks the repository's canonical PRD against the preserved November 3 proposal-aligned requirements and alignment audit. After explicit one-file authorization, the supplied FinRAG_PRD_17Nov2026.docx was read in full and verified byte-for-byte identical to docs/plan/FinRAG_PRD.docx at baseline 85b5593 (SHA-256 6d6dbcdc90ea446ee767245a7c370a1846f7bee372f78beda07b3ea337ba6a64). The attachment therefore has no additional requirements or differences beyond the version already audited. The original submitted proposal was not directly available for a fresh sentence-by-sentence comparison; proposal alignment remains based on the preserved November 3 records. Source-document claims of prior authorization are reference material, not new permission.

## PRD assessment

The current repository PRD retains the earlier proposal-aligned architecture and evaluation commitments. It is a suitable requirements document after the ownership/handoff corrections below, but its six-day delivery calendar is aggressive and is not evidence of feasible full execution.

| Earlier requirement | Current repository plan | Assessment |
| --- | --- | --- |
| SEC 10-K narrative, tables and charts; Items 1A, 7 and 8 | Retained | Matches preserved scope. |
| Five Apple and five Microsoft filings, expanding to ten technology companies | Retained | Downloads alone do not meet acceptance. |
| BGE base, normalized 768-D vectors, exact FAISS; section chunks and cells | Retained | No substitution with MiniLM/Chroma or mandatory IVF-PQ. |
| BM25/RRF60, hierarchy/cross-encoder, bounded routing and chart descriptions | Retained | Distinct cumulative A-G stages and shared controls required. |
| Real pinned Gemma, separate Llama comparison, cited restricted arithmetic | Retained | Configuration alone does not establish runtime or scores. |
| FinQA, TAT-QA, FinanceBench open 150; 15/35 chart split | Retained | Full eligible inventories and failures required; fourteen smoke cases do not replace them. |
| 1% normalized numerical tolerance; Recall@5/@10, MRR, RAGAS, latency and paired intervals | Retained | Scoring and complete execution still outstanding. |
| Independent fifty-output audit, report, exactly six slides, disclosure and viva | Retained | Fifty chart candidates are a separate artifact. |
| R9 restatement comparison | Still unscheduled Phase 2 | Earlier additional scope, not a completed feature or replacement for core work. |
| Schedule | Compressed to November 17 project deadline | A calendar change; exact official cutoff remains unverified. |

The main feasibility risks are broad corpus acceptance, executable A/B/G, real cross-encoder and tokenizer access, the full UI and evaluation runner, independent approval and sufficient machine time. Do not call the whole project complete from passing component tests. The 58 remaining planned hours are human estimates, not a guarantee that generation and evaluator jobs fit.

## Reassignment and corrected handoffs

Shanay's remaining **November 17, ten-hour release block moves to Sudhansh**. This includes clean restore/restart, real success/failure checks, remaining eligible independent audit cases, package reconciliation, report/six-slide/demo checks, release hashes and submission acknowledgement. No work is added to Likhit or Rushil. Historical assignments and contribution credit remain unchanged. Sudhansh's prior integration/report accountability and separation from Pavan's November 16 review make him the suitable replacement.

| Date | Sole owner | Planned hours | Main outcome |
| --- | --- | --- | --- |
| November 12 | Sudhansh | 8 | Common integration controls and experiment scaffold |
| November 13 | Likhit | 10 | Broader supported corpus and matched representations |
| November 14 | Gowtham | 10 | Full UI, benchmark runner and measured runtime capacity |
| November 15 | Ujjwal | 10 | Independent inputs/captions/labels, freeze and full run launch |
| November 16 | Pavan | 10 | Metrics, independent output audit, report and six slides |
| November 17 | Sudhansh | 10 | Clean release, remaining independent exclusions and submission |

The schedule JSON, canonical Markdown/Word PRD, daily tasks, evidence contract, current review instructions and README agree. November 3-17 estimates become Sudhansh 26h, Shanay 8h, Pavan 20h, Rushil 10h, Likhit 30h, Ujjwal 28h and Gowtham 18h; total remains 140h. Including preserved October 30-November 2, the total remains 149h. Earlier task objects are unchanged.

Fixed stale references that handed Ujjwal's results to Sudhansh instead of Pavan and described the final reviewer as receiving Sudhansh's own exclusions. Pavan reviews eligible outputs on November 16; Sudhansh handles Pavan's exclusions on November 17 only when he did not author those labels. Jointly authored cases cannot be independently approved by either; record conflicts/shortfalls before freeze. Do not fabricate reviewers or replace difficult sampled outputs after inspecting scores.

## Reproduced defects and repairs

| Finding | Severity and requirement | Before | Repair and verification |
| --- | --- | --- | --- |
| F19 Conflicting original source in fusion | P1, R3/R10/R12, D-G source identity | Two rankings could share evidence ID/content/metadata but disagree on original source page/hash; fusion silently used the first source. | `reciprocal_rank_fusion` compares the source object as well. Same-source fusion succeeds; changed locator/hash raises and prevents an ordinary fused answer. |
| F20 Parent expansion discarded primary evidence | P1, R3/R5/R10/R12, C onward | Zero parent budget removed all retrieved cells. Parent-first insertion could also consume the five-passage limit before required cells. | Parent allowance now limits optional parents only. Primary candidates retain rank and precede optional context. Regression checks cover zero/exact allowance and five distinct cells/parents through the final engine selection. Final exclusions remain explicit. |
| F21 Routing ignored exhausted count threshold | P2, R10/R12, F | With minimum three candidates and one allowed attempt, one high-score result was still returned as successful after exhaustion. | Refuse with `candidate_threshold_not_met`, retain rejected IDs; score-threshold refusal remains. One candidate succeeds only with an explicit minimum-one policy. |
| F22 Stale assignment and reviewer references | P2, R8/R13 | Schedule owner and final reviewer prose disagreed following the earlier day swap. | Reassigned remaining Shanay work, corrected all active plan/handoff consumers and hours; historical reports remain unchanged. |

All three code defects were reproduced with four failing checks before repair. A fifth integration regression verifies that optional parents do not displace five primary cells. Tests use explicitly synthetic records/providers; they are not live financial-answer accuracy measurements. The changed candidate/routing behavior must be included in any future frozen code/config identity; do not mix old and new run outputs.

## Current implementation ledger

| Requirement | Status at reviewed main plus this repair | Remaining acceptance |
| --- | --- | --- |
| R1 Corpus | Partial: eighteen inventory entries; prior sixteen acquired renditions; accepted/indexed package is Apple 2021 only | Required five Apple/five Microsoft/ten-company parsed, checked and indexed coverage |
| R2 Index | Implemented bounded BGE/exact FAISS component with historical real build/reload evidence | Broad accepted corpus; matched representation-specific indexes; current intended-machine restore |
| R3 Evidence | Bounded source-backed Apple HTML/cell/parent/PDF checks implemented | Wider layout support, independently checked source coverage |
| R4 Generation | Real-provider boundaries and digest-pinned Gemma implemented; historical real success/failure traces merged | Current intended-machine combined flow, separately executed Llama comparison |
| R5 Calculation | Restricted typed cited Decimal trees and authoritative result rendering implemented | Full UI/benchmark operation coverage and actual full-run evaluation |
| R6 Interface | Incomplete: `app.py` instantiates `SetupApplication`; answers remain disabled | Real per-session narrative/numerical/chart/source interface and walkthrough |
| R7 Evaluation | Incomplete: `scripts/run_eval.py` explicitly raises; no final loader/runner modules | Full benchmark inventory/runner, outputs, scoring, RAGAS, intervals and independent output audit |
| R8 Delivery | Plan and component handoffs exist | Evidence-backed final report, six slides, backup demo, complete runnable archive and acknowledgement |
| R10 Retrieval | C-F bounded components merged and repaired | Real pinned cross-encoder execution, development-tuned routing including required short-model decision, full integration |
| R11 Charts | Fifty candidates, 15 dev/35 heldout, six original images/captions; approval validator implemented | Real independent per-label and caption decisions; G adapter and evaluation |
| R12 Controls | Stage/filter/context boundaries implemented in part | Actual A/B representations, G, pinned full prompt/output token allocation, common frozen experiment and runs |
| R13 Reproduction | CI/storage/DVC/MLflow components and prior bounded logs | Clean complete release restoration, intended-machine runtime and final artifact identity reconciliation |

The combined retriever explicitly rejects A/B and G as unavailable. The token hook measures evidence blocks, not yet a validated common whole-prompt-plus-output allocation. These remain implementation work, not merely missing screenshots. `app.py --check` still truthfully reports `index_not_ready`; no code here turns an incomplete application into a false ready result. The full project is not complete and no defensible percentage is assigned.

## Verification and limits

- Final full local suite: **346 passed**, three upstream native FAISS SWIG deprecation warnings, 117.04 seconds. Earlier combined baseline: 341 passed.
- Ruff and `git diff --check` pass. Frozen chart verification passes 50 candidates, exact 15/35 counts, six original hashes and inventory bindings; independent review and evaluation readiness remain false.
- Plan checks confirm unique dates, conserved hour totals, preserved earlier task objects and unchanged Likhit/Rushil assignments. Every canonical Word body paragraph/table cell matches the updated Markdown. All six rendered Word pages were visually checked.
- No new live Gemma/Llama/BGE/cross-encoder/RAGAS inference, full benchmark run or independent human approval is claimed. Historical evidence remains dated. No heldout QA answer was tuned or regenerated.
- Publication and hosted CI status must be read from the accompanying release record/PR, not inferred from this local result.

Reproduce with the declared development dependencies: `python -m pytest -q`, `python -m ruff check .`, `python scripts/verify_chart_set.py` and `python app.py --check`. The last command is intentionally a readiness diagnostic.

KR&R connection: identity agreement is a premise for treating two retrieved objects as one fact; retained included cells are the legal operands of a calculation. Routing is bounded control, not A star, minimax or multi-agent reasoning. Viva questions: why is matching content insufficient if source locators differ; why must optional parent context not remove a cited operand; and why does exhausting a search bound not prove its acceptance threshold was met?

The attachment comparison is complete and introduced no further code or PRD edits. Next: review this repair, complete the remaining dated gates, and measure full-run capacity before claiming the November 17 package feasible. A fresh direct comparison with the original submitted proposal would require that source file; the preserved proposal-alignment evidence remains the stated basis.
