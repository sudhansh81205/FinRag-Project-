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

        if any(type(limit) is not int or limit < 0 for limit in (top_k_text, top_k_tables)):
            raise ValueError("Retrieval limits must be nonnegative integers.")
        text_limit = min(2, top_k_text) if is_num else top_k_text
        table_limit = top_k_tables if (is_num or force_multimodal) else min(1, top_k_tables)

        results = {
            "query": query,
            "is_numerical_intent": is_num,
            "text_evidence": [],
            "table_evidence": [],
        }

        if self.vector_collection is None or not (text_limit or table_limit):
            return results

        query_vector = self.embedding_fn(query) if self.embedding_fn else None

        # A disabled stream must not call the backend, even for numerical intent.
        for stream, limit, where in (
            ("text", text_limit, {"type": "narrative_text"}),
            ("table", table_limit, {"type": {"$in": ["financial_table", "clean_financial_table"]}}),
        ):
            if limit == 0:
                continue
            try:
                kwargs = {"n_results": limit, "where": where}
                kwargs.update({"query_embeddings": [query_vector]} if query_vector is not None
                              else {"query_texts": [query]})
                response = self.vector_collection.query(**kwargs)
                documents = response["documents"][0]
                identities = response["ids"][0]
                metadata = response["metadatas"][0]
                if not len(documents) == len(identities) == len(metadata):
                    raise ValueError("Inconsistent index rows.")
                records = []
                for identity, document, meta in zip(identities, documents, metadata):
                    if not isinstance(identity, str) or not identity.strip() or not isinstance(meta, dict):
                        raise ValueError("Missing evidence identity or metadata.")
                    records.append({"id": identity, "content": document, "metadata": meta})
                results[f"{stream}_evidence"] = records
            except Exception:
                results[f"{stream}_error"] = "Index query or evidence mapping failed."

        return results
