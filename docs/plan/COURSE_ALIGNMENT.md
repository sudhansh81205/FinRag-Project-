# FinRAG implementation and course alignment

Effective November 12, 2026. Read the current PRD and one-owner calendar through November 17. A course mapping is a claim to demonstrate in code and evidence, not a substitute for a working feature or an experiment.

## Connection to Course Concepts

| Course concept | Concrete implementation target | Success and relevant failure | Viva question |
| --- | --- | --- | --- |
| KR&R ontology and typed facts, T1 chapters 7-10 | A canonical source/cell binds issuer, accession, statement/metric, scope, period, value, currency/unit/scale, parent and original source. | Correct source-derived metadata survives restore; changed period, scale, parent or source hash is rejected. | Why can valid JSON and matching content bytes still contain a wrong financial fact? |
| KR&R predicates and inference | Deterministic premises license only a restricted cited operation tree; retain rules, operands and exact conclusion. | Apple 2021 sales 365,817 and cost 212,981 USD million imply gross margin 41.78 percent; wrong issuer/period/unit, excluded operand or zero denominator blocks the result. | Which exact premises justify this conclusion, and which may a model never override? |
| DL for NLP, T1 chapter 25 | Pinned BGE separately embeds question/evidence; bge-reranker-base jointly scores pairs; Gemma proposes bounded programs or grounded explanations. | Real compatible embeddings/scores/generation succeed; wrong model revision, malformed reranker scores or provider failure is explicit. | How does cross-encoding differ from cosine ranking, and why must its failure not count as a successful variant? |
| Computer vision, T1 chapter 27 | A pretrained vision-language model describes an original report image with source/hash/model provenance and unknown values. | A readable printed title/axis is source-linked; unprinted or ambiguous point values remain unknown and pending labels stay excluded. | Why do a chart image hash and syntactically valid caption not prove that caption is true? |
| Ethics and safety, T1 chapter 28 | AI-use disclosure, source checks, honest errors/coverage, independent labels and no unsupported financial advice. | A supported answer cites actual included sources; no-evidence/model failure clears output rather than returning a mock success. | What uncertainty and limitations should the user see? |

These are pretrained-model applications, not model training or fine-tuning. BM25/RRF are information retrieval and routing is bounded control logic. Do not claim A star, CSP, minimax, game theory or multi-agent reasoning from them. Packaging, CI, DVC/MLflow and deployment are supporting engineering for reproducibility.

## Required proof in meaningful changes and reviews

Record the applicable R requirement and canonical A-G stage or common control, exact code/data/model revision, actual success and a relevant failure path, commands/results and unrun checks. Explain the rule or model boundary that causes each outcome. Distinguish real source/model evidence from injected tests, planned features and PR-only work; include a concrete viva explanation. Never infer understanding or hours from commits.

Canonical stages are A fixed overlapping narratives/flattened tables, B section-aware narratives, C cells/parents, D dense/BM25 RRF60, E hierarchical candidates/cross-encoder, F bounded routing and G approved source-linked chart descriptions. Common explicit eligibility is not the E-only hierarchical change. A-G share BGE/exact FAISS, corpus, answer model, prompt, calculator, five final passages, tokenizer/budget and random settings.

For example, pre-top-k company/period eligibility implements an input precondition; typed calculator comparability implements financial inference. A parent/source hash alone does not do either. Original-image extraction is a source capability, not evidence that a vision model ran or an independent label passed.

## Sequential review and independent evidence

Pavan on November 12 accepts integration/common controls and the experiment scaffold. Likhit on November 13 builds supported corpus and matched representations with methods evidence. Gowtham on November 14 connects the UI, loaders/runner and measured real capacity. Ujjwal on November 15 independently checks source/index/benchmark/chart inputs, freezes accepted controls and launches complete jobs. Sudhansh on November 16 verifies metrics, audits non-self-authored outputs and completes report/six-slide drafts. Shanay on November 17 completes remaining independent exclusions and release/submission. One named worker owns each date, including reviews and handoffs; no off-day background reviewer is assigned.

Preserve named label authors and reviewers. A member cannot independently certify their own labels. Fifty chart questions with fifteen development/thirty-five held-out image groups are separate from fifty stratified generated outputs audited against exact included context and original sources.

The final report must contain the explicit section Connection to Course Concepts and a testable research question. Retain full benchmark/A-G metrics, 1 percent normalized numerical tolerance with zero-gold policy, RAGAS, latency, paired 95 percent confidence intervals and failure/exclusion denominators. Fourteen smoke cases are not the final experiment. Individual official viva attendance remains required when the course schedules it; project development/operational ownership remains one member per date.

