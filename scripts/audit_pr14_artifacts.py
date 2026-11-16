"""Mechanical evidence audit of the submitted PR14 records (Pavan, November 16; R1/R7/R11/R12/R13).

Re-derives what can be re-derived from the repository (hashes, counts, bindings, gate state)
and records everything else as UNVERIFIED or BLOCKED. It never creates a reviewer identity,
an approval, an output or a metric: a hash agreeing with a ledger shows the bytes are unchanged,
not that a human reviewed them or that an answer/caption is true.

Usage: python scripts/audit_pr14_artifacts.py [--write docs/reports/2026-11-16_pavan_evidence_audit.json]
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark.gates import evaluate_gates  # noqa: E402
from src.benchmark.loaders import assess_suite_provenance, load_benchmark  # noqa: E402

REPORTS = ROOT / "docs" / "reports"
checks: list[dict] = []


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str | None:
    return sha_bytes(path.read_bytes()) if path.is_file() else None


def sha_lf(path: Path) -> str | None:
    """SHA-256 after CRLF->LF normalization (Windows checkouts rewrite line endings)."""
    return sha_bytes(path.read_bytes().replace(b"\r\n", b"\n")) if path.is_file() else None


def load(name: str):
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def record(check_id, requirement, status, observed, expected, note=""):
    checks.append({"check_id": check_id, "requirement": requirement, "status": status,
                   "observed": observed, "expected": expected, "note": note})


def audit_fixtures():
    frozen = load("2026-11-15_frozen_manifest.json")["benchmark_data"]
    for name, key in (("FinanceBench", "FinanceBench_Open150"), ("FinQA", "FinQA_Candidate"), ("TAT-QA", "TAT-QA_Candidate")):
        suite = load_benchmark(name)
        prov = assess_suite_provenance(suite)
        entry = frozen[key]
        path = ROOT / entry["path"]
        record(f"F26-{name}-provenance", "R7/R12 F26", "FAIL" if not prov["full_evaluation_eligible"] else "PASS",
               prov, "every record declares official id/version/split/license/source sha256",
               "Generated smoke fixture: quarantine as smoke; full evaluation BLOCKED.")
        record(f"F26-{name}-frozen-hash", "R12", "PASS" if sha_lf(path) == entry["sha256"] or sha_file(path) == entry["sha256"] else "FAIL",
               {"frozen": entry["sha256"], "actual_lf_normalized": sha_lf(path), "actual_raw": sha_file(path)},
               "frozen manifest hash equals current file", "Hash agreement shows unchanged bytes, not authenticity.")
        claimed_subset = entry["is_subset"]
        record(f"F26-{name}-subset-claim", "R7", "FAIL" if (name == "FinanceBench" and claimed_subset is False) else "INFO",
               {"manifest_is_subset": claimed_subset, "records": prov["records"], "classification": prov["classification"]},
               "official full/subset claim must follow actual provenance",
               "The frozen manifest labels the FinanceBench fixture is_subset=false although no record is source-bound."
               if name == "FinanceBench" else "Labelled subset; still synthetic.")


def audit_charts():
    from src.charts.dataset import load_candidate_set, load_reviewed_set

    promo = load("2026-11-15_chart_promotion_report.json")
    ledger_path = REPORTS / "2026-11-15_chart_approvals_ujjwal.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    cases, _manifest, audit = load_candidate_set(ROOT / "data" / "charts")
    by_split: dict[str, set[str]] = {}
    for c in cases:
        by_split.setdefault(c.get("split", "?"), set()).add(c["original_image_group"])
    record("R11-split-counts", "R11", "PASS" if audit["counts"] == {"dev": 15, "heldout": 35} else "FAIL",
           audit["counts"], {"dev": 15, "heldout": 35})
    overlap = sorted(set.intersection(*by_split.values())) if len(by_split) > 1 else []
    record("R11-no-cross-split-image-group", "R11", "PASS" if not overlap else "FAIL",
           {"splits": {k: len(v) for k, v in by_split.items()}, "shared_groups": overlap}, "no image group in two splits")
    unknown = sum(1 for c in cases if "unknown" in json.dumps(c).lower())
    record("R11-unknowns-retained", "R11", "INFO", {"cases_mentioning_unknown": unknown},
           "unprinted/ambiguous values stay unknown", "Not independently judged here.")

    try:
        load_reviewed_set(ROOT / "data" / "charts", ledger_path, trusted_reviewers=[ledger["reviewer_identity"]],
                          label_authors=promo["label_authors"])
        structural = "PASS"
        err = ""
    except Exception as exc:  # noqa: BLE001 - report the exact refusal
        structural, err = "FAIL", str(exc)
    record("R11-ledger-structural-binding", "R11", structural, {"error": err, "decisions": len(ledger["decisions"])},
           "ledger binds the unchanged 50-case set with a non-author reviewer",
           "Structural only: this does not establish that a human viewed the images.")
    actual = sha_file(ledger_path)
    actual_lf = sha_lf(ledger_path)
    recorded = promo.get("approval_sha256")
    record("R11-promotion-report-matches-ledger", "R11", "PASS" if recorded in {actual, actual_lf} else "FAIL",
           {"report_approval_sha256": recorded, "ledger_sha256_raw": actual, "ledger_sha256_lf": actual_lf},
           "promotion report hash equals the current ledger bytes",
           "A stale or mismatched hash means the report does not describe the ledger now on disk.")
    bases = [d.get("basis", "") for d in ledger["decisions"]]
    times = {ledger["reviewed_at"]}
    record("R11-human-review-authenticity", "R11", "UNVERIFIED",
           {"reviewer_identity": ledger["reviewer_identity"], "reviewed_at": ledger["reviewed_at"],
            "decisions": len(bases), "passed": sum(d["decision"] == "passed" for d in ledger["decisions"]),
            "rejected": sum(d["decision"] == "rejected" for d in ledger["decisions"]), "distinct_review_timestamps": len(times),
            "distinct_basis_texts": len(set(bases)), "label_authors": promo["label_authors"]},
           "real reviewer identity/time/basis, a plausible rejection rate, per-case timing",
           "50/50 passed, 0 rejected, one timestamp. Authenticity cannot be certified from the file; captions "
           "and G execution are not covered; reviewer must confirm in person.")


def audit_corpus():
    audit = load("2026-11-15_corpus_audit.json")
    registry = {r["accession"]: r for r in json.loads((ROOT / "data" / "application_filings.json").read_text(encoding="utf-8"))}
    profiles = json.loads((ROOT / "data" / "corpus_html_profiles.json").read_text(encoding="utf-8"))
    present = missing = mismatched = 0
    copied = 0
    identity_problems = []
    for f in audit["filing_audits"]:
        reg = registry.get(f["accession"])
        if reg is None or (reg["ticker"], reg["period_end"]) != (f["ticker"], f["period_end"]):
            identity_problems.append(f["accession"])
        path = ROOT / reg["rendition_path"] if reg else None
        actual = sha_file(path) if path else None
        if actual is None:
            missing += 1
        elif actual == reg["rendition_sha256"]:
            present += 1
        else:
            mismatched += 1
        if profiles.get(f["accession"], {}).get("sha256") == f["rehashed_source_sha256"] == f["profile_sha256"]:
            copied += 1
    n = len(audit["filing_audits"])
    record("R1-registry-identity", "R1", "PASS" if not identity_problems else "FAIL",
           {"filings": n, "mismatches": identity_problems}, "audit tuples equal data/application_filings.json")
    record("R1-source-bytes-reverified-here", "R1", "BLOCKED" if missing else ("PASS" if not mismatched else "FAIL"),
           {"rendition_present_and_matching": present, "rendition_missing_locally": missing, "rendition_hash_mismatch": mismatched},
           "re-hash every source rendition from this checkout",
           "data/raw/ is untracked; missing sources cannot be re-verified here.")
    record("R1-rehash-vs-profile", "R1", "INFO", {"entries_where_rehash_equals_profile_sha": copied, "of": n},
           "independent rehash of source bytes",
           "The audit's rehashed value equals the stored profile hash for these entries; vectors, rows, "
           "parent mappings and counts are copied from earlier ledgers and not reopened.")
    ibm = next((f for f in audit["filing_audits"] if f["ticker"] == "IBM"), None)
    record("R1-IBM-exhibit-identity", "R1", "UNVERIFIED", {"entry_present": ibm is not None,
           "has_exhibit_field": bool(ibm and "exhibit" in json.dumps(ibm).lower())},
           "explicit IBM exhibit identity check", "No separate exhibit identity check is recorded in the ledger.")
    record("R1-acceptance-status", "R1/R2", "UNVERIFIED", {"status": audit["status"],
           "accepted_filings_claimed": n}, "independent human acceptance of 18 filings",
           "Status 'ai_assisted_accepted' is not independent human acceptance; one accepted Apple filing remains the verified scope.")


def audit_freeze_and_status():
    frozen = load("2026-11-15_frozen_manifest.json")
    status = load("2026-11-16_run_status.json")
    gates = evaluate_gates()
    open_gates = sorted(g for g, v in gates.items() if v["open"])
    record("F34-gates-from-actual-artifacts", "R12/R13", "PASS" if not open_gates else "INFO",
           {"open_gates": open_gates, "closed": sorted(set(gates) - set(open_gates))},
           "gates open only with bound artifacts + acceptance record", gates["bm25_index"]["reasons"][0])
    claims = {v["gate_status"] for v in status["variants"].values()}
    record("F34-run-status-gate-claims", "R12", "FAIL" if "unlocked" in claims and not open_gates else "PASS",
           {"claimed_gate_status": sorted(claims), "actual_open_gates": open_gates,
            "completed_cells": status["summary"]["completed"], "blocked_cells": status["summary"]["blocked"],
            "not_started_cells": status["summary"]["not_started"]},
           "A-D 'unlocked'/'ready' claims must match actual adapters/resources and D's bm25_index requirement",
           "Variants A-D are marked unlocked while no gate can be opened from actual artifacts.")
    thresholds = frozen["execution_parameters"]["route_thresholds"]
    record("F34-routing-thresholds-frozen", "R10/R12", "FAIL" if thresholds == "unfrozen" else "PASS",
           {"route_thresholds": thresholds}, "frozen thresholds before F/G")
    record("F34-capacity-estimates", "R13", "FAIL", {"capacity_gate_decision": frozen.get("capacity_gate_decision")},
           "measured cold/warm/evaluator timings with pilot IDs",
           "Frozen snapshot repeats the unmeasured 72h/9.05h assumptions; capacity is unknown, not decided.")
    head, frozen_commit = git("rev-parse", "HEAD"), frozen["git_commit"]
    record("F34-freeze-revision", "R12", "FAIL", {"frozen_git_commit": frozen_commit, "current_head": head,
           "prompt_sha_matches_current": frozen["execution_parameters"]["prompt_template_sha256"] == sha_file(ROOT / "src/llm/prompts.py")},
           "freeze names the exact code revision that will run",
           "A snapshot with unfrozen routing and copied capacity estimates is not a valid final freeze.")


def audit_outputs_and_sample():
    sample = load("2026-11-15_audit_sampling_predeclaration.json")
    fixtures = {}
    for name in ("FinanceBench", "FinQA", "TAT-QA"):
        for case, _ in load_benchmark(name):
            fixtures[case.case_id] = case.question
    in_fixture = [c for c in sample["cases"] if c["case_id"] in fixtures]
    mismatched_text = [c["case_id"] for c in in_fixture if fixtures[c["case_id"]] != c["question_text"]]
    chart_ids = {json.loads(p.read_text(encoding="utf-8"))[i]["id"] for p in
                 [ROOT / "data/charts/apple-2021-candidate-questions.json", ROOT / "data/charts/heldout-35-candidate-questions.json"]
                 for i in range(len(json.loads(p.read_text(encoding="utf-8"))))}
    missing_ids = [c["case_id"] for c in sample["cases"]
                   if c["case_id"] not in fixtures and c["case_id"] not in chart_ids]
    record("R7-sample-size-and-strata", "R7", "PASS" if sample["total_sample_count"] == len(sample["cases"]) == 50 else "FAIL",
           {"total": len(sample["cases"]), "strata": sample["strata_distribution"]}, "50 predeclared pairs")
    record("R7-sample-case-resolution", "R7", "PASS" if not mismatched_text and not missing_ids else "FAIL",
           {"resolved_to_fixtures": len(in_fixture), "question_text_mismatch": mismatched_text, "unresolved": missing_ids},
           "sample pairs resolve to inventoried cases")
    authors = sorted({c["label_author"] for c in sample["cases"]})
    record("R7-label-author-provenance", "R7", "FAIL",
           {"label_authors_recorded": authors, "authorship_conflict_all_false": not any(c["authorship_conflict"] for c in sample["cases"])},
           "authorship validated against real provenance",
           "'FinanceBench/FinQA/TAT-QA Official' is hard-coded for generated fixtures (committed by Gowtham270807 in PR13); "
           "conflict=False is asserted, not derived. Actual authorship of fixtures is the generating team member/tool.")
    record("R7-generated-outputs-available", "R7", "BLOCKED", {"completed_output_cells": 0, "audit_pairs_with_output": 0,
           "required": 50}, "independent audit of 50 generated outputs",
           "Zero completed outputs exist (PR14 run status). No audit decision, metric or interval can be produced; "
           "shortfall is 50 of 50.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", default=None, help="Write the JSON ledger to this path.")
    args = parser.parse_args()
    audit_fixtures()
    audit_charts()
    audit_corpus()
    audit_freeze_and_status()
    audit_outputs_and_sample()
    counts: dict[str, int] = {}
    for c in checks:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    report = {
        "schema_version": 1,
        "report_type": "pr14_evidence_audit",
        "auditor_role": "Pavan November 16 sole owner (automated re-derivation; no human approval implied)",
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": {"head": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                       "pr14_head_in_history": subprocess.run(
                           ["git", "merge-base", "--is-ancestor", "8927378d59983c4c5bc85c7fb14398c8d8896890", "HEAD"],
                           cwd=ROOT).returncode == 0},
        "counts": counts,
        "checks": checks,
        "policy": "PASS only for mechanically re-derived facts; human identity/approval, captions, outputs and metrics "
                  "are UNVERIFIED or BLOCKED and are never synthesized.",
    }
    text = json.dumps(report, indent=2)
    if args.write:
        Path(args.write).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
