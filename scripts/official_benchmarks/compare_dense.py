"""BGE/exact-FAISS retrieval over complete official source pools, with checkpoints."""

import hashlib
import json
import os
import sys
import time

import numpy as np
from run_evaluation import OUTPUT_DIR, REPO, load_suite, metrics, write

sys.path.insert(0, str(REPO))
from src.indexing.bge import BGEEncoder
from src.validation_metrics import clustered_interval


def main():
    import faiss
    import torch

    encoder = BGEEncoder(
        cache_folder=os.environ.get("FINRAG_BGE_CACHE", str(REPO / "output/models-http")),
        batch_size=16,
    )
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    encoder.model.to(device)
    print("Embedding device", device, flush=True)
    tokenizer = encoder.model.tokenizer
    output = OUTPUT_DIR
    for name in ("TAT-QA", "FinQA", "FinanceBench"):
        folder = output / name
        cases, records, hashes = load_suite(name)
        chunks = []
        for record in records:
            ids = tokenizer.encode(record["text"], add_special_tokens=False, truncation=False)
            for offset in range(0, len(ids), 400):
                text = tokenizer.decode(ids[offset : offset + 440], skip_special_tokens=True)
                if text.strip():
                    chunks.append(
                        {"source_id": record["evidence_id"], "offset": offset, "text": text}
                    )
                if offset + 440 >= len(ids):
                    break
        fingerprint = hashlib.sha256(
            json.dumps(
                {"sources": hashes, "chunks": chunks, "encoder": encoder.spec.manifest_fields()},
                sort_keys=True,
            ).encode()
        ).hexdigest()
        cache = folder / ("dense-cache-" + device)
        cache.mkdir(exist_ok=True)
        manifest = cache / "identity.json"
        identity = {
            "device": device,
            "fingerprint": fingerprint,
            "chunks": len(chunks),
            "token_window": 440,
            "token_stride": 400,
            "encoder": encoder.spec.manifest_fields(),
        }
        if manifest.exists():
            assert json.loads(manifest.read_text()) == identity
        else:
            write(manifest, identity)
        print(name, "embedding", len(chunks), "chunks", flush=True)
        batches = []
        started = time.perf_counter()
        for offset in range(0, len(chunks), 256):
            checkpoint = cache / f"{offset:06d}.npy"
            if not checkpoint.exists():
                vectors = encoder.encode([c["text"] for c in chunks[offset : offset + 256]])
                with checkpoint.with_suffix(".tmp").open("wb") as stream:
                    np.save(stream, vectors, allow_pickle=False)
                checkpoint.with_suffix(".tmp").replace(checkpoint)
            batch = np.load(checkpoint, allow_pickle=False)
            assert batch.shape == (min(256, len(chunks) - offset), 768) and np.isfinite(batch).all()
            batches.append(batch)
            if offset % 2048 == 0:
                print(name, min(offset + 256, len(chunks)), "/", len(chunks), flush=True)
        vectors = np.concatenate(batches)
        query_vectors = encoder.encode([c["question"] for c in cases], query=True)
        index = faiss.IndexFlatIP(768)
        index.add(vectors)
        # Search up to 400 chunks, then retain ten distinct original sources.
        _, ranked = index.search(query_vectors, min(400, len(chunks)))
        bm25 = {r["case_id"]: r for r in json.loads((folder / "rankings.json").read_text())}
        rows = []
        for case, order in zip(cases, ranked, strict=True):
            dense = list(dict.fromkeys(chunks[i]["source_id"] for i in order))[:10]
            assert len(dense) == 10, (
                "Increase retrieval depth to obtain ten distinct original sources"
            )
            lexical = bm25[case["case_id"]]["ranked_ids"]
            scores = {}
            for ranking in (dense, lexical):
                for rank, eid in enumerate(ranking, 1):
                    scores[eid] = scores.get(eid, 0) + 1 / (60 + rank)
            hybrid = sorted(scores, key=lambda eid: (-scores[eid], eid))[:10]
            gold = case["gold"].get("gold_evidence_ids", [])
            rows.append(
                {
                    "case_id": case["case_id"],
                    "document": case["doc_name"],
                    "dense_ids": dense,
                    "hybrid_ids": hybrid,
                    "dense": metrics(dense, gold),
                    "hybrid": metrics(hybrid, gold),
                }
            )
        write(folder / "dense-hybrid-rankings.json", rows)
        summary = {
            "suite": name,
            "cases": len(rows),
            "embedding_and_search_seconds": time.perf_counter() - started,
            "representation": "440-token windows, stride 400; rank original pages/paragraphs/whole tables by first chunk hit",
            "scope": "Pooled source retrieval baseline; cumulative PRD A-G representations pending",
            "metrics": {},
        }
        for metric in next(r["dense"] for r in rows if r["dense"]):
            values = [
                {
                    "accession": r["document"],
                    "dense": r["dense"][metric],
                    "hybrid": r["hybrid"][metric],
                    "delta": r["hybrid"][metric] - r["dense"][metric],
                }
                for r in rows
                if r["dense"]
            ]
            summary["metrics"][metric] = {
                method: clustered_interval(values, method)
                for method in ("dense", "hybrid", "delta")
            }
        write(folder / "dense-hybrid-summary.json", summary)
        print(name, "dense/hybrid evaluation complete", flush=True)


if __name__ == "__main__":
    main()
