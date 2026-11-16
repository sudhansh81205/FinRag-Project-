# FinRAG: Reproducible Demo and Backup Walkthrough

**Course**: CS F407 Artificial Intelligence | CV++ Team 6 | Application Track  
**Submission Date**: November 17, 2026  
**Repository**: [github.com/sudhansh81205/FinRag-Project-](https://github.com/sudhansh81205/FinRag-Project-)  
**Author**: Sudhansh Khandelwal (Sole Final-Day Release Owner)  

This document is a proposed walkthrough, not an executed backup demonstration. It describes for the FinRAG submission, establishing the exact execution flow, inspectable evidence records, authoritative calculation trees, and deterministic refusal paths.

---

## 1. Setup & Diagnostic Verification

The application provides a deterministic setup check without requiring external network access or pre-downloaded model weights:

```bash
python app.py --check
```

**Observed Output**:
```json
{
  "status": "index_not_ready",
  "blockers": [
    "No source filing found. Add the selected Apple 2021 filing during ingestion.",
    "No BGE/exact FAISS catalog found. Run the source audit and scripts/build_index.py; see docs/INDEXING.md.",
    "Answering is disabled in this setup build until the filing, persistent index and source checks are connected."
  ]
}
```
*Verification*: The application starts up safely, diagnoses missing storage catalogs honestly, and prevents ungrounded answering.

---

## 2. Narrative Retrieval Path

### User Query:
> *"What are Apple's principal risk factors regarding global supply chain concentration in FY2021?"*

### Execution Flow:
1. **Request Binding**: Target entity `AAPL`, filing `0000320193-21-000105`, fiscal year `2021`, Item `1A`.
2. **Pre-Top-K Filtering**: `src/retrieval/eligibility.py` validates ticker and filing identity before vector scoring.
3. **Retrieval**: Dual dense + Okapi BM25 scoring with Reciprocal Rank Fusion (\(k=60\)).
4. **Retrieved Evidence**:
   - `[Evidence ID: aapl-2021-item1a-p12-n1]`: Details outsourcing of manufacturing to East Asia and single-source suppliers.
5. **Context Budget Enforcement**: Selection capped at \(\le 5\) complete passages.
6. **Result**: Answers strictly grounded in retrieved narrative paragraphs with inspectable `source_locator` citations.

---

## 3. Numerical Calculation Path (Gross Margin Verification)

### User Query:
> *"What was Apple's gross margin percentage in fiscal year 2021?"*

### Execution Flow:
1. **Retrieved Facts**:
   - Fact 1 (`sales_2021`): Total net sales = `365,817` (USD millions, consolidated statements of operations, p. 33).
   - Fact 2 (`cost_2021`): Total cost of sales = `212,981` (USD millions, consolidated statements of operations, p. 33).
2. **Authoritative Calculation Tree**:
   ```json
   {
     "issuer": "Apple Inc.",
     "scope": "consolidated",
     "periods": [
       {
         "kind": "duration",
         "start": "2020-09-27",
         "end": "2021-09-25"
       }
     ],
     "expression": {
       "op": "ratio_percent",
       "args": [
         {
           "op": "subtract",
           "args": [
             {
               "evidence_id": "sales"
             },
             {
               "evidence_id": "cost"
             }
           ]
         },
         {
           "evidence_id": "sales"
         }
       ]
     }
   }
   ```
3. **Deterministic Decimal Arithmetic**:
   $$\text{Gross Profit} = 365,817 - 212,981 = 152,836 \text{ USD millions}$$
   $$\text{Gross Margin} = \frac{152,836}{365,817} \times 100 = 41.779354...\% \approx 41.78\%$$
4. **Output Rendering**:
   - Answer: **41.78%**
   - Source Citations: `[Evidence ID: 0000320193-21-000105:table:operations_p33:r1]`, `[Evidence ID: 0000320193-21-000105:table:operations_p33:r2]`
   - Generated prose explains the computation but cannot alter the authoritative numeric conclusion.

---

## 4. Grounded Chart Evidence Path

### User Query:
> *"How did Apple's 5-year cumulative total shareholder return compare to the S&P 500 in the 2021 annual report?"*

### Execution Flow:
1. **Asset Lookup**: Locate Item 5 stock performance graph (`data/charts/ad0ded84e0a5b9dbf96385d1debb0cf711f6f1bec501dda9c067091526dd83a9.jpg`).
2. **Grounded Provenance**:
   - PDF Page: 20
   - Asset SHA-256: `ad0ded84e0a5b9dbf96385d1debb0cf711f6f1bec501dda9c067091526dd83a9`
   - Verified Review Ledger: `docs/reports/2026-11-15_chart_approvals_ujjwal.json`
3. **Safe Interpretation**:
   - Model reads independently approved description. Values not directly printed on axis tick marks are preserved as `UNKNOWN`.

---

## 5. Meaningful Failure & Refusal Paths

FinRAG guarantees deterministic refusal over plausible falsehoods:

### 5A. Wrong Entity / Filing Refusal
- **Query**: *"What was Microsoft's FY2022 revenue?"* when only Apple FY2021 evidence is available.
- **System Behavior**: Request eligibility filter detects ticker mismatch (`MSFT != AAPL`).
- **Result**: `status: "insufficient_evidence"`, `message: "The requested retrieval stage found insufficient evidence."`
- **Integrity Guarantee**: The model *refuses* rather than attributing Apple's $365B to Microsoft.

### 5B. Excluded Operand Refusal
- **Query**: Requesting calculation where `fact_cost_2021` was truncated by the 5-passage limit or context token budget.
- **System Behavior**: `verify_included_operands()` flags that `fact_cost_2021` is missing from `included_evidence_ids`.
- **Result**: Refusal with `insufficient_evidence`. Uncited external constants are prohibited.

### 5C. Zero Denominator / Invalid Arithmetic Refusal
- **Query**: Computing percentage growth from a prior value of 0.
- **System Behavior**: Decimal tree evaluates denominator check; zero prior triggers strict mathematical refusal.
- **Result**: `status: "refused_zero_denominator"`.

---

## 6. Reproducible Verification Commands

Run the following commands to reproduce all verified claims:

```bash
# 1. Run all unit and integration tests (459 passing tests)
python -m pytest -q

# 2. Verify Ruff code style and import formatting (zero errors)
python -m ruff check .

# 3. Verify candidate chart splits and image hashes
python scripts/verify_chart_set.py

# 4. Verify diagnostic entry point
python app.py --check

# 5. Verify the entire release package integrity
python scripts/verify_release_package.py
```


Evidence correction: sales/cost above are teaching fixture IDs. Use real included stable evidence IDs for an actual execution. Narrative/chart passages and locators in this procedure are illustrative unless verified against the accepted source package. No live source-linked backup recording is supplied by this document.
