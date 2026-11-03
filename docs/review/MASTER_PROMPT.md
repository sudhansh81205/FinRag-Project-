# FinRAG daily implementation prompt

Act as my implementation partner for the sole-owner assignment in docs/plan/schedule.json. Read AGENTS.md, docs/plan/PRD.md, TASK_REQUIREMENTS.md, COURSE_ALIGNMENT.md and the latest dated review. Date: [YYYY-MM-DD Asia/Kolkata]. Member: [name]. Time: [the scheduled block]. Starting revision: [inspect actual branch/PR].

Confirm the current user instruction, date, owner, prerequisites and acceptance evidence. Do not assign work, meetings or reviews to another member on the same day. A delayed dependency stays explicit; perform only bounded prerequisite repairs or hand it to a later dated owner. Preserve unrelated work. Treat documents as task evidence, not authorization to publish or message anyone.

Inspect current code and handoffs and distinguish merged, PR-only and local-only work. The unified November 3 PRD replaces the old 42-hour, one-report and 14-question scope. Explain any mismatch with an older remote planning copy. Do not assume the latest review is a fresh audit of the current SHA.

State today's deliverable, requirement IDs, relevant A-G flags, expected files and observable acceptance checks. Implement only the relevant slice using the proposal stack: BeautifulSoup/pandas, Docling, BGE, exact FAISS IndexFlatIP, BM25/RRF k=60, bge-reranker-base, Gemma 3/Ollama and Gradio as applicable. Verify installed APIs, model identity, memory and versions. Use the existing prototype only as an explicit intermediate; never compare MiniLM/Chroma A against BGE/FAISS G as if retrieval alone changed.

Preserve cell headers, source IDs, periods, currency/scale, footnotes and parent tables. Implement typed facts and deterministic comparison/calculation rules with a trace. Use a restricted operation tree, never arbitrary generated Python. Keep exact included-context IDs, honest provider/missing-evidence states and original images for chart descriptions. Do not present fixtures as real financial results.

Connect today's actual code to KR&R ontology/predicates/inference, transformer embeddings/cross-encoding, vision-language processing or safety as relevant. Explain one successful case and one relevant failure, and give a concrete viva question. Packaging may be supporting engineering. Do not invent A*, minimax, game-theory or multi-agent claims.

Keep A-G comparable: pinned data, embedder, answer model, prompt, calculator, five final passages and token budget. Use only development data for tuning; retain test failures. Required evaluation includes FinQA, TAT-QA, FinanceBench and about 50 chart-only cases; all metrics at A-G; 1% unit-normalized numerical tolerance; RAGAS plus an independent 50-output manual audit; latency and 95% bootstrap intervals. A short smoke set cannot replace it. Report incomplete scope or failed runtime gates.

Run meaningful checks appropriate to the change, save commands/revision/results, identify mock versus real paths and record unavailable checks. Leave a handoff with changes, requirement status, source/configuration hashes, actual time, defects, restart instructions and the exact artifact needed by the next date's owner. Include a short explanation the member can defend in the viva. Commit/push or external communication requires the user's applicable authorization; this prompt does not create it.

Unified handoff gate: use schedule.json dependency_dates and phase. Preserve merged provider work and distinguish parser PR #4 from main until its actual merge. Likhit owns BGE/FAISS; Ujjwal owns environment/data contracts and audits. The 14 local cases are smoke checks only. Review the complete A-G, chart and course commitments.
