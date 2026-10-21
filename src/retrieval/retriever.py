"""
Hybrid and Tiered Retrieval Pipeline (Member 2: RAG Architecture Lead)
Handles dual-retrieval routing across narrative text chunks and financial tables.
"""

from typing import Any


class DualHybridRetriever:
    """
    Manages dual-stream retrieval:
    1. Narrative text chunks for qualitative queries (risk factors, strategies).
    2. Structured financial tables for quantitative queries (revenue, balance sheets).
    Automatically routes or escalates when numerical triggers are detected.
    """

    NUMERICAL_TRIGGERS = [
        "revenue", "sales", "net income", "loss", "ebit", "ebitda", "margin",
        "diluted", "eps", "shares", "dividend", "cash flow", "assets", "liabilities",
        "debt", "growth", "percentage", "%", "$", "balance sheet", "quarter", "fiscal",
        "2021", "2022", "2023", "2024", "2025", "2026", "products", "services"
    ]

    def __init__(self, vector_collection=None, embedding_fn=None):
        """
        vector_collection: Stored ChromaDB collection or FAISS index wrapper.
        embedding_fn: Callable taking text -> vector list.
        """
        self.vector_collection = vector_collection
        self.embedding_fn = embedding_fn

    def is_numerical_query(self, query: str) -> bool:
        """Determines if query targets quantitative/financial statement metrics."""
        query_lower = query.lower()
        return any(trigger in query_lower for trigger in self.NUMERICAL_TRIGGERS)

    def retrieve(
        self,
        query: str,
        top_k_text: int = 3,
        top_k_tables: int = 3,
        force_multimodal: bool = True,
    ) -> dict[str, Any]:
        """
        Executes tiered retrieval.
        If numerical query is detected, table search is prioritized and escalated.
        """
        is_num = self.is_numerical_query(query)

        text_limit = 2 if is_num else top_k_text
        table_limit = top_k_tables if (is_num or force_multimodal) else 1

        results = {
            "query": query,
            "is_numerical_intent": is_num,
            "text_evidence": [],
            "table_evidence": [],
        }

        if self.vector_collection is None:
            return results

        query_vector = self.embedding_fn(query) if self.embedding_fn else None

        # 1. Retrieve narrative text
        try:
            text_query_kwargs = {
                "n_results": text_limit,
                "where": {"type": "narrative_text"},
            }
            if query_vector is not None:
                text_query_kwargs["query_embeddings"] = [query_vector]
            else:
                text_query_kwargs["query_texts"] = [query]

            text_res = self.vector_collection.query(**text_query_kwargs)
            if text_res and "documents" in text_res and text_res["documents"]:
                for i, doc in enumerate(text_res["documents"][0]):
                    meta = text_res["metadatas"][0][i] if "metadatas" in text_res else {}
                    results["text_evidence"].append({"content": doc, "metadata": meta})
        except Exception as e:
            results["text_error"] = str(e)

        # 2. Retrieve financial tables
        try:
            table_query_kwargs = {
                "n_results": table_limit,
                "where": {"type": {"$in": ["financial_table", "clean_financial_table"]}},
            }
            if query_vector is not None:
                table_query_kwargs["query_embeddings"] = [query_vector]
            else:
                table_query_kwargs["query_texts"] = [query]

            table_res = self.vector_collection.query(**table_query_kwargs)
            if table_res and "documents" in table_res and table_res["documents"]:
                for i, doc in enumerate(table_res["documents"][0]):
                    meta = table_res["metadatas"][0][i] if "metadatas" in table_res else {}
                    results["table_evidence"].append({"content": doc, "metadata": meta})
        except Exception as e:
            results["table_error"] = str(e)

        return results
