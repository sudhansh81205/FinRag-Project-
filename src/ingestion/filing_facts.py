"""Verified source disclosures for the interactive workspace."""
import gzip
from datetime import date
from decimal import Decimal
from hashlib import sha256

from src.ingestion.corpus import open_html, typed_fact, validate_identity
from src.ingestion.filing_parser import clean_text, is_hidden, locator
from src.ingestion.statement_cells import period_of


def open_filing(root, filing, profile):
    source_file = f"data/source/corpus/{filing['accession']}.html.gz"
    soup = open_html(gzip.decompress((root / source_file).read_bytes()), profile["sha256"])
    validate_identity(soup, filing)
    return soup, source_file


def iphone_revenue_evidence(root, filing, profile, period_end):
    """Use a visible iPhone row and its one exact iXBRL product dimension."""
    if filing["ticker"] != "AAPL":
        return None
    soup, source_file = open_filing(root, filing, profile)
    ids = {n["id"]: n for n in soup.find_all(id=True)}
    matches = []
    for fact in soup.find_all("ix:nonfraction", attrs={
        "name": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    }):
        context = ids.get(fact.get("contextref"))
        if context is None:
            continue
        members = [(n.get("dimension"), n.get_text(strip=True))
                   for n in context.find_all("xbrldi:explicitmember")]
        if members != [("srt:ProductOrServiceAxis", "aapl:IPhoneMember")]:
            continue
        row = fact.find_parent("tr")
        label = row.find(["td", "th"], recursive=False) if row else None
        if label is None or not clean_text(label).startswith("iPhone") or is_hidden(fact):
            continue
        period = period_of(context)
        if period["period_kind"] != "duration" or period["period_end"] != period_end:
            continue
        if not 350 <= (date.fromisoformat(period_end) - date.fromisoformat(period["period_start"])).days <= 380:
            continue
        raw = clean_text(fact)
        meta = typed_fact(fact, ids, raw, date.fromisoformat(period_end), "iPhone", filing["cik"])
        if meta["unit"] == "USD" and Decimal(meta["normalized_value"]) > 0:
            matches.append((fact, raw, meta))
    if len(matches) != 1:
        return None

    fact, raw, meta = matches[0]
    value = meta["normalized_value"]
    location = locator(fact)
    source_id = sha256(location.encode()).hexdigest()[:12]
    content = f"iPhone net sales for the fiscal year ended {period_end}: {Decimal(value):,} USD (displayed as {raw})."
    return {
        "evidence_id": f"{filing['accession']}:item8:iphone_net_sales:{source_id}",
        "metadata": {
            "type": "table_cell", "row_headers": ["iPhone"], "metric": "iPhone net sales",
            "section": "Item 8", "scope": "product", "dimensions": meta["dimensions"],
            "accession": filing["accession"], "ticker": filing["ticker"], "company": filing["issuer"],
            "period_kind": meta["period_kind"], "period_start": meta["period_start"], "period_end": period_end,
            "unit": "USD", "currency": "USD", "raw_value": raw,
            "raw_unit": f"USD (scale 10^{meta['scale_power10']})",
            "normalized_unit": "USD", "normalized_value_decimal": value,
            "source_url": filing["source_url"], "source_file": source_file, "source_locator": location,
            "source_sha256": profile["sha256"], "content_sha256": sha256(content.encode()).hexdigest(),
        },
        "content": content,
    }
