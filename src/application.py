"""Setup-stage application boundary and explicit backend assembly for the next owner.

R3/R5/R6/R12, common A-G eligibility. KR&R: a financial conclusion is licensed only when the
included, accepted evidence agrees with the *request* (issuer, exact filing, value period,
scope). Arithmetic that is correct for another issuer/period is still an invalid answer
(F27/F32). Synthetic demonstrations are a separate, never-"ok" status.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from src.config import Settings

ROOT = Path(__file__).resolve().parents[1]
FILINGS_PATH = ROOT / "data" / "application_filings.json"

# Filings the interface offers (exact accessions); issuer/period come from the filing registry.
UI_FILING_ACCESSIONS: tuple[str, ...] = (
    "0000320193-21-000105", "0000320193-22-000108", "0000320193-23-000106",
    "0001564590-21-039151", "0001564590-22-026876",
)
SUPPORTED_SCOPES = frozenset({"consolidated"})


@dataclass(frozen=True)
class FilingOption:
    label: str
    ticker: str
    issuer: str
    cik: str
    accession: str
    filing_period_end: str


def load_filing_options(path: Path | str = FILINGS_PATH) -> tuple[FilingOption, ...]:
    """Selectable filings, each bound to its exact registry tuple (never inferred from a ticker)."""
    registry = {r["accession"]: r for r in json.loads(Path(path).read_text(encoding="utf-8"))}
    options = []
    for accession in UI_FILING_ACCESSIONS:
        r = registry[accession]
        options.append(FilingOption(
            label=f"{r['issuer']} ({r['ticker']}) — {r['period_end'][:4]} {r['form']}",
            ticker=r["ticker"], issuer=r["issuer"], cik=r["cik"], accession=accession,
            filing_period_end=r["period_end"],
        ))
    return tuple(options)


@dataclass(frozen=True)
class RequestConstraints:
    """Independently validated request premises that evidence must satisfy."""
    ticker: str
    company: str
    accession: str
    filing_period_end: str
    value_period_end: str
    scope: str

    def engine_filters(self) -> dict[str, str]:
        # ticker/accession are canonical eligibility keys (retrieval/eligibility.py). The value
        # period and scope are verified on the typed evidence after retrieval.
        return {"ticker": self.ticker, "accession": self.accession}


def _comparative_gap_ok(filing_end: date, value_end: date) -> bool:
    """A 10-K carries the fiscal year and its prior comparatives (52/53-week tolerance)."""
    days = (filing_end - value_end).days
    return 0 <= days <= 10 or 355 <= days <= 375 or 720 <= days <= 745


def resolve_request(choice: str | None, value_period_end: str | None, scope: str | None,
                    options: tuple[FilingOption, ...] | None = None) -> tuple[RequestConstraints | None, str]:
    """Map a selected filing label + value period + scope to validated constraints.

    Filing identity (accession) and the comparative value period are different things: the
    2023 filing legitimately reports FY2021 values, but it must forward the 2023 accession.
    """
    options = options if options is not None else load_filing_options()
    option = next((o for o in options if o.label == choice), None)
    if option is None:
        return None, f"Unsupported filing selection: {choice!r}."
    try:
        value_end = date.fromisoformat((value_period_end or "").strip())
    except ValueError:
        return None, "Value period end must be an ISO date (YYYY-MM-DD)."
    if not _comparative_gap_ok(date.fromisoformat(option.filing_period_end), value_end):
        return None, (f"Value period {value_end} is not a reported period of the {option.accession} "
                      f"filing (fiscal year end {option.filing_period_end}).")
    scope_norm = (scope or "").strip().lower()
    if scope_norm not in SUPPORTED_SCOPES:
        return None, f"Unsupported scope {scope!r}; supported: {sorted(SUPPORTED_SCOPES)}."
    return RequestConstraints(option.ticker, option.issuer, option.accession, option.filing_period_end,
                              value_end.isoformat(), scope_norm), ""


def validate_request_binding(request: RequestConstraints, plan: dict[str, Any] | None,
                             records: list[dict[str, Any]]) -> str:
    """Return '' when plan and included records agree with the request, else the refusal reason."""
    if not records:
        return "No accepted evidence was included; refusing rather than answering from defaults."
    if plan is not None:
        if plan.get("issuer") != request.company:
            return f"Plan issuer {plan.get('issuer')!r} does not match requested company {request.company!r}."
        if str(plan.get("scope", "")).strip().lower() != request.scope:
            return f"Plan scope {plan.get('scope')!r} does not match requested scope {request.scope!r}."
        ends = [p.get("end") for p in plan.get("periods", []) if isinstance(p, dict)]
        if not ends or max(ends) != request.value_period_end:
            return f"Plan periods {ends} do not end at the requested value period {request.value_period_end}."
    for record in records:
        meta = record.get("metadata", {}) if isinstance(record, dict) else {}
        ident = record.get("evidence_id", record.get("id")) if isinstance(record, dict) else None
        if meta.get("accession") != request.accession:
            return f"Evidence {ident!r} comes from filing {meta.get('accession')!r}, not requested {request.accession!r}."
        if "company" not in meta and "ticker" not in meta:
            return f"Evidence {ident!r} lacks issuer identity."
        if meta.get("company") not in (None, request.company) or meta.get("ticker") not in (None, request.ticker):
            return f"Evidence {ident!r} is for another issuer."
        if meta.get("type") == "table_cell" and str(meta.get("scope", "")).strip().lower() != request.scope:
            return f"Evidence {ident!r} scope {meta.get('scope')!r} differs from requested scope."
    return ""


def make_demo_records() -> list[dict[str, Any]]:
    """Synthetic Apple FY2021 sales/cost cells for the explicit demo-only path (never a live answer)."""
    def make_fact(identity, value, year, metric):
        c = f"Apple Inc. | {metric} | {year} | {value} | USD millions"
        return {
            "evidence_id": identity,
            "content": c,
            "metadata": {
                "type": "table_cell", "company": "Apple Inc.", "ticker": "AAPL", "metric": metric,
                "scope": "consolidated", "table_title": "Statement of Operations",
                "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm",
                "source_locator": "Consolidated Statements of Operations",
                "accession": "0000320193-21-000105",
                "content_sha256": hashlib.sha256(c.encode()).hexdigest(),
                "period_kind": "duration", "period_start": f"{year-1}-09-27", "period_end": f"{year}-09-25",
                "normalized_unit": "USD", "unit": "USD", "currency": "USD",
                "scale": 1000000, "scale_power10": 6, "raw_value": str(value), "raw_unit": "millions",
                "normalized_value_decimal": str(value * 1000000), "normalized_value": value * 1000000,
            },
        }
    return [make_fact("sales", 365817, 2021, "Revenue"), make_fact("cost", 212981, 2021, "CostOfSales")]


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
        *,
        request: RequestConstraints | None = None,
        demo_only: bool = False,
    ) -> dict[str, Any]:
        """Answer one request, binding every result to validated request constraints.

        ``request`` carries the validated company/filing/value-period/scope (see
        :func:`resolve_request`). Without it, a request is assembled from the loose
        ``company``/``filing``/``period_end``/``scope`` arguments, and a calculation requires
        all of them. Defaults are never substituted: with no engine and no included records
        the result is a refusal, unless ``demo_only`` explicitly asks for the synthetic Apple
        FY2021 demonstration, which is reported as status ``demo_only`` and never as ``ok``.
        """
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
            "request": None,
            "evidence_origin": None,
        }

        def finish(status: str, message: str = "", answer: str = ""):
            keep_answer = status in {"ok", "demo_only"}
            result.update(
                status=status,
                message=message,
                answer=answer if keep_answer else "",
                latency_seconds=round(time.monotonic() - start, 3),
            )
            if not keep_answer:  # a refusal/error never leaves prior or partial output behind
                result["evidence"], result["calculations"] = [], []
            return result

        if not isinstance(question, str) or not question.strip():
            return finish("invalid_request", "Please enter a nonempty question.")

        if chart_asset_id:
            # Independent chart approval gate check (PRD R11, Variant G)
            return finish(
                "index_not_ready",
                f"Chart asset '{chart_asset_id}' is candidate-only. Independent chart approval (Variant G) is pending review (scheduled for Ujjwal on Nov 15).",
            )

        constraints = request
        if constraints is None and filing and company and period_end and scope:
            constraints = self._constraints_from_loose_args(company, filing, period_end, scope)
        if constraints is None and (self.engine is not None or included_records is not None
                                    or (calculation_plan is not None and not demo_only)):
            return finish(
                "invalid_request",
                "A validated request (company, exact filing, value period end and scope) is required "
                "to bind evidence and calculations; select a supported filing.",
            )
        if constraints is not None:
            result["request"] = asdict(constraints)

        if self.engine is not None:
            return self._answer_with_engine(result, finish, question, constraints, calculation_plan, start)

        # No engine: only caller-supplied included records or the explicit demo path may calculate.
        if calculation_plan is not None:
            from src.llm.typed_calculator import evaluate, render_result
            from src.pipeline.experiment_scaffold import verify_included_operands

            if included_records is not None:
                records, origin = included_records, "caller_supplied"
            elif demo_only:
                records, origin = make_demo_records(), "synthetic_demo"
                if constraints is not None:
                    # Even a demo cannot answer a different issuer/filing/period's request.
                    problem = validate_request_binding(constraints, calculation_plan, records)
                    if problem:
                        return finish("insufficient_evidence", f"Demo facts do not match the request: {problem}")
            else:
                return finish("index_not_ready",
                              "No accepted retrieved evidence is available for this request; the application "
                              "does not substitute default facts. " + "\n".join(self._setup_app.readiness()["blockers"]))
            result["evidence_origin"] = origin

            if origin == "caller_supplied":
                problem = validate_request_binding(constraints, calculation_plan, records)
                if problem:
                    return finish("insufficient_evidence", problem)

            included_ids = [r.get("evidence_id", r.get("id")) for r in records]
            valid_operands, err_msg = verify_included_operands(calculation_plan, included_ids)
            if not valid_operands:
                return finish("insufficient_evidence", err_msg)

            calc_result = evaluate(calculation_plan, records)
            if calc_result["status"] != "ok":
                return finish("insufficient_evidence", calc_result["message"])
            result["calculations"] = [calc_result]
            result["evidence"] = records

            rendered = render_result(calc_result)
            if origin == "synthetic_demo":
                return finish(
                    "demo_only",
                    "DEMO ONLY: synthetic Apple FY2021 facts; this is not a source-grounded financial answer.",
                    answer="[DEMO ONLY - not a verified live answer] " + rendered,
                )
            return finish("ok", "Calculated using verified restricted Decimal operations over caller-supplied included records.",
                          answer=rendered)

        # Standard unindexed narrative question without engine
        blockers = self._setup_app.readiness()["blockers"]
        return finish("index_not_ready", "\n".join(blockers))

    @staticmethod
    def _constraints_from_loose_args(company, filing, period_end, scope) -> RequestConstraints | None:
        """Build constraints only when company/filing agree with the filing registry tuple."""
        for option in load_filing_options():
            if option.accession == filing and option.issuer == company:
                resolved, _ = resolve_request(option.label, period_end, scope)
                return resolved
        return None

    def _answer_with_engine(self, result, finish, question, constraints, calculation_plan, start):
        import time

        try:
            engine_res = self.engine.answer_financial_question(
                question=question,
                calculation_plan=calculation_plan,
                filters=constraints.engine_filters(),
            )
        except Exception as exc:  # provider/index failure must not leave a stale or partial answer
            return finish("service_error", f"Answer engine failed: {type(exc).__name__}.")
        status = engine_res.get("status", "service_error")
        evidence = engine_res.get("evidence", [])
        result.update(
            route=engine_res.get("retrieval_trace", {}).get("routing", "exact_engine"),
            provider=engine_res.get("provider", self.settings.provider),
            model=engine_res.get("model", self.settings.model),
            evidence_origin="engine_retrieved",
        )
        if status != "ok":
            return finish(status, engine_res.get("message", ""))
        problem = validate_request_binding(constraints, calculation_plan, evidence)
        if problem:
            return finish("insufficient_evidence", f"Engine evidence does not satisfy the request: {problem}")
        result.update(evidence=evidence, calculations=engine_res.get("calculations", []))
        finish("ok", engine_res.get("message", ""), answer=engine_res.get("answer", ""))
        result["latency_seconds"] = engine_res.get("latency_seconds", round(time.monotonic() - start, 3))
        return result


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
