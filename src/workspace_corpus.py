"""Small source-checked demonstration corpus; never final experiment acceptance."""
import gzip
import hashlib
import json
from pathlib import Path

ACCESSIONS = ("0000320193-21-000105", "0001564590-21-039151")


def checked_workspace_records(root, corpus, store):
    """Bind the two selected native-index generations to pinned source/package bytes."""
    from src.indexing.store import validate_records

    root, corpus = Path(root), Path(corpus)
    profiles = json.loads((root / "data/corpus_html_profiles.json").read_bytes())
    coverage = {f["accession"]: f for f in json.loads((corpus / "coverage.json").read_bytes())["filings"]}
    selected = []
    for accession in ACCESSIONS:
        row, profile = coverage[accession], profiles[accession]
        raw = gzip.decompress((root / "data/source/corpus" / f"{accession}.html.gz").read_bytes())
        if hashlib.sha256(raw).hexdigest() != profile["sha256"]:
            raise ValueError("Workspace source bytes changed")
        payload = (corpus / "records" / f"{accession}.json").read_bytes()
        package = json.loads(payload)
        if (hashlib.sha256(payload).hexdigest() != row["package_sha256"]
                or package["source_sha256"]["html"] != profile["sha256"]):
            raise ValueError("Workspace package/source identity changed")
        if exhibit := profile.get("exhibit"):
            raw = gzip.decompress((root / "data/source/corpus" / (exhibit["filename"] + ".gz")).read_bytes())
            if (hashlib.sha256(raw).hexdigest() != exhibit["sha256"]
                    or package["source_sha256"].get("exhibit_html") != exhibit["sha256"]):
                raise ValueError("Workspace exhibit bytes changed")
        records, parents = package["variants"]["C"]["records"], package["variants"]["C"]["parents"]
        validate_records(records, parents)
        indexed = [r for r in store.records if r["metadata"]["accession"] == accession]
        if {r["evidence_id"]: r for r in indexed} != {r["evidence_id"]: r for r in records}:
            raise ValueError("Workspace native index differs from source package")
        if any(store.parents.get(p["evidence_id"]) != p for p in parents):
            raise ValueError("Workspace native parent differs from source package")
        selected.extend(records)
    return selected


def build_workspace_engine(settings, corpus, *, token_counter, tokenizer_id, model_cache=None):
    from src.application import assemble_exact_engine
    from src.indexing.bge import BGEEncoder
    from src.indexing.store import ExactStore
    from src.llm.client import UnifiedLLMClient
    from src.llm.token_budget import BudgetedClient
    from src.runtime_support import model_cache as resolve_model_cache

    store = ExactStore(Path(corpus) / "C")
    records = checked_workspace_records(settings.root, corpus, store)
    encoder = BGEEncoder(local_files_only=True, cache_folder=str(resolve_model_cache(settings.root, model_cache)))
    client = BudgetedClient(UnifiedLLMClient.from_settings(settings), token_counter,
                            context_tokens=settings.ollama_num_ctx, output_tokens=settings.ollama_num_predict)
    engine = assemble_exact_engine(settings, store=store, encoder=encoder, llm_client=client, variant="D",
                                   filters={"accession": list(ACCESSIONS)}, token_counter=token_counter,
                                   context_token_budget=3000, tokenizer_id=tokenizer_id)
    engine.web_source_records = records
    engine.acceptance_scope = "two source-checked development filings; independent final-study acceptance pending"
    return engine
