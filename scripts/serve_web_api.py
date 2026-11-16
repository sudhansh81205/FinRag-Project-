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
from src.web_api import WebApplication, build_prepared_engine  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--enable-engine", action="store_true")
    parser.add_argument("--variant", choices=["C", "D"], default="D")
    parser.add_argument("--tokenizer-dir")
    args = parser.parse_args()
    token = os.environ.get("FINRAG_API_TOKEN", "")
    if len(token) < 32:
        parser.error("Set FINRAG_API_TOKEN to a private value of at least 32 characters.")
    settings = load_settings()
    engine = build_prepared_engine(settings, variant=args.variant, tokenizer_dir=args.tokenizer_dir) if args.enable_engine else None
    app = WebApplication(settings, engine)

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
            self.respond(app.health() if self.path == "/health" else {"status": "not_found"}, 200 if self.path == "/health" else 404)

        def do_POST(self):
            if not self.authorized():
                return
            if self.path != "/answer":
                self.respond({"status": "not_found"}, 404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 12000:
                    raise ValueError("size")
                result = app.answer(json.loads(self.rfile.read(size)))
            except (ValueError, TypeError):
                result = {"status": "invalid_request", "answer": "", "message": "Invalid JSON request."}
            except Exception:
                result = {"status": "service_error", "answer": "", "message": "Financial execution failed; no fallback used."}
            self.respond(result, 400 if result["status"] == "invalid_request" else 200)

    print(f"FinRAG authenticated API on {args.host}:{args.port}; engine enabled: {engine is not None}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
