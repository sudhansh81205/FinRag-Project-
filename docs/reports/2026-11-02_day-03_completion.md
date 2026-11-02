# Rushil first assignment completion

Execution date: 2 November 2026, Asia/Kolkata. Planned day: 1 November 2026.
Starting shared revision: `307c933`. Work branch: `rushil/day-03-real-model`.

## Checked outcome

The live provider check passed all five assertions: a real Gemini answer, the
expected source-fixture value/period/unit, abstention on empty evidence, zero
model calls for empty evidence, and a deliberate invalid-key failure returning
no answer. The fixed mock financial answer and silent fallback chain are gone.
The explicit verified model is `gemini-3.5-flash-lite`; billing remains unset.

[Live JSON evidence](2026-11-02_day-03_live-check.json) retains the real response,
source locator, evidence record, statuses and timings without credentials.
[Handoff](../handoffs/2026-11-02_day-03_rushil.md) explains changes and commands.

## Verification

- 51 automated tests passed, including new generation/error-path regressions.
- Ruff lint passed.
- `pip check` found no broken requirements in the isolated Python 3.14 environment.
- The source-fixture live script passed with Gemini.
- The actual Gradio HTTP callback returned `index_not_ready` for a question and
  `invalid_request` for empty input, with empty answers and evidence in both cases.
- The in-app browser confirmed the question flow shows those missing prerequisites.
- Readiness reports `index_not_ready` and does not create an empty database.

The dependencies used in this session were tested on Python 3.14.2/macOS arm64.
The repository's earlier Python 3.12/Windows setup verification is historical;
it was not rerun on Windows or Python 3.12 in this session.

## Evidence limits

The manual provider fixture comes from the SEC-hosted Apple 2021 filing, Item 7,
net sales by category, Services row (printed page 21). It is deliberately not a
full parsed corpus or gold evaluation set. No retrieval accuracy, calculator
integration, citation audit, held-out score or final app readiness is claimed.

Source: https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm
SDK reference: https://googleapis.github.io/python-genai/
