# FinRAG

FinRAG is a prototype for answering questions about SEC 10-K annual reports using retrieved narrative and table evidence. The completion plan focuses on source citations, checked calculations, clear failure states and a small measured comparison.

## Team plan

The revised plan runs from **October 30 through November 17, 2026**, with **seven members and exactly one assigned worker per day**. Each member has six planned hours across the schedule.

- [Read the PRD](docs/plan/PRD.md)
- [Download the editable PRD](docs/plan/FinRAG_PRD_17Nov2026.docx)
- [See the dated assignments and completion checks](docs/plan/schedule.json)
- [Use the daily implementation master prompt](docs/review/MASTER_PROMPT.md)
- [Understand the nightly review process](docs/review/README.md)

## Prototype status

The default branch contains the notebook and Gradio application prototype. The `feature/engine-backend` branch contains the modular backend prototype for integration review. These versions need integration; the PRD records the remaining work and does not claim that the planned fixes have been implemented.

The project currently uses Chroma, MiniLM embeddings, a cross encoder and a real language-model provider. The reduced delivery scope retains this stack. BM25 search, chart understanding, vector-store migration and broad benchmark evaluation are deferred.

## Daily workflow

The scheduled owner reads the revised PRD, their dated task and the latest available nightly review, then fills in the master prompt. Work includes verification and a written handoff for the next scheduled owner. Code and check results must support completion claims; commit messages alone are not proof.

The nightly review is configured separately in the desktop app for 11:59 PM Asia/Kolkata. This repository provides its instructions and report template; cloning the repository does not start that automation. Generated reports and personal delivery settings stay local unless deliberately shared after review.
