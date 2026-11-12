# FinRAG

FinRAG is a prototype for answering questions about SEC 10-K annual reports using retrieved narrative and table evidence. The unified completion plan adds grounded chart evidence, checked calculations, clear failure states and the matched A-G experiment with named benchmarks and independent audits.

## Team plan

The current plan uses **seven members and exactly one assigned worker per day**. The submission deadline is **November 17, 2026**, under the latest user instruction. **Shanay owns November 17** for final verification, release and submission. Earlier calendars are preserved as history.

- [Read the PRD](docs/plan/PRD.md)
- [Download the editable PRD](docs/plan/FinRAG_PRD.docx)
- [See the dated assignments and completion checks](docs/plan/schedule.json)
- [Use the daily implementation master prompt](docs/review/MASTER_PROMPT.md)
- [Understand the nightly review process](docs/review/README.md)
- [Read the November 5 repair review and remaining gates](docs/reports/2026-11-05_gap-repair-review.md)
- [Learn the repaired code and next-owner handoff](docs/handoffs/2026-11-05_gap-repair-learning.md)
- [Review the combined November 12 repairs](docs/reports/2026-11-12_integration-review.md)
- [Use the current code handoff](docs/handoffs/2026-11-12_integrated-repairs.md)

## Run the shared project

Use **`main`** for the shared project. The UI, modular backend, PRD and review kit are combined here. The original UI/container are preserved under `prototypes/`, and the notebook remains an ingestion reference.

Start with the [setup guide](docs/SETUP.md). The single entry point is `python app.py`. This setup milestone launches without a key or model download and clearly reports `index_not_ready`. Real answering, validated ingestion, citations and calculations remain scheduled work.

The first two assignments were completed together at the user's request on October 30. Read the [handoff](docs/handoffs/2026-10-30_days-01-02.md) and [completion report](docs/reports/2026-10-30_days-01-02_completion.md) before starting later work. Those reports describe the historical checkpoint; the current PRD controls subsequent scope and dates.

The current proposal plan requires BGE with exact FAISS search, BM25/RRF, table and chart evidence, reranking, routing and controlled A-G evaluation. These are implementation requirements, not completion claims. The existing MiniLM/Chroma prototype remains a historical baseline and recovery aid.

## Daily workflow

The scheduled owner reads the revised PRD, their dated task and the latest available nightly review, then fills in the master prompt. Work includes verification and a written handoff for the next scheduled owner. Code and check results must support completion claims; commit messages alone are not proof.

The nightly review is configured separately in the desktop app for 11:59 PM Asia/Kolkata. This repository provides its instructions and report template; cloning the repository does not start that automation. Generated reports and personal delivery settings stay local unless deliberately shared after review.

### Rushil Day 3 generation work

Real Gemini generation and explicit failure handling are verified with a checked
source fixture. The full UI remains gated on the later filing/index work. See
[Day 3 handoff](docs/handoffs/2026-11-02_day-03_rushil.md) and
[completion evidence](docs/reports/2026-11-02_day-03_completion.md).

The [publication recheck](docs/reports/2026-11-02_day-03_recheck.md) covers the
final failure-boundary corrections, 59 tests and fresh live/UI evidence.

## November 2 filing parser

The supported Apple 2021 filing now has a repeatable offline parsing entry point:
`python scripts/parse_filing.py`. See [parsing instructions](docs/PARSING.md) for
dependencies, source snapshot provenance, output records and the indexing handoff.
This prepares data; it does not make the application/index ready.

The parser handoff records the November 2 scope. Its single-filing output remains
a starting artifact; later indexing, corpus expansion and evaluation must follow
the current unified plan rather than the older handoff's scheduling assumptions.

## Current unified plan

The single current [PRD](docs/plan/PRD.md) and its [editable Word copy](docs/plan/FinRAG_PRD.docx) consolidate the submitted proposal, professor feedback, course requirements and sequential implementation advice. The [dated tasks](docs/plan/TASK_REQUIREMENTS.md), [schedule](docs/plan/schedule.json), [course mapping](docs/plan/COURSE_ALIGNMENT.md) and [review guide](docs/review/README.md) use that same revision. Older plans in history are reference only.

Exactly one member is assigned per date through November 17. Pavan handles November 12 integration, Likhit November 13 corpus and representations, Gowtham November 14 interface and runner, Ujjwal November 15 independent approvals and runs, Sudhansh November 16 results and reporting, and Shanay November 17 release and submission. The old later recovery dates are superseded. Features and hours are requirements and estimates, not completion claims. The current integration report distinguishes code fixes, accepted inputs and unverified runtime/evaluation gates.

## Canonical data acceptance

Build Likhit's merged source package with `python scripts/prepare_evidence.py`,
then run `python scripts/verify_canonical_data.py` for Shanay's independent
source/identity checks, real DVC restore and local tracking readback.
See the [validation handoff](docs/handoffs/2026-11-05_shanay.md) and
[review](docs/reports/2026-11-05_shanay-review.md). This validates the bounded
Apple input package. The next gate now has a real pinned BGE/exact FAISS build:
see [indexing and restart instructions](docs/INDEXING.md), the
[November 6 handoff](docs/handoffs/2026-11-06_likhit.md), and the
[proposal review and coverage limits](docs/reports/2026-11-07_index-review.md).
Final models, cumulative retrieval stages and A-G evaluation remain separate gates.

The current dense index contains 316 narratives and 219 cells from the accepted
Apple 2021 package, with three parent tables stored separately. The expanded
manifest accounts for 18 filings across ten companies; downloaded PDF renditions
are **not** counted as parsed or indexed filings. The application UI remains gated
until the complete answer path is validated.
