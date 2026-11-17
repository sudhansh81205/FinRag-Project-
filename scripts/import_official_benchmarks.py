"""Import complete hash-pinned publisher test splits; generated fixtures stay separate."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmark.importers import SOURCES, bind_financebench_pages, import_official, source_url  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True,
                        help="Canonical local resource folder containing the four pinned publisher files")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/benchmarks/official")
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--financebench-pages", type=Path,
                        help="Attach all verified full-document pages after their independent restore step")
    args = parser.parse_args()
    if args.list_sources:
        print(json.dumps({name: {**spec, "url": source_url(spec)} for name, spec in SOURCES.items()}, indent=2))
        return
    result = import_official(args.source_dir, args.output_dir)
    if args.financebench_pages:
        result["full_document_binding"] = bind_financebench_pages(
            args.output_dir / "financebench_open150.json", args.financebench_pages,
            args.output_dir / "financebench_full_document_150.json")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
