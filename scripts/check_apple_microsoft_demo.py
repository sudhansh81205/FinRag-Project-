"""Exercise the real FinRAG gateway or Python API with the Apple/Microsoft demo set."""
import argparse
import json
import os
import re
from decimal import Decimal
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {"AAPL": [154000, 164000, 161000, 164000, 166000],
          "MSFT": [181000, 221000, 221000, 228000, 228000]}


def build_cases():
    previous = json.loads((ROOT / "docs/validation/2026-11-18-results/cases.json").read_text())
    inventory = json.loads((ROOT / "data/application_filings.json").read_text())
    cases = []
    for row in previous:
        if row["category"] == "numerical" and row["input"]["ticker"] in COUNTS:
            ref = row["reference"]
            cases.append({"id": row["id"], "input": row["input"],
                          "numbers": [[ref["value"], ref["unit"]]], "status": "ok"})

    def add(identity, ticker, year, question, *, kind="duration", mode="auto", **expected):
        f = next(f for f in inventory if f["ticker"] == ticker and f["period_end"].startswith(str(year)))
        cases.append({"id": identity, "status": "ok", **expected, "input": {
            "ticker": ticker, "accession": f["accession"], "scope": "consolidated",
            "value_period_end": f["period_end"], "period_kind": kind, "mode": mode, "question": question}})

    for ticker, values in COUNTS.items():
        company = "Apple" if ticker == "AAPL" else "Microsoft"
        for year, count in enumerate(values, 2021):
            add(f"{ticker}-{year}-employees", ticker, year,
                f"How many total employees did {company} have at the end of FY{year}?",
                count=count, basis="full-time equivalent employees" if ticker == "AAPL" else "full-time employees")
    add("CSCO-2024-employees", "CSCO", 2024, "how many total employees in cisco as of july 2024",
        count=90400, basis="employees")
    add("AAPL-2025-assets", "AAPL", 2025, "What were Apple's total assets as of September 27, 2025?",
        kind="instant", numbers=[["359241000000", "USD"]])
    add("MSFT-2025-assets", "MSFT", 2025, "What were Microsoft's total assets as of June 30, 2025?",
        kind="instant", numbers=[["619003000000", "USD"]])
    add("AAPL-2021-margin-relative", "AAPL", 2021,
        "By what percentage did Apple's gross margin increase from FY2020 to FY2021?",
        numbers=[["9.2749429047", "percent"]])
    add("AAPL-2021-margin-points", "AAPL", 2021,
        "By how many percentage points did Apple's gross margin increase from FY2020 to FY2021?",
        numbers=[["3.5461118974", "percentage points"]])
    add("AAPL-2025-iphone-sales", "AAPL", 2025, "How much revenue did Apple report from iPhone in FY2025?",
        disclosed_value="209586000000", disclosed_unit="USD")
    add("AAPL-2025-revenue-income", "AAPL", 2025, "What were Apple's revenue and net income in FY2025?",
        numbers=[["416161000000", "USD"], ["112010000000", "USD"]])
    add("MSFT-2025-revenue-income", "MSFT", 2025, "What were Microsoft's revenue and net income in FY2025?",
        numbers=[["281724000000", "USD"], ["101832000000", "USD"]])
    add("MSFT-2025-azure-dollars", "MSFT", 2025, "How much revenue did Microsoft report from Azure in FY2025?",
        status="insufficient_evidence")
    add("AAPL-2025-count-wrong-date", "AAPL", 2025, "How many employees did Apple have as of September 29, 2025?",
        status="insufficient_evidence")
    add("MSFT-2025-offices", "MSFT", 2025, "How many offices did Microsoft have worldwide at the end of FY2025?",
        status="insufficient_evidence")
    add("MSFT-2025-wrong-company", "MSFT", 2025, "What was Apple's revenue in FY2025?", status="invalid_request")
    add("AAPL-2021-supply", "AAPL", 2021,
        "Why does Apple say obtaining enough components on commercially reasonable terms matters?",
        mode="narrative", answer_pattern=r"components?", source_pattern=r"obtain components|supply|availability")
    add("MSFT-2025-azure-growth", "MSFT", 2025,
        'What growth rate did Microsoft state for "Azure and other cloud services" in FY2025? Cite the filing.',
        mode="narrative", answer_pattern=r"\b34\s*(?:%|percent)", source_pattern=r"Azure and other cloud services.{0,65}34\s*%")
    return cases


def validate(case, result):
    if result["status"] != case["status"]:
        return f"expected {case['status']}, received {result['status']}"
    evidence = result.get("evidence", [])
    if result["status"] != "ok":
        return "refusal carried an answer" if result.get("answer") or evidence else ""
    question = case["input"]
    request = result.get("request", {})
    if any(request.get(key) != question[key] for key in ("ticker", "accession", "value_period_end", "period_kind")):
        return "answer did not bind the selected filing and period"
    if not result.get("answer") or not evidence:
        return "answer or evidence missing"
    if {e["evidence_id"] for e in evidence} != set(result.get("included_evidence_ids", [])):
        return "included source IDs mismatch"
    if any(e["metadata"]["accession"] != question["accession"] for e in evidence):
        return "source outside the selected filing"
    if "numbers" in case:
        calculations = result.get("calculations", [])
        if len(calculations) != len(case["numbers"]):
            return "wrong number of checked calculations"
        for calc, (value, unit) in zip(calculations, case["numbers"], strict=True):
            if calc["unit"] != unit or abs(Decimal(calc["result"]) - Decimal(value)) > Decimal("0.000001"):
                return f"wrong checked value/unit: {calc['result']} {calc['unit']}"
    if "count" in case and not any(
        e["metadata"].get("raw_value") == case["count"] and
        e["metadata"].get("raw_unit") == case["basis"] and
        e["metadata"].get("period_end") == question["value_period_end"]
        for e in evidence
    ):
        return "missing the original dated count and workforce definition"
    if "disclosed_value" in case and not any(
        e["metadata"].get("normalized_value_decimal") == case["disclosed_value"] and
        e["metadata"].get("normalized_unit") == case["disclosed_unit"] and
        e["metadata"].get("period_end") == question["value_period_end"] for e in evidence
    ):
        return "missing the correctly scoped disclosed value"
    if "answer_pattern" in case and (not re.search(case["answer_pattern"], result["answer"], re.I)
        or not any(re.search(case["source_pattern"], e["content"], re.I) for e in evidence)):
        return "expected claim or source passage missing"
    return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:4180/api/answer")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", help="Select exact case IDs; default runs the full set.")
    args = parser.parse_args()
    cases = [c for c in build_cases() if not args.case or c["id"] in args.case]
    if not cases or (args.case and {c["id"] for c in cases} != set(args.case)):
        parser.error("Select existing case IDs")
    token = os.environ.get("FINRAG_DEMO_API_TOKEN")
    headers = {"Authorization": "Bearer " + token} if token else {}
    rows = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with requests.Session() as client:
        for case in cases:
            try:
                result = client.post(args.url, json=case["input"], headers=headers, timeout=245).json()
                problem = validate(case, result)
            except (requests.RequestException, ValueError, KeyError) as exc:
                result, problem = {}, f"request/response error: {type(exc).__name__}"
            rows.append({"case": case, "passed": not problem, "problem": problem, "result": result})
            args.output.write_text(json.dumps(rows, indent=2) + "\n")
            print(case["id"], "PASS" if not problem else problem, flush=True)
    print(f"{sum(r['passed'] for r in rows)}/{len(rows)} passed", flush=True)
    raise SystemExit(0 if all(r["passed"] for r in rows) else 1)


if __name__ == "__main__":
    main()
