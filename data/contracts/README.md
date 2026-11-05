# Canonical data and index contracts

These contracts are the handoff boundary between parsing, validation and the
future BGE/FAISS index. `evidence_id` is the single logical identity. A physical
index and its metadata sidecar must use the same ordered ID list and hashes.

The canonical record keeps source URL/locator, accession, source checksum and
record type. Table-cell records extend it with parent table, row/column headers,
raw and normalized values, period boundaries, currency/scale, footnote links and
grid coordinates. A parent table remains independently stored even when an
embedding model has an input limit. Chart records link generated descriptions to
the original image path/locator/hash and identify unknown values.

`index_sidecar.schema.json` describes the final proposal index, not the current
historical MiniLM/Chroma recovery artifact. BGE revision, preprocessing,
normalization and dimension must be recorded before a final index is accepted.

## Executable boundary and explicit limits (November 5 repair)

`src.contracts.canonical_record` is a lossless adapter: rename the old `id` to
`evidence_id`, reject conflicting aliases, and retain the full `source_rows`.
It does not write a new data package or invent cell facts. Schema version 1 has
conditional mandatory fields for parents, typed cells and chart descriptions.
The latter two contracts are targets, not an assertion that their parser exists.
For an instant fact, period_start is null; duration facts require a real start.
Shanay's independent semantic audit must enforce period order, unit consistency,
parent/grid resolution and original-source truth beyond JSON field shapes.

`verify_parser_package` validates the existing Apple HTML parent profile only:
nonempty files, summary/manifest counts, output/source/archive/content hashes,
JSON Schema, deterministic IDs, uniqueness and self-parent identity. It rejects
missing/corrupt input and always marks full canonical package readiness false.
Matching regenerated hashes do not replace independent source verification.

Index-sidecar contract (not index implementation): row i of the vector matrix
must refer to entry i of the ordered canonical ID list and metadata sidecar.
Hash ordered IDs as SHA-256 of `json.dumps(ids, ensure_ascii=False,
separators=(",", ":")).encode("utf-8")` with no newline. Never sort this row map.
The parser smoke's sorted newline ID-set hash is a DIFFERENT diagnostic, not
the vector-row hash. Hash serialized index, sidecar and full parent-store bytes
separately. Pin a full model commit, normalization, dimension and preprocessing.
Any mismatch blocks use; Likhit implements actual row/vector checks later.

Run `python scripts/parse_filing.py`, then
`python scripts/verify_day05_environment.py`. See [environment setup](../../docs/ENVIRONMENT.md).
