# November 2 parser completion and verification

Work performed November 3, 2026, Asia/Kolkata, for Likhit's Day 4 assignment.
The implementation follows the revised reduced scope: keep Chroma/MiniLM and
prepare one traceable Apple 10-K. It does not implement the earlier hybrid-stack
migration or the later owners' indexing, retrieval, generation or evaluation work.

## Upstream state inspected

Fetched team `origin/main` at `6f9f236` (merge of PR #3, November 3 local time).
The repository already contained the Days 1–2 integration/configuration/setup
work, an exact filing manifest and evidence contract, plus Rushil's Day 3
provider/failure fixes. His handoff includes earlier live Gemini checks; those
were reviewed as saved evidence, not rerun or claimed as today's checks.
The existing local suite passed 59 tests before the parser was added.
No repeatable parser or populated index was present in that revision.

## November 2 acceptance

| Required result | Delivered evidence |
| --- | --- |
| Exact company, accession, year, URL, local path and checksum | `data/filing_manifest.json`; Apple 2021, accession 0000320193-21-000105 |
| Repeatable parsing function and one command | `src/ingestion/filing_parser.py`; `python scripts/parse_filing.py` |
| Bounded Items 1A, 7 and 8; TOC excluded | Verified body anchor pairs in the saved summary; actual and synthetic boundary tests |
| Separate narrative and statement records | 316 narrative records plus 3 table records; separate JSONL files |
| Source locations, titles, periods and units retained | CSS locators, source hash, raw table cell structure, actual header periods and unit text |
| Saved parsing summary and next-owner handoff | Tracked JSON summary, parsing instructions and Day 4 handoff |

## Local verification results

- 79 tests pass, including all 59 prior tests and 20 parser tests/parameter cases.
- Ruff passes for the whole project; `pip check` reports no broken requirements.
- The parser runs against the real pinned filing and emits 319 unique IDs.
- Every narrative chunk matches the normalized text slice at its source locator.
- A separate saved-output audit resolves all 119 table-row locators and matches
  every retained raw cell against the source DOM.
- A second parse has identical records, IDs, counts and output hashes.
- A fresh temporary raw directory is restored from the archive, and two CLI-core
  runs produce byte-identical output files. Both compressed and expanded source
  hashes are checked when restoring.
- Wrong checksum/company/accession, manifest scope mismatch, absent boundaries,
  wrong body headings, missing titles/units and unsupported row spans fail visibly.
- Blank table values stay in their correct columns. Parentheses and unit
  exceptions remain present; raw values are not silently converted.
- A failing parse leaves the previous output and manifest unchanged.
- `python app.py --check` returns `index_not_ready`, with no financial answer.
  This is expected: there is no validated persistent index or connected final UI.
- Git whitespace checks pass. The old hybrid draft and application/provider
  implementation are not part of this change.

These are correctness/regression checks, not proof that software has no possible
defects or that financial answer accuracy improved. Final retrieval evaluation
has not run. These results were recorded before publication; consult the PR
for subsequent GitHub CI results.

## Source checks

Original reference:
https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm

The source manifest records fiscal 2021, period ended September 25, 2021 and
filing date October 29, 2021. Inline XBRL identity facts are checked at parse time.
Operations and cash flows retain 2021/2020/2019; the balance sheet retains
2021/2020. Sample source regressions include total net sales 365,817/274,515/260,174,
total assets 351,002/323,888 and operating cash flow 104,038/80,674/69,391, with
the source's millions declaration preserved. They are parser checks, not a
reserved evaluation question set.

Saved source SHA-256:
`8d9e6dbb6acd1f24dbc4345f74240b255ceaaf5beadb5874b143c7f67032e9d2`.
The source is a complete browser DOM snapshot because direct HTTP downloads
returned 403. Scripts and the empty browser overlay were removed. This hash
does not identify original SEC response bytes. See `data/source/README.md` for
the acquisition method and the bundled 174,200-byte archive.

## Review corrections and remaining work

The first real-source inspection showed that the inline XBRL period-end fact is
displayed as a month-name date. Validation now accepts that source format as
well as ISO format without assuming transformed XBRL values. Review also added
explicit rejection of metadata/company/scope drift and filtering of hidden
inline content. The final suite was rerun after these corrections.

Short blocks under 80 characters and nonselected tables are excluded by design.
This parser handles one declared layout; it does not promise other years/filers.
Full table parents are not yet normalized row evidence. Ujjwal's Nov 3 task
builds/reopens the persistent index; Likhit's Nov 6 task prepares validated row
records. Readiness remains gated until those downstream checks are complete.

Actual human time was not measured; no claim is made that the planned two-hour
allocation was spent. Code and verification were prepared with AI assistance.
The initial handoff left changes local on `likhit/day-04-filing-parser`.
Likhit subsequently connected GitHub and authorized branch publication and a
pull request. Publication instructions and the PR description remain included
for reference; consult GitHub for the current review status.
