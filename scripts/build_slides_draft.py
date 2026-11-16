"""Build the exactly-six-slide PARTIAL DRAFT deck from recorded evidence (R8, November 16).

Slide order follows the course guideline recorded in docs/plan/PRD.md: (1) title/team/repository/
track/area, (2) problem, (3) related work, (4) methods, (5) results, (6) management/work division.
The results slide states what was and was not measured; no experimental metric is shown because
none exists (zero completed A-G outputs). Usage: python scripts/build_slides_draft.py
"""

import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "reports" / "2026-11-16_slides_draft.pptx"
NAVY, GREY, RED = RGBColor(0x1F, 0x2A, 0x44), RGBColor(0x44, 0x44, 0x44), RGBColor(0xA0, 0x1C, 0x1C)

audit_path = ROOT / "docs" / "reports" / "2026-11-16_pavan_evidence_audit.json"
audit_counts = json.loads(audit_path.read_text(encoding="utf-8"))["counts"] if audit_path.is_file() else {}

SLIDES = [
    ("FinRAG: Source-Grounded Financial QA over SEC 10-K Filings", [
        "CS F407 Artificial Intelligence | CV++ Team 6 | Application track | Area: financial NLP (RAG)",
        "Team: Sudhansh Khandelwal, Agrawal Pavan Shailesh, B Rushil Mohan, Sri Sai Likhit Boddada, "
        "Ujjwal Chandak, Shanay Ghodasara, Muppidi Gowtham Sai",
        "Repository: github.com/sudhansh81205/FinRag-Project-",
        "STATUS: PARTIAL DRAFT (November 16). Full A-G experiment not run; see slide 5.",
    ]),
    ("Problem", [
        "Analysts need answers from annual reports that can be traced to the original narrative, table cell or chart.",
        "Plausible numbers are not enough: correct arithmetic on the wrong issuer, filing, period, scope or unit "
        "is an invalid answer (e.g. Apple FY2021 margin 41.78% offered for a Microsoft 2022 request).",
        "Research question: with corpus, embedder, answer model, prompt, calculator and five final passages fixed, how do "
        "section-aware chunks, self-describing cells, hybrid retrieval, reranking, routing and chart descriptions change "
        "recall, answer quality, faithfulness and latency versus standard dense RAG?",
    ]),
    ("Related work", [
        "Retrieval-augmented generation: Lewis et al., 2020. Financial QA benchmarks: FinanceBench (Islam et al., 2023), "
        "FinQA (Chen et al., 2021), TAT-QA (Zhu et al., 2021).",
        "Dense embeddings and reranking: BGE / C-Pack (Xiao et al., 2023), bge-reranker-base cross-encoder. "
        "Lexical retrieval and fusion: BM25 (Robertson & Zaragoza, 2009), reciprocal rank fusion (Cormack et al., 2009).",
        "Faithfulness evaluation: RAGAS (Es et al., 2023). Our lexical overlap check is a labelled diagnostic, not RAGAS.",
        "Bibliographic details to be re-verified against the originals before submission.",
    ]),
    ("Methods", [
        "Controlled cumulative variants A-G: fixed chunks, section-aware, self-describing cells + parents, BM25/RRF60 "
        "fusion, hierarchical cross-encoder, bounded routing, approved chart descriptions.",
        "Common controls: BGE-base-en-v1.5 (768-D) + exact FAISS, Gemma 3 4B via Ollama, one prompt, five passages, one token budget.",
        "KR&R: typed facts + predicates license a restricted, cited Decimal expression tree; wrong issuer/period/unit, "
        "excluded operand or zero denominator refuses. DL: pretrained embeddings, cross-encoder, generation, chart vision.",
        "Safety: request-bound evidence, explicit refusals, AI-use disclosure; no investment advice.",
    ]),
    ("Results (what is and is not established)", [
        "NOT AVAILABLE: no A-G benchmark outputs exist (28 run cells: 0 completed), so no accuracy, Recall@5/10, MRR, RAGAS, "
        "latency or interval is reported. 150/50/50 benchmark files are generated smoke fixtures, not official data.",
        "Established: November 16 repairs with regression tests - request-bound answers (wrong issuer/filing/period/scope "
        "refuse), unit-normalized scoring (100M = 0.1B, 100B fails), artifact-bound resume, gates from real artifacts.",
        f"PR14 audit: {audit_counts.get('FAIL', '?')} failed claims, {audit_counts.get('UNVERIFIED', '?')} unverifiable, "
        f"{audit_counts.get('BLOCKED', '?')} blocked checks; chart/human approvals remain submitted claims.",
        "Blocked: live engine, Ollama/Gemma (not running on this machine), RAGAS, 50-output independent audit.",
    ]),
    ("Management and work division", [
        "One sole owner per date: Ujjwal Nov 15 (inputs/freeze), Pavan Nov 16 (audit/metrics/report), final-day owner Nov 17 "
        "(Sudhansh per repository docs; the review PDFs name Shanay - authority to be confirmed by the team).",
        "Earlier work: Likhit (parsing, BGE/FAISS, corpus), Rushil (model, calculator, charts), Gowtham (UI, loaders, runner), "
        "Sudhansh (scaffold, integration), Shanay (setup, reviews). Hours are estimates, not measured effort.",
        "AI use: AI coding assistants helped write and review code and tests; every claim above is tied to a saved artifact.",
        "Next: confirm Nov 17 owner, wire engine, run frozen jobs if compute exists, otherwise submit a transparent partial package.",
    ]),
]


def build() -> Path:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    for index, (title, bullets) in enumerate(SLIDES, start=1):
        slide = prs.slides.add_slide(blank)
        box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(1.0))
        run = box.text_frame.paragraphs[0].add_run()
        run.text = title
        run.font.size, run.font.bold, run.font.color.rgb = Pt(32), True, NAVY
        body = slide.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(11.9), Inches(5.4)).text_frame
        body.word_wrap = True
        for i, text in enumerate(bullets):
            p = body.paragraphs[0] if i == 0 else body.add_paragraph()
            p.space_after = Pt(10)
            r = p.add_run()
            r.text = ("" if index == 1 and i < 3 else "• ") + text
            r.font.size = Pt(18)
            r.font.color.rgb = RED if text.startswith(("STATUS", "NOT AVAILABLE")) else GREY
        foot = slide.shapes.add_textbox(Inches(0.6), Inches(7.0), Inches(12), Inches(0.4)).text_frame
        foot.text = f"FinRAG | PARTIAL DRAFT 2026-11-16 | {index}/6"
        foot.paragraphs[0].runs[0].font.size = Pt(11)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    assert len(Presentation(OUT).slides) == 6
    return OUT


if __name__ == "__main__":
    print(build(), file=sys.stdout)
