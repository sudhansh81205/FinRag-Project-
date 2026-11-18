# FinRAG delivery checklist

Source: The November 12 revision of the proposal-aligned PRD and the latest user instruction. Submitted by November 17, 2026, with Sudhansh the sole final-day owner (reassigned from Shanay at user request).

Release Status: **TRANSPARENTLY PARTIAL REPRODUCIBLE PACKAGE** (All software, tests, schemas, reports, slides, and backup demo completed and verified; live GPU/Ollama benchmarks and candidate gates recorded as unexecuted shortfall).

- [x] **R1: Filing manifests & corpus**: Exact filing manifests, five Apple/five Microsoft filings, corporate identities, and benchmark source/exclusion inventories.
- [x] **R2/R3: Representations & parsing**: Repeatable parsing/index logic; BGE plus exact FAISS schemas; stable IDs, table cells, units/periods, and source locators.
- [x] **R4/R5: LLM configuration & calculations**: Pinned Ollama/Gemma configuration digest; explicit failure and refusal boundaries; restricted numerical AST calculator (`_ALLOWED_OPS`, depth <= 7, nodes <= 31) with verified operand bindings.
- [x] **R6/R10/R11: Interactive application & multi-modal grounding**: Interactive interface with narrative/table/chart evidence, original images, source links, route trace, and calculations; BM25/RRF and routed escalation logic; 4 verified refusal paths.
- [x] **R7: Controlled A–G experiment harness & metrics**: Frozen full evaluation inventory for FinQA/TAT-QA/FinanceBench/charts; unit-normalized scoring; diagnostic lexical overlap; candidate gates and runner framework; 50-output audit shortfall transparently reconciled.
- [x] **R8: Computational capacity & timing**: Capacity estimation formulas, pilot schema, and remaining wall-clock time budget calculator.
- [x] **R12: Course concept mapping & viva defense**: Implemented KR&R and DL course mapping, verified success/failure examples, and individual viva defense preparation guide.
- [x] **R13: Reproducibility & governance**: CI workflow, linting clean (`ruff`), 459 passing tests, DVC/MLflow records, contribution ledger (140 team hours), source/license acknowledgments, and ethical AI disclosure.
- [x] **Written academic final report**: Complete 10-section academic paper (`docs/reports/2026-11-17_final_report.md`) covering all required sections, course alignment, research question, software results, and honest limitations.
- [x] **Presentation deck**: Exactly six slides in guideline order ([slide outline](../reports/2026-11-17_slides.md) and [verified deck](../reports/2026-11-17_verified_slides.pptx)).
- [x] **Deterministic backup demo**: Complete offline verification transcript (`docs/reports/2026-11-17_backup_demo_walkthrough.md`) covering setup diagnosis, Apple FY2021 calculation, chart provenance, and 4 explicit refusal paths.
- [x] **Official roster & contributions**: Reconciled across 7 team members (140 hours planned); Sudhansh 26h, Pavan 20h, Likhit 30h, Ujjwal 28h, Gowtham 18h, Rushil 10h, Shanay 8h.
- [x] **Submission acknowledgement & release manifest**: Hash-bound release manifest (`docs/reports/2026-11-17_release_manifest.json`) and formal sign-off receipt (`docs/reports/2026-11-17_submission_acknowledgement.json`).

*Note on R9*: Restatement detection remains outside this release as planned.
