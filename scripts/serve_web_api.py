"""Run the authenticated FinRAG service on a prepared machine (no model downloads)."""
import argparse
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import load_settings  # noqa: E402
from src.web_api import WebApplication, build_prepared_engine, build_source_checked_engine  # noqa: E402
from src.web_jobs import AnswerJobs  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    runtime = parser.add_mutually_exclusive_group()
    runtime.add_argument("--enable-engine", action="store_true")
    runtime.add_argument("--workspace-corpus", type=Path, help="Source-checked application corpus with per-filing exact indexes")
    runtime.add_argument("--source-audit", type=Path,
                         help="Bounded checked Apple development runtime; never final experiment acceptance")
    parser.add_argument("--variant", choices=list("ABCDEFG"), default="D")
    parser.add_argument("--representation", choices=["A", "B"])
    parser.add_argument("--reranker-dir", type=Path)
    parser.add_argument("--tokenizer-dir")
    parser.add_argument("--tokenizer-url", help="Existing local llama.cpp tokenizer service")
    parser.add_argument("--gguf", type=Path, help="Existing generator GGUF file used by that service")
    parser.add_argument("--gguf-sha256", help="Expected SHA-256 of the installed generator GGUF")
    parser.add_argument("--model-cache", type=Path)
    parser.add_argument("--gradio-port", type=int, help="Also serve the required Gradio UI on loopback using this same engine")
    parser.add_argument("--job-store", type=Path, default=ROOT / "output/web-jobs.sqlite3",
                        help="Private single-process job state; unfinished jobs fail on restart")
    args = parser.parse_args()
    token = os.environ.get("FINRAG_API_TOKEN", "")
    if len(token) < 32:
        parser.error("Set FINRAG_API_TOKEN to a private value of at least 32 characters.")
    settings = load_settings()
    counter, tokenizer_id = None, None
    if args.tokenizer_url:
        if not args.gguf or not args.gguf_sha256:
            parser.error("--tokenizer-url requires --gguf and --gguf-sha256")
        from src.llm.token_budget import GGUFTokenCounter
        counter = GGUFTokenCounter(args.tokenizer_url, args.gguf, args.gguf_sha256, server_root=ROOT)
        tokenizer_id = counter.identity
    if args.workspace_corpus:
        if counter is None or args.variant != "D":
            parser.error("Workspace corpus requires D and the identified generator tokenizer")
        from src.workspace_corpus import build_workspace_engine
        engine = build_workspace_engine(settings, args.workspace_corpus, token_counter=counter,
                                        tokenizer_id=tokenizer_id, model_cache=args.model_cache)
    elif args.source_audit:
        if args.variant != "D":
            parser.error("The bounded source-audit development runtime is D; use accepted --enable-engine for other variants.")
        if counter is None:
            parser.error("The bounded source runtime requires the identified installed GGUF tokenizer")
        engine = build_source_checked_engine(settings, args.source_audit, token_counter=counter,
                                              tokenizer_id=tokenizer_id, model_cache=args.model_cache)
    elif args.enable_engine:
        engine = build_prepared_engine(settings, variant=args.variant, tokenizer_dir=args.tokenizer_dir,
                                        token_counter=counter, tokenizer_id=tokenizer_id, model_cache=args.model_cache,
                                        representation=args.representation, reranker_dir=args.reranker_dir)
    else:
        engine = None
    app = WebApplication(settings, engine)
    jobs = AnswerJobs(args.job_store, app.answer)
    gradio_demo = None
    if args.gradio_port is not None:
        if not 1024 <= args.gradio_port <= 65535 or args.gradio_port in {args.port, 11434, 11435}:
            parser.error("Choose a separate Gradio port between 1024 and 65535")
        from app import create_demo
        from src.web_api import GradioApplication
        gradio_demo = create_demo(GradioApplication(app))
        gradio_demo.launch(server_name="127.0.0.1", server_port=args.gradio_port, share=False,
                           inbrowser=False, show_error=False, prevent_thread_lock=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # questions, authorization headers and provider messages are not request logs

        def respond(self, body, status=200):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def authorized(self):
            if not hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}"):
                self.respond({"status": "unauthorized", "answer": ""}, 401)
                return False
            return True

        def do_GET(self):
            if not self.authorized():
                return
            self.respond({**app.health(), "jobs_supported": True} if self.path == "/health" else {"status": "not_found"}, 200 if self.path == "/health" else 404)

        def do_POST(self):
            if not self.authorized():
                return
            if self.path not in {"/answer", "/jobs", "/jobs/poll"}:
                self.respond({"status": "not_found"}, 404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 12000:
                    raise ValueError("size")
                payload = json.loads(self.rfile.read(size))
                if self.path == "/jobs":
                    result = jobs.submit(payload)
                elif self.path == "/jobs/poll":
                    result = jobs.poll(payload.get("job_id") if isinstance(payload, dict) else None)
                else:
                    result = app.answer(payload)
            except (ValueError, TypeError):
                result = {"status": "invalid_request", "answer": "", "message": "Invalid JSON request."}
            except Exception:
                result = {"status": "service_error", "answer": "", "message": "Financial execution failed; no fallback used."}
            self.respond(result, 400 if result["status"] == "invalid_request" else 429 if result["status"] == "busy" else 200)

    print(f"FinRAG authenticated API on {args.host}:{args.port}; engine enabled: {engine is not None}")
    try:
        ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    finally:
        jobs.close()
        if gradio_demo is not None:
            gradio_demo.close()


if __name__ == "__main__":
    main()
