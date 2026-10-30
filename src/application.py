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
        if not (settings.index_dir / "chroma.sqlite3").is_file():
            blockers.append("No persistent Chroma index found. Build and validate it during the indexing task.")
        else:
            blockers.append("An index file exists, but its collection, records and source identity are not validated.")
        if settings.provider == "unconfigured" or not settings.model:
            blockers.append("No verified model configured. The provider connection is the next implementation task.")
        if settings.provider == "gemini" and not settings.gemini_api_key:
            blockers.append("Gemini credentials are missing. Set GEMINI_API_KEY privately when testing the provider.")
        # A folder/key alone must never enable the prototype's hidden mock fallback.
        blockers.append("Answering is disabled in this setup build until real-provider and evidence checks are connected.")
        return {"status": "not_ready", "blockers": blockers}

    def answer(self, question: str) -> dict[str, Any]:
        if not question.strip():
            return asdict(AnswerResult(status="invalid_input", question=question,
                                       message="Please enter a question."))
        return asdict(AnswerResult(status="not_ready", question=question,
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
    """One adapter for retrieval settings; the legacy return contract still needs repair."""
    return engine.answer_financial_question(
        question, top_k_text=settings.top_k_text,
        top_k_tables=settings.top_k_tables, rerank_top_n=settings.rerank_top_n,
    )
