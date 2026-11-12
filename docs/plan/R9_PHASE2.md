# Unscheduled Phase 2 restatement specification

The November 3 revision preserves this requirement outside the proposal release calendar.

## R9 Cross report restatement detection

November 2 scope addition: R9 defines cross-report restatement detection as a planned Phase 2 requirement. The November 3 proposal calendar covers the original release requirements and does not allocate R9 effort. R9 needs a separate effort estimate, named owners and dated completion checks before scheduling; it is not an implemented feature.

### Purpose and delivery phase

Help an annual-report reader identify when a previously reported value for the same fiscal period changes in a later filing. R9 is a planned Phase 2 extension recorded on November 2, 2026. The original proposal scope takes priority through the current November 17 submission deadline. R9 has no assigned delivery date or additional hours in this calendar.

### Supported report pair

Start with two exact SEC annual filings, including a relevant amendment where applicable, from the same issuer with at least one overlapping fiscal period. Compare one supported statement and metric family first, preferably revenue where a verified source pair exists. Keep the current Apple report for the core demo; do not assume that it contains a restatement. Select and document another issuer for this extension if required to obtain a real confirmed example.

### Matching and normalization

Match issuer identity, statement, metric meaning, period start and end, duration or instant, currency, consolidation or segment scope, and accounting basis. Preserve original row labels, headers, raw values, scale and filing identity. Normalize supported scales with decimal arithmetic. A different year, currency, segment, accounting basis or uncertain metric mapping is not a comparable pair. Do not treat ordinary year-over-year growth as a restatement.

### Detection and evidence rules

Compare the same-period values across filing versions using a declared tolerance based on displayed precision and rounding; do not reuse the core evaluation percentage tolerance to hide small changes. A difference alone is a potential revision. Use confirmed_restatement only when a cited issuer disclosure explicitly identifies a restatement and links it to the affected period and metric. Label an explicitly disclosed reclassification or recast separately. Preserve the original disclosure wording; never infer fraud, materiality or a cause from a number mismatch.

### Result shown to the reader

Show both filing dates and accessions, the shared fiscal period, old and later reported values, raw and normalized units, absolute difference, comparison outcome and links to both table rows. Include a disclosure citation when a cause or confirmed label is shown. Use the existing positive-prior rule for any percentage difference and label it a revision difference, not business growth. Explain missing or incomparable evidence.

### Acceptance and implementation plan

### Data and interface contract

Retain each filing version independently; ingestion of a later report must not overwrite the earlier report. Extend evidence with issuer ID, accession, filing date, period boundaries, metric ID, statement, scope, accounting basis and source locator. A comparison stores both operand evidence IDs, disclosure evidence IDs, raw and normalized values, precision and tolerance, formula, delta, outcome and explanation. Store outcome separately from the existing answer status.

### Comparison outcomes

Support unchanged, potential_revision, confirmed_restatement, disclosed_reclassification, disclosed_recast, incomparable and insufficient_evidence. Matching values mean unchanged for the selected metric and period, not proof that the whole filing has no restatements. Ambiguous mappings require abstention. Provider and retrieval failures retain their existing error statuses and cannot become a successful comparison.

### Acceptance cases

Before tuning, define and independently review at least eight cases: an unchanged same-period value; an equivalent value in different scales; a confirmed real restatement with its disclosure; a changed value without a confirming disclosure; an explicit reclassification; an explicit recast; a mismatched period or scope; and missing or ambiguous evidence. Add fixtures for precision boundaries and zero or negative priors. Synthetic fixtures must be labeled and cannot replace the real restatement acceptance case.

### Completion evidence

Every required case must return its reviewed outcome, correct normalized values and applicable delta. Both operand citations must resolve, and every confirmed label must have supporting disclosure evidence. Save expected and actual outputs, false positives, missed confirmed cases, abstentions and observed timing with counts. Verify rerun and restart behavior and rerun the core R1 through R8 checks. Keep this evaluation separate from the proposal A-G experiment.

### Implementation sequence and dependencies

After reliable parsing, persistent indexing, provenance, typed calculations and honest failure handling are verified, select and label the filing pair; extend versioned evidence; implement deterministic matching and comparisons; add the cited disclosure check; expose the comparison in the UI; then run independent acceptance and regression checks. Reuse the existing stack. Limit the first release to the declared issuer, statement and metric family.

### Scheduling and reporting

Estimate these steps and assign owners, hours and dates in a separate Phase 2 schedule before implementation. Inclusion in the PRD authorizes the requirement, not a claim that it fits the revised proposal execution calendar. Bringing R9 into the November build requires an explicit capacity and scope revision. Report it as planned until its completion evidence is saved; any novelty or accuracy claim requires measured comparison with relevant existing approaches.
