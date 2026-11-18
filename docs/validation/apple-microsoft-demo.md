# Apple and Microsoft demonstration checks

Select the company, filing and fiscal-year end shown for each prompt. Use **Auto** unless a different mode is listed. Use **Year-end balance** for total assets and the fiscal-year total option for the monetary flow questions. Open the evidence card and check the issuer, accession, period and unit.

## Verified results

The existing local gateway passed **44 of 49** numerical and scope checks. Five failures covered the two-metric prompts, relative margin change, and substitution of company totals for iPhone and Azure. A separate candidate gateway loaded the prepared 18-filing index and passed **64 of 64** checks: 46 financial calculation requests, 12 direct disclosures, two real Gemma narrative requests and four expected refusals.

Initial narrative calls hit the provider timeout. A shorter free-form prompt finished but still introduced extra claims or unreliable citations. In the final candidate, Gemma selected relevant excerpts and the workspace rendered the original filing sentences with their exact source citations. Both narrative passages were inspected against their cited context. The Apple and Microsoft narrative calls took about 11 and 10 seconds respectively in the final local run.

[Per-case results and evidence](apple-microsoft-demo-results.json)

## Prompts to demonstrate

| Selection | Prompt to paste | Expected |
| --- | --- | --- |
| Apple FY2025 · 2025-09-27 | How many total employees did Apple have at the end of FY2025? | Approximately **166,000 full-time equivalent employees**, Item 1. |
| Microsoft FY2025 · 2025-06-30 | How many total employees did Microsoft have at the end of FY2025? | Approximately **228,000 full-time employees**, Item 1. |
| Apple FY2025 · 2025-09-27 | What were Apple's revenue and net income in FY2025? | **$416.161 billion** revenue and **$112.010 billion** net income, each with a checked source. |
| Microsoft FY2025 · 2025-06-30 | What were Microsoft's revenue and net income in FY2025? | **$281.724 billion** revenue and **$101.832 billion** net income, each with a checked source. |
| Apple FY2021 · 2021-09-25 | What was Apple Inc.'s gross margin in FY2021? | **41.78%** with gross profit and revenue operands. |
| Apple FY2021 · 2021-09-25 | By what percentage did Apple's gross margin increase from FY2020 to FY2021? | **9.27%** relative increase. |
| Apple FY2021 · 2021-09-25 | By how many percentage points did Apple's gross margin increase from FY2020 to FY2021? | **3.55 percentage points**. |
| Apple FY2025 · 2025-09-27 | How much revenue did Apple report from iPhone in FY2025? | **$209.586 billion** from the original iPhone row, scoped to the product. |
| Microsoft FY2025 · 2025-06-30 · Year-end balance | What were Microsoft's total assets as of June 30, 2025? | **$619.003 billion**. |
| Apple FY2021 · 2021-09-25 · Narrative | Why does Apple say obtaining enough components on commercially reasonable terms matters? | A filing-grounded explanation with a passage about component availability and operating results. |
| Microsoft FY2025 · 2025-06-30 · Narrative | What growth rate did Microsoft state for "Azure and other cloud services" in FY2025? Cite the filing. | **34%**, with the matching passage from Item 7. |

## Questions that should refuse

- Microsoft FY2025 · “How much revenue did Microsoft report from Azure in FY2025?” The 10-K and selected evidence support the reported growth rate. An Azure-only dollar total requires a separate source.
- Microsoft FY2025 · “What was Apple's revenue in FY2025?” The question and selection name different companies.
- Apple FY2025 · “How many employees did Apple have as of September 29, 2025?” The filing workforce disclosure is dated September 27.
- Microsoft FY2025 · “How many offices did Microsoft have worldwide at the end of FY2025?” A verified office count is unavailable in this query path.

## Workforce checks across the ten Apple and Microsoft filings

Use “How many total employees did [company] have at the end of FY[year]?” and select the matching filing and date. The numbers below preserve the scope used by the issuers.

| Fiscal year | Apple full-time equivalents | Microsoft full-time employees |
| --- | ---: | ---: |
| 2021 | 154,000 as of Sep 25 | 181,000 as of Jun 30 |
| 2022 | 164,000 as of Sep 24 | 221,000 as of Jun 30 |
| 2023 | 161,000 as of Sep 30 | 221,000 as of Jun 30 |
| 2024 | 164,000 as of Sep 28 | 228,000 as of Jun 30 |
| 2025 | 166,000 as of Sep 27 | 228,000 as of Jun 30 |

Cisco FY2024 remains a regression check. “how many total employees in cisco as of july 2024” yields approximately **90,400 employees as of July 27, 2024**.

## Repeat the check

Apply the branch's Python code to the prepared runtime and start the local workspace as described in [START_HERE.txt](../../START_HERE.txt). Then run:

```sh
.venv/bin/python scripts/check_apple_microsoft_demo.py --output output/apple-microsoft-demo.json
```

The check uses the real gateway, 18-filing backend and selected model. The 40 annual financial references come from the earlier source-verified development ledger. Balance-sheet and disclosure expectations come from the cited original filings. Automated checks compare the checked value, unit, accession, period and included evidence IDs. Narrative responses also need a claim-level reading of the returned context. These are interactive demonstration regressions, with model output and evidence available for inspection.

[Apple FY2025 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm) · [Apple FY2021 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm) · [Microsoft FY2025 10-K](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm) · [Cisco FY2024 10-K](https://www.sec.gov/Archives/edgar/data/858877/000085887724000017/csco-20240727.htm)
