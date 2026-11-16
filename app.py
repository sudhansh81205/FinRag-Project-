"""Canonical local launch: python app.py.

Supports interactive Gradio UI with:
- Client session isolation (no shared global state between browser sessions).
- Narrative, table cell, and chart evidence inspection.
- Typed calculator rule execution traces and explicit refusal paths.
- Offline readiness check via --check.
"""

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["HF_HUB_OFFLINE"] = "1"

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.application import InteractiveApplication, load_filing_options, resolve_request  # noqa: E402
from src.config import ConfigurationError, load_settings  # noqa: E402


def create_demo(application):
    import gradio as gr

    def init_session():
        return {
            "query_count": 0,
            "last_query": "",
            "last_status": "",
            "session_filters": {},
        }

    readiness = application.readiness()
    is_ready = readiness.get("status") == "ready"

    # Every selectable option is bound to its exact registry tuple (issuer, accession, fiscal
    # year end); nothing is inferred from a ticker substring (F32).
    filing_options = load_filing_options()
    company_options = [o.label for o in filing_options]
    filing_period_by_label = {o.label: o.filing_period_end for o in filing_options}

    sample_calc_plan = json.dumps({
        "issuer": "Apple Inc.",
        "scope": "consolidated",
        "periods": [
            {"kind": "duration", "start": "2020-09-27", "end": "2021-09-25"}
        ],
        "expression": {
            "op": "ratio_percent",
            "args": [
                {
                    "op": "subtract",
                    "args": [
                        {"evidence_id": "sales"},
                        {"evidence_id": "cost"}
                    ]
                },
                {"evidence_id": "sales"}
            ]
        }
    }, indent=2)

    chart_assets = [
        "ad0ded84e0a5b9dbf96385d1debb0cf711f6f1bec501dda9c067091526dd83a9 (Apple 2021)",
        "41716e31eeb23fe0a516c2fb510c56ea5fa400fddf25a8c8310f8acd921f9e5a (NVIDIA 2024)",
        "a64c086a9af2be3b7aa2a0a69177acc2dd73b64fadedda64c6cc86cc4ca729e0 (AMD 2024)",
        "3642d2aa1cafa2bf25997038d695b2444169d4737f3d14a8a539b281259a7568 (Intel 2024)",
    ]

    with gr.Blocks(title="FinRAG") as demo:
        session_state = gr.State(init_session)

        gr.Markdown(
            "# FinRAG: Financial Question Answering System\n"
            "Grounding annual report questions on verified narrative passages, typed statement cells, "
            "and inspectable arithmetic trees. Client sessions are strictly isolated."
        )

        if not is_ready:
            with gr.Accordion("System Readiness Warnings", open=False):
                gr.Markdown(
                    "**Notice**: Full end-to-end model and persistent index integration is currently unconfigured or gated.\n\n"
                    + "\n".join(f"- {b}" for b in readiness.get("blockers", []))
                )

        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown("### 1. Document & Scope Selection")
                selected_company = gr.Dropdown(
                    label="Company & Filing",
                    choices=company_options,
                    value=company_options[0],
                )
                with gr.Row():
                    filter_period = gr.Textbox(label="Value Period End (ISO date)", value=filing_options[0].filing_period_end)
                    filter_scope = gr.Textbox(label="Scope", value="consolidated")

                gr.Markdown("### 2. Financial Question")
                query_input = gr.Textbox(
                    label="Question",
                    placeholder="e.g. What was Apple's gross margin in fiscal year 2021?",
                    lines=2,
                    value="What was Apple's gross margin in fiscal year 2021?",
                )

                mode_selector = gr.Radio(
                    label="Question Mode",
                    choices=["Narrative / Table QA", "Typed Calculation Plan", "Chart Question"],
                    value="Typed Calculation Plan",
                )

                with gr.Accordion("Calculation Plan (JSON)", open=True):
                    calc_plan_input = gr.Code(
                        label="Declarative Calculator Tree (operands resolve to included cell IDs)",
                        language="json",
                        value=sample_calc_plan,
                    )

                with gr.Accordion("Chart Evidence Selection", open=False):
                    chart_selector = gr.Dropdown(
                        label="Select SEC Filing Chart Asset",
                        choices=["None"] + chart_assets,
                        value="None",
                    )

                demo_only = gr.Checkbox(
                    label="Demo only: use synthetic Apple FY2021 facts (never a verified live answer)",
                    value=False,
                )

                with gr.Row():
                    submit_btn = gr.Button("Submit Query", variant="primary")
                    clear_btn = gr.Button("Clear All", variant="secondary")

            with gr.Column(scale=5):
                gr.Markdown("### 3. Answer & Evidence")
                answer_output = gr.Textbox(label="Primary Answer", lines=3, interactive=False)

                with gr.Row():
                    status_badge = gr.Textbox(label="Status", value="ready", interactive=False)
                    latency_badge = gr.Textbox(label="Latency", value="0.000s", interactive=False)
                    route_badge = gr.Textbox(label="Pipeline Route", value="unrouted", interactive=False)

                diag_message = gr.Textbox(label="Diagnostics & Refusal Reason", lines=2, interactive=False)

                with gr.Accordion("Source Citations & Evidence Table", open=True):
                    evidence_table = gr.JSON(label="Included Evidence Context", value=[])

                with gr.Accordion("Verified Calculator Rule Trace", open=True):
                    calc_trace = gr.JSON(label="Evaluated Operation Tree & Rule Premises", value={})

        def handle_query(
            question, comp_choice, period, scope, mode, plan_str, chart_choice, demo, session
        ):
            # Session isolation: mutate only session-local state
            session["query_count"] += 1
            session["last_query"] = question
            session["session_filters"] = {
                "company_choice": comp_choice,
                "period": period,
                "scope": scope,
            }

            # Immediate clearing of outputs on empty question
            if not isinstance(question, str) or not question.strip():
                return (
                    "",
                    "invalid_request",
                    "0.000s",
                    "rejected",
                    "Please enter a nonempty question.",
                    [],
                    {},
                    session,
                )

            # Resolve the selected filing to its exact registry tuple and validate the value period
            # and scope; unsupported selections refuse instead of defaulting to another filing.
            request, request_error = resolve_request(comp_choice, period, scope)
            if request is None:
                return ("", "invalid_request", "0.000s", "rejected", request_error, [], {}, session)

            calc_plan = None
            if mode == "Typed Calculation Plan" and plan_str.strip():
                try:
                    calc_plan = json.loads(plan_str)
                except Exception as exc:
                    return (
                        "",
                        "invalid_request",
                        "0.000s",
                        "rejected",
                        f"Malformed JSON in calculation plan: {exc}",
                        [],
                        {},
                        session,
                    )

            chart_id = None
            if mode == "Chart Question" and chart_choice != "None":
                chart_id = chart_choice.split()[0]

            # Call application
            if hasattr(application, "answer_interactive"):
                res = application.answer_interactive(
                    question=question,
                    request=request,
                    calculation_plan=calc_plan,
                    chart_asset_id=chart_id,
                    demo_only=bool(demo),
                )
            else:
                raw_ans = application.answer(question)
                res = {
                    "status": raw_ans.get("status", "unknown"),
                    "answer": raw_ans.get("answer", ""),
                    "message": raw_ans.get("message", ""),
                    "latency_seconds": 0.001,
                    "route": "setup_fallback",
                    "evidence": raw_ans.get("evidence", []),
                    "calculations": raw_ans.get("calculations", []),
                }

            status = res.get("status", "unknown")
            ans = res.get("answer", "")
            msg = res.get("message", "")
            lat = f"{res.get('latency_seconds', 0.0):.3f}s"
            route = res.get("route", "direct")
            ev = res.get("evidence", [])
            calcs = res.get("calculations", [{}])[0] if res.get("calculations") else {}

            session["last_status"] = status

            # On failure or refusal, ensure answer text is cleared
            if status not in {"ok", "demo_only"}:
                ans = ""

            return ans, status, lat, route, msg, ev, calcs, session

        def handle_clear(session):
            session["last_query"] = ""
            session["last_status"] = ""
            return (
                "",
                "ready",
                "0.000s",
                "cleared",
                "",
                [],
                {},
                session,
            )

        submit_btn.click(
            handle_query,
            inputs=[
                query_input,
                selected_company,
                filter_period,
                filter_scope,
                mode_selector,
                calc_plan_input,
                chart_selector,
                demo_only,
                session_state,
            ],
            outputs=[
                answer_output,
                status_badge,
                latency_badge,
                route_badge,
                diag_message,
                evidence_table,
                calc_trace,
                session_state,
            ],
            api_name="answer_interactive",
        )

        selected_company.change(
            lambda choice: filing_period_by_label.get(choice, ""),
            inputs=[selected_company],
            outputs=[filter_period],
            api_name="select_filing",
        )

        clear_btn.click(
            handle_clear,
            inputs=[session_state],
            outputs=[
                query_input,
                status_badge,
                latency_badge,
                route_badge,
                diag_message,
                evidence_table,
                calc_trace,
                session_state,
            ],
            api_name="clear_session",
        )

    return demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Print readiness without starting a server.")
    args = parser.parse_args()
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        parser.exit(2, f"Configuration error: {exc}\n")

    application = InteractiveApplication(settings)

    if args.check:
        print(json.dumps(application.readiness(), indent=2))
        return

    demo = create_demo(application)
    demo.launch(
        server_name=settings.host,
        server_port=settings.port,
        share=False,
        inbrowser=False,
        show_error=False,
    )


if __name__ == "__main__":
    main()
