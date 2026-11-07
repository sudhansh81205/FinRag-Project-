# Build and inspect the exact BGE index

This implements the November 6 R1/R2 index handoff on the independently accepted
November 5 data. It is a dense retrieval component, not the completed A-G system.
The tested Windows runtime is Python 3.12 on CPU. A fresh install needs several
GB for PyTorch and dependencies; model weights are a separate public download.

## Reproduce

From the repository root, in an activated environment:

```powershell
python -m pip install -r requirements-dev.txt -r requirements-index.txt
python scripts/parse_filing.py
python scripts/prepare_evidence.py
python scripts/verify_canonical_data.py
python scripts/build_index.py --download-model
python scripts/query_index.py 'What were Apple total net sales in 2021?' --filters '{"ticker":"AAPL","type":"table_cell","period_end":"2021-09-25"}' --k 3
python scripts/verify_index.py
```

Only the first model download needs `--download-model`. Builds and queries default
to offline cached weights; missing weights, overlong inputs and failed audits are
errors. There is no MiniLM, mock or approximate-index fallback. Windows native
FAISS must run in a normal Python process; a restricted execution sandbox can
block its native libraries. `verify_index.py` runs real BGE, rebuilds and reopens
in a fresh process; ordinary pytest uses explicitly synthetic vectors with real
FAISS and does not download a model. Limit OMP/MKL threads if sharing a CPU.

The source verifier checks source facts, exact sidecars, a real DVC restoration
and MLflow readback. The build reruns source predicates and compares the report's
code/source/schema/sidecar hashes. An old or incomplete audit cannot authorize
changed input. The current independent audit supports the bounded Apple HTML
profile only. New filing layouts require parsing and independent acceptance
before adding their candidates; simply downloading a PDF does not pass this gate.

## Model and similarity

Pinned model: `BAAI/bge-base-en-v1.5`, revision
`a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`, 768 dimensions.
Documents have no instruction; queries receive
`Represent this sentence for searching relevant passages: `.
Both are L2 normalized. The 512-token limit includes the instruction and special
tokens. Oversized evidence is rejected, never silently truncated.

```python
# src/indexing/store.py: vectors have already been checked and normalized.
index = faiss.IndexFlatIP(768)
index.add(vectors)
scores, rows = index.search(normalized_query, k)
```

For unit vectors, their dot product equals cosine similarity. `IndexFlatIP`
exhaustively scores the eligible vectors; it needs no training and uses no IVF-PQ
compression. Scores are similarity signals, not confidence probabilities.
See the [BGE model card](https://huggingface.co/BAAI/bge-base-en-v1.5) and
[FAISS metric documentation](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances).

## Storage and query contract

`data/index/bge-faiss/catalog.json` selects one immutable generation per accession.
Each generation contains `index.faiss`, canonical `records.json`, ordered
`candidate_ids.json`, row-aligned `candidate_metadata.json`, full `parent_tables.json`,
`manifest.json` and `provenance.json`. Its directory name hashes all seven files.
The reader checks hashes, schema, model/preprocessing, IDs/metadata, dimensions,
index type and vector norms before serving a query. These hashes detect mismatch;
they are not signatures against an attacker who can rewrite every local file.

Publishing replaces one filing's active generation under an exclusive writer lock
and atomic catalog switch. This removes that filing's stale candidates from active
search and preserves other filings. Identical inputs reuse the same generation.
Old generations remain for recovery; they are not searched. An interrupted write
may leave an unreferenced incomplete generation or a lock; inspect the active
catalog and confirm no writer is running before manual recovery. Automatic deletion
of generations or somebody else's lock is intentionally absent.

```python
from src.indexing.bge import BGEEncoder
from src.indexing.store import ExactStore
from src.retrieval.dense import DenseRetriever

store = ExactStore("data/index/bge-faiss")
encoder = BGEEncoder(cache_folder="output/models")
retriever = DenseRetriever(store, encoder, filters={"ticker": "AAPL"})
streams = retriever.retrieve("What were net sales in 2021?", top_k_text=3, top_k_tables=3)
# streams['table_evidence'] contains whole canonical cells, including evidence_id.
# store.parents[cell['metadata']['parent_table_id']] resolves the full grid.
```

Filters support exact equality or list membership for ticker, accession, section,
type, period start/end, fiscal year, scope and normalized unit. They apply **before**
top-k. Unknown fields/invalid types fail; a valid unindexed company returns an empty
list. Request filters must come from the caller, not guessed silently. Results
retain complete records plus `dense_rank`, cosine `score`, `score_type` and
`eligible_count`. Ties use evidence ID. Disabled streams make no search call, and
disabling both makes no embedding call. Parents are not separate dense candidates.

The current reader loads vectors in memory and rebuilds a filtered exact index
for each query, scoring all eligible rows for deterministic ties. This is correct
for the accepted corpus, but full-corpus latency/memory still need measurement.
`DenseRetriever` fits the engine's retrieval boundary. Pavan must supply the matched
A-F stages, BM25 over these same IDs, RRF, explicit reranking and bounded parent
expansion. The legacy Chroma assembly and heuristic reranker are not the final
pipeline. A/B flattened-table representations and G chart descriptions are also
not constructed by this canonical-cell index.

## Corpus accounting

```powershell
python scripts/acquire_corpus.py --download
```

The manifest identifies five Apple, five Microsoft and eight additional company
filings. Canonical SEC URLs and rendition URLs are separate. Already verified PDF
bytes are checksum-pinned; the downloader validates issuer/form/exact fiscal-period
cover text and refuses changed checksums. The command returns nonzero when any
source is missing or fails. `--download` is optional for an offline inventory.
AnnualReports copies are labelled mirrors, not original SEC response bytes.

See `docs/reports/2026-11-07_corpus-coverage.json`: 16 verified local PDF renditions,
18 inventoried filings, nine companies with a verified rendition, one accepted
canonical/indexed filing. Microsoft 2022 lacks a qualifying 10-K cover in the
selected rendition; Oracle 2024's extracted issuer text fails the strict check.
IBM's 10-K incorporates financial sections by reference, so its short PDF is not
complete statement coverage. New PDF layouts, footnotes, captions and benchmark
corpora remain explicit work. None of these downloaded files is silently embedded.
