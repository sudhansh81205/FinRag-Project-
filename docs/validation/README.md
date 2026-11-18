# FinRAG validation

The [protocol](2026-11-18_protocol.md) and [actual results/presentation defence](2026-11-18-results/RESULTS_AND_PRESENTATION.md) document a PRD-aligned **development subset**, not the full final A–G study. The [slide copy and speaking script](2026-11-18-results/SLIDE_COPY.txt) can be used in the existing results slide of the required six-slide deck.

-90 actual local application requests:72numerical,12adversarial and6narrative.
-71 numerical references corroborated against original inline source values, scales and context dates; one separate missing-evidence case.
-71 original-query retrieval comparisons: same canonical cells/BGE/exact FAISS/filing filters/depth; dense versus BM25/RRF60.
-10,000 paired filing-cluster bootstrap resamples; all failures retained.
-[Actual narrative review packet](2026-11-18-results/narrative-review.html): six outputs and their exact included source contexts; all semantic decisions remain unreviewed.
-Raw cases, responses, references, ranking IDs, hashes and the disclosed retrieval API-binding correction are retained with the report.

Use `scripts/evaluate_workspace.py --help` to reproduce on a prepared machine. Never add the source references to a model prompt or reclassify the development questions as held-out. No application code, deployment, independent approvals or original PRD scope was changed by this study.

[Plain-text benchmark report](../../BENCHMARK_RESULTS.txt) summarizes the application and retrieval metrics. Reproduce the supplemental operand-level nDCG@10 from the saved rankings with `python scripts/score_development_rankings.py`. The [per-question scores and paired interval](2026-11-18-results/operand-ndcg.json) use the original labels and rankings. No new retrieval or generation runs were used for this supplemental metric.


The [official-source retrieval evaluation](official-source/README.md) adds pooled FinanceBench, FinQA and TAT-QA retrieval results, three Gemma pilots and a measured runtime projection. Its per-question source mappings and scoring artifacts are retained alongside the earlier development validation.
