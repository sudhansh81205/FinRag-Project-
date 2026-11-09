# Complete candidate chart set — 9 November follow-up

**The missing 35 candidates are now delivered: 15 dev / 35 heldout, 50 total, on six original charts.**
Candidate count target is met. Independent label/caption approval remains pending; the author cannot self-certify it.

## Verification

- 207 tests passed (three upstream SWIG deprecation warnings). New image/hash/source/split failure fixtures pass.
- Exact source revision: `f0c91feb9f6af9c424286bcfc8b90db82eef4ee5`. Later changes only update handoff/evidence.
- Six original image hashes, all source references, frozen question-file hashes, exact 15/35 split and no source/group leakage verified.
- Six local filing PDF hashes and exact issuer/Form10-K/SEC-cover/fiscal-end checks passed.
- Existing 15-question Apple dev file remains byte-for-byte unchanged.
- Five new real Gemma captions plus the reused Apple caption exist; all remain candidate/pending independent review.
- Frozen prompt hash: `320ce4ef97839a593e6c48342ed156cff6d660789d132be45dee43ca608e310a`; same pinned model/profile and image-only prompt as initial development caption.
- Caption script never loads QA files. This is corpus preprocessing, not a heldout application-QA/evaluation run.

## Actual caption timings

| Source | Seconds |
| --- | ---: |
| NVDA | 64.18 |
| AMD | 48.585 |
| INTC | 164.017 |
| CSCO | 50.016 |
| ADBE | 43.212 |

Total new-caption preprocessing: 370.102 seconds on the existing 8 GiB arm64 Mac. These are observed timings, with some other verification concurrent, not an isolated full-run capacity benchmark.

Raw model drafts are preserved. For example the model inferred a percent unit on a source whose ticks do not specify units; the explicit source annotation preserves that uncertainty. All corrections are labelled source-checked author work, with AI assistance, not independent human approval.

## Scope and source handling

- New heldout sources: NVIDIA, AMD, Intel, Cisco and Adobe, seven questions each. Apple remains wholly dev.
- Original embedded chart bytes or bounded source-PDF chart renders; nearby numerical tables excluded. No graph was reconstructed or exact curve values estimated.
- Six image groups are not fifty independent images; all are stock-performance line charts. Report that limited diversity and use image-clustered analysis.
- Questions test legend/marker style, visible ordering/trends, axes/counts and unknown-value handling. Independent review must check source overlap/ambiguity and whether descriptions adequately cover the requested visual facts; no perfect G answerability claim.
- Candidate labels were AI-assisted and visually checked during implementation. They still require a separate reviewer before freeze/evaluation.
- These extra chart assets do not establish wider narrative/table parsing, BGE indexing, final A-F integration or full evaluation readiness.
- Original PDFs are stored only in the canonical course folder, not committed again. Acquisition retry/exclusion details are retained in `acquisition.json`.

## Requirements and course connection

R11: source-linked original chart descriptions and the full candidate question target. R12: split controls, reproducible assets and honest evaluation boundaries. Pretrained multimodal inference is the CV connection; hash/source/split checks are supporting engineering. No vision model was trained, and metadata checks alone are not a new KR inference system.

Reproduce with `python scripts/verify_chart_set.py`; optional `--source-dir` verifies original PDFs. `data/charts/README.md` explains assets, the gallery export and source/caption commands. `run_rushil_checks.py` now audits the complete candidate set after its development-only model smoke.
