"""Dense-only adapter for the existing engine; BM25/RRF remains a separate stage."""


class DenseRetriever:
    def __init__(self, store, encoder, *, filters=None):
        self.store, self.encoder = store, encoder
        self.filters = dict(filters or {})
        if "type" in self.filters:
            raise ValueError("Use stream limits for the record type filter")

    def retrieve(self, query, top_k_text=3, top_k_tables=3):
        if any(type(k) is not int or k < 0 for k in (top_k_text, top_k_tables)):
            raise ValueError("Retrieval budgets must be nonnegative integers")
        result = {
            "query": query,
            "text_evidence": [],
            "table_evidence": [],
            "retrieval_mode": "dense_only",
        }
        if not (top_k_text or top_k_tables):
            return result
        if self.encoder.spec.manifest_fields() != self.store.spec.manifest_fields():
            raise ValueError("Dense query encoder does not match the index")
        vector = self.encoder.encode([query], query=True)[0]
        for stream, kind, limit in (
            ("text_evidence", "narrative_text", top_k_text),
            ("table_evidence", "table_cell", top_k_tables),
        ):
            if limit:
                result[stream] = self.store.search(
                    vector, k=limit, filters={**self.filters, "type": kind}
                )
        return result
