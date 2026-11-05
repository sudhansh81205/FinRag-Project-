"""Checked programmatic PDF pages from the pinned Apple 2021 rendition."""

from collections import defaultdict

from docling_parse.pdf_parser import ContentConfig, ContentLevel, DoclingPdfParser
from pypdf import PdfReader

from src.ingestion.filing_parser import ParseError, sha256
from src.ingestion.statement_cells import displayed_amount


def words_on_page(document, page_number):
    words = []
    for word in document.get_page(page_number).word_cells:
        bounds = word.rect.to_bounding_box()
        words.append(
            {
                "text": word.text,
                "bbox": list(bounds.as_tuple()),
                "origin": bounds.coord_origin.value,
            }
        )
    return words


def match_pdf_row(words, row_label, headers):
    # Rows align within a point despite bold versus regular font baselines.
    # Headers on these checked pages are above the data, years on a separate line.
    years = [header[-4:] for header in headers]
    for year in years:
        if not any(w["text"] == year for w in words):
            raise ParseError(f"Missing PDF year header {year}")
    year_words = [
        max((w for w in words if w["text"] == y), key=lambda w: w["bbox"][1]) for y in years
    ]
    centers = [(w["bbox"][0] + w["bbox"][2]) / 2 for w in year_words]
    if (
        centers != sorted(centers)
        or max(w["bbox"][1] for w in year_words) - min(w["bbox"][1] for w in year_words) > 1
    ):
        raise ParseError("Unsupported comparative PDF headers")
    hits = []
    for word in words:
        if word["text"] != row_label.split()[0] or word["bbox"][1] >= year_words[0]["bbox"][1]:
            continue
        line = sorted(
            (w for w in words if abs(w["bbox"][1] - word["bbox"][1]) < 1.2),
            key=lambda w: w["bbox"][0],
        )
        first_col = centers[0] - (centers[1] - centers[0]) / 2
        label = " ".join(w["text"] for w in line if w["bbox"][2] < first_col)
        if label != row_label:
            continue
        groups = [[] for _ in headers]
        for w in line:
            if w["bbox"][2] >= first_col:
                center = (w["bbox"][0] + w["bbox"][2]) / 2
                col = min(range(len(centers)), key=lambda j: abs(centers[j] - center))
                groups[col].append(w)
        hits.append(groups)
    if len(hits) != 1:
        raise ParseError(f"Expected one PDF statement row for {row_label}, found {len(hits)}")
    return hits[0]


def corroborate_pdf(path, spec, records):
    if sha256(path.read_bytes()) != spec["sha256"]:
        raise ParseError("PDF rendition checksum mismatch")
    by_row = defaultdict(list)
    for record in records:
        by_row[record["metadata"]["table_title"], record["metadata"]["row_label"]].append(record)
    parser = DoclingPdfParser(loglevel="fatal")
    pdf = parser.load(
        path,
        content_config=ContentConfig(word_cells_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE),
    )
    checks = []
    try:
        for page in spec["statement_pages"]:
            words = words_on_page(pdf, page["page"])
            text = " ".join(w["text"] for w in words).casefold()
            if page["title"].casefold() not in text or "in millions" not in text:
                raise ParseError("PDF title or unit declaration mismatch")
            for label in page["checked_rows"]:
                html = by_row[page["title"], label]
                if len(html) < 2:
                    raise ParseError(f"Missing comparative HTML evidence for {label}")
                headers = [r["metadata"]["column_header"] for r in html]
                for record, spans in zip(html, match_pdf_row(words, label, headers), strict=True):
                    raw = " ".join(w["text"] for w in spans)
                    cell = record["metadata"]
                    if (
                        not spans
                        or displayed_amount(raw, cell["scale_power10"])
                        != cell["normalized_value_decimal"]
                    ):
                        raise ParseError(
                            f"PDF/HTML disagreement: {label} / {cell['column_header']}"
                        )
                    checks.append(
                        {
                            "canonical_id": record["evidence_id"],
                            "page": page["page"],
                            "title": page["title"],
                            "row_label": label,
                            "column_header": cell["column_header"],
                            "pdf_sha256": spec["sha256"],
                            "raw_value": raw,
                            "source_spans": spans,
                        }
                    )
    finally:
        pdf.unload()
    return checks


def original_chart(pdf_path, spec, soup):
    chart = spec["chart"]
    matches = soup.select(chart["html_selector"])
    if len(matches) != 1:
        raise ParseError("Chart HTML source locator did not resolve uniquely")
    images = PdfReader(pdf_path).pages[chart["page"] - 1].images
    image = next((im for im in images if im.name == chart["pdf_image"]), None)
    if image is None or sha256(image.data) != chart["image_sha256"]:
        raise ParseError("Embedded chart identity mismatch")
    return image.data
