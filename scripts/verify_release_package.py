"""Verify the final release package and generate/check cryptographic manifests.

Usage:
    python scripts/verify_release_package.py [--write-manifest]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_RELEASE_FILES = [
    "docs/reports/2026-11-17_final_report.md",
    "docs/reports/2026-11-17_slides.md",
    "docs/reports/2026-11-17_verified_slides.pptx",
    "docs/reports/2026-11-17_runtime-verification.json",
    "docs/handoffs/2026-11-17_runtime-completion.md",
    "docs/reports/2026-11-17_backup_demo_walkthrough.md",
    "docs/reports/2026-11-17_independent_audit_reconciliation.json",
    "docs/reports/2026-11-17_sudhansh_completion.md",
    "docs/reports/2026-11-17_submission_acknowledgement.json",
    "docs/handoffs/2026-11-17_sudhansh.md",
    "scripts/build_final_slides.py",
]

CORE_SOURCE_FILES = [
    "START_HERE.txt",
    "ATTRIBUTION.md",
    "docs/SETUP.md",
    "docs/FINAL_CHECKPOINT.md",
    "scripts/check_project_readiness.py",
    "scripts/check_experiment_acceptance.py",
    "scripts/build_demo_questions.py",
    "web/data/project-status.json",
    "web/tests/saved-persistence.test.mjs",
    "docs/reports/2026-11-18_final-completion.md",
    "docs/review/final-input-review/index.html",
    "docs/review/final-input-review/review-marks-template.json",
    "outputs/finrag-final-20261118/FinRAG_Sample_Questions.xlsx",
    "outputs/finrag-final-20261118/FinRAG_Demonstration_Questions.pdf",
    "outputs/finrag-final-20261118/sample-questions.json",
    "docs/reports/2026-11-18-functional-checks/production.json",
    "docs/reports/2026-11-18-functional-checks/deployment.json",
    "src/llm/request_intent.py",
    "tests/test_request_intent.py",
    "docs/reports/2026-11-18_functional-repair.md",
    "docs/reports/2026-11-18-functional-checks/live-core.json",
    "docs/reports/2026-11-18-functional-checks/saved-isolation.json",
    "docs/reports/2026-11-18-functional-checks/pytest.txt",
    "docs/reports/2026-11-18-functional-checks/node.txt",
    "docs/reports/2026-11-18-checks/hosted-limited-verification.json",
    "docs/reports/2026-11-18-checks/limited-pytest.txt",
    "docs/reports/2026-11-18-checks/limited-node.txt",
    "src/workspace_corpus.py",
    "web/data/filings.json",
    "docs/reports/2026-11-18_limited-workspace.md",
    "docs/reports/2026-11-18-checks/limited-live.json",
    ".gitattributes",
    "completion_status.md",
    "docs/reports/2026-11-18_code-review.md",
    "docs/handoffs/2026-11-18_manual-workspace.md",
    "src/charts/approval.py",
    "src/retrieval/cross_encoder.py",
    "src/retrieval/variants.py",
    "scripts/build_web_review_assets.py",
    "scripts/prepare_reranker.py",
    "tests/test_additional_variants.py",
    "tests/test_manual_workspace.py",
    "web/dev.mjs",
    "web/public/review/charts.json",
    "web/public/review/review-marks-template.json",
    "web/public/review/ad0ded84e0a5b9dbf96385d1debb0cf711f6f1bec501dda9c067091526dd83a9.jpg",
    "web/public/review/41716e31eeb23fe0a516c2fb510c56ea5fa400fddf25a8c8310f8acd921f9e5a.png",
    "web/public/review/a64c086a9af2be3b7aa2a0a69177acc2dd73b64fadedda64c6cc86cc4ca729e0.jpg",
    "web/public/review/3642d2aa1cafa2bf25997038d695b2444169d4737f3d14a8a539b281259a7568.jpg",
    "web/public/review/00a0413e774c92f87057747c8cfa9aa0fbaf8da5d952666fa9e84b94a3980098.png",
    "web/public/review/18b7538a6a3bb7b25dbab03a1b764a17a0d52941feba6f1ef157b34a37c3bb97.png",
    "docs/reports/2026-11-18_deployment-receipt.json",
    "docs/reports/2026-11-17-deployment/https-gateway.json",
    "docs/reports/2026-11-17-deployment/https-gateway-initial-failure.json",
    "README.md",
    "web/README.md",
    "docs/reports/2026-11-15_frozen_manifest.json",
    "docs/reports/2026-11-17_code-review.md",
    "docs/handoffs/2026-11-17_deployment-review.md",
    "docs/reports/2026-11-17-deployment/pytest.txt",
    "docs/reports/2026-11-17-deployment/node.txt",
    "docs/reports/2026-11-17-deployment/ruff.txt",
    "src/web_jobs.py",
    "src/benchmark/inventory.py",
    "src/benchmark/runtime.py",
    "src/benchmark/capacity.py",
    "scripts/freeze_controls_manifest.py",
    "scripts/generate_case_inventory.py",
    "tests/test_web_jobs.py",
    "tests/test_live_inventory.py",
    "tests/test_benchmark_runtime.py",
    "tests/test_nov16_runner_capacity_gates.py",

    ".github/workflows/ci.yml",
    "scripts/run_local_workspace.py",
    "tests/test_local_workspace.py",
    "docs/reports/2026-11-17-runtime/launcher-tests.txt",
    "docs/reports/2026-11-17-runtime/ruff.txt",
    "docs/reports/2026-11-17-runtime/pytest.txt",
    "docs/reports/2026-11-17-runtime/official-import-manifest.json",
    "docs/reports/2026-11-17-runtime/live-generation.json",
    "docs/reports/2026-11-17-runtime/focused-tests.txt",
    "docs/reports/2026-11-17-runtime/financebench-context-manifest.json",
    "docs/reports/2026-11-17-runtime/financebench-binding.json",
    "docs/reports/2026-11-17-runtime/corpus-reproduction.json",
    "docs/reports/2026-11-17-runtime/corpus-coverage.json",
    "docs/reports/2026-11-17-runtime/canonical_audit.json",
    "docs/reports/2026-11-17-runtime/browser-margin-corrected.json",
    "docs/reports/2026-11-17-runtime/api-narrative.json",
    "web/tests/api.test.mjs",
    "tests/test_web_api.py",
    "tests/test_named_financial_formulas.py",
    "tests/test_generator_token_budget.py",
    "tests/test_official_benchmark_import.py",
    "web/dev.mjs",
    "data/contracts/financebench_documents.json",
    "scripts/prepare_independent_review.py",
    "scripts/restore_financebench_documents.py",
    "scripts/import_official_benchmarks.py",
    "scripts/generate_chart_approvals.py",
    "scripts/audit_corpus_candidates.py",
    "src/benchmark/importers.py",
    "src/retrieval/eligibility.py",
    "src/pipeline/finrag_engine.py",
    "src/llm/token_budget.py",
    "src/llm/financial_semantics.py",
    "src/llm/calculation_planner.py",
    "src/indexing/store.py",
    "src/indexing/bge.py",
    "app.py",
    "src/application.py",
    "src/pipeline/experiment_scaffold.py",
    "src/llm/typed_calculator.py",
    "src/benchmark/metrics.py",
    "src/benchmark/loaders.py",
    "scripts/run_benchmarks.py",
    "src/benchmark/runner.py",
    "src/benchmark/gates.py",
    "scripts/verify_release_package.py",
    "scripts/serve_web_api.py",
    "scripts/preflight_handoff.py",
    "scripts/check_handoff.py",
    "scripts/run_rushil_checks.py",
    "src/runtime_support.py",
    "src/indexing/bge.py",
    "tests/test_runtime_completion.py",
    "src/web_api.py",
    "web/public/index.html",
    "web/public/app.js",
    "web/public/style.css",
    "web/public/mark.svg",
    "web/public/fonts/geist-sans.woff2",
    "web/public/fonts/geist-mono.woff2",
    "web/api/index.mjs",
    "web/lib/api.mjs",
    "web/data/filings.json",
    "web/package.json",
    "web/vercel.json",
    "supabase/schema.sql",
    "supabase/migrations/20261116194117_finrag_private_saved_queries.sql",
    "web/public/fonts/LICENSE-geist-sans.txt",
    "web/public/fonts/LICENSE-geist-mono.txt",
    "supabase/verify_rls.sql",
]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest() -> dict[str, str]:
    manifest: dict[str, str] = {}
    all_files = sorted(set(CRITICAL_RELEASE_FILES + CORE_SOURCE_FILES))
    for rel_path in all_files:
        p = ROOT / rel_path
        if not p.is_file():
            raise FileNotFoundError(f"Missing required release file: {rel_path}")
        manifest[rel_path.replace("\\", "/")] = sha256_of_file(p)
    return manifest


def verify_manifest(manifest_path: Path) -> tuple[bool, list[str]]:
    if not manifest_path.is_file():
        return False, [f"Manifest file missing: {manifest_path}"]
    try:
        recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, ["Manifest must be readable JSON."]
    if not isinstance(recorded, dict) or not isinstance(recorded.get("file_hashes"), dict):
        return False, ["Manifest lacks a file_hashes object."]
    expected_files = set(CRITICAL_RELEASE_FILES + CORE_SOURCE_FILES)
    hashes = recorded["file_hashes"]
    if set(hashes) != expected_files or type(recorded.get("file_count")) is not int or recorded["file_count"] != len(expected_files):
        return False, ["Manifest inventory/count differs from the required release files."]

    mismatches: list[str] = []
    for rel_path, expected_hash in hashes.items():
        if (PurePosixPath(rel_path).is_absolute() or ".." in PurePosixPath(rel_path).parts
                or "\\" in rel_path or ":" in rel_path
                or not isinstance(expected_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_hash)):
            mismatches.append(f"Invalid path/digest: {rel_path}")
            continue
        p = ROOT / rel_path
        if not p.resolve().is_relative_to(ROOT.resolve()):
            mismatches.append(f"File escapes release root: {rel_path}")
            continue
        if not p.is_file():
            mismatches.append(f"Missing file: {rel_path}")
            continue
        actual_hash = sha256_of_file(p)
        if actual_hash != expected_hash:
            mismatches.append(f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
    return len(mismatches) == 0, mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify FinRAG final release package.")
    parser.add_argument("--write-manifest", action="store_true", help="Generate and write release manifest")
    args = parser.parse_args()

    manifest_path = ROOT / "docs" / "reports" / "2026-11-17_release_manifest.json"

    print("Verifying critical release files exist...")
    for rel in CRITICAL_RELEASE_FILES:
        p = ROOT / rel
        if not p.is_file():
            print(f"FAILED: Missing file {rel}")
            return 1
        print(f"  [OK] {rel} ({p.stat().st_size} bytes)")

    if args.write_manifest:
        file_hashes = generate_manifest()
        manifest_data = {
            "release": "FinRAG application delivery and research acceptance status",
            "release_owner": "Sudhansh Khandelwal",
            "release_designation": "TRANSPARENTLY PARTIAL REPRODUCIBLE PACKAGE",
            "date": date.today().isoformat(),
            "file_count": len(file_hashes),
            "file_hashes": file_hashes,
        }
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            f.write("\n")
        print(f"Manifest written to {manifest_path} with {len(file_hashes)} entries.")

    ok, mismatches = verify_manifest(manifest_path)
    if not ok:
        print("Manifest verification FAILED:")
        for m in mismatches:
            print(f"  - {m}")
        return 1
    print("Manifest verification: SUCCESS (all required cryptographic digests match).")

    print("Package byte integrity passed; runtime readiness and submission are separate checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
