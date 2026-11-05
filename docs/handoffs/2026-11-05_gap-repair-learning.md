# FinRAG learning and handoff

November 5, 2026 repair | How the existing work runs and what the repair changes

Work date and delivery date: November 5, 2026. Exact implementation commit: [19457fe40ec95080da52c9b24f30304f744ba383](https://github.com/sudhansh81205/FinRag-Project-/commit/19457fe40ec95080da52c9b24f30304f744ba383). This guide explains the user's daytime repair through Ujjwal's task, not fictional completion of the previous day's missing extraction. Use the paired review for acceptance status and prioritized gaps. Current review model is gpt-6.1-sol, exposed by this session; earlier review versions remain unknown. FinRAG's current configured inference route is Gemini, while final Gemma remains planned.

## What the project is doing

FinRAG aims to answer questions about company annual reports using evidence the reader can inspect. Retrieval-augmented generation means finding relevant source material before asking a language model to write an answer. A narrative paragraph explains business risks; a financial table carries values, dates and units; a chart is an image whose labels and values must be checked. A reliable answer needs the right source, the right period/unit, justified arithmetic and honest failure states.

Today, one bounded Apple 2021 HTML parser and provider safety boundary exist. The UI deliberately reports index_not_ready. The parser extracts 316 narratives and three full table parents; it does not yet produce the promised typed cells, PDF/chart sources or final corpus. This repair makes current interfaces safer and gives reproducible environment evidence. It is not the full final question-to-answer system.

## Pipeline map: actual versus planned

Actual source path: pinned gzip browser snapshot + filing manifest -> existing parse_filing.py -> filing_parser.parse_filing -> narrative.jsonl / tables.jsonl / parsing_summary.json -> verify_day05_environment.build_report -> contracts.verify_parser_package -> saved diagnostic + DVC fixture restore + MLflow run/artifact readback.

Existing callable engine path, tested with fixtures: FinRAGEngine.answer_financial_question -> DualHybridRetriever.retrieve -> SimpleFinancialReranker.rerank -> whole-record context selection -> build_finrag_prompt -> explicit UnifiedLLMClient.generate -> response status checks. Real index assembly and UI integration remain pending; passing a stub test does not demonstrate end-to-end live retrieval.

Planned final additions: typed cells/PDF/image locators -> independent source audit -> BGE vectors/exact FAISS -> dense plus BM25/RRF -> cross-encoding and routing -> cited restricted calculations and Gemma/chart descriptions -> Gradio answers -> full A-G evaluation. Schemas define the boundary; they do not generate these artifacts.

## Step 1 - preserve evidence identity

An evidence ID is a stable label for one source-backed record. It is different from a row number that can change when a file is reordered. The current parser combines filing accession, section, type, location hash and content hash. A hash is a deterministic fingerprint of bytes; it detects changes but does not establish that the interpretation is correct.

Before the repair, the collection returned IDs but the retriever discarded them. Now [src/retrieval/retriever.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/retrieval/retriever.py#L88) appends `{"id": identity, "content": document, "metadata": meta}`. Metadata means descriptive fields such as accession/type/locator; content is the text itself. Misaligned ID/document/metadata lists fail instead of silently pairing a source with the wrong identity.

The canonical boundary uses evidence_id. [src/contracts.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/contracts.py#L14) deep-copies the record, removes the physical id key, assigns exactly the same value to evidence_id and rejects conflicting aliases. It retains source_rows, so a complete parent table is not flattened away by the adapter. This is a rename, not a new identity or a new parsing algorithm.

Input: a legacy parser record with id/content/metadata and optional full source_rows. Output: equivalent canonical record with evidence_id. Success: identity and grid remain identical; failure: conflicting id/evidence_id raises an error. Exercise: open one actual parent and list the fields that would be lost if you copied only its content string.

## Step 2 - distinguish disabled retrieval from an empty search

A retrieval stream is one category of evidence, such as narratives or tables. A budget of zero means do not search that stream. Before, a text-only baseline still called the table backend with zero results and numerical intent could override the text budget.

The repaired loop includes `if limit == 0: continue` at [src/retrieval/retriever.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/retrieval/retriever.py#L72). A numerical query may prioritize tables, but it cannot exceed the caller's text limit. If both limits are zero, no embedding call is made either. A spy is a test object that records calls; it proves the disabled backend was not contacted, rather than merely checking an empty returned list.

Success trace: text=1/tables=0 -> one text query -> source-1 retained. Failure trace: a backend result has documents but no IDs -> stream error -> engine service_error -> no generation. This supports fair A-G comparisons; it is not BM25, reciprocal rank fusion, A* or a completed router.

## Step 3 - choose complete context before writing the prompt

Context is the evidence sent to the model. Before, the engine listed two table IDs, then prompt formatting cut the combined tables at 4,000 characters. A cited table could be missing or partially cut in the model input. That makes the answer trace unreliable.

Now [src/pipeline/finrag_engine.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/pipeline/finrag_engine.py#L64) selects complete records first. Each rendered block starts with `[Evidence ID: ...]`. Missing IDs, conflicting aliases, duplicates, wrong types and empty content are excluded. A record that would exceed the declared intermediate 8,000-character budget is excluded whole, with reason context_budget. The included IDs are derived from that same selection. Prompt rendering never silently slices it afterward.

Success trace: a 4,500-character table ending END-MARKER fits; the model input still contains END-MARKER and its ID. Failure trace: a 5,000-character table under a 200-character test budget is excluded; a later fitting record is included. If all are too large, insufficient_evidence is returned and the provider is not called.

The budget covers rendered evidence blocks, not full prompt tokens or question text. Characters and tokens differ: a token is a model-specific text unit. Pavan must later use one tokenizer/five-passage budget across A-G and handle full-parent expansion. A source's presence in the prompt also does not prove that every claim in a generated answer cites it correctly.

## Step 4 - repair the existing arithmetic helper

The old growth result divided by abs(prior), while the displayed formula divided by prior. With a negative prior, the shown formula and returned sign disagreed. The unified policy avoids ordinary growth percentages for negative priors altogether.

At [src/llm/financial_reasoning.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/llm/financial_reasoning.py#L18), positive prior 100 and current 120 give (120-100)/100 times 100 = 20%. Prior zero is undefined. Prior -100 and current -50 give absolute change 50 with growth_percentage null and an explanation. Null means no valid value is being asserted, not zero growth.

`parse_currency_amount` handles explicit K/M/B multipliers in base units: 2.5B becomes 2,500,000,000; parentheses mean negative. Do not multiply again because a table header also says millions. This helper does not infer currency, period or scale from source metadata. Tests reject malformed comma grouping, NaN and ambiguous strings. The final pass also guards finite inputs whose subtraction or ratio overflows: 1e308 divided by 1e-308 returns an error and null, never JSON Infinity. Huge Python integers are rejected safely. Final typed cited arithmetic, operation allowlists, depth limits and comparability rules remain future work; a plain float helper is not that reasoning system.

## Step 5 - execute the contract rather than merely describe it

A JSON Schema declares required keys and types. A record can still have the right shape and the wrong source, so the checker also verifies relationships. [src/contracts.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/src/contracts.py#L42) reads the manifest, source archive, parser summary and both JSONL files without editing them.

Checks run in this order: schema availability -> source/archive identity -> file hashes and declared counts -> canonical adapter -> schema -> accession/ticker/URL/hash/parser/type matches -> content fingerprint and deterministic ID -> parent identity -> unique IDs and total reconciliation. The actual source package has 316 narratives and three parents, matching 319 total. Every failure is retained in a reject list, not turned into passed.

Relevant code expressions include `len(identities) != len(set(identities))` for duplicates and comparing `sha256(record['content'].encode('utf-8'))` with metadata content_sha256. A set contains unique values, so unequal lengths expose repeated identities. Checks against expected hashes use original manifest/summary contracts, while the tests deliberately update file-level hashes to prove deeper corruption checks still fail.

The schema has separate requirements for financial_table, table_cell and chart. Current parents require a complete source_rows grid. Future cells need row/column headers, raw/normalized value, period, units/scale, parent and coordinates. Future chart descriptions need original-image identity and unknown-value markers. Those are declared interfaces; no real new cells/charts are created by validating the schema.

Crucial limitation: a mechanically consistent package may still misinterpret a comparative year, scale or footnote. This checker explicitly reports independent_source_audit pending and full_canonical_package_ready false. Shanay must inspect original sources and future cross-record relationships. Never update an expected checksum merely to make a corrupted package pass.

## Step 6 - preserve reproducibility evidence

DVC is a data-versioning/cache tool. [scripts/verify_day05_environment.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/scripts/verify_day05_environment.py#L58) creates a fresh local no-SCM test directory, writes a tiny fixture, adds it to DVC, records its SHA-256, deletes only that just-created fixture, restores it with checkout and compares the bytes. The project dataset is untouched. Success demonstrates a working local cache/restore tool; it does not prove the full corpus was restored. Shanay must do that with actual accepted data.

MLflow records parameters, metrics and artifacts. A parameter describes a run (contract version/source hash); a metric is a numerical observation (319 checked records); an artifact is a saved file (the contract JSON). The old temporary directory vanished after the check. [scripts/verify_day05_environment.py](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/scripts/verify_day05_environment.py#L86) now creates a persistent SQLite database and artifact store under output/environment/runs, logs the data, ends the run, opens a second client and reads back both run and artifact.

Verified local run ID: 31615ebb6dfe40dca2c11d78cc6d448a. It is not a cloud dashboard URL. The report records its local tracking URI so a teammate can create their own equivalent run; a local path is not a phone-accessible link. The retained artifact hash is fa8324a84012e7e9419dffbb619ed96d019a73dd9632a2fff4305dd14fa41018.

Missing dependencies now return blocked rather than throwing before the report is saved. MLflow requires a passed parser contract and skips invalid input. The command prints the report location/status and exits nonzero on smoke failure. `full_pipeline_ready` remains false even when smoke passes. The current interpreter/version is recorded directly; the program does not confuse it with another Python on PATH.

## Setup, reproducible checks and expected results

Use [docs/ENVIRONMENT.md](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/docs/ENVIRONMENT.md) and [requirements-dev.txt](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/requirements-dev.txt). Tested local interpreter: Python 3.14.3; CI uses 3.12. A virtual environment isolates dependencies from other projects. Install the declared packages in it; model weights are separate and are not required for these checks. DVC and MLflow here need no cloud login.

1. `python scripts/parse_filing.py` -> parsed_not_indexed, 316 narratives, 3 tables. Use the intended venv executable. Save any supplied candidate package separately before regenerating files.
2. `python scripts/verify_day05_environment.py` -> environment smoke passed and full_pipeline_ready false; inspect output/environment/report.json and persistent run directories.
3. `python -m pytest -q` -> final code revision: 123 passed. Provider tests use explicit stubs; they do not consume API quota or prove live availability.
4. `python -m ruff check .` and `python -m pip check` -> passed. Ruff finds code-quality errors; pip check finds incompatible installed package requirements.
5. `python app.py --check` -> index_not_ready. This is the truthful expected state, not a test failure or an instruction to invent an empty index.

Common failures: absent JSONL means regenerate existing parser input; wrong hashes mean retain and investigate the package; missing DVC/MLflow means install declared packages in the correct interpreter; local SQLite permissions or missing stored artifacts break readback; unavailable Ollama remains a runtime blocker. Do not paste credentials into reports. The prototype keeps its existing Gemini configuration; this repair does not make a paid call or install Gemma/FAISS/Docling.

## Handoff contracts for Shanay and Likhit

Read [docs/handoffs/2026-11-05_gap-repairs.md](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/docs/handoffs/2026-11-05_gap-repairs.md), [data/contracts/README.md](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/data/contracts/README.md), [data/contracts/canonical_record.schema.json](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/data/contracts/canonical_record.schema.json) and [data/contracts/index_sidecar.schema.json](https://github.com/sudhansh81205/FinRag-Project-/blob/19457fe40ec95080da52c9b24f30304f744ba383/data/contracts/index_sidecar.schema.json) at this exact commit. Current raw-source hash: 8d9e6dbb6acd1f24dbc4345f74240b255ceaaf5beadb5874b143c7f67032e9d2. Existing sorted ID-set hash: 515781949cf725684a60d1d79401a7d4b8b3b7dfcb599b771dc1ba13b723ee1e.

Shanay November 5 (8 estimated hours) independently verifies source facts/periods/units/parents, real canonical data and a clean actual-package restore. Missing Likhit November 4 inputs keep full acceptance blocked. This repair's own regression tests do not count as an independent audit. Preserve reject cases and source versions.

Likhit November 6 (10 estimated hours) uses only the accepted package for BGE normalized 768-D exact FAISS. Ordered vector row i, ID i and sidecar row i must agree. Hash the ordered compact UTF-8 JSON ID array without sorting; it is different from the existing sorted newline ID-set diagnostic. Pin model revision/preprocessing and hash the index/sidecar/parent store. Real duplicate/dimension/model/hash/reload/replacement cases must be checked. His missing cell/PDF/chart work was deliberately not implemented here. Exactly one owner is assigned per date; tutorial viewing is guidance within that allocation, not extra compulsory team hours.

## Concepts and viva questions with answers

1. What is KR&R here? Typed evidence identity and integrity predicates are implemented. Full financial inference will conclude an operation is allowed only when cited operands satisfy issuer/metric/scope/period/unit rules. Metadata storage alone is not that inference layer.

2. Why cannot matching hashes prove a financial fact? Hashes detect byte changes. They do not interpret headers, fiscal periods or footnotes, so independent source checks remain necessary.

3. What is the difference between BGE and a cross-encoder? BGE separately encodes query/document to vectors for search. A cross-encoder jointly reads a pair to score relevance. The final BGE/cross-encoder runs are planned, not demonstrated by this repair.

4. Why normalize vectors before IndexFlatIP? For unit-length vectors, inner product equals cosine similarity. IndexFlatIP compares exactly against stored vectors; it does not itself prove correct source mapping or financial truth. Actual normalization/index construction remains Likhit's work.

5. What safety behavior is implemented? Provider failures and test-only mocks never become financial success; missing evidence stops generation; complete included records and IDs stay aligned. A saved failure is more useful than a missing diagnostic.

6. Is chart schema validation computer vision? No. Vision requires actual image processing/description and independent comparison against the source image. Unreadable values must remain unknown.

7. Does this implement A*, minimax or multi-agent reasoning? No. Retrieval/fusion/routing are information-retrieval/control methods; these course claims would be inaccurate.

8. Why are the two groups of 50 different? Chart questions test chart-only answerability; the separate 50-output audit independently checks faithfulness of sampled generated answers. Neither is replaced by 14 smoke questions.

## Understanding exercises

- Trace one table from archive to source_rows to canonical adapter. Write down which identity remains the same and which file hash changes if serialization changes. Do not edit the real source package.
- Run the named duplicate-ID regression and explain why updating the JSONL file hash still cannot make duplicates valid.
- Predict the included IDs for three records sized 100, 9000 and 200 characters under the 8000-character evidence budget, then inspect the exclusion reason in a test fixture.
- Compare 120/100, -50/-100 and 1/0 through the legacy growth helper. Explain why a missing percentage is neither zero nor a model failure.
- Open the saved environment report and identify a parameter, a metric, an artifact hash, a verified smoke result and a still-blocked final dependency.

## Verified video tutorials

The following direct video links and creator/title metadata were checked against YouTube oEmbed on November 5, 2026. Videos were not claimed to be watched; no timestamps are invented. They teach concepts, while installed versions and official documentation govern current APIs.

- [Corey Schafer - Python Tutorial: Working with JSON Data using the json Module](https://www.youtube.com/watch?v=9N6a-VLBa2I). Topic: JSON records and serialization. Follow-along: Read one parser JSONL line with json.loads, show id/content/metadata, and explain why a JSON Schema shape check needs additional cross-record hashes.

- [freeCodeCamp.org - Git and GitHub for Beginners - Crash Course](https://www.youtube.com/watch?v=RGOj5yH7evk). Topic: Exact revisions and shared main. Follow-along: Use git show on the reviewed SHA, compare it with the starting main SHA, and distinguish a branch name from immutable code identity. Do not force-push.

- [freeCodeCamp.org - Pytest Tutorial – How to Test Python Code](https://www.youtube.com/watch?v=cHYq1MRoyI0). Topic: Regression tests and failure paths. Follow-along: Run the duplicate/corrupt-data and context-budget tests, identify their synthetic inputs, and explain what a passing stub cannot prove about real models.

Official references checked for the implemented tools: [JSON Schema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/), [DVC checkout](https://doc.dvc.org/command-reference/checkout), [MLflow client](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.client.html). Future index concepts: [official BGE model card](https://huggingface.co/BAAI/bge-base-en-v1.5) and [FAISS IndexFlatIP](https://faiss.ai/cpp_api/struct/structfaiss_1_1IndexFlatIP.html).

Final scope reminder: full named benchmarks and A-G metrics, 1% unit-normalized tolerance, RAGAS, latency/confidence intervals and independent audits remain open. November 17 is the internal target, November 21 demo/viva and November 22 final submission. This guide improves understanding and the prerequisite handoff; it is not a claim of a completed project or measured human effort.
