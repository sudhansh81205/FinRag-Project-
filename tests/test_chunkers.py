from src.retrieval.chunkers import SlidingWindowChunker, TableChunker


def test_sliding_window_chunker_basic():
    sample_text = (
        "Item 7. Management's Discussion and Analysis of Financial Condition. "
        "During fiscal 2024, our total net sales increased by 8% to $390 billion. "
        "Products revenue accounted for $290 billion while Services generated $100 billion. "
        "Operating expenses grew primarily due to research and development investments."
    )
    chunker = SlidingWindowChunker(chunk_size=120, chunk_overlap=30, min_chunk_length=30)
    chunks = chunker.split_text(sample_text, metadata={"ticker": "AAPL", "year": "2024"})

    assert len(chunks) > 0
    assert chunks[0]["metadata"]["type"] == "narrative_text"
    assert chunks[0]["metadata"]["ticker"] == "AAPL"
    assert "content" in chunks[0]


def test_sliding_window_chunker_empty():
    chunker = SlidingWindowChunker()
    chunks = chunker.split_text("")
    assert chunks == []


def test_table_chunker_formatting():
    chunker = TableChunker(min_length=20)
    raw_md_table = "| Category | 2024 | 2023 |\n| Products | $290B | $270B |\n| Services | $100B | $85B |"
    result = chunker.format_table_chunk(
        table_markdown=raw_md_table,
        table_context="Revenue by Reportable Segment",
        metadata={"ticker": "AAPL"},
        table_index=1,
    )

    assert result is not None
    assert result["metadata"]["type"] == "financial_table"
    assert "Table Context: Revenue by Reportable Segment" in result["content"]
    assert "| Products | $290B |" in result["content"]
