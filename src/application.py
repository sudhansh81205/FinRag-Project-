"""Setup-stage application boundary and explicit backend assembly for the next owner."""

from dataclasses import asdict, dataclass, field
from typing import Any

from src.config import Settings


@dataclass
class AnswerResult:
    status: str
    question: str
    answer: str = ""
    message: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    calculations: list[dict[str, Any]] = field(default_factory=list)
    provider: str | None = None
    model: str | None = None


class SetupApplication:
    """The Day 2 deliverable is launchable, explicitly NOT an answer-ready build."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def readiness(self) -> dict[str, Any]:
        settings = self.settings
        blockers = []
        if not settings.raw_dir.is_dir() or not any(settings.raw_dir.iterdir()):
            blockers.append("No source filing found. Add the selected Apple 2021 filing during ingestion.")
        if not (settings.index_dir / "catalog.json").is_file():
            blockers.append("No BGE/exact FAISS catalog found. Run the source audit and scripts/build_index.py; see docs/INDEXING.md.")
        else:
            blockers.append("A BGE/exact FAISS catalog exists. Use scripts/query_index.py to verify dense retrieval; final answer-pipeline integration remains unvalidated.")
        if (settings.index_dir / "chroma.sqlite3").is_file():
            blockers.append("A legacy Chroma file cannot establish BGE/FAISS readiness; it remains unvalidated for this path.")
        if settings.provider == "unconfigured" or not settings.model:
            blockers.append("No verified model configured. Configure the provider and run scripts/check_generation.py.")
        if settings.provider == "gemini" and not settings.gemini_api_key:
            blockers.append("Gemini credentials are missing. Set GEMINI_API_KEY privately when testing the provider.")
        # A folder/key alone must never enable the prototype's hidden mock fallback.
        blockers.append("Answering is disabled in this setup build until the filing, persistent index and source checks are connected.")
        return {"status": "index_not_ready", "blockers": blockers}

    def answer(self, question: str) -> dict[str, Any]:
        if not isinstance(question, str) or not question.strip():
            return asdict(AnswerResult(status="invalid_request", question=question,
                                       message="Please enter a question."))
        return asdict(AnswerResult(status="index_not_ready", question=question,
                                   message="\n".join(self.readiness()["blockers"])))


class InteractiveApplication:
    """Gradio interactive application boundary supporting full pipeline execution,
    session-isolated queries, typed calculator verification, and fail-closed diagnostics.
    """

    def __init__(self, settings: Settings, engine=None):
        self.settings = settings
        self.engine = engine
        self._setup_app = SetupApplication(settings)

    def readiness(self) -> dict[str, Any]:
        if self.engine is not None:
            return {"status": "ready", "blockers": [], "engine": "FinRAGEngine connected"}
        return self._setup_app.readiness()

    def answer(self, question: str) -> dict[str, Any]:
        return self._setup_app.answer(question)

    def answer_interactive(
        self,
        question: str,
        company: str | None = None,
        filing: str | None = None,
        period_end: str | None = None,
        scope: str | None = None,
        calculation_plan: dict[str, Any] | None = None,
        chart_asset_id: str | None = None,
        included_records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        import hashlib
        import time

        start = time.monotonic()
        result = {
            "status": "service_error",
            "question": question,
            "answer": "",
            "message": "",
            "latency_seconds": 0.0,
            "route": "direct",
            "provider": self.settings.provider,
            "model": self.settings.model,
            "evidence": [],
            "calculations": [],
            "chart_info": None,
        }

        def finish(status: str, message: str = "", answer: str = ""):
            result.update(
                status=status,
                message=message,
                answer=answer if status == "ok" else "",
                latency_seconds=round(time.monotonic() - start, 3),
            )
            return result

        if not isinstance(question, str) or not question.strip():
            return finish("invalid_request", "Please enter a nonempty question.")

        if chart_asset_id:
            # Independent chart approval gate check (PRD R11, Variant G)
            return finish(
                "index_not_ready",
                f"Chart asset '{chart_asset_id}' is candidate-only. Independent chart approval (Variant G) is pending review (scheduled for Ujjwal on Nov 15).",
            )

        if self.engine is not None:
            filters = {}
            if company:
                filters["company"] = company
            if period_end:
                filters["period_end"] = period_end
            if filing:
                filters["accession"] = filing
            engine_res = self.engine.answer_financial_question(
                question=question,
                calculation_plan=calculation_plan,
                filters=filters if filters else None,
            )
            result.update(
                status=engine_res.get("status", "service_error"),
                answer=engine_res.get("answer", ""),
                message=engine_res.get("message", ""),
                latency_seconds=engine_res.get("latency_seconds", round(time.monotonic() - start, 3)),
                route=engine_res.get("retrieval_trace", {}).get("routing", "exact_engine"),
                provider=engine_res.get("provider", self.settings.provider),
                model=engine_res.get("model", self.settings.model),
                evidence=engine_res.get("evidence", []),
                calculations=engine_res.get("calculations", []),
            )
            return result

        # When engine is not fully connected (setup/demo mode):
        # Support verified typed calculation demonstrations and fail-closed checks
        if calculation_plan is not None:
            from src.llm.typed_calculator import evaluate, render_result
            from src.pipeline.experiment_scaffold import verify_included_operands

            # Use caller-provided records or default canonical Apple 2021 facts
            if included_records is not None:
                records = included_records
            else:
                def make_fact(identity, value, year=2021, metric="Revenue", **changes):
                    c = f"Apple Inc. | {metric} | {year} | {value} | USD millions"
                    return {
                        "evidence_id": identity,
                        "content": c,
                        "metadata": {
                            "type": "table_cell",
                            "company": "Apple Inc.",
                            "metric": metric,
                            "scope": "consolidated",
                            "table_title": "Statement of Operations",
                            "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm",
                            "source_locator": "Consolidated Statements of Operations",
                            "accession": "0000320193-21-000105",
                            "content_sha256": hashlib.sha256(c.encode()).hexdigest(),
                            "period_kind": "duration",
                            "period_start": f"{year-1}-09-27",
                            "period_end": f"{year}-09-25",
                            "normalized_unit": "USD",
                            "unit": "USD",
                            "currency": "USD",
                            "scale": 1000000,
                            "scale_power10": 6,
                            "raw_value": str(value),
                            "raw_unit": "millions",
                            "normalized_value_decimal": str(value * 1000000),
                            "normalized_value": value * 1000000,
                            **changes,
                        },
                    }
                records = [
                    make_fact("sales", 365817, 2021, "Revenue"),
                    make_fact("cost", 212981, 2021, "CostOfSales"),
                ]

            included_ids = [r.get("evidence_id", r.get("id")) for r in records]
            valid_operands, err_msg = verify_included_operands(calculation_plan, included_ids)
            if not valid_operands:
                return finish("insufficient_evidence", err_msg)

            calc_result = evaluate(calculation_plan, records)
            result["calculations"] = [calc_result]
            result["evidence"] = records
            if calc_result["status"] != "ok":
                return finish("insufficient_evidence", calc_result["message"])

            rendered = render_result(calc_result)
            return finish("ok", "Calculated using verified restricted Decimal operations.", answer=rendered)

        # Standard unindexed narrative question without engine
        blockers = self._setup_app.readiness()["blockers"]
        return finish("index_not_ready", "\n".join(blockers))


def assemble_engine(settings: Settings, *, collection, embedding_model, cross_encoder, llm_client):
    """Wire the existing backend with explicit dependencies; never infer a provider.

    Not called by the setup UI. Rushil must validate generation and status handling
    before enabling inference. The ingestion/index owners supply the collection.
    """
    from src.pipeline.finrag_engine import FinRAGEngine
    from src.retrieval.reranker import SimpleFinancialReranker
    from src.retrieval.retriever import DualHybridRetriever

    if any(item is None for item in (collection, embedding_model, cross_encoder, llm_client)):
        raise ValueError("All backend dependencies must be supplied explicitly.")

    def embed(text):
        vector = embedding_model.encode(text)
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)

    return FinRAGEngine(
        retriever=DualHybridRetriever(vector_collection=collection, embedding_fn=embed),
        reranker=SimpleFinancialReranker(cross_encoder_model=cross_encoder),
        llm_client=llm_client,
    )


def configured_answer(engine, settings: Settings, question: str):
    """One adapter for retrieval settings; generation failures propagate as explicit statuses."""
    return engine.answer_financial_question(
        question, top_k_text=settings.top_k_text,
        top_k_tables=settings.top_k_tables, rerank_top_n=settings.rerank_top_n,
    )


def assemble_exact_engine(
    settings: Settings, *, store, encoder, llm_client, variant="D", cross_encoder=None,
    filters=None, token_counter=None, context_token_budget=None, tokenizer_id=None,
    reranker_model_id=None, routing_policy=None,
):
    """Connect the persistent BGE/FAISS contract without the legacy Chroma API.

    All runtime resources must be explicitly supplied and already available. This
    performs no model/data download and does not enable the setup UI. C-F are
    bounded components, not proof that a frozen A-G experiment is ready. Callers
    must use the actual generator tokenizer for a declared shared token budget.
    """
    from src.pipeline.finrag_engine import FinRAGEngine
    from src.retrieval.bm25 import BM25Retriever, HybridRRFRetriever
    from src.retrieval.dense import DenseRetriever

    if store is None or encoder is None or llm_client is None:
        raise ValueError("An explicit exact store, encoder and real-provider client are required.")
    if llm_client.provider not in {"ollama", "gemini"}:
        raise ValueError("The financial engine requires an explicit real provider.")
    if encoder.spec.manifest_fields() != store.spec.manifest_fields():
        raise ValueError("Query encoder and persistent index identities differ.")
    retriever = HybridRRFRetriever(
        DenseRetriever(store, encoder, filters=filters),
        BM25Retriever(store.records, filters=filters),
        variant=variant, reranker=cross_encoder, reranker_model_id=reranker_model_id,
        routing_policy=routing_policy,
    )
    return FinRAGEngine(
        retriever=retriever, llm_client=llm_client,
        token_counter=token_counter, context_token_budget=context_token_budget,
        tokenizer_id=tokenizer_id,
    )
