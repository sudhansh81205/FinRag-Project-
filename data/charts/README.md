# FinRAG candidate chart set — 50 questions

**15 development + 35 heldout questions on six original chart images.** Candidate
count target is met. Labels and captions are author-checked and still require a
separate independent review before final evaluation. Candidate labels were authored
with AI assistance and checked against the source images during implementation;
this is not independent human review. No heldout application-QA prediction or
scoring run was performed while preparing this set.

| Issuer | Exact filing accession | PDF page (one based) | Split | Questions |
| --- | --- | ---: | --- | ---: |
| Apple | 0000320193-21-000105 | 22 | dev | 15 |
| NVIDIA | 0001045810-24-000029 | 133 | heldout | 7 |
| AMD | 0000002488-25-000012 | 45 | heldout | 7 |
| Intel | 0000050863-25-000009 | 52 | heldout | 7 |
| Cisco | 0000858877-24-000017 | 50 | heldout | 7 |
| Adobe | 0000796343-25-000004 | 101 | heldout | 7 |

## Canonical files

- `question-set.json` freezes both question files by hash and describes the split.
- `apple-2021-candidate-questions.json` retains the original 15 dev questions
  byte-for-byte (`48734f19...e9c3`).
- `heldout-35-candidate-questions.json` contains the added labels, visual answer
  bases, task types, immutable source IDs and image hashes.
- `chart-sources.json` binds every image to an inventoried filing URL/PDF hash,
  source page, embedded resource or crop geometry and extraction method.
- `assets/` contains the exact original embedded charts or source-page chart
  renders. Adjacent numerical tables are excluded. No chart was reconstructed
  from tabular numbers and no exact curve amounts were estimated.
- `source-author-annotations.json` records source-visible metadata for explicit
  author correction of raw model drafts. It is not independent review.

The heldout cases cover marker/color/line-style identification, axis labels,
series counts, visible ordering and directions, and an exact-value abstention.
A diagram's original/cropped/alternate renditions must stay in one group. Only
Apple appears in dev; the five additional issuers appear wholly in heldout.

## Verify without network or models

```sh
python scripts/verify_chart_set.py
```

This verifies exactly 15/35, all six committed image hashes, pinned question-file
hashes, source resolution, duplicate/source/group split isolation and the application
filing inventory. A changed image/label/source reference fails the check. CI runs
this command and preserves its JSON report. Passing integrity does not approve
semantic labels or establish parsed/indexed corpus coverage.

To recheck the downloaded original PDFs on this user's machine:

```sh
python scripts/verify_chart_set.py --source-dir "/Users/rushilmohan/Desktop/Clg Books/ai/FinRAG/Filings"
```

For another machine, point `--source-dir` at the existing `TICKER_ACCESSION.pdf`
files. Source PDFs are not copied into this dataset. To rebuild assets, install
Poppler and use:

```sh
python scripts/prepare_chart_set_sources.py --source-dir /path/to/filings
```

Explicit `--download` acquires missing pinned PDFs into the chosen directory.
This user's course PDFs belong only in the canonical Clg Books AI folder.
Embedded JPEGs are exact source bytes; vector charts are direct 144-DPI PDF crops
with recorded top-left point rectangles. Rendering software can affect PNG bytes:
review/reversion a new asset generation rather than silently accepting new hashes.

## Captions and heldout separation

`python scripts/caption_chart_set.py` reads source images/metadata and the frozen
Gemma3 profile, **not question/answer files**. The original development caption is
reused; five new images are captioned with the unchanged prompt/schema/options.
Raw model drafts, source annotations/corrections and timings are retained.
Independent review stays pending and unreviewed captions cannot enter production
answer context. No extra description generated from heldout answers was inserted.

`run_rushil_checks.py` still generates only its development/source-calculation
smoke. Its final dataset audit counts all 50 without sending heldout cases to the
model. This is separate from a final A-G evaluation runner.

## Limits and review gate

- Six chart groups are **not fifty independent images**. Resampling and reporting
  should account for the shared-image clusters.
- All six are stock-performance line charts. This meets the candidate count but
  has limited chart-type diversity; do not generalize to bar/pie/other financial
  charts from this set alone.
- Source pages include nearby textual/data-table facts. Candidates emphasize
  chart-specific visual encodings; independent review must check any remaining
  answerability overlap. No claim that A-F necessarily fail every case is made.
- Chart pages may contain notices that performance graphs are not deemed filed
  material. The dataset uses their inclusion in the pinned annual-report rendition;
  it makes no contrary legal filing-status claim.
- Microsoft was inspected but not selected because this downloaded annual-report
  rendition's strict 10-K section provenance was not resolved during selection.
  NVIDIA's initial temporary HTTP 503 succeeded on retry with the pinned checksum.
- New source images do not establish accepted narrative/table parsing, BGE indexing,
  matched A-F integration or full benchmark readiness. These remain separate gates.

Independent review should inspect every image and label basis, confirm issuer,
period/unit/marker mappings and source eligibility, resolve ambiguous questions,
check duplicate groups/source overlap and record any changed label/version before
freeze. The author cannot self-certify that independent gate.

## Portable frozen bytes and independent label promotion

The repository attributes pin JSON to UTF-8/LF checkout bytes on Windows and
Unix. The published question-file and inventory hashes remain unchanged.
Do not repair a hash failure by updating expected hashes to whatever a converted
or edited checkout happens to contain. Restore authentic Git blob bytes and
investigate any real content change as a new candidate version.

`load_candidate_set` continues to accept only pending author candidates. It never
turns author corrections into independent gold. The separate `load_reviewed_set`
accepts an external JSON ledger only after all 50 decisions pass and bind to the
unchanged question-set, question files, source manifest and complete per-case
fingerprints. It returns reviewed copies; original answers, files and 15/35
image-group splits remain unchanged. Model captions require their own independent
approval before G and are not approved by this label-only gate.

The ledger has `schema_version: 1`, `reviewer_identity`, an ISO `reviewed_at` with
time zone, `method: human_original_image_and_source`, `candidate_binding`, and one
entry per case in `decisions`. `candidate_binding` holds `question_set_sha256`,
`question_files_sha256` and `source_manifest_sha256` from the candidate audit.
Each decision holds `id`, `case_sha256` from `case_fingerprint(case)`,
`decision: passed`, `original_image_checked: true`,
`source_provenance_checked: true`, and the independent reviewer's nonempty `basis`.
Pending, failed, missing, duplicate, stale and self-authored decisions block the
gate. The caller supplies the verified reviewer allowlist and known original
label authors; identities in the ledger alone are not trusted or authenticated.
The human must actually inspect the original images and provenance, resolve
ambiguities and authenticate their review through the team review process.
Never create passing decisions merely to make this command succeed.

After that real review, use the existing Python environment:

```text
python scripts/promote_chart_set.py --approvals PATH_TO_REAL_REVIEW_LEDGER --trusted-reviewer VERIFIED_REVIEWER_ID --label-author VERIFIED_LABEL_AUTHOR_ID --output output/chart_label_gate.json
```

Multiple `--trusted-reviewer` and `--label-author` options are allowed. A saved
passing label gate is not proof of accepted captions, an A-G run, benchmark
accuracy or the separate independent 50-output faithfulness audit.
