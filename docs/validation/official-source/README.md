# Official-source retrieval evaluation

The [plain-text report](BENCHMARK_RESULTS.txt) contains completed retrieval results, three actual Gemma pilot responses, and the projected generation workload. It records the time available, incomplete runs and remaining PRD requirements.

The run attempted 150 FinanceBench, 1,147 FinQA and 1,663 TAT-QA questions. Keyword retrieval completed all three suites. BGE/exact FAISS and BM25/RRF60 completed FinQA and TAT-QA. Three TAT-QA questions lack evidence labels, so they have undefined retrieval metrics. FinanceBench dense/hybrid remains incomplete.

## Method and PRD mapping

This R7/R12 baseline evaluates original questions against pooled official sources. FinanceBench uses all readable pages from 84 reports. FinQA and TAT-QA pool their declared test contexts. Table records retain whole-table identities. Dense BGE embeds 440-token windows with stride 400, retrieves up to 400 chunks and ranks ten distinct original sources by first hit. Hybrid fuses the dense and lexical top tens with RRF rank constant 60. Gold evidence IDs enter scoring after retrieval.

This representation evaluates source retrieval. Cumulative PRD A-G representations and generated-answer scoring still require integration and acceptance. Gemma pilots use retrieved passages with a character budget, and retain exactly the context shown to the model. Their answers expose errors and refusals, with claim-level review pending. The pilots use a direct model call without the application's typed calculator.

Per-question Recall@5/10, complete-evidence coverage, MRR@10 and nDCG@10 are retained. Paired intervals use 10,000 whole-document bootstrap resamples with seed 42. FinQA whole-table labels cannot establish individual-cell retrieval accuracy. Different corpus sizes and source granularities limit cross-suite comparisons.

## Inspect the results

Each suite under `results/` contains an input manifest with source hashes, a source ID map, keyword rankings and summary, and the generation pilot. FinQA and TAT-QA also include dense/hybrid rankings and paired summaries. `artifact-hashes.json` binds the exported reports, scripts and result JSON files to their bytes.

The three pilot times imply approximately 403 machine-hours for 20,720 generation requests under a uniform-rate extrapolation. The report gives the exact arithmetic and sample-size limitation. Full A-G execution, RAGAS, the separate Llama comparison, chart acceptance and the independent 50-output audit remain outstanding. Team chart review was reported verbally, with reviewer and approved item IDs still unspecified.

## Reproduce on a prepared machine

Use the repository's existing index/provider environment and pinned local BGE/Gemma assets, then install the supplemental sparse dependency with `python -m pip install -r requirements-benchmark.txt`.

Restore the pinned official datasets with `scripts/import_official_benchmarks.py` and the FinanceBench documents using `scripts/restore_financebench_documents.py`. The default input directory is `output/benchmarks/official`. The FinanceBench full-page corpus and bound 150-case dataset must be present. All checked filenames and hashes are recorded in the suite manifests. Source repositories and revisions are pinned in `src/benchmark/importers.py` for Patronus FinanceBench, FinQA and TAT-QA. Retain their notices and access terms when obtaining data.

Run from the repository root. Set the variables below to existing source assets, an existing BGE cache and a fresh output directory as needed. No credentials belong in the results.

```sh
export FINRAG_BENCHMARK_SOURCE_DIR=/path/to/official
export FINRAG_BGE_CACHE=/path/to/existing/bge-cache
export FINRAG_BENCHMARK_OUTPUT=output/official-evaluation
python scripts/official_benchmarks/run_evaluation.py
python scripts/official_benchmarks/compare_dense.py
python scripts/official_benchmarks/run_evaluation.py --pilot
```

The default output directory is `output/official-evaluation`. Dense batches checkpoint every 256 chunks with source/model/device identity. Generation pilots require the existing Gemma service specified by `configs/gemma3-4b.json`. Choose a fresh output directory for changed sources or settings. The observed original GPU device was Apple Metal, while CPU checkpoints are kept separately.

Verify the published results against local source assets, or regenerate this published text report from its saved results.

```sh
python scripts/official_benchmarks/verify_results.py
python scripts/official_benchmarks/make_report.py
```

Model weights, full source corpora and embedding caches are local runtime assets. Completed ranking and scoring records provide the evidence for the reported results.
