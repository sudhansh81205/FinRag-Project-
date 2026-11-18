"""Extract an explicitly dated company-wide employee count from a pinned filing."""

import gzip
import re
from datetime import date
from hashlib import sha256

from src.ingestion.corpus import (
    body_blocks,
    open_html,
    parse_date,
    section_bounds,
    validate_identity,
)
from src.ingestion.filing_parser import clean_text, locator

HEADCOUNT = re.compile(
    r"^As of (?P<date>[A-Za-z]+\s+\d{1,2},\s+\d{4}),\s+"
    r"(?:we|the company) (?:had|employed) (?P<approx>approximately |about )?"
    r"(?P<count>[0-9]+(?:,[0-9]{3})*) employees"
    r"(?=\.|$| worldwide\b| and they are categorized as follows:)", re.I,
)


def headcount_evidence(root, filing, profile, period_end):
    """Return a unique, directly stated unqualified count for the selected instant."""
    accession = filing["accession"]
    source_file = f"data/source/corpus/{accession}.html.gz"
    raw = gzip.decompress((root / source_file).read_bytes())
    soup = open_html(raw, profile["sha256"])
    validate_identity(soup, filing)
    blocks = body_blocks(soup)
    bounds = profile.get("block_ranges")
    if bounds is None:
        bounds = section_bounds(blocks, profile, absent={"Item 7", "Item 8"} if profile.get("exhibit") else ())
    matches = []
    for node in blocks[:bounds["Item 1A"][0]]:
        text = clean_text(node)
        match = HEADCOUNT.match(text)
        if match and parse_date(match["date"]) == date.fromisoformat(period_end):
            matches.append((node, text, match))
    if len(matches) != 1:
        return None

    node, text, match = matches[0]
    digest = sha256(text.encode()).hexdigest()
    location = locator(node)
    identity = sha256(location.encode()).hexdigest()[:12]
    return {
        "evidence_id": f"{accession}:item1:employee_headcount:{identity}:{digest[:16]}",
        "content": text,
        "metadata": {
            "type": "narrative_text", "metric": "Employee headcount", "section": "Item 1",
            "accession": accession, "ticker": filing["ticker"], "company": filing["issuer"],
            "scope": "consolidated", "period_kind": "instant", "period_end": period_end,
            "raw_unit": "employees", "raw_value": int(match["count"].replace(",", "")),
            "approximate": match["approx"] is not None, "source_file": source_file,
            "source_locator": location, "source_sha256": profile["sha256"], "content_sha256": digest,
            "source_url": filing["source_url"],
        },
    }
