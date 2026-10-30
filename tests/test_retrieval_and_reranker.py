from src.retrieval.reranker import SimpleFinancialReranker
from src.retrieval.retriever import DualHybridRetriever


def test_dual_retriever_query_classification():
    retriever = DualHybridRetriever()
    assert retriever.is_numerical_query("What was total net revenue in 2024?") is True
    assert retriever.is_numerical_query("What is the gross margin for products?") is True
    assert retriever.is_numerical_query("Describe the general corporate leadership culture.") is False


def test_simple_financial_reranker():
    reranker = SimpleFinancialReranker()
    candidates = [
        {
            "content": "General corporate overview: The company designs consumer electronics.",
            "metadata": {"type": "narrative_text"},
        },
        {
            "content": "Table Context: Net Sales by Segment\n| Segment | 2024 ($M) |\n| Total | $383,285 |",
            "metadata": {"type": "financial_table"},
        },
        {
            "content": "Risk factors: Competition in the tech industry could affect sales.",
            "metadata": {"type": "narrative_text"},
        },
    ]

    reranked = reranker.rerank(
        query="What is total net sales in 2024?",
        candidates=candidates,
        top_n=2,
    )

    assert len(reranked) == 2
    # Table with specific numbers should be prioritized
    assert reranked[0]["metadata"]["type"] == "financial_table"
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]
