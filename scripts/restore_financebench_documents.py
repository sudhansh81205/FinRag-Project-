"""R7/R13: restore all declared full PDFs, verify publisher Git blobs, prepare all pages.

Use a canonical course-resource directory. Restarts reuse matching documents;
changed files are refused. Selected gold pages never define this retrieval corpus.
"""

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

INVENTORY = ROOT / "data/contracts/financebench_documents.json"
REVISION = "cc39aeb4afdf33909ee1412188bf89035950c2eb"


def verify_document(data, spec):
    if len(data) != spec["size"] or not data.startswith(b"%PDF"):
        raise ValueError("PDF format/size differs from the pinned official inventory")
    blob = b"blob " + str(len(data)).encode() + b"\x00" + data
    if hashlib.sha1(blob).hexdigest() != spec["sha"]:
        raise ValueError("Publisher Git blob checksum mismatch")
    return hashlib.sha256(data).hexdigest()


def restore_one(spec, directory, download):
    rel = Path(spec["path"])
    if len(rel.parts) != 2 or rel.parts[0] != "pdfs" or rel.suffix != ".pdf":
        raise ValueError("Inventory entry is outside the official PDF directory")
    target = directory / rel.name
    url = f"https://raw.githubusercontent.com/patronus-ai/financebench/{REVISION}/{rel.as_posix()}"
    result = {"doc_name": rel.stem, "filename": rel.name, "source_url": url,
              "git_blob_sha": spec["sha"], "status": "missing"}
    try:
        if target.is_file():
            data = target.read_bytes()
        elif not download:
            return result
        else:
            for attempt in range(3):
                try:
                    response = requests.get(url, timeout=(10, 45))
                    response.raise_for_status()
                    data = response.content
                    break
                except requests.RequestException:
                    if attempt == 2:
                        raise
        digest = verify_document(data, spec)
        if not target.exists():
            temporary = target.with_suffix(".pdf.part")
            temporary.write_bytes(data)
            temporary.replace(target)
        result.update(status="source_bytes_verified", sha256=digest, bytes=len(data))
    except (OSError, ValueError, requests.RequestException) as exc:
        result.update(status="failed", error=type(exc).__name__)
    return result


def restore(directory, *, download=False, output_dir=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    inventory = json.loads(INVENTORY.read_bytes())
    if inventory["repository"] != "patronus-ai/financebench" or inventory["revision"] != REVISION:
        raise ValueError("Inventory publisher/revision differs from the pinned official source")
    rows = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(restore_one, spec, directory, download) for spec in inventory["files"]]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(f"{len(rows)}/{len(futures)} {row['doc_name']}: {row['status']}", flush=True)
    rows.sort(key=lambda r: r["doc_name"])
    manifest = {"repository": inventory["repository"], "revision": REVISION,
                "selection": inventory["selection"], "required_documents": len(inventory["files"]),
                "verified_documents": sum(r["status"] == "source_bytes_verified" for r in rows),
                "documents": rows, "independent_acceptance": "pending"}
    (directory / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        contexts, failures = [], []
        for row in rows:
            if row["status"] != "source_bytes_verified":
                failures.append({"doc_name": row["doc_name"], "reason": row["status"]})
                continue
            try:
                reader = PdfReader(directory / row["filename"])
                for index, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    contexts.append({"evidence_id": f"FinanceBench:{row['doc_name']}:page:{index}",
                                     "doc_name": row["doc_name"], "page_index": index,
                                     "text": text, "source_sha256": row["sha256"],
                                     "source_url": row["source_url"], "readable": bool(text.strip())})
            except Exception as exc:
                failures.append({"doc_name": row["doc_name"], "reason": type(exc).__name__})
        payload = (json.dumps(contexts, ensure_ascii=False) + "\n").encode()
        (output_dir / "financebench_full_pages.json").write_bytes(payload)
        corpus_manifest = {"source_manifest_sha256": hashlib.sha256((directory / "source-manifest.json").read_bytes()).hexdigest(),
                           "corpus_sha256": hashlib.sha256(payload).hexdigest(),
                           "document_count": len({c["doc_name"] for c in contexts}),
                           "page_count": len(contexts), "unreadable_pages": sum(not c["readable"] for c in contexts),
                           "failures": failures, "gold_selected_pages_used": False,
                           "context_universe": inventory["selection"], "final_experiment_ready": False}
        (output_dir / "financebench_context_manifest.json").write_text(json.dumps(corpus_manifest, indent=2) + "\n")
        manifest["context_preparation"] = corpus_manifest
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--prepare-contexts", type=Path)
    args = parser.parse_args()
    report = restore(args.directory, download=args.download, output_dir=args.prepare_contexts)
    print(json.dumps({k: v for k, v in report.items() if k != "documents"}, indent=2))
    return int(report["verified_documents"] != report["required_documents"]
               or bool(report.get("context_preparation", {}).get("failures")))


if __name__ == "__main__":
    raise SystemExit(main())
