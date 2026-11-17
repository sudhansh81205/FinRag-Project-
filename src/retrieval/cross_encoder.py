"""R10/E-G: identified local BAAI cross-encoder with finite scalar scores.

Official revision and file identities were verified at the publisher's HTTPS API.
Runtime never downloads models or silently truncates a query/passage pair.
"""
import hashlib
import json
from pathlib import Path

MODEL = "BAAI/bge-reranker-base"
REVISION = "2cfc18c9415c912f9d8155881c133215df768a70"
# algorithm, publisher content identity, byte count
ASSETS = {
    "config.json": ("git", "ff248a5f7d76e27b10778b3c593c9fba1df4c448", 799),
    "model.safetensors": ("sha256", "ced967c45fd1902eb92716c9ceeca7c95a936770ea9db611f5a841b926e33fbd", 1112206140),
    "sentencepiece.bpe.model": ("sha256", "cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865", 5069051),
    "special_tokens_map.json": ("git", "68171d1ff68b731a33d119708476692c094a466b", 279),
    "tokenizer.json": ("sha256", "9eb652ac4e40cc093272bbbe0f55d521cf67570060227109b5cdc20945a4489e", 17098107),
    "tokenizer_config.json": ("git", "059214673d9d6d2ee319411e2ffec8c024b816d5", 443),
}


def verify_assets(directory):
    directory = Path(directory)
    digests = {}
    for name, (algorithm, expected, size) in ASSETS.items():
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise ValueError("Missing or changed pinned cross-encoder asset")
        digest = hashlib.sha256() if algorithm == "sha256" else hashlib.sha1()
        if algorithm == "git":
            digest.update(f"blob {size}\0".encode())
        actual_sha = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(block)
                actual_sha.update(block)
        if digest.hexdigest() != expected:
            raise ValueError("Cross-encoder asset differs from the publisher's pinned revision")
        digests[name] = actual_sha.hexdigest()
    config = json.loads((directory / "config.json").read_text())
    if config.get("model_type") != "xlm-roberta" or config.get("num_labels", 1) != 1:
        raise ValueError("Cross-encoder architecture differs from the pinned profile")
    return {"model": MODEL, "revision": REVISION, "file_sha256": digests}


class PinnedCrossEncoder:
    def __init__(self, directory, *, batch_size=4):
        self.fingerprint = verify_assets(directory)
        if type(batch_size) is not int or not 1 <= batch_size <= 16:
            raise ValueError("Cross-encoder batch size must be between 1 and 16")
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        torch.set_num_threads(1)
        self.tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            directory, local_files_only=True, trust_remote_code=False, use_safetensors=True).to("cpu").eval()
        self.batch_size = batch_size
        self.model_id = MODEL + "@" + REVISION
        self.identity_verified = True

    def predict(self, pairs):
        import torch
        if not isinstance(pairs, list) or any(not isinstance(pair, (list, tuple)) or len(pair) != 2
            or any(not isinstance(value, str) or not value.strip() for value in pair) for pair in pairs):
            raise ValueError("Cross-encoder needs nonempty question/passage pairs")
        scores = []
        with torch.inference_mode():
            for offset in range(0, len(pairs), self.batch_size):
                batch = pairs[offset:offset + self.batch_size]
                tokens = self.tokenizer(batch, padding=True, truncation=False, return_tensors="pt")
                if tokens["input_ids"].shape[1] > 512:
                    raise ValueError("Cross-encoder pair exceeds the pinned 512-token budget")
                logits = self.model(**tokens).logits
                if logits.shape != (len(batch), 1) or not torch.isfinite(logits).all():
                    raise ValueError("Cross-encoder returned invalid logits")
                scores.extend(logits[:, 0].float().tolist())
        return scores
