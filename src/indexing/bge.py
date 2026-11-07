"""BGE inference with explicit query instructions and no silent truncation."""

from dataclasses import asdict, dataclass

import numpy as np

MODEL = "BAAI/bge-base-en-v1.5"
REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
DIMENSION = 768


@dataclass(frozen=True)
class EmbeddingSpec:
    embedding_model: str = MODEL
    embedding_revision: str = REVISION
    dimension: int = DIMENSION
    normalization: str = "l2"

    def manifest_fields(self):
        return {
            **asdict(self),
            "preprocessing": {
                "query_instruction": "Represent this sentence for searching relevant passages: ",
                "document_instruction": "",
                "max_seq_length": 512,
                "truncation_policy": "reject_over_limit_including_special_tokens",
            },
        }


def unit_vectors(values, count):
    values = np.asarray(values, dtype=np.float32)
    if values.shape != (count, DIMENSION) or not np.isfinite(values).all():
        raise ValueError("Embedding dimension/count/finite-value mismatch")
    norms = np.linalg.norm(values, axis=1)
    if not np.isfinite(norms).all() or np.any(norms <= 0):
        raise ValueError("Zero embedding cannot represent cosine similarity")
    return np.ascontiguousarray(values / norms[:, None])


class BGEEncoder:
    def __init__(self, *, cache_folder=None, local_files_only=True, batch_size=16):
        from sentence_transformers import SentenceTransformer

        self.spec = EmbeddingSpec()
        self.batch_size = batch_size
        self.model = SentenceTransformer(
            MODEL,
            revision=REVISION,
            device="cpu",
            cache_folder=cache_folder,
            local_files_only=local_files_only,
            trust_remote_code=False,
            model_kwargs={"use_safetensors": True},
        )
        self.model.max_seq_length = 512
        if self.model.get_embedding_dimension() != DIMENSION:
            raise ValueError("Downloaded model has the wrong embedding dimension")

    def encode(self, texts, *, query=False):
        if not texts:
            return np.empty((0, DIMENSION), dtype=np.float32)
        if any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("Embedding input must contain nonempty text")
        prefix = self.spec.manifest_fields()["preprocessing"][
            "query_instruction" if query else "document_instruction"
        ]
        prepared = [prefix + text for text in texts]
        lengths = [
            len(ids)
            for ids in self.model.tokenizer(
                prepared, truncation=False, padding=False, add_special_tokens=True
            )["input_ids"]
        ]
        if max(lengths) > 512:
            raise ValueError(
                f"BGE token limit exceeded ({max(lengths)} > 512); split evidence before indexing"
            )
        vectors = self.model.encode(
            prepared,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
            prompt="",
        )
        return unit_vectors(vectors, len(texts))
