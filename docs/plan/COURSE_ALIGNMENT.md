# Implementation and code review course mapping

## Connection to course concepts

The strongest course connection is Knowledge Representation and Reasoning combined with Applications of Deep Learning. The course handout names predicate logic, ontology/categories, word embeddings, transformers and computer vision. Implement and explain the connection below instead of merely listing retrieval packages.

| Course topic | Concrete project behavior | Proof and viva question |
| --- | --- | --- |
| KR&R ontology and predicates \| T1 chapters 7-10 | Represent issuer, filing, period, statement, metric, unit, value, table cell and source as typed facts. Explicit rules check comparability and whether an operation is justified. | Show facts and a rule trace. Why is a 2023 consolidated USD-million value incompatible with a 2024 segment value? |
| KR&R inference | Infer that a requested calculation is allowed only when all required operands are cited, comparable and valid. Record rule failures and abstain. | A missing operand or zero denominator blocks the result. Which premises established the displayed result? |
| DL for NLP \| T1 chapter 25 | BGE embeds question and evidence; the cross-encoder jointly scores pairs; Gemma generates a grounded explanation. Use pretrained transformer models without fine-tuning. | Explain cosine retrieval versus cross-encoding, normalization and context limits. Save measured A-G outcomes. |
| Computer vision \| T1 chapter 27 | Use a pretrained vision-language model to convert report images into cited chart descriptions. | Compare the image with its caption and explain an unreadable-value failure. No claim of training a vision model. |
| Ethics and safety \| T1 chapter 28 | Disclose AI help, retain source provenance, expose uncertainty and provider failures, and avoid unsupported financial claims. | Show an abstention, an AI-use entry and source verification. |

Search and Problem Solving is a limited supporting analogy: evidence candidates, constrained selection and tier escalation define a search process, but BM25/RRF/nearest-neighbour retrieval are information-retrieval methods, not implementations of A*, CSP, minimax or a syllabus state-space algorithm. Agents and Game Theory is not a claimed implemented contribution; bounded routing alone is not multi-agent planning or equilibrium reasoning. No extra game or planner is added merely to name all four areas.

In the report, include the explicit section title Connection to Course Concepts. In every meaningful code review, name the applicable concept, point to its implementation, inspect one successful and one failing case, and record what the member must explain in the viva. An ordinary packaging change may say supporting engineering rather than forcing a false algorithm connection.

## Knowledge rules and evidence contracts

### Minimal executable reasoning

Implement the rules as deterministic typed Python predicates with recorded premises and outcomes. This is a small rule-based reasoning layer; do not claim a general theorem prover, resolution engine, knowledge graph database or probabilistic inference system.

- Value facts bind issuer, metric, period boundaries, statement, scope, currency, scale, normalized value and evidence ID.
- Comparable requires matching issuer, metric meaning, scope, currency and appropriate periods for the requested operation. A year-over-year comparison deliberately allows two specified periods; a same-period comparison requires the same one.
- Allowed division requires valid, cited operands and a nonzero denominator. Missing, ambiguous or incompatible facts cause an explicit rule failure.
- For ordinary growth, a positive prior value permits (current - prior) / prior times 100. A zero prior is undefined. For a negative prior, display absolute change and an explanation unless a separately documented benchmark operation explicitly defines another calculation.
- Conclusions retain operand IDs, rule IDs, normalized values, units, expression and result. The language model may explain a validated result but cannot override a failed rule.

| Record | Mandatory contents |
| --- | --- |
| Evidence | Stable ID; issuer and filing identity; type; section/page/HTML locator; source URL; content hash; parser version; readable content; parent ID. |
| Cell | Table title; row and column headers; raw value; metric; period boundaries; raw and normalized unit/currency/scale; footnote links; parent grid coordinates. |
| Retrieval trace | Eligible corpus/filter; dense and BM25 ranks; RRF and reranker scores with type; route/escalation; candidate IDs; selected IDs; expansions; budget. |
| Answer | Status; answer text; actual included IDs; resolvable citations; provider/model/configuration; operation tree and rule trace; warnings; timing. |
| Run | Code SHA; data/model/configuration hashes; variant A-G; question/split IDs; output; scores; failure code; hardware; timestamp; duration. |

### Reliability

Reject missing indexes, invalid requests and unusable evidence before financial generation. Provider errors cannot turn into successful mock answers. Separate test fixtures from real outputs; never log secrets. Data replacement must not delete unrelated filings. Preserve cited context exactly; list retrieved-but-excluded IDs separately.

