"""
Prompt Engineering Templates (Member 3: LLM Integration Specialist)
Specialized prompts for numerical financial reasoning, strict grounding, and automated evaluation.
"""



def build_finrag_prompt(
    question: str,
    text_evidence: list[str],
    table_evidence: list[str],
    max_table_chars: int | None = None,
    *, chart_evidence: list[str] | None = None,
) -> str:
    """
    Render already selected complete evidence. Never silently slice a source.
    """
    joined_text = "\n\n".join(text_evidence) if text_evidence else "No narrative evidence retrieved."
    joined_tables = "\n\n".join(table_evidence) if table_evidence else "No tabular evidence retrieved."
    if max_table_chars is not None and table_evidence and len(joined_tables) > max_table_chars:
        raise ValueError("Select complete tables within the budget before rendering.")

    chart_section = ("\n--- GENERATED CHART DESCRIPTIONS (source-linked; values marked unknown remain unknown) ---\n"
                     + "\n\n".join(chart_evidence)) if chart_evidence else ""
    prompt = f"""You are a financial evidence assistant.
Your objective is to answer the user's question accurately using ONLY the provided Narrative Evidence and Tabular Evidence from SEC filings.

--- GROUNDING & REASONING RULES ---
1. STRICT EVIDENCE FAITHFULNESS: Use ONLY facts, figures, and dates explicitly present in the evidence. Do NOT extrapolate or introduce outside knowledge.
2. NUMERICAL ACCURACY: State exact dollar figures (with units, e.g. in millions or billions), fiscal years, and percentages.
3. ARITHMETIC REASONING: If calculating growth rates, margins, or differences:
   - State the raw formula used (e.g., (New - Old) / Old * 100).
   - Show the exact substituted numbers from the evidence.
   - Show the final calculated result.
4. CITATION: Explicitly mention which table, statement, or section supplied the data (e.g., 'From Consolidated Statements of Operations: ...').
5. MISSING DATA: If the evidence does not contain sufficient data to fully answer the query, clearly state what information is missing.

--- NARRATIVE EVIDENCE ---
{joined_text}

--- TABULAR EVIDENCE ---
{joined_tables}
{chart_section}

--- USER QUESTION ---
{question}

Provide your response structured as:
### Direct Answer:
<Concise answer with core numbers>

### Step-by-Step Financial Evidence & Arithmetic:
<Exact breakdown from tables/text, including any arithmetic steps>

### Sources Cited:
<List of specific tables or narrative sections used>
"""
    return prompt.strip()


def build_baseline_prompt(question: str, text_evidence: list[str]) -> str:
    """
    Constructs the standard text-only baseline prompt for academic evaluation.
    """
    joined_text = "\n\n".join(text_evidence) if text_evidence else "No narrative evidence available."
    return f"""You are a financial analyst. Answer the user's question using ONLY the narrative text below.
If exact numbers or financial statements are missing, state what is available.

--- NARRATIVE EVIDENCE ---
{joined_text}

--- QUESTION ---
{question}
""".strip()


def build_eval_prompt(question: str, ground_truth: str, baseline_answer: str, finrag_answer: str) -> str:
    """
    Automated evaluator prompt to compare Baseline vs FinRAG.
    """
    return f"""You are an objective academic evaluator grading two Financial AI systems on a scale of 1 to 10.

Question: {question}
Expected Ground Truth: {ground_truth}

--- SYSTEM A (Text-Only Baseline RAG) ---
{baseline_answer}

--- SYSTEM B (FinRAG Multimodal Text + Tables) ---
{finrag_answer}

Evaluate both systems on:
1. Accuracy (exact match with ground truth numbers and dates)
2. Faithfulness (absence of hallucinations)
3. Completeness (sufficient financial detail)

Format your evaluation as:
- Baseline Accuracy (1-10):
- Baseline Faithfulness (1-10):
- FinRAG Accuracy (1-10):
- FinRAG Faithfulness (1-10):
- Score Justification:
""".strip()
