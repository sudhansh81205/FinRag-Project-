"""Existing retrieval/reranking pipeline with explicit generation failure states."""

import time
from typing import Any

from ..llm.client import UnifiedLLMClient
from ..llm.prompts import build_baseline_prompt, build_finrag_prompt
from ..retrieval.reranker import SimpleFinancialReranker
from ..retrieval.retriever import DualHybridRetriever


class FinRAGEngine:
    def __init__(self, retriever=None, reranker=None, llm_client=None, *, context_char_budget=8000):
        self.retriever = retriever if retriever is not None else DualHybridRetriever()
        self.reranker = reranker if reranker is not None else SimpleFinancialReranker()
        self.llm_client = llm_client if llm_client is not None else UnifiedLLMClient()
        if type(context_char_budget) is not int or context_char_budget < 1:
            raise ValueError("Context character budget must be a positive integer.")
        # Intermediate safety budget; final matched A-G tokenizer budget remains future work.
        self.context_char_budget = context_char_budget

    def answer_financial_question(
        self, question: str, top_k_text: int = 3, top_k_tables: int = 3,
        rerank_top_n: int = 4, *, _baseline: bool = False,
    ) -> dict[str, Any]:
        start = time.monotonic()
        result = {
            "status": "service_error", "question": question, "answer": "", "message": "",
            "evidence": [], "calculations": [], "provider": self.llm_client.provider,
            "model": self.llm_client.model, "included_evidence_ids": [], "warnings": [],
            "excluded_evidence": [],
            "retrieved_evidence": {"text_count": 0, "table_count": 0,
                                   "text_snippets": [], "table_snippets": []},
        }

        def finish(status, message=""):
            result.update(status=status, message=message,
                          latency_seconds=round(time.monotonic() - start, 3))
            if status != "ok":
                result["answer"] = ""
            return result

        if not isinstance(question, str) or not question.strip():
            return finish("invalid_request", "Please enter a nonempty question.")
        if (not isinstance(top_k_text, int) or not isinstance(top_k_tables, int)
                or not isinstance(rerank_top_n, int) or min(top_k_text, top_k_tables) < 0
                or top_k_text + top_k_tables == 0 or rerank_top_n < 1):
            return finish("invalid_request", "Select positive retrieval and reranking limits.")
        if isinstance(self.retriever, DualHybridRetriever) and self.retriever.vector_collection is None:
            return finish("index_not_ready", "No validated search index is connected.")
        try:
            retrieval = self.retriever.retrieve(
                query=question, top_k_text=top_k_text, top_k_tables=top_k_tables,
            )
            if retrieval.get("text_error") or retrieval.get("table_error"):
                return finish("service_error", "Source retrieval failed; no answer was generated.")
            candidates = retrieval.get("text_evidence", []) + retrieval.get("table_evidence", [])
            if not candidates:
                return finish("insufficient_evidence", "No source evidence was retrieved; no model call was made.")
            ranked = self.reranker.rerank(query=question, candidates=candidates, top_n=rerank_top_n)
            # Only content actually passed into the existing prompt counts as evidence.
            allowed = {"narrative_text"} if _baseline else {
                "narrative_text", "financial_table", "clean_financial_table",
            }
            included, seen, used_chars = [], set(), 0
            rendered = {"narrative_text": [], "table": []}
            for item in ranked:
                identity = item.get("evidence_id", item.get("id"))
                kind = item.get("metadata", {}).get("type")
                content = item.get("content")
                reason = None
                if not isinstance(identity, str) or not identity.strip():
                    reason = "missing_identity"
                elif item.get("id", identity) != identity:
                    reason = "conflicting_identity"
                elif identity in seen:
                    reason = "duplicate_identity"
                elif not isinstance(content, str) or not content.strip() or kind not in allowed:
                    reason = "unusable_content_or_type"
                block = f"[Evidence ID: {identity}]\n{content}"
                stream = "narrative_text" if kind == "narrative_text" else "table"
                cost = len(block) + (2 if rendered[stream] else 0)
                if reason is None and used_chars + cost > self.context_char_budget:
                    reason = "context_budget"
                if reason:
                    result["excluded_evidence"].append({"id": identity, "reason": reason})
                    continue
                included.append(item)
                seen.add(identity)
                used_chars += cost
                rendered[stream].append(block)
            if not included:
                return finish("insufficient_evidence", "No usable source evidence remained after ranking.")
            text, tables = rendered["narrative_text"], rendered["table"]
            result["evidence"] = included
            result["included_evidence_ids"] = [item.get("evidence_id", item.get("id")) for item in included]
            result["context_budget"] = {"unit": "characters", "limit": self.context_char_budget,
                                        "used": used_chars, "scope": "rendered evidence blocks"}
            result["retrieved_evidence"] = {"text_count": len(text), "table_count": len(tables),
                                             "text_snippets": text, "table_snippets": tables}
            prompt = (build_baseline_prompt(question, text) if _baseline
                      else build_finrag_prompt(question, text, tables))
            response = self.llm_client.generate(prompt)
        except Exception:
            return finish("service_error", "Retrieval, ranking or generation failed; no fallback answer was used.")
        if not isinstance(response, dict):
            return finish("service_error", "The configured provider returned an invalid response.")
        if response.get("provider") == "mock" or response.get("status") == "test_only":
            return finish("service_error", "Test-only mock output is rejected by the financial answer path.")
        if (self.llm_client.provider not in {"gemini", "ollama"}
                or response.get("provider") != self.llm_client.provider
                or response.get("model") != self.llm_client.model):
            return finish("service_error", "The response did not match the configured real provider and model.")
        if (not response.get("success") or response.get("status") != "ok"
                or not isinstance(response.get("text"), str) or not response["text"].strip()):
            # Provider is responsible for sanitizing its own diagnostics. Keep this boundary safe too.
            result["error_code"] = "generation_failed"
            return finish("service_error", "The configured real provider failed or returned no answer.")
        result["answer"] = response["text"].strip()
        return finish("ok")

    def run_baseline_comparison(self, question: str) -> dict[str, Any]:
        """Legacy development comparison, not the final matched evaluation design."""
        if self.llm_client.provider not in {"gemini", "ollama"}:
            raise ValueError("Comparison requires one explicitly configured real provider; mock is forbidden.")
        baseline = self.answer_financial_question(question, top_k_tables=0, _baseline=True)
        finrag = self.answer_financial_question(question)
        return {"question": question, "baseline_answer": baseline["answer"],
                "baseline_status": baseline["status"], "finrag_answer": finrag["answer"],
                "finrag_status": finrag["status"], "finrag_latency": finrag["latency_seconds"]}
