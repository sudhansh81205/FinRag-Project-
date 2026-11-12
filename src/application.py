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
