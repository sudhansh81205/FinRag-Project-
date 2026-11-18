"""Source-checked application corpus; independent experiment acceptance is separate."""
import gzip
import hashlib
import json
from pathlib import Path


def checked_workspace_records(root, corpus, store):
    """Bind every indexed filing to its registry, source, schema and package bytes."""
    from src.indexing.store import validate_records

    root, corpus = Path(root), Path(corpus)
    profiles = json.loads((root / "data/corpus_html_profiles.json").read_bytes())
    coverage = {f["accession"]: f for f in json.loads((corpus / "coverage.json").read_bytes())["filings"]}
    registry = {f["accession"]: f for f in json.loads((root / "data/application_filings.json").read_bytes())}
    accessions = tuple(sorted(store.catalog["filings"]))
    if not accessions or set(accessions) - set(registry):
        raise ValueError("Workspace index contains no supported filings or an unknown filing")
    schema_hash = hashlib.sha256((root / "data/contracts/canonical_record.schema.json").read_bytes()).hexdigest()
    selected = []
    for accession in accessions:
        row, profile = coverage[accession], profiles[accession]
        filing = registry[accession]
        if (not row.get("parsed") or not row.get("indexed_for_review")
                or any(row.get(k) != filing[k] for k in ("ticker", "issuer", "period_end", "source_url"))):
            raise ValueError("Workspace filing is not fully processed or its registry identity changed")
        raw = gzip.decompress((root / "data/source/corpus" / f"{accession}.html.gz").read_bytes())
        if hashlib.sha256(raw).hexdigest() != profile["sha256"]:
            raise ValueError("Workspace source bytes changed")
        payload = (corpus / "records" / f"{accession}.json").read_bytes()
        package = json.loads(payload)
        if (hashlib.sha256(payload).hexdigest() != row["package_sha256"]
                or package["source_sha256"]["html"] != profile["sha256"]
                or package["schema_sha256"] != schema_hash or package["accession"] != accession):
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
                                   filters={"accession": sorted({r["metadata"]["accession"] for r in records})}, token_counter=token_counter,
                                   context_token_budget=3000, tokenizer_id=tokenizer_id)
    engine.web_source_records = records
    engine.acceptance_scope = "source-checked application filings; independent final-study acceptance pending"
    return engine
