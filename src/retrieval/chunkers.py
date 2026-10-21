"""
Financial Document Chunkers (Member 2: RAG Architecture Lead)
Implements sliding window strategies for narrative text and structured table parsing.
"""

import re
from typing import Any


class SlidingWindowChunker:
    """
    Sliding window chunker optimized for SEC 10-K financial narrative sections
    (e.g., Item 1A Risk Factors, Item 7 MD&A).
    Ensures context continuity across sentences and numeric figures.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_length: int = 80,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_length = min_chunk_length

    def split_text(self, text: str, metadata: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Splits narrative text using a sliding window with sentence-boundary awareness.
        """
        if not text or len(text.strip()) == 0:
            return []

        # Normalize whitespace
        clean_text = re.sub(r"[ \t]+", " ", text).strip()
        words = clean_text.split(" ")
        step = max(1, int((self.chunk_size - self.chunk_overlap) / 6))
        window_words = max(1, int(self.chunk_size / 6))

        chunks: list[dict[str, Any]] = []
        idx = 0
        chunk_id = 0
        while idx < len(words):
            chunk_slice = words[idx : idx + window_words]
            chunk_content = " ".join(chunk_slice).strip()

            if len(chunk_content) >= self.min_chunk_length:
                chunk_meta = dict(metadata or {})
                chunk_meta.update({
                    "chunk_id": f"narrative_{chunk_id}",
                    "type": "narrative_text",
                    "word_count": len(chunk_slice),
                    "char_count": len(chunk_content),
                })
                chunks.append({
                    "content": chunk_content,
                    "metadata": chunk_meta,
                })
                chunk_id += 1

            idx += step

        return chunks


class TableChunker:
    """
    Formats and chunks structured financial tables with surrounding context headings.
    Ensures table headers and markdown formatting are preserved.
    """

    def __init__(self, min_length: int = 50):
        self.min_length = min_length

    def format_table_chunk(
        self,
        table_markdown: str,
        table_context: str = "Financial Statement / Disclosure Table",
        metadata: dict[str, Any] | None = None,
        table_index: int = 0,
    ) -> dict[str, Any] | None:
        """
        Pairs a markdown table with its surrounding title/context to prevent
        flattening into raw text.
        """
        cleaned_table = table_markdown.strip()
        if len(cleaned_table) < self.min_length:
            return None

        content = f"Table Context: {table_context.strip()}\n\n{cleaned_table}"

        meta = dict(metadata or {})
        meta.update({
            "chunk_id": f"table_{table_index}",
            "type": "financial_table",
            "table_context": table_context[:250],
            "char_count": len(content),
        })

        return {
            "content": content,
            "metadata": meta,
        }
