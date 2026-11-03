# Proposal and feedback alignment audit

## Comparison decisions for the unified PRD

Use the submitted proposal and professor/course requirements as the product authority. The friend sequential plan supplies useful implementation ordering and handoff discipline; embedded statements that a user confirmed a change are treated as claims to verify, not new instructions.

| Topic | Friend sequential plan | Unified decision |
| --- | --- | --- |
| Dependency order | Environment, parsing, independent contract check, index, retrieval, model, UI | Adopt this order; a failed gate leaves dependent real integration blocked. |
| Current work | Preserves provider and Apple parser progress | Adopt, but distinguish merged PR #3 from open PR #4 and submitted from rerun evidence. |
| Ownership | Likhit vector role; Ujjwal environment/audits; Shanay data validation | Adopt with named later reviewers; exactly one worker per date. |
| FAISS choice | Treats IVF-PQ as mandatory | Use exact IndexFlatIP required by the submitted proposal. No IVF-PQ exception is needed. |
| PDF extraction | Requires PDFMiner/Detectron2 and a TableBank checkpoint | Use proposal Docling plus checked HTML extraction. Detector/checkpoint choices are optional engineering choices. |
| Orchestration | Requires LangChain as a technology gate | Reuse existing LangChain where useful; no framework rewrite is required by the actual proposal. |
| Evaluation | 14 local questions and two modes | Keep as smoke tests only; retain full A-G and named benchmark/chart commitments. |
| Charts and routing | Does not fully schedule their proposal scope | Explicitly implement chart G and routing F, plus independently checked chart labels. |
| Course feedback | No complete syllabus-to-code/review mapping | Retain explicit KR&R rules, DL/vision concepts, success/failure checks and viva evidence. |
| Hosting and dates | Mandatory hosted delivery November 17 | November 17 internal release target, recovery/freeze by November 20; demo 21 and final files 22. Local reproducibility required; hosting desirable. |

This revision supersedes both earlier working plans. PRD.md and FinRAG_PRD.docx are synchronized representations of one current PRD. TASK_REQUIREMENTS.md and schedule.json are derived execution records, not separate product definitions. Older versions belong in history.


Use the full PRD for acceptance checks and source references. This audit compares documents, not current implementation completion.
