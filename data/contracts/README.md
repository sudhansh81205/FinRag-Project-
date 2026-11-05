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
