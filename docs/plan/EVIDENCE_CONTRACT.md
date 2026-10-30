# Evidence and answer contract, version 1

Agreed implementation target for the October 30 scope task. This defines the next
owners' interface; it does not claim the legacy chunker/engine already preserves it.

## Search record

Each record has `id`, `content` and `metadata`. A stable ID combines accession,
section, source locator, record type and content hash; rebuilding identical inputs
must produce identical IDs. A numeric loop counter alone is insufficient.

Required metadata: `accession`, `ticker`, `fiscal_year`, `section`, `source_url`,
`source_locator`, `source_sha256`, `type`, `record_schema_version`. Types remain
`narrative_text`, `financial_table` or `clean_financial_table` to reuse the retriever.
Table rows also carry `parent_table_id`, `table_title`, `row_label`, `periods_json`,
`units_json` and `headers_json`. JSON strings keep complex values compatible with
scalar Chroma metadata. Keep the original source hash separate from the record hash.

The parent table retains complete headers, row labels and footnotes; table-row
content repeats needed headers/units. A retrieval result adds distance/score while
retaining the original ID and metadata. Reranking must not replace a record with
only its text. Source locators are verified HTML IDs or documented table/row
selectors, never invented page numbers.

See [record_examples.json](record_examples.json). All `EXAMPLE` strings and null
hashes are design examples and must be replaced during ingestion. Do not index
these examples or use them as gold evaluation cases.

## Answer response

Required keys: `status`, `question`, `answer`, `message`, `evidence`, `calculations`,
`provider`, `model`. Later evaluation adds latency, revision and frozen settings.

| Status | Meaning | Answer/evidence rule |
| --- | --- | --- |
| `not_ready` | Application prerequisites or integration incomplete | No financial answer or invented evidence |
| `invalid_input` | Empty or unsupported request format | Explain how to correct it |
| `insufficient_evidence` | A validated search did not find enough support | Abstain, distinguish from service failure |
| `service_error` | Retrieval or provider failed | No successful-looking fallback answer |
| `ok` | Verified real provider answered from included evidence | Citations map to included record IDs |

Only `not_ready` and `invalid_input` are implemented in the setup application.
Rushil implements generation/error semantics next; retrieval provenance and final
UI citation display remain the later owners' work.

Calculations contain an allowlisted operation (`sum`, `difference`, `percent_change`),
typed operands, each operand's record ID/row/period/unit, formula, result and unit.
Reject incompatible units, missing periods and zero denominators. Do not execute
generated Python. Sign handling and rounding must be documented in calculator tests.
