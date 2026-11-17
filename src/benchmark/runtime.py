"""R4/R7/R12: explicit prepared runtime factory; no downloads or implicit model.

This wires the explicitly selected A/B representation or C-G resources only when
their acceptance gates pass. Benchmark source-equivalence is a separate runner
gate; a prepared filing index does not make it bound.
"""
from src.web_api import build_prepared_engine


def build_benchmark_engine(settings, *, variant, tokenizer_dir=None, token_counter=None,
                           tokenizer_id=None, model_cache=None, representation=None, reranker_dir=None):
    if variant in {"A", "B"} and representation != variant:
        raise ValueError("A/B resources are unavailable without an explicitly selected matching representation index.")
    if variant in {"E", "F", "G"} and reranker_dir is None:
        raise ValueError("E/F/G resources are unavailable without the pinned cross-encoder assets.")
    if settings.provider != "ollama" or settings.model != "gemma3:4b" or not settings.ollama_digest:
        raise ValueError("Primary runs require the explicit digest-pinned Gemma3:4b Ollama profile.")
    return build_prepared_engine(settings, variant=variant, tokenizer_dir=tokenizer_dir,
                                 token_counter=token_counter, tokenizer_id=tokenizer_id,
                                 model_cache=model_cache, **({"representation": representation} if representation else {}),
                                 **({"reranker_dir": reranker_dir} if reranker_dir else {}))
