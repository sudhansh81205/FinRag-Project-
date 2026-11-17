"""R7/R12: inventory actual selected inputs; counts never grant acceptance."""
import hashlib
import json
from pathlib import Path

from src.benchmark.loaders import assess_suite_provenance, load_benchmark

FILES = {"FinanceBench": "financebench_open150.json", "FinQA": "finqa_candidate_universe.json",
         "TAT-QA": "tatqa_candidate_universe.json"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ids_digest(ids):
    return hashlib.sha256(json.dumps(sorted(ids), separators=(",", ":")).encode()).hexdigest()


def build_inventory(directory, charts):
    directory, charts = Path(directory), Path(charts)
    report = {"schema_version": 2, "purpose": "actual_selected_case_inventory",
              "independent_acceptance": "pending", "final_experiment_ready": False,
              "benchmarks": {}}
    manifest_path = directory / "import_manifest.json"
    imported = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None
    for name, filename in FILES.items():
        path = directory / filename
        suite = load_benchmark(name, path)
        ids = [case.case_id for case, _ in suite]
        if len(ids) != len(set(ids)) or not ids:
            raise ValueError("Duplicate or empty benchmark case inventory")
        actual = digest(path)
        provenance = assess_suite_provenance(suite)
        if imported and (imported.get("files_sha256", {}).get(filename) != actual
                         or imported.get("counts", {}).get(filename) != len(ids)):
            raise ValueError("Selected data differs from its official import manifest")
        report["benchmarks"][name] = {
            "path": str(path), "file_sha256": actual, "total_cases": len(ids),
            "case_ids": ids, "case_ids_sha256": ids_digest(ids),
            "provenance": provenance,
            "import_manifest_sha256": digest(manifest_path) if imported else None,
            "scope": "complete_imported_public_split" if imported and imported.get("subsets") is False
                     and provenance["full_evaluation_eligible"] else "selected_file_only",
            "exclusions": [], "exclusion_note": "No selected cases excluded; external unreleased scope is not inferred.",
        }
    chart_ids, chart_paths, splits = [], {}, {}
    for split, filename in (("dev", "apple-2021-candidate-questions.json"), ("heldout", "heldout-35-candidate-questions.json")):
        path = charts / filename
        rows = json.loads(path.read_text())
        ids = [row["id"] for row in rows]
        chart_ids.extend(ids)
        splits[split] = len(ids)
        chart_paths[str(path)] = digest(path)
    if len(chart_ids) != len(set(chart_ids)):
        raise ValueError("Duplicate chart case IDs")
    report["benchmarks"]["Charts"] = {"total_cases": len(chart_ids), "case_ids": chart_ids,
        "case_ids_sha256": ids_digest(chart_ids), "files_sha256": chart_paths, "splits": splits,
        "independent_acceptance": "pending", "scope": "authored_candidate_questions"}
    report["total_selected_cases"] = sum(b["total_cases"] for b in report["benchmarks"].values())
    report["primary_variant_queries"] = report["total_selected_cases"] * 7
    return report
