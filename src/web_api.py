"""R6/R13 HTTP boundary for the existing real engine; no synthetic/default financial answers.

Serving is opt-in and authenticated. Browser hosting is separate from the prepared BGE/FAISS/
Gemma machine. Common A-G source identity and KR typed request/period rules remain enforced.
"""
import json
import re
import threading
from pathlib import Path

from src.application import FilingOption, InteractiveApplication, resolve_request


class WebApplication:
    def __init__(self, settings, engine=None):
        self._answer_lock = threading.Lock()
        self.app = InteractiveApplication(settings, engine)
        self.settings = settings
        registry = json.loads((settings.root / "data/application_filings.json").read_text(encoding="utf-8"))
        self.options = tuple(FilingOption(f["accession"], f["ticker"], f["issuer"], f["cik"],
                                         f["accession"], f["period_end"]) for f in registry)

    def health(self):
        ready = self.app.engine is not None
        return {"status": "ready" if ready else "index_not_ready",
                "message": ("Accepted engine resources connected; answers still require matching evidence."
                            if ready else "No prepared BGE/FAISS/model engine is connected."),
                "final_experiment_ready": False}

    def answer(self, payload):
        if not self._answer_lock.acquire(blocking=False):
            return {"status": "service_error", "message": "The model is busy. Try again shortly.",
                    "answer": "", "evidence": [], "calculations": [], "included_evidence_ids": []}
        try:
            return self._answer(payload)
        finally:
            self._answer_lock.release()

    def _answer(self, payload):
        def failure(status, message):
            return {"status": status, "message": message, "answer": "", "evidence": [],
                    "calculations": [], "included_evidence_ids": []}

        if not isinstance(payload, dict) or not isinstance(payload.get("question"), str):
            return failure("invalid_request", "A question and filing are required.")
        if not 3 <= len(payload["question"].strip()) <= 2000:
            return failure("invalid_request", "Question must contain 3 to 2,000 characters.")
        request, problem = resolve_request(payload.get("accession"), payload.get("value_period_end"),
                                           payload.get("scope"), options=self.options)
        if problem or request.ticker != payload.get("ticker"):
            return failure("invalid_request", problem or "Company and filing disagree.")
        mode = payload.get("mode", "auto")
        if mode not in {"auto", "narrative", "numerical", "chart"}:
            return failure("invalid_request", "Unsupported question type.")
        if mode == "chart":
            return failure("index_not_ready", "Independent chart/caption acceptance and G execution are not ready.")
        period_kind = payload.get("period_kind")
        if period_kind is not None and period_kind not in {"instant", "duration"}:
            return failure("invalid_request", "Choose a fiscal-year total or year-end balance.")
        numerical = mode == "numerical" or mode == "auto" and re.search(
            r"\b(margin|growth|percent|ratio|how much|how many|revenue|cost|earnings|income|cash flow)\b",
            payload["question"], re.I)
        planning_request = None
        if numerical and self.app.engine is not None:
            # Only source-derived period boundaries can enter the planner's premises.
            periods = set()
            for record in getattr(self.app.engine, "web_source_records", []):
                m = record.get("metadata", {})
                if (m.get("accession") == request.accession and m.get("type") == "table_cell"
                        and m.get("scope") == request.scope and m.get("period_end") == request.value_period_end
                        and (period_kind is None or m.get("period_kind") == period_kind)):
                    periods.add((m.get("period_kind"), m.get("period_start"), m.get("period_end")))
            if len(periods) != 1:
                return failure("insufficient_evidence", "The selected value period has missing or ambiguous typed source boundaries.")
            kind, start, end = periods.pop()
            planning_request = {"issuer": request.company, "scope": request.scope,
                                "periods": [{"kind": kind, "start": start, "end": end}]}
        options = {"top_k_text": 5, "top_k_tables": 0} if mode == "narrative" else None
        result = self.app.answer_interactive(payload["question"], request=request,
                                             calculation_request=planning_request, retrieval_options=options)
        if numerical and result.get("status") == "ok":
            calculations = result.get("calculations", [])
            if not calculations:
                return failure("insufficient_evidence", "A numerical answer requires a checked source-bound calculation.")
            if period_kind is not None and any(
                p.get("kind") != period_kind for calc in calculations
                for p in calc.get("program", {}).get("periods", [])
            ):
                return failure("insufficient_evidence", "The calculation period type differs from the requested value type.")
        if isinstance(result.get("request"), dict) and period_kind is not None:
            result["request"]["period_kind"] = period_kind
        result["included_evidence_ids"] = [r.get("evidence_id", r.get("id")) for r in result.get("evidence", [])]
        return result


def build_prepared_engine(settings, *, variant="D", tokenizer_dir=None, context_tokens=3000,
                          token_counter=None, tokenizer_id=None, model_cache=None):
    """Reopen existing local assets only, without installing or downloading any model."""
    from src.application import assemble_exact_engine
    from src.benchmark.gates import detect_available_gates
    from src.indexing.bge import BGEEncoder
    from src.indexing.store import ExactStore
    from src.llm.client import UnifiedLLMClient
    from src.pipeline.experiment_scaffold import get_variant_spec, validate_experiment_manifest

    gate = validate_experiment_manifest(get_variant_spec(variant), detect_available_gates())
    if not gate["is_ready"]:
        raise ValueError("Independent artifact acceptance gates are closed.")
    if variant not in {"C", "D"}:
        raise ValueError("This web adapter supports prepared C/D; E-G need real identified stage adapters.")
    if token_counter is None:
        if not tokenizer_dir or not Path(tokenizer_dir).is_dir():
            raise ValueError("An existing local generator tokenizer is required.")
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir, local_files_only=True, trust_remote_code=False)
        def token_counter(text):
            return len(tokenizer.encode(text, add_special_tokens=True))
        tokenizer_id = str(Path(tokenizer_dir).resolve())
    from src.llm.token_budget import BudgetedClient
    encoder = BGEEncoder(local_files_only=True, cache_folder=str(model_cache or settings.root / "output/models"))
    store = ExactStore(settings.index_dir)
    client = BudgetedClient(UnifiedLLMClient.from_settings(settings), token_counter,
                            input_tokens=context_tokens, context_tokens=settings.ollama_num_ctx,
                            output_tokens=settings.ollama_num_predict)
    engine = assemble_exact_engine(
        settings, store=store, encoder=encoder, llm_client=client,
        variant=variant, token_counter=token_counter,
        context_token_budget=context_tokens, tokenizer_id=tokenizer_id)
    engine.web_source_records = store.records
    return engine


def build_source_checked_engine(settings, audit_path, *, token_counter, tokenizer_id, model_cache=None):
    """Bounded Apple C/D development runtime; does not open final/human review gates.

    Reproduce the previously accepted package predicates and require the exact
    immutable indexed records/parents. This cannot license the wider corpus,
    unaccepted charts or a final A-G benchmark run.
    """
    from scripts.build_index import accepted_input
    from src.application import assemble_exact_engine
    from src.indexing.bge import BGEEncoder
    from src.indexing.store import ExactStore
    from src.llm.client import UnifiedLLMClient
    from src.llm.token_budget import BudgetedClient

    records, parents, _ = accepted_input(settings.root / "data/processed/nov04", Path(audit_path))
    store = ExactStore(settings.index_dir)
    if store.records != records or store.parents != {p["evidence_id"]: p for p in parents}:
        raise ValueError("Bounded source runtime requires exactly the checked Apple records/parents")
    encoder = BGEEncoder(local_files_only=True, cache_folder=str(model_cache or settings.root / "output/models"))
    client = BudgetedClient(UnifiedLLMClient.from_settings(settings), token_counter,
                            context_tokens=settings.ollama_num_ctx, output_tokens=settings.ollama_num_predict)
    engine = assemble_exact_engine(settings, store=store, encoder=encoder, llm_client=client,
                                   variant="D", token_counter=token_counter, context_token_budget=3000,
                                   tokenizer_id=tokenizer_id)
    engine.web_source_records = store.records
    engine.acceptance_scope = "bounded Apple source-predicate development runtime; final A-G acceptance pending"
    return engine
