"""Canonical local launch: python app.py. No model/data downloads on startup."""

import argparse
import json

from src.application import SetupApplication
from src.config import ConfigurationError, load_settings


def create_demo(application):
    import gradio as gr

    readiness = application.readiness()
    with gr.Blocks(title="FinRAG") as demo:
        gr.Markdown("# FinRAG\nAsk questions about a company annual report and check the evidence.")
        gr.Markdown("**Setup build — not ready to answer yet.**\n\n" +
                    "\n".join(f"- {item}" for item in readiness["blockers"]))
        query = gr.Textbox(label="Your question", placeholder="How did Apple's revenue change?", lines=2)
        button = gr.Button("Check readiness", variant="primary")
        status = gr.Textbox(label="Status", value=readiness["status"], interactive=False)
        message = gr.Textbox(label="What is needed", lines=6, interactive=False)
        answer = gr.Textbox(label="Answer", interactive=False)
        with gr.Accordion("Source evidence", open=False):
            evidence = gr.JSON(label="Evidence", value=[])

        def respond(question):
            result = application.answer(question)
            return result["status"], result["message"], result["answer"], result["evidence"]

        button.click(respond, inputs=query, outputs=[status, message, answer, evidence],
                     api_name="check_readiness")
    return demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Print readiness without starting a server.")
    args = parser.parse_args()
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        parser.exit(2, f"Configuration error: {exc}\n")
    application = SetupApplication(settings)
    if args.check:
        print(json.dumps(application.readiness(), indent=2))
        return
    demo = create_demo(application)
    demo.launch(server_name=settings.host, server_port=settings.port, share=False,
                inbrowser=False, show_error=False)


if __name__ == "__main__":
    main()
