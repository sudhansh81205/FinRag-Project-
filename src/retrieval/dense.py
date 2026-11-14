"""Dense-only adapter for the existing engine; BM25/RRF remains a separate stage."""

from .eligibility import empty_scope, intersect_filters, validated_filters


class DenseRetriever:
    def __init__(self, store, encoder, *, filters=None, table_kind="table_cell"):
        if table_kind not in {"table_cell", "financial_table"}:
            raise ValueError("Unsupported dense table representation")
        self.store, self.encoder = store, encoder
        self.filters = validated_filters(filters)
        self.table_kind = table_kind

    def retrieve(self, query, top_k_text=3, top_k_tables=3, *, filters=None):
        if any(type(k) is not int or k < 0 for k in (top_k_text, top_k_tables)):
            raise ValueError("Retrieval budgets must be nonnegative integers")
        scope = intersect_filters(self.filters, filters)
        result = {
            "query": query,
            "text_evidence": [],
            "table_evidence": [],
            "retrieval_mode": "dense_only",
            "eligibility_filters": scope,
        }
        if not (top_k_text or top_k_tables) or empty_scope(scope):
            return result
        if self.encoder.spec.manifest_fields() != self.store.spec.manifest_fields():
            raise ValueError("Dense query encoder does not match the index")
        vector = self.encoder.encode([query], query=True)[0]
        for stream, kind, limit in (
            ("text_evidence", "narrative_text", top_k_text),
            ("table_evidence", self.table_kind, top_k_tables),
        ):
            if limit:
                result[stream] = self.store.search(
                    vector, k=limit, filters={**scope, "type": kind}
                )
        if self.table_kind == "financial_table":
            ranked = sorted(
                result["text_evidence"] + result["table_evidence"],
                key=lambda record: (-record["score"], record["evidence_id"]),
            )
            result.update(
                all_evidence=ranked,
                ranked_evidence_ids=[record["evidence_id"] for record in ranked],
                ranking_applied=True,
            )
        return result
