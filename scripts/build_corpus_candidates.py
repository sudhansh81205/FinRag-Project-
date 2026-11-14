"""Build and reopen matched corpus candidates in an isolated review directory."""

import argparse
import gzip
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_index import accepted_input  # noqa: E402
from scripts.parse_filing import json_bytes, write_atomic  # noqa: E402
from src.contracts import sha256  # noqa: E402
from src.evidence_audit import encoded  # noqa: E402
from src.indexing.bge import BGEEncoder, EmbeddingSpec  # noqa: E402
from src.indexing.representations import matched_representations  # noqa: E402
from src.indexing.store import ExactStore, publish_filing, read_generation, validate_records  # noqa: E402
from src.ingestion.corpus import parse_corpus_filing  # noqa: E402

APPLE = "0000320193-21-000105"
VARIANTS = "ABC"


def pinned_source(directory, name, url, digest, download):
    path = directory / name
    archive = ROOT / "data/source/corpus" / (name + ".gz")
    if not path.exists() and archive.is_file():
        raw = gzip.decompress(archive.read_bytes())
        if sha256(raw) != digest:
            raise ValueError(f"Archived source checksum mismatch: {name}")
        return raw
    if not path.exists() and download:
        response = requests.get(
            url,
            timeout=45,
            headers={
                "User-Agent": "FinRAG academic project research contact finrag.research@example.com"
            },
        )
        response.raise_for_status()
        if sha256(response.content) != digest:
            raise ValueError(f"Downloaded source checksum mismatch: {name}")
        write_atomic(path, response.content)
    raw = path.read_bytes()
    if sha256(raw) != digest:
        raise ValueError(f"Local source checksum mismatch: {name}")
    return raw


def prepare(filing, profile, args):
    accession = filing["accession"]
    if accession == APPLE:
        accepted, parents, provenance = accepted_input(args.package, args.audit)
        package = {
            "narrative_blocks": [r for r in accepted if r["metadata"]["type"] == "narrative_text"],
            "cells": [r for r in accepted if r["metadata"]["type"] == "table_cell"],
            "parents": parents,
            "omitted_cells": {},
        }
        return package, {"html": provenance["source_sha256"], "pdf": provenance["pdf_sha256"]}
    source_url = filing["source_url"]
    raw = pinned_source(args.raw, accession + ".html", source_url, profile["sha256"], args.download)
    hashes = {"html": profile["sha256"]}
    exhibit_raw = None
    if exhibit := profile.get("exhibit"):
        exhibit_raw = pinned_source(
            args.raw,
            exhibit["filename"],
            source_url.rsplit("/", 1)[0] + "/" + exhibit["filename"],
            exhibit["sha256"],
            args.download,
        )
        hashes["exhibit_html"] = exhibit["sha256"]
    return parse_corpus_filing(raw, filing, profile, exhibit_raw), hashes


def existing_generation(path, accession, variant, records, parents, provenance):
    catalog = path / "catalog.json"
    if not catalog.is_file():
        return None
    generation = json.loads(catalog.read_bytes())["filings"].get(accession)
    if generation is None:
        return None
    stored, stored_parents, _, _ = read_generation(path, accession, generation, EmbeddingSpec())
    stamp = path / "filings" / accession / generation / "provenance.json"
    if (
        stored != records
        or stored_parents != parents
        or json.loads(stamp.read_bytes())
        != {
            **provenance,
            "variant": variant,
        }
    ):
        raise ValueError(
            "Existing candidate generation has different inputs; use a new output directory"
        )
    return generation


def index_filing(args, accession, variants, get_encoder, provenance):
    built = {
        n: existing_generation(args.output / n, accession, n, rs, ps, provenance)
        for n, (rs, ps) in variants.items()
    }
    if all(built.values()):
        return built
    # Shared B/C narratives and A/B table passages get one identical BGE vector.
    text_ids = {}
    for records, _ in variants.values():
        for r in records:
            text_ids.setdefault(r["content"], len(text_ids))
    vectors = get_encoder().encode(list(text_ids))
    for name, (records, parents) in variants.items():
        if built[name] is not None:
            continue
        result = publish_filing(
            args.output / name,
            records,
            parents,
            vectors[[text_ids[r["content"]] for r in records]],
            {**provenance, "variant": name},
        )
        built[name] = result["generation"]
    return built


def verify_reloaded(args, coverage):
    for name in VARIANTS:
        store = ExactStore(args.output / name)
        expected = {
            row["accession"]: row["generations"][name] for row in coverage if row.get("generations")
        }
        if store.catalog["filings"] != expected:
            raise ValueError(f"Variant {name} catalog disagrees with this run's coverage ledger")
        actual = [record["evidence_id"] for record in store.records]
        expected_ids = [
            r["evidence_id"]
            for accession in sorted(expected)
            for r in json.loads((args.output / "records" / (accession + ".json")).read_bytes())[
                "variants"
            ][name]["records"]
        ]
        if actual != expected_ids:
            raise ValueError(f"Variant {name} reload changed ordered IDs")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/raw/html")
    parser.add_argument("--package", type=Path, default=ROOT / "data/processed/nov04")
    parser.add_argument("--audit", type=Path, default=ROOT / "output/shanay/canonical_audit.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/nov13")
    parser.add_argument("--model-cache", type=Path, default=ROOT / "output/models")
    parser.add_argument(
        "--download", action="store_true", help="Fetch missing pinned SEC source HTML."
    )
    parser.add_argument(
        "--build", action="store_true", help="Build review-only exact indexes with cached BGE."
    )
    parser.add_argument(
        "--accession",
        action="append",
        help="Restrict to selected accession(s) in a separate output directory.",
    )
    args = parser.parse_args(argv)
    filings = json.loads((ROOT / "data/application_filings.json").read_bytes())
    profiles = json.loads((ROOT / "data/corpus_html_profiles.json").read_bytes())
    if args.accession and set(args.accession) - {r["accession"] for r in filings}:
        parser.error("Unknown accession")
    chosen = [r for r in filings if not args.accession or r["accession"] in args.accession]
    accessions = {r["accession"] for r in chosen}
    for variant in VARIANTS:
        catalog = args.output / variant / "catalog.json"
        if catalog.is_file() and set(json.loads(catalog.read_bytes())["filings"]) - accessions:
            parser.error("Output directory contains other accessions; choose a separate directory")
    coverage, prepared = [], []
    schema = sha256((ROOT / "data/contracts/canonical_record.schema.json").read_bytes())
    for filing in chosen:
        accession = filing["accession"]
        row = {
            **{
                k: filing[k]
                for k in ("accession", "ticker", "issuer", "period_end", "filed_date", "source_url")
            },
            "independent_acceptance": "pending",
            "independently_accepted_canonical_records": 0,
            "parsed": False,
            "indexed_for_review": False,
        }
        coverage.append(row)
        profile = profiles.get(accession)
        row["html_present"] = (
            accession == APPLE
            or (args.raw / (accession + ".html")).is_file()
            or (ROOT / "data/source/corpus" / (accession + ".html.gz")).is_file()
        )
        try:
            package, sources = prepare(filing, profile, args)
            row.update(source_sha256=sources, html_present=True)
            variants = matched_representations(
                package["narrative_blocks"], package["parents"], package["cells"]
            )
            for records, parents in variants.values():
                validate_records(records, parents)
            data = {
                "accession": accession,
                "source_sha256": sources,
                "schema_sha256": schema,
                **package,
                "variants": {
                    variant: {"records": rs, "parents": ps}
                    for variant, (rs, ps) in variants.items()
                },
            }
            payload = encoded(data)
            path = args.output / "records" / (accession + ".json")
            if path.exists() and path.read_bytes() != payload:
                raise ValueError("Review records changed; use a new output directory")
            if not path.exists():
                write_atomic(path, payload)
            row.update(
                parsed=True,
                package_sha256=sha256(payload),
                omitted_cells=package["omitted_cells"],
                independently_accepted_canonical_records=535 if accession == APPLE else 0,
                independent_acceptance="canonical_apple_input_only"
                if accession == APPLE
                else "pending",
                candidate_counts={n: len(rs) for n, (rs, _) in variants.items()},
                cells=len(package["cells"]),
                parent_tables=len(package["parents"]),
            )
            prepared.append((row, variants))
        except (
            ValueError,
            KeyError,
            IndexError,
            OSError,
            EOFError,
            requests.RequestException,
        ) as exc:
            row["error"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(
            row["ticker"],
            row["period_end"],
            row.get("error", row.get("candidate_counts")),
            flush=True,
        )

    def save(reload_verified=False):
        write_atomic(
            args.output / "coverage.json",
            json_bytes(
                {
                    "purpose": "independent_review_candidates",
                    "schema_sha256": schema,
                    "reload_order_verified": reload_verified,
                    "declared_filings": len(filings),
                    "filings": coverage,
                    "verified_source_filings": sum("source_sha256" in r for r in coverage),
                    "parsed_filings": sum(r["parsed"] for r in coverage),
                    "candidate_indexed_filings": sum(r["indexed_for_review"] for r in coverage),
                    "candidate_indexed_companies": len(
                        {r["ticker"] for r in coverage if r["indexed_for_review"]}
                    ),
                    "independently_accepted_canonical_filings": sum(
                        r["independent_acceptance"] == "canonical_apple_input_only"
                        for r in coverage
                    ),
                }
            ),
        )

    save()
    if args.build and prepared:
        encoder = None

        def get_encoder():
            nonlocal encoder
            if encoder is None:
                encoder = BGEEncoder(cache_folder=str(args.model_cache), batch_size=24)
            return encoder

        for row, variants in prepared:
            try:
                row["generations"] = index_filing(
                    args,
                    row["accession"],
                    variants,
                    get_encoder,
                    {
                        "candidate_package_sha256": row["package_sha256"],
                        "source_sha256": row["source_sha256"],
                        "schema_sha256": schema,
                        "independent_acceptance": row["independent_acceptance"],
                    },
                )
                row["indexed_for_review"] = True
            except (ValueError, OSError) as exc:
                row["index_error"] = str(exc)
            save()
            print(
                "Index",
                row["ticker"],
                row["period_end"],
                row.get("index_error", "built"),
                flush=True,
            )
        verify_reloaded(args, coverage)
        save(reload_verified=True)
    return int(
        any(not row["parsed"] or (args.build and not row["indexed_for_review"]) for row in coverage)
    )


if __name__ == "__main__":
    raise SystemExit(main())
