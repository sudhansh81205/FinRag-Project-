import os
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from google import genai
import gradio as gr

# Connect to the persistent vector database
chroma_client = chromadb.PersistentClient(path="./sec_vector_db")
collection = chroma_client.get_or_create_collection(name="sec_10k_filings")

# Load models
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def retrieve_and_rerank(query, doc_type, top_k_initial=3, top_k_final=2):
    q_vec = embedding_model.encode(query).tolist()
    initial_results = collection.query(
        query_embeddings=[q_vec],
        n_results=top_k_initial,
        where={"type": doc_type}
    )
    candidate_docs = initial_results['documents'][0]
    if not candidate_docs:
        return ["No documents found in local vector DB."]
    pairs = [[query, doc] for doc in candidate_docs]
    scores = reranker.predict(pairs)
    ranked_docs = [doc for _, doc in sorted(zip(scores, candidate_docs), key=lambda x: x[0], reverse=True)]
    return ranked_docs[:top_k_final]

def finrag_ui_pipeline(user_query, api_key_input):
    if not user_query.strip():
        return "Please enter a question.", "", "", ""

    if not api_key_input or not api_key_input.strip():
        return "❌ Missing API Key", "Please paste your API key in the box above.", "", ""

    try:
        os.environ["GEMINI_API_KEY"] = api_key_input.strip()
        active_client = genai.Client()

        # 1. Retrieve & Rerank Narrative Text
        narrative_docs = retrieve_and_rerank(user_query, "narrative_text", 3, 2)
        narrative_context = "\n\n".join(narrative_docs)

        # 2. Check if Table Escalation is Needed
        check_prompt = f"""
        Does the following Narrative Evidence contain all exact numbers needed to completely answer the User Question?
        Reply with ONLY the word 'SUFFICIENT' or 'ESCALATE'.

        Narrative Evidence:
        {narrative_context}

        User Question:
        {user_query}
        """
        decision = active_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=check_prompt
        ).text.strip().upper()

        # 3. Dynamic Escalation to Cleaned Tables
        if "ESCALATE" in decision:
            routing_status = "⚡ ESCALATED TO MULTIMODAL TABLES + CROSS-ENCODER RERANKED"
            reranked_tables = retrieve_and_rerank(user_query, "clean_financial_table", 3, 2)
            table_context = "\n\n".join(reranked_tables)[:4000]
            final_prompt = f"""
            You are an expert financial analyst. Answer the question using BOTH the narrative text and financial tables below.
            Cite exact figures and years from the tables.

            --- NARRATIVE EVIDENCE ---
            {narrative_context}

            --- TABULAR EVIDENCE ---
            {table_context}

            --- QUESTION ---
            {user_query}
            """
        else:
            routing_status = "✅ HANDLED BY NARRATIVE TEXT ONLY (CROSS-ENCODER RERANKED)"
            table_context = "No table escalation required for this query."
            final_prompt = f"""
            You are an expert financial analyst. Answer the question using the narrative text below.

            --- NARRATIVE EVIDENCE ---
            {narrative_context}

            --- QUESTION ---
            {user_query}
            """

        final_answer = active_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=final_prompt
        ).text

        return routing_status, final_answer, narrative_context, table_context

    except Exception as e:
        return "❌ API Error", f"**Error Details:** `{str(e)}`", "", ""

with gr.Blocks() as demo:
    gr.Markdown("# 📊 FinRAG: Multimodal Financial Document Analyzer (Team CV ++)")

    api_key_box = gr.Textbox(
        label="🔑 Step 1: Paste Your API Key Here",
        placeholder="AQ... or AIza...",
        type="password"
    )

    query_input = gr.Textbox(
        label="💬 Step 2: Ask a Financial Question",
        placeholder="e.g., What is the exact breakdown of net sales between Products and Services for 2021?",
        lines=2
    )

    gr.Examples(
        examples=[
            ["What is the exact breakdown of net sales between Products and Services for 2021, 2020, and 2019?"],
            ["What was the Research and Development (R&D) expense in 2021 and 2020?"]
        ],
        inputs=query_input
    )

    submit_btn = gr.Button("Analyze SEC Filing", variant="primary")
    routing_box = gr.Textbox(label="Retrieval Router & Reranker Status", interactive=False)
    answer_box = gr.Markdown(label="Generated Financial Analysis")

    with gr.Accordion("🔍 View Retrieved & Reranked SEC 10-K Evidence", open=True):
        with gr.Row():
            text_evidence_box = gr.Textbox(label="Top Reranked Narrative Chunks", lines=10, interactive=False)
            table_evidence_box = gr.Textbox(label="Top Reranked Markdown Tables", lines=10, interactive=False)

    submit_btn.click(
        fn=finrag_ui_pipeline,
        inputs=[query_input, api_key_box],
        outputs=[routing_box, answer_box, text_evidence_box, table_evidence_box]
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
