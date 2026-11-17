"""R4/R7/R12: explicit prepared runtime factory; no downloads or implicit model.

This wires C/D when their acceptance gates pass. Benchmark source-equivalence
is a separate runner gate; a prepared filing index does not make it bound.
"""
from src.web_api import build_prepared_engine


def build_benchmark_engine(settings, *, variant, tokenizer_dir=None, token_counter=None,
                           tokenizer_id=None, model_cache=None):
    if variant not in {"C", "D"}:
        raise ValueError("The prepared factory supports C/D. A/B/E/F/G adapters remain unavailable.")
    if settings.provider != "ollama" or settings.model != "gemma3:4b" or not settings.ollama_digest:
        raise ValueError("Primary runs require the explicit digest-pinned Gemma3:4b Ollama profile.")
    return build_prepared_engine(settings, variant=variant, tokenizer_dir=tokenizer_dir,
                                 token_counter=token_counter, tokenizer_id=tokenizer_id,
                                 model_cache=model_cache)
