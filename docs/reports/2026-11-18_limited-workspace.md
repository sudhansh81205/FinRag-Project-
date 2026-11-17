# Limited two-filing workspace and gross-margin repair

Observed18November2026. The user requested fixing a gross-margin refusal and a limited usable filing set. The workspace is now limited to Apple FY2021 (2021-09-25) and Microsoft FY2021 (2021-06-30). The full18-filing research inventory is retained separately; reducing the demonstration does not revise the final-study PRD or certify independent acceptance.

## Root cause and repair

The exact question `what was Apple's gross margin in fy2021` retrieved GrossProfit but missed the revenue operand in the ranked shortlist. The untrusted planner then proposed a denominator with the wrong metric; the semantic validator correctly refused it. The UI's blanket statement that the filing could not answer was misleading.

Interactive numerical requests now use explicit table retrieval; recognized single-period gross-margin questions use exact typed source operands from the connected records, with the same filing/issuer/scope/period eligibility ceiling. Total revenue must identify an original total row. The existing unique-operand, typed-calculation and token/passage constraints still apply. No numeric answer is hardcoded. Default benchmark retrieval is unchanged; this is an explicit interactive policy, not an A-G experimental result. Missing or ambiguous operands still refuse. The UI heading now says a verified answer could not be constructed.

## Two-filing development scope

`src/workspace_corpus.py` reproduces the selected original HTML/exhibit and package hashes, validates canonical schemas/content hashes, compares native indexed records and parent tables with the exact selected packages and restricts retrieval to the two accessions. Existing BGE768/exact-FAISS assets are reused; no model download. This is source-checked development use, not newly invented human approval. Wider source, chart and final-study gates remain unchanged.

The web filing list contains only these two reports. Example questions follow the selected company and fiscal year rather than switching back to Apple. The prepared launcher uses `--workspace-corpus output/nov17/corpus`; other machines need the actual prepared corpus/assets. Gradio continues sharing the same engine/lock.

## Actual verification

Real authenticated API results after the typed lookup: Apple41.78%; Microsoft68.93% from115856000000/168088000000; Microsoft revenue168088000000USD. Included evidence was checked to belong to the requested accession. Full real result records are retained in `2026-11-18-checks/limited-live.json`.

The first Microsoft lexical-shortlist attempt failed and was retained as the reason to use exact typed operands. Earlier focused/full tests exposed one strict fixture signature and a sandbox loopback permission failure; fixture updated and permitted test run passed. New regression tests check original question preservation, unchanged benchmark defaults, filing isolation and missing-operand refusal.

Publication of the frontend requires the existing Vercel account. The connector now sees a different team and cannot access the existing Rushil project; CLI was logged out and a device-login request is pending. No replacement project, billing or protection change was made. The live backend has the calculation fix, but the old hosted filing list remains until deployment. Prior PDFs/receipt describe their earlier verified revision and are not overwritten as if they covered this change.

Final local regression:554 Python tests passed,3 FAISS/SWIG deprecation warnings,77.41seconds;17 Node tests passed; Ruff and browser syntax passed.1329 selected source/index records matched pinned packages. Source-operand focused checks22passed. Full-study acceptance remains incomplete.
