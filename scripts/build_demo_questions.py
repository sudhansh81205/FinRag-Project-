"""Build demonstration questions from actual parsed filing facts, without model gold."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.application import FilingOption, resolve_request  # noqa: E402
from src.llm.financial_semantics import known_source_program  # noqa: E402
from src.llm.request_intent import requested_periods  # noqa: E402
from src.llm.typed_calculator import evaluate  # noqa: E402


def build(corpus, output):
    filings = json.loads((ROOT / "data/application_filings.json").read_text())
    questions, cross = [], []
    for f in filings:
        year = int(f["period_end"][:4])
        name = f["issuer"]
        records = json.loads((corpus / "records" / (f["accession"] + ".json")).read_text())["variants"]["C"]["records"]
        option = FilingOption(f["accession"], f["ticker"], name, f["cik"], f["accession"], f["period_end"])
        request, error = resolve_request(f["accession"], f["period_end"], "consolidated", (option,))
        assert not error
        cases = [("Numerical", f"How much revenue did {name} report in FY{year}?"),
                 ("Numerical", f"What was {name}'s net income in FY{year}?"),
                 ("Numerical", f"What was {name}'s gross margin in FY{year}?"),
                 ("Comparison", f"What was {name}'s revenue growth from FY{year-1} to FY{year}?"),
                 ("Straightforward", f"What risks does {name} describe in its FY{year} annual report?"),
                 ("Citation check", f"How much revenue did {name} report in FY{year}? Cite the original statement row, period and units.")]
        for kind, question in cases:
            periods, problem = requested_periods(question, request, records, "duration")
            program = known_source_program(question, {"issuer": name, "scope": "consolidated", "periods": periods}, records) if periods else None
            calc = evaluate(program, records) if program else None
            narrative = kind == "Straightforward"
            if narrative:
                basis = [r for r in records if r["metadata"].get("type") == "narrative_text" and "1A" in r["metadata"].get("section", "")]
                if not basis:
                    basis = [r for r in records if r["metadata"].get("type") == "narrative_text" and "risk" in r["content"].lower()]
                expected = "Explain risks supported by the included Item 1A passages; inspect every cited passage. No fixed model wording."
                ids = [r["evidence_id"] for r in basis[:2]]
                support = "Narrative source present; manually inspect generated answer" if basis else "Insufficient evidence expected"
            elif calc and calc["status"] == "ok":
                expected = f"{calc['result']} {calc['unit']}"
                ids = calc["operand_ids"]
                support = "Source-derived checked result; demo answer must match and cite operands"
            else:
                expected = "Honest insufficient-evidence refusal: " + (problem or (calc or {}).get("message", "No unambiguous original typed source program"))
                ids = []
                support = "Refusal expected; do not invent a result"
            questions.append({"id": f"{f['ticker']}-{year}-{len(questions)+1:03d}", "ticker": f["ticker"],
                "issuer": name, "accession": f["accession"], "period_end": f["period_end"], "type": kind,
                "question": question, "expected": expected, "source_ids": ids, "source_url": f["source_url"],
                "support": support, "cross_filing": False, "mode": "narrative" if narrative else "numerical",
                "basis": "Actual source package and deterministic calculator; not independently approved benchmark gold"})
    for ticker in ("AAPL", "MSFT"):
        group = [f for f in filings if f["ticker"] == ticker]
        first, last = group[0], group[-1]
        cross.append({"ticker": ticker, "question": f"Compare {first['issuer']} total revenue in FY{first['period_end'][:4]} and FY{last['period_end'][:4]}.",
                      "filings": [first["accession"], last["accession"]], "source_urls": [first["source_url"], last["source_url"]],
                      "expected": "Cross-filing question: ask the revenue question separately with each filing selected, then compare the two cited outputs. A single automatic cross-filing answer is not supported.", "cross_filing": True})
    cross.append({"ticker": "AAPL / MSFT", "question": "Compare Apple and Microsoft FY2025 revenue and gross margin.",
                  "filings": [f["accession"] for f in filings if f["ticker"] in {"AAPL", "MSFT"} and f["period_end"].startswith("2025")],
                  "source_urls": [f["source_url"] for f in filings if f["ticker"] in {"AAPL", "MSFT"} and f["period_end"].startswith("2025")],
                  "expected": "Two company selections and separate cited answers are required; automatic multi-company aggregation refuses.", "cross_filing": True})
    result = {"scope": "108 source-derived demonstration questions across all 18 available filings; separate cross-filing exercises are explicitly manual", "filings": filings, "questions": questions, "cross_filing": cross}
    output.mkdir(parents=True, exist_ok=True)
    (output / "sample-questions.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path, default=ROOT / "output/nov17/corpus")
    p.add_argument("--output", type=Path, default=ROOT / "outputs/finrag-final-20261118")
    a = p.parse_args()
    result = build(a.corpus, a.output)
    print(json.dumps({"questions": len(result["questions"]), "filings": len(result["filings"]), "cross_filing_exercises": len(result["cross_filing"]), "source_program_refusals": sum("Refusal expected" in q["support"] for q in result["questions"])}))
