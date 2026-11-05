# November 5: Likhit review, fallback checks and Shanay validation

User-requested on-demand review and implementation. This report does not replace
the scheduled 23:59 IST review or advance its last successful cutoff.

## Snapshot, attribution and coverage

Remote snapshot: November 5, 2026, 23:04:26 IST (17:34:26 UTC), before the
23:59 IST / 18:29 UTC nightly cutoff. Main was
[`5fef2085376c554635f3c0a4937adfa5fbb94b5f`](https://github.com/sudhansh81205/FinRag-Project-/commit/5fef2085376c554635f3c0a4937adfa5fbb94b5f).
GitHub connector metadata confirms merged
[PR 6](https://github.com/sudhansh81205/FinRag-Project-/pull/6), head
`673fed624ee07dd23378fa995911834257d8563e`, submitted by `likhit-09B` and
merged November 5 at 22:26:30 IST. The named handoff identifies Likhit; commits
do not prove sole authorship or hours. Main's
[workflow 42069637473](https://github.com/sudhansh81205/FinRag-Project-/actions/runs/42069637473)
passed. No open PRs or independent unmerged remote-branch work were observed.
Public API access was rate-limited; authenticated read-only access supplied the
workflow snapshot. The connector supplied repository and PR metadata first.

The last nightly cutoff remains November 4, 23:59 IST. Earlier daytime reports
reviewed main `e273b22` and application `19457fe`. The newly visible change is
Likhit's late November 4 submission, not a newly assigned second November 5
worker. Today's sole scheduled owner is Shanay, 8 estimated hours, R2/R3/R13.
This task's implementation and source inspection are AI-assisted. Actual human
hours and viva understanding are unverified. Existing dirty work in the original
and old planning checkouts was preserved; work used the clean existing repair
checkout, fast-forwarded to current main.

## Initial review and prioritized gaps

**F11, P1: schema-valid metadata can disagree with the original fact.**
At reviewed main,
[validate_records, lines 21-33](https://github.com/sudhansh81205/FinRag-Project-/blob/5fef2085376c554635f3c0a4937adfa5fbb94b5f/scripts/prepare_evidence.py#L21)
checks schema, duplicate IDs and content hashes. Mutating a cell's period,
scale, unit, normalized amount, scope, metric, footnote or parent can pass that
boundary. Executed regressions reproduce 13 shape-valid mutations and require
the new source predicates to reject them. This is a missing independent
acceptance gate; no claim is made that the submitted actual values were wrong.
Consequence: invalid metadata could reach indexing despite a green shape check.
Repair: compare records against the original DOM facts, grid and typed contexts;
bind candidates, metadata and parents with exact ordered sidecars. Confidence
high. R2/R3/R13, common A-G identity and C/G provenance. KR&R integrity predicates.
Viva: which premises establish the period and scale beyond matching bytes?

**F12, P2: output selection can overwrite a different generation.**
At reviewed main,
[prepare, lines 103-106](https://github.com/sudhansh81205/FinRag-Project-/blob/5fef2085376c554635f3c0a4937adfa5fbb94b5f/scripts/prepare_evidence.py#L103)
unconditionally replaces four filenames under the caller's output directory.
This is a source-confirmed destination-safety defect; the review did not erase
an existing user's package to demonstrate it. Repair: allow only identical
reingestion into an existing destination and require a fresh directory for
different generations. Verification proves identical bytes remain and a foreign
filing destination is rejected without changing it or the original package.
Confidence high. R2/R13, common A-G reproducibility; supporting engineering and
source integrity. Viva: why does atomic replacement of one file not establish
that replacing a whole filing's data is safe?

**P1 task gate: real-package restoration was missing.** Ujjwal's synthetic DVC
fixture and the parser's own tests did not establish the November 5 acceptance.
Shanay's new command restores the actual package and all references and reruns
the independent audit. It preserves failure reports and blocks on missing tools.
This closes a scheduled acceptance gap, not a newly discovered extraction defect.

## What was completed and verified

Verified implementation revision: [`3f54580727a198c325297a39756c712c473d34f9`](https://github.com/sudhansh81205/FinRag-Project-/commit/3f54580727a198c325297a39756c712c473d34f9). Final full suite: 153 passed in 165.16 seconds. Real-package validation and tracking were repeated on this committed code.

The baseline at `5fef208` passed 131 tests. The expanded suite passes 153 tests;
the adjacent JSON records the final code revision, file fingerprints, test
duration, package/tool versions, artifact hashes and reject-case ledger.

- Accepted unchanged real source package: 316 narratives, 3 full parents,
  219 cells, 11 PDF corroborations and one original chart asset.
- Independently checked all narrative slices and cell contexts, parent/grid
  links, comparative periods, scales, scope, signs, footnotes and readable facts.
  Seven saved fixtures cover sales, EPS/share-count scale exceptions, assets,
  negative repurchases and the opening-balance period exception.
- Visually inspected statement pages 32/34/36 and the original performance graph.
  A second PDF text extractor checks the selected values. The original chart
  object bytes match; no generated captions or question labels are certified.
- Repeated builds match all four package files exactly. The 535 candidate IDs
  and metadata are aligned; parents are stored separately. Swapped rows fail.
- Real DVC restoration of 11 files matches every before/after SHA-256 and repeats
  the source/sidecar acceptance from the restored references. Persistent MLflow
  readback verifies the completed run and downloaded JSON artifact bytes.
- Missing data/DVC, empty/duplicate/corrupt input and shape-valid semantic
  corruptions leave explicit rejections. Existing output cannot be silently
  replaced with another generation. CI now executes this real-data gate.
- Ruff, dependency consistency and whitespace checks pass. The old environment
  command also passes its scoped parser/DVC/MLflow smoke. Setup still returns
  the expected `index_not_ready`; no live generation was performed.

The first new audit run exposed overly strict auditor assumptions: statement
titles differ only in case; opening cash is a prior instant; numeric label facts
and hidden blank-row tags are not extra value cells. Those assumptions were
corrected against the original pages and protected by fixtures. An intermediate
new-test run had one failing acceptance assertion before the title fix. Final
results supersede that run and do not hide it.

## Fallback and inherited finding history

F1/F2/F6 provider/error fixes and F3/F4/F5/F7/F8/F9/F10 repairs were already merged
before PR 6. Current regression checks preserve explicit provider failure, no
mock success, no generation without usable evidence, retained retrieval IDs,
zero disabled-stream calls, whole included context, honest arithmetic failures,
updated handoff directions and saved missing-tool diagnostics. No duplicate
repair credit is assigned to this task. MiniLM/Chroma is retained as historical
recovery code; it is not silently substituted for final BGE/exact FAISS.

## Cumulative project position

| Requirement | Actual acceptance position after this task |
| --- | --- |
| R1 corpus | Partial: ten filing identities inventoried; only Apple 2021 processed; ten-company coverage unmet |
| R2 index | Accepted bounded input/sidecar/restore gate; actual BGE/FAISS and vector-row proof pending |
| R3 evidence | Checked HTML cell/parent profile accepted; PDF corroboration bounded, general layouts/OCR absent |
| R4 generation | Earlier real-provider boundary preserved; final measured Gemma/Ollama pin pending |
| R5 calculations | Legacy safety repairs preserved; typed cited restricted multi-step inference pending |
| R6 interface | Setup and explicit failure statuses exist; complete real answer workflow pending |
| R7 evaluation | Full benchmarks, all metrics, independent audits and confidence intervals pending |
| R8 report/course | Plans and dated evidence exist; final report, six slides and demo still pending |
| R9 restatements | Unscheduled Phase 2, unchanged |
| R10 retrieval | Earlier ID/context repairs preserved; final hybrid/reranking/routing stages pending |
| R11 charts | Original asset accepted; generated descriptions and independently checked 50 questions absent |
| R12 A-G controls | Required comparison retained; full matched stages and measured experiment pending |
| R13 reproducibility | Bounded canonical restore/tracking gate passes; clean final index/model release remains later work |

An overall completion percentage is not defensible from these mixed gates.
The full application is still not ready. No paid inference, model download,
benchmark run, hosting or external message occurred in this task. Declared parser
dependencies were installed locally for implementation verification, not treated
as evidence that models or the broader parser pipeline are ready.

## November 6: next sole owner and improvement bridge

Likhit, 10 estimated hours, R1/R2. Consume the accepted package and exact hashes
from the [handoff](../handoffs/2026-11-05_shanay.md); retain the limitations.
Pin BAAI/bge-base-en-v1.5 revision/preprocessing; use 768-D normalized embeddings
and exact FAISS IndexFlatIP consistently for A-G. Bind vector row i to candidate
ID and metadata row i, keep parents separately and validate schema/data/model
fingerprints. Test real repeat ingestion/reload, wrong dimensions/models/IDs,
filters, stale-row replacement and unrelated-filing retention. Continue corpus
coverage with explicit parsed/indexed versus inventory counts.

The current stack is Python, BeautifulSoup/lxml, JSON Schema, docling-parse,
pypdf, DVC and MLflow. Exact locally verified versions are in the JSON. CI uses
Python 3.12; the local audit used 3.14.3. BGE/FAISS libraries/model weights and
their runtime compatibility are not installed or certified by this task.
No new framework/service is needed for this data gate. The next owner must
verify model assets and supported APIs on the intended embedding machine.

F11 missing source predicates -> accepted source/sidecar gate -> indexing can
reject altered facts before model execution -> source-corruption and row-swap
checks. F12 unsafe destination -> immutable generations -> another filing is
preserved -> identical rerun plus foreign-destination rejection. Missing real
restore -> checked 11-file restoration -> source identities survive storage ->
equal hashes, counts, IDs and source audit after checkout.

Deferred work remains with later scheduled owners: Pavan retrieval/context,
Rushil final model/inference/chart captions and subsequent evaluation/audits.
No same-day background tasks are assigned. If index/corpus work exceeds the
November 6 slot, report the exact unmet gate and later recovery need rather than
claiming the entire corpus is ready. November 17 is internal checkpoint,
November 20 freeze, November 21 demo/individual viva, November 22 final files;
the exact Classroom cutoff is unverified. No scheduler changes were made.

## Copy-ready prompts

Implementation: Act as Likhit's partner for November 6, sole owner, 10 estimated
hours. Read AGENTS.md, unified PRD/TASK_REQUIREMENTS/COURSE_ALIGNMENT/schedule,
MASTER_PROMPT.md and Shanay's dated handoff. Inspect actual main and the accepted
package/code/schema hashes. Build pinned BGE 768-D normalized exact IndexFlatIP
with stable candidate IDs and separate parents. Prove repeats/reload/filtering,
reject stale/wrong sidecars/models/dimensions, preserve unrelated filings and
report actual corpus counts. Do not use MiniLM/Chroma for the final A-G baseline
or invent missing model assets. Save success/failure evidence and a viva trace.

Verification/handoff: Audit Likhit's exact revision and real model/data/index
artifacts. Run the canonical gate first, then trace a narrative and a table cell
from source to ordered sidecar to actual vector row and retrieved ID. Test
reload, mismatched rows/models/dimensions and isolated replacement. Record
commands, versions, hashes and absent checks. Explain transformer embeddings
versus typed integrity predicates. Give November 7 Pavan exact accepted inputs
or an explicit dependency block; assign nobody background work off their date.

## Connection to Course Concepts and experiment controls

R2/R3/R13 and common A-G identity, C parent/cell representation and G original
image provenance map to KR&R ontology and deterministic integrity predicates.
The implementation checks premises against the original source and concludes
only bounded package acceptance. Matching hashes/schema alone is insufficient.
Success: a negative displayed repurchase cell preserves its period, unit, parent
and ID through DVC. Failure: a schema-valid changed scale is rejected against
the source fact; a swapped metadata row fails. Viva: why is opening cash a prior
instant, and why does accepted input not establish financial comparability or
an existing vector index? Final financial inference remains R5's later work.

DL embeddings, cross-encoding, generation and chart vision remain separate
stages. This task runs none of those final models. No A*, minimax, game theory
or multi-agent reasoning is claimed from retrieval/routing. Safety includes
explicit blocking, source fidelity and AI-use disclosure.

Preserve FinQA, TAT-QA and FinanceBench, cumulative A-G with common corpus/BGE/
FAISS/model/prompt/calculator/five passages/token budget, 1% unit-normalized
numerical tolerance with a declared zero-gold policy, Recall@5/@10, MRR,
narrative/answer metrics, RAGAS, median latency and paired 95% intervals.
The independent 50-output faithfulness audit is separate from 50 chart-only
questions (15 development / 35 held-out grouped by image). Retain failures,
exclusions, coverage and denominators. Source fixtures and 14 local smoke cases
do not replace any of these commitments. Real throughput/capacity remains open.

## Delivery

The user authorized committing and pushing these changes to main after checks.
The machine evidence records the code revision; the final chat confirms the
actual pushed head. No ChatGPT coauthor trailer is added, per the user's request.
Reports/handoffs are saved in the repository; private runtime artifacts remain
local. Nothing was emailed or sent to WhatsApp, and no delivery/read claim is made.
