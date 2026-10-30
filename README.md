# FinRAG

FinRAG is a prototype for answering questions about SEC 10-K annual reports using retrieved narrative and table evidence. The completion plan focuses on source citations, checked calculations, clear failure states and a small measured comparison.

## Team plan

The revised plan runs from **October 30 through November 17, 2026**, with **seven members and exactly one assigned worker per day**. Each member has six planned hours across the schedule.

- [Read the PRD](docs/plan/PRD.md)
- [Download the editable PRD](docs/plan/FinRAG_PRD_17Nov2026.docx)
- [See the dated assignments and completion checks](docs/plan/schedule.json)
- [Use the daily implementation master prompt](docs/review/MASTER_PROMPT.md)
- [Understand the nightly review process](docs/review/README.md)

## Run the shared project

Use **`main`** for the shared project. The UI, modular backend, PRD and review kit are combined here. The original UI/container are preserved under `prototypes/`, and the notebook remains an ingestion reference.

Start with the [setup guide](docs/SETUP.md). The single entry point is `python app.py`. This setup milestone launches without a key or model download and clearly reports `not_ready`. Real answering, validated ingestion, citations and calculations remain scheduled work.

The first two assignments were completed together at the user's request on October 30. Read the [handoff](docs/handoffs/2026-10-30_days-01-02.md) and [completion report](docs/reports/2026-10-30_days-01-02_completion.md) before starting later work. November 17 is the team's completion target; the official course cutoff is unconfirmed.

The planned integrated answering path retains Chroma, MiniLM embeddings, a cross encoder and a verified real language-model provider. BM25 search, chart understanding, vector-store migration and broad benchmark evaluation are deferred.

## Daily workflow

The scheduled owner reads the revised PRD, their dated task and the latest available nightly review, then fills in the master prompt. Work includes verification and a written handoff for the next scheduled owner. Code and check results must support completion claims; commit messages alone are not proof.

The nightly review is configured separately in the desktop app for 11:59 PM Asia/Kolkata. This repository provides its instructions and report template; cloning the repository does not start that automation. Generated reports and personal delivery settings stay local unless deliberately shared after review.
