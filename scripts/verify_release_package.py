"""Verify the final release package and generate/check cryptographic manifests.

Usage:
    python scripts/verify_release_package.py [--write-manifest]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_RELEASE_FILES = [
    "docs/reports/2026-11-17_final_report.md",
    "docs/reports/2026-11-17_slides.md",
    "docs/reports/2026-11-17_final_slides.pptx",
    "docs/reports/2026-11-17_backup_demo_walkthrough.md",
    "docs/reports/2026-11-17_independent_audit_reconciliation.json",
    "docs/reports/2026-11-17_sudhansh_completion.md",
    "docs/reports/2026-11-17_submission_acknowledgement.json",
    "docs/handoffs/2026-11-17_sudhansh.md",
    "scripts/build_final_slides.py",
]

CORE_SOURCE_FILES = [
    "app.py",
    "src/application.py",
    "src/pipeline/experiment_scaffold.py",
    "src/llm/typed_calculator.py",
    "src/benchmark/metrics.py",
    "src/benchmark/runner.py",
    "src/benchmark/gates.py",
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
    with manifest_path.open("r", encoding="utf-8") as f:
        recorded = json.load(f)

    mismatches: list[str] = []
    for rel_path, expected_hash in recorded.get("file_hashes", {}).items():
        p = ROOT / rel_path
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
            "release": "FinRAG November 17 Final Release",
            "release_owner": "Sudhansh Khandelwal",
            "release_designation": "TRANSPARENTLY PARTIAL REPRODUCIBLE PACKAGE",
            "date": "2026-11-17",
            "file_count": len(file_hashes),
            "file_hashes": file_hashes,
        }
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            f.write("\n")
        print(f"Manifest written to {manifest_path} with {len(file_hashes)} entries.")

    if manifest_path.is_file():
        ok, mismatches = verify_manifest(manifest_path)
        if not ok:
            print("Manifest verification FAILED:")
            for m in mismatches:
                print(f"  - {m}")
            return 1
        print("Manifest verification: SUCCESS (all cryptographic digests match).")

    print("Release package verification: ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
