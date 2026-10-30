# Day 1 integration decision and acceptance checklist

Completed for Sudhansh's October 30 assignment with AI assistance on October 30,
2026. The user also authorized completing Shanay's October 31 task early. The
remaining one-owner-per-date schedule and equal planned allocations stay unchanged;
this is not evidence that either member personally spent the scheduled hours.

## One project, one branch, one entry point

`main` is the shared branch. Combine main's UI/notebook, the modular backend and the
PRD/review kit with a history-preserving merge. Do not pick one version and discard
the other. Keep the original UI and container under `prototypes/` as historical
references. Team launch command: **`python app.py`** from the repository root.

| Existing component | Integration decision | Remaining owner/task |
| --- | --- | --- |
| Main Gradio UI | Reuse question/status/answer/evidence layout in `app.py`; lazy UI import | Gowtham adds source-linked results Nov 5 |
| Notebook ingestion | Keep reference, select exact source in manifest | Likhit implements reproducible parser Nov 2 |
| `DualHybridRetriever` | Reuse through `assemble_engine`; dense dual-stream, no BM25 claim | Ujjwal index Nov 3; Pavan metadata Nov 4 |
| `SimpleFinancialReranker` | Inject existing cross encoder, keep record objects | Pavan context selection Nov 8 |
| `UnifiedLLMClient` and engine | Keep modules, explicit dependency assembly, no default creation in UI | Rushil removes false success Nov 1 |
| Config / dependencies | One YAML loader and private env overrides; MiniLM replaces unused BGE setting | Shanay's setup task |
| Calculator helpers | Preserve as prototype, not connected or claimed validated | Rushil typed operations Nov 7 |
| Old evaluation / Docker | Historical only; native launch is canonical | Matched evaluation later; container deferred |

## Fixed scope

One [Apple fiscal 2021 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm),
accession `0000320193-21-000105`, period ended September 25, 2021; selected Items
1A, 7 and 8. Comparative statements use 2021/2020/2019 where present; the balance
sheet uses its own actual periods. Proposed three tables: operations, balance
sheets and cash flows. Source identity is recorded in
[`data/filing_manifest.json`](../../data/filing_manifest.json). It is selected,
not downloaded or parsed in this task. Null checksum/count fields are intentional.

Keep Python 3.12, Gradio, Chroma, MiniLM and the existing cross encoder. Use one
verified real provider later. Required outcomes: source-backed narrative/table
answers, typed basic arithmetic, explicit abstention/failure, repeatable launch,
14 checked questions with a 7/7 split and two controlled retrieval modes. BM25,
charts, extra corpora, cloud/container work and broad benchmarks remain deferred.

## Day 1 acceptance

- [x] One integration route and canonical launch path selected.
- [x] Exact proposed filing and three proposed tables recorded.
- [x] [Evidence/status contract](EVIDENCE_CONTRACT.md) and [examples](record_examples.json) saved.
- [x] [Team delivery checklist](DELIVERY_CHECKLIST.md) saved, with unknown official requirements visible.
- [x] Shared [Day 1/2 handoff](../handoffs/2026-10-30_days-01-02.md) created.

Model-access assumption: a teammate can provide a privately configured Gemini key
or working local Ollama model during November 1 verification. No model ID or live
availability is assumed from the old hardcoded names. A missing provider must not
silently invoke a mock.

## Delivery clarification from the user

November 17 is the **team's internal completion target**, not a confirmed hard
course cutoff. The original request mentioned November 21 submission; its exact
time, portal and mandatory course rubric remain unconfirmed. This clarification
supersedes the stronger deadline wording in the original Word snapshot. Continue
planning to finish by November 17; do not invent an official cutoff time.
