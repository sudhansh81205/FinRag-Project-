"""
FinRAG Engine (Members 2 & 3 Orchestration)
Glues together the DualHybridRetriever, SimpleFinancialReranker, and UnifiedLLMClient.
Provides a clean, unified API for Member 7 (Frontend) and Member 8 (Testing).
"""

import time
from typing import Any

from ..llm.client import UnifiedLLMClient
from ..llm.prompts import build_baseline_prompt, build_finrag_prompt
from ..retrieval.reranker import SimpleFinancialReranker
from ..retrieval.retriever import DualHybridRetriever


class FinRAGEngine:
    def __init__(
        self,
        retriever: DualHybridRetriever | None = None,
        reranker: SimpleFinancialReranker | None = None,
        llm_client: UnifiedLLMClient | None = None,
    ):
        self.retriever = retriever or DualHybridRetriever()
        self.reranker = reranker or SimpleFinancialReranker()
        self.llm_client = llm_client or UnifiedLLMClient(provider="auto")

    def answer_financial_question(
        self,
        question: str,
        top_k_text: int = 3,
        top_k_tables: int = 3,
        rerank_top_n: int = 4,
    ) -> dict[str, Any]:
        """
        Executes end-to-end FinRAG inference:
        1. Query analysis & Dual-retrieval (narrative + tables)
        2. Candidate aggregation & Hierarchical reranking
        3. CFA-level prompt formatting with strict grounding
        4. LLM response generation with latency tracking
        """
        start_time = time.time()

        # Step 1: Dual Retrieval
        retrieval_res = self.retriever.retrieve(
            query=question,
            top_k_text=top_k_text,
            top_k_tables=top_k_tables,
        )

        raw_candidates: list[dict[str, Any]] = (
            retrieval_res.get("text_evidence", []) +
            retrieval_res.get("table_evidence", [])
        )

        # Step 2: Reranking
        reranked_items = self.reranker.rerank(
            query=question,
            candidates=raw_candidates,
            top_n=rerank_top_n,
        )

        # Separate reranked evidence back into text and tables
        final_text = [
            item["content"] for item in reranked_items
            if item.get("metadata", {}).get("type") == "narrative_text"
        ]
        final_tables = [
            item["content"] for item in reranked_items
            if item.get("metadata", {}).get("type") in ["financial_table", "clean_financial_table"]
        ]

        # Step 3: Prompt Building
        prompt = build_finrag_prompt(
            question=question,
            text_evidence=final_text,
            table_evidence=final_tables,
        )

        # Step 4: Generation
        llm_response = self.llm_client.generate(prompt)

        latency = round(time.time() - start_time, 3)

        return {
            "question": question,
            "answer": llm_response.get("text", ""),
            "provider": llm_response.get("provider", "unknown"),
            "model": llm_response.get("model", "unknown"),
            "latency_seconds": latency,
            "retrieved_evidence": {
                "text_count": len(final_text),
                "table_count": len(final_tables),
                "text_snippets": final_text,
                "table_snippets": final_tables,
            },
        }

    def run_baseline_comparison(self, question: str) -> dict[str, Any]:
        """
        Runs text-only baseline alongside FinRAG for evaluation comparison.
        """
        retrieval_res = self.retriever.retrieve(query=question, top_k_text=3, top_k_tables=0)
        baseline_text = [t["content"] for t in retrieval_res.get("text_evidence", [])]
        baseline_prompt = build_baseline_prompt(question, baseline_text)
        baseline_out = self.llm_client.generate(baseline_prompt)

        finrag_out = self.answer_financial_question(question)

        return {
            "question": question,
            "baseline_answer": baseline_out.get("text", ""),
            "finrag_answer": finrag_out.get("answer", ""),
            "finrag_latency": finrag_out.get("latency_seconds", 0.0),
        }
