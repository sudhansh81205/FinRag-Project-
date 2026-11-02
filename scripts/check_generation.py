"""Live Day 3 generation/failure checks with a small source-checked fixture.

No Chroma/embedding model is required. This does not measure retrieval quality or
run the held-out evaluation. Credentials come only from load_settings().
"""

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import PROJECT_ROOT, load_settings
from src.llm.client import UnifiedLLMClient
from src.pipeline.finrag_engine import FinRAGEngine
from src.retrieval.reranker import SimpleFinancialReranker


class FixtureRetriever:
    def __init__(self, records):
        self.records = records

    def retrieve(self, **kwargs):
        return {"text_evidence": [], "table_evidence": self.records}


class CountingClient:
    def __init__(self, client):
        self.client = client
        self.provider = client.provider
        self.model = client.model
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        return self.client.generate(prompt)


def check_generation(settings):
    if settings.provider not in {"gemini", "ollama"} or not settings.model:
        raise ValueError("Configure a real FINRAG_PROVIDER and FINRAG_MODEL before this check.")
    fixture = json.loads((PROJECT_ROOT / "tests/fixtures/provider_services_row.json").read_text())
    client = CountingClient(UnifiedLLMClient.from_settings(settings))

    def run(records, provider):
        return FinRAGEngine(FixtureRetriever(records), SimpleFinancialReranker(), provider).answer_financial_question(fixture["question"])

    live = run(fixture["records"], client)
    calls_before = client.calls
    empty = run([], client)
    no_call_for_empty = client.calls == calls_before
    if settings.provider == "gemini":
        failed_settings = replace(settings, gemini_api_key="deliberately-invalid-test-key")
        failure_kind = "live invalid credential"
    else:
        failed_settings = replace(settings, model="finrag-deliberately-missing-model:invalid")
        failure_kind = "live nonexistent Ollama model (Ollama does not require an API key)"
    failure = run(fixture["records"], UnifiedLLMClient.from_settings(failed_settings))
    normalized = live["answer"].replace(",", "").lower()
    checks = {
        "real_provider_answer": live["status"] == "ok" and live["provider"] in {"gemini", "ollama"},
        "fixture_value_period_unit": all(s in normalized for s in ["68425", "2021", "million"]),
        "empty_evidence_abstains": empty["status"] == "insufficient_evidence" and not empty["answer"],
        "empty_evidence_skips_provider": no_call_for_empty,
        "provider_failure_no_answer": failure["status"] == "service_error" and not failure["answer"],
    }
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    return {
        "executed_at": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        "base_or_current_revision": revision,
        "scope": "Provider and answer-boundary smoke check with manually transcribed SEC row; no index, final evaluation or citation audit.",
        "provider": settings.provider, "configured_model": settings.model,
        "source_url": fixture["source_url"], "source_location": fixture["source_location"],
        "failure_kind": failure_kind, "checks": checks,
        "passed": all(checks.values()), "live_answer": live,
        "empty_evidence": empty, "deliberate_provider_failure": failure,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON evidence record (contains no key).")
    args = parser.parse_args()
    try:
        report = check_generation(load_settings())
    except Exception:
        parser.exit(2, "Provider check could not start; check configuration and dependencies. No credentials were printed.\n")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "provider": report["provider"],
                      "model": report["configured_model"], "checks": report["checks"]}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
