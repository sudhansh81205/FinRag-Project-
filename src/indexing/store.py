"""Exact cosine search with immutable generations and per-filing replacement.

The writer switches one catalog atomically only after validating the new generation.
Old generations remain available; no recursive deletion or pickle loading occurs.
"""

import copy
import json
import os
import re
import uuid
from contextlib import contextmanager
from pathlib import Path

import faiss
import numpy as np
from jsonschema import Draft202012Validator, FormatChecker

from src.contracts import sha256, strict_json
from src.evidence_audit import encoded
from src.indexing.bge import DIMENSION, EmbeddingSpec, unit_vectors

ROOT = Path(__file__).resolve().parents[2]
FILTERS = {
    "ticker",
    "accession",
    "section",
    "type",
    "period_end",
    "period_start",
    "fiscal_year",
    "scope",
    "normalized_unit",
}
FILES = {
    "index.faiss",
    "records.json",
    "candidate_ids.json",
    "candidate_metadata.json",
    "parent_tables.json",
    "manifest.json",
    "provenance.json",
}


def checked(condition, message):
    if not condition:
        raise ValueError(message)


def digest_files(payloads):
    return sha256(encoded({name: sha256(payloads[name]) for name in sorted(payloads)}))


def validate_records(records, parents):
    schema = json.loads((ROOT / "data/contracts/canonical_record.schema.json").read_bytes())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    checked(bool(records), "Cannot publish an empty filing")
    ids = set()
    parent_map = {}
    for record in [*records, *parents]:
        validator.validate(record)
        identity, meta = record["evidence_id"], record["metadata"]
        checked(identity not in ids, "Duplicate evidence identity")
        ids.add(identity)
        checked(
            sha256(record["content"].encode()) == meta["content_sha256"], "Content hash mismatch"
        )
    for parent in parents:
        m = parent["metadata"]
        checked(
            m["type"] == "financial_table" and m["parent_table_id"] == parent["evidence_id"],
            "Invalid parent table",
        )
        parent_map[parent["evidence_id"]] = parent
    for record in records:
        m = record["metadata"]
        checked(
            m["type"] in {"narrative_text", "table_cell", "financial_table"},
            "Unsupported candidate type",
        )
        if m["type"] == "financial_table":
            checked(
                isinstance(m.get("source_evidence_ids"), list) and bool(m["source_evidence_ids"]),
                "Flattened table requires source cell identities",
            )
        if m["type"] == "table_cell":
            p = parent_map.get(m["parent_table_id"])
            checked(
                p is not None and p["metadata"]["accession"] == m["accession"],
                "Missing/mismatched parent",
            )
            rows = p["source_rows"]
            checked(
                m["row_index"] < len(rows)
                and m["column_index"] in [c["column"] for c in rows[m["row_index"]]["cells"]],
                "Invalid cell grid coordinate",
            )


def atomic_write(path, payload):
    temporary = path.with_name(".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextmanager
def writer_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".writer.lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ValueError(
            "Index writer lock exists; check for another writer before removing it"
        ) from exc
    try:
        os.close(descriptor)
        yield
    finally:
        path.unlink()


def read_generation(root, accession, generation, spec):
    checked(bool(re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession)), "Invalid accession")
    checked(bool(re.fullmatch(r"[a-f0-9]{64}", generation)), "Invalid generation")
    path = root / "filings" / accession / generation
    checked(path.resolve().is_relative_to(root.resolve()), "Generation escapes index store")
    payloads = {name: (path / name).read_bytes() for name in FILES}
    checked(digest_files(payloads) == generation, "Index generation checksum mismatch")
    manifest = strict_json(payloads["manifest.json"].decode())
    schema = json.loads((ROOT / "data/contracts/index_sidecar.schema.json").read_bytes())
    Draft202012Validator(schema).validate(manifest)
    for key, value in spec.manifest_fields().items():
        checked(manifest[key] == value, "Model/preprocessing mismatch; rebuild required")
    for field, filename in (
        ("index_sha256", "index.faiss"),
        ("evidence_ids_sha256", "candidate_ids.json"),
        ("metadata_sidecar_sha256", "candidate_metadata.json"),
        ("parent_table_sha256", "parent_tables.json"),
    ):
        checked(manifest[field] == sha256(payloads[filename]), f"Invalid {field}")
    checked(manifest["parent_table_storage"] == "parent_tables.json", "Wrong parent store")
    records = strict_json(payloads["records.json"].decode())
    parents = strict_json(payloads["parent_tables.json"].decode())
    ids = strict_json(payloads["candidate_ids.json"].decode())
    meta = strict_json(payloads["candidate_metadata.json"].decode())
    validate_records(records, parents)
    checked(ids == [r["evidence_id"] for r in records], "Row identity mismatch")
    checked(
        meta
        == [
            {"row": i, "evidence_id": r["evidence_id"], "metadata": r["metadata"]}
            for i, r in enumerate(records)
        ],
        "Metadata row mismatch",
    )
    checked(
        all(r["metadata"]["accession"] == accession for r in [*records, *parents]),
        "Filing identity mismatch",
    )
    index = faiss.deserialize_index(np.frombuffer(payloads["index.faiss"], dtype=np.uint8))
    checked(
        type(index) is faiss.IndexFlatIP
        and index.d == DIMENSION
        and index.ntotal == len(records) == manifest["record_count"],
        "Index type/dimension/count mismatch",
    )
    vectors = index.reconstruct_n(0, index.ntotal)
    checked(
        np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5),
        "Stored vectors are not finite unit vectors",
    )
    return records, parents, vectors, manifest


def publish_filing(root, records, parents, vectors, provenance, *, spec=EmbeddingSpec()):
    """Internal storage boundary. CLI first reruns the independent source audit.

    Replacement rebuilds exactly one filing, dropping its stale rows in the new
    active generation while preserving every other catalog entry.
    """
    root = Path(root)
    validate_records(records, parents)
    accessions = {r["metadata"]["accession"] for r in [*records, *parents]}
    checked(len(accessions) == 1, "Publish one complete filing at a time")
    accession = accessions.pop()
    checked(bool(re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession)), "Invalid accession")
    vectors = unit_vectors(vectors, len(records))
    index = faiss.IndexFlatIP(DIMENSION)
    index.add(vectors)
    payloads = {
        "index.faiss": faiss.serialize_index(index).tobytes(),
        "records.json": encoded(records),
        "candidate_ids.json": encoded([r["evidence_id"] for r in records]),
        "candidate_metadata.json": encoded(
            [
                {"row": i, "evidence_id": r["evidence_id"], "metadata": r["metadata"]}
                for i, r in enumerate(records)
            ]
        ),
        "parent_tables.json": encoded(parents),
        "provenance.json": encoded(provenance),
    }
    manifest = {
        **spec.manifest_fields(),
        "index_format": "faiss.IndexFlatIP",
        "record_count": len(records),
        "index_sha256": sha256(payloads["index.faiss"]),
        "evidence_ids_sha256": sha256(payloads["candidate_ids.json"]),
        "metadata_sidecar_sha256": sha256(payloads["candidate_metadata.json"]),
        "parent_table_storage": "parent_tables.json",
        "parent_table_sha256": sha256(payloads["parent_tables.json"]),
        "id_order_encoding": "utf8-json-array-compact-no-ascii-escape",
    }
    payloads["manifest.json"] = encoded(manifest)
    generation = digest_files(payloads)
    with writer_lock(root):
        catalog_path = root / "catalog.json"
        if catalog_path.exists():
            old = ExactStore(root, spec=spec)  # Refuse to extend an already corrupt store.
            catalog = copy.deepcopy(old.catalog)
        else:
            catalog = {"schema_version": 1, "filings": {}}
        destination = root / "filings" / accession / generation
        if destination.exists():
            read_generation(root, accession, generation, spec)
        else:
            destination.mkdir(parents=True)
            for name, payload in payloads.items():
                atomic_write(destination / name, payload)
            read_generation(root, accession, generation, spec)
        catalog["filings"][accession] = generation
        atomic_write(catalog_path, encoded(catalog))
    return {
        "accession": accession,
        "generation": generation,
        "record_count": len(records),
        "manifest": manifest,
    }


def eligible(record, filters):
    return all(
        record["metadata"].get(key) in value
        if isinstance(value, list)
        else record["metadata"].get(key) == value
        for key, value in filters.items()
    )


class ExactStore:
    def __init__(self, root, *, spec=EmbeddingSpec()):
        self.root, self.spec = Path(root), spec
        self.catalog = strict_json((self.root / "catalog.json").read_text(encoding="utf-8"))
        checked(
            set(self.catalog) == {"schema_version", "filings"}
            and self.catalog["schema_version"] == 1
            and bool(self.catalog["filings"]),
            "Invalid/empty catalog",
        )
        self.records, self.parents, matrices = [], {}, []
        for accession, generation in sorted(self.catalog["filings"].items()):
            records, parents, vectors, _ = read_generation(self.root, accession, generation, spec)
            self.records.extend(records)
            self.parents.update({p["evidence_id"]: p for p in parents})
            matrices.append(vectors)
        ids = [r["evidence_id"] for r in self.records]
        checked(len(ids) == len(set(ids)), "Duplicate identity across filings")
        self.vectors = np.concatenate(matrices)

    def search(self, query_vector, *, k=5, filters=None):
        checked(type(k) is int and k >= 0, "k must be a nonnegative integer")
        filters = {} if filters is None else filters
        checked(
            isinstance(filters, dict) and not set(filters) - FILTERS,
            "Unsupported eligibility filter",
        )
        checked(
            all(
                isinstance(v, (str, int, list))
                and not isinstance(v, bool)
                and (
                    not isinstance(v, list)
                    or all(isinstance(x, (str, int)) and not isinstance(x, bool) for x in v)
                )
                for v in filters.values()
            ),
            "Invalid filter value",
        )
        query = np.asarray(query_vector)
        checked(query.shape in {(DIMENSION,), (1, DIMENSION)}, "Invalid query vector shape")
        query = unit_vectors(query.reshape(1, DIMENSION), 1)
        selected = [i for i, record in enumerate(self.records) if eligible(record, filters)]
        if not selected or k == 0:
            return []
        # Filter BEFORE top-k. Scoring all eligible rows also makes boundary ties deterministic.
        index = faiss.IndexFlatIP(DIMENSION)
        index.add(np.ascontiguousarray(self.vectors[selected]))
        scores, positions = index.search(query, len(selected))
        ranked = sorted(
            ((float(s), selected[int(p)]) for s, p in zip(scores[0], positions[0])),
            key=lambda pair: (-pair[0], self.records[pair[1]]["evidence_id"]),
        )[:k]
        return [
            {
                **copy.deepcopy(self.records[row]),
                "score": score,
                "score_type": "cosine",
                "dense_rank": rank,
                "eligible_count": len(selected),
            }
            for rank, (score, row) in enumerate(ranked, 1)
        ]

    def query(self, text, encoder, *, k=5, filters=None):
        checked(
            encoder.spec.manifest_fields() == self.spec.manifest_fields(), "Query encoder mismatch"
        )
        if k == 0:
            return self.search(np.eye(1, DIMENSION)[0], k=k, filters=filters)
        return self.search(encoder.encode([text], query=True)[0], k=k, filters=filters)
