"""Start the bounded loopback development workspace from existing verified assets.

R4/R6/R13: explicit assets, private server-side token, health-checked startup.
No downloads, final acceptance, cloud exposure or login changes are performed.
Child services detach from the calling terminal and write only local logs.
"""
import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
GGUF_SHA256 = "f06e91e18fc74295d0c781bf91622508c75655e2c18ed869d52447ffe1e667e1"


def validate_assets(ollama, llama_server, models, gguf, audit, cache):
    for binary in (ollama, llama_server):
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError("An explicit existing executable is required")
    if not models.is_dir() or not cache.is_dir() or not audit.is_file():
        raise ValueError("Existing model/cache/source audit paths are required")
    digest = hashlib.sha256()
    with gguf.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != GGUF_SHA256:
        raise ValueError("The existing GGUF differs from the pinned Gemma source")


def ensure_ports_free(ports):
    for port in ports:
        with socket.socket() as connection:
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise ValueError(f"Port {port} is occupied; inspect the existing service before restarting")


def private_token(path):
    if path.exists():
        if path.is_symlink() or path.stat().st_mode & 0o077:
            raise ValueError("Existing private state must be a regular owner-only file")
        data = json.loads(path.read_text())
        token = data.get("api_token") or data.get("token")
        if not isinstance(token, str) or len(token) < 32:
            raise ValueError("Existing local API token is invalid; do not silently replace credentials")
        return token
    token = secrets.token_urlsafe(48)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump({"api_token": token}, stream)
    return token


def wait_ready(process, url, *, token=None, deadline=120):
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        if process.poll() is not None:
            raise RuntimeError("A local service exited before readiness; inspect its local log")
        try:
            headers = {"Authorization": "Bearer " + token} if token else {}
            response = requests.get(url, headers=headers, timeout=3)
            if response.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(0.3)
    raise RuntimeError("Local service startup deadline exceeded; inspect its local log")


def start(args):
    paths = [Path(getattr(args, key)).expanduser().resolve() for key in
             ("ollama", "llama_server", "models", "gguf", "source_audit", "model_cache")]
    validate_assets(*paths)
    ensure_ports_free((11434, 11435, 8000, args.web_port, *([args.gradio_port] if args.gradio_port else [])))
    state = ROOT / "output/nov17"
    state.mkdir(parents=True, exist_ok=True)
    token = private_token(state / "local-service.json")
    ollama, llama, models, gguf, audit, cache = paths
    children = []

    def launch(name, command, env, cwd=ROOT):
        with (state / f"{name}.log").open("ab") as log:
            child = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True, close_fds=True)
        children.append(child)
        return child

    try:
        env = dict(os.environ, OLLAMA_HOST="127.0.0.1:11434", OLLAMA_MODELS=str(models))
        process = launch("ollama", [str(ollama), "serve"], env)
        wait_ready(process, "http://127.0.0.1:11434/api/tags")
        print("Pinned-model service reachable on loopback", flush=True)
        process = launch("tokenizer", [str(llama), "--model", str(gguf), "--host", "127.0.0.1",
                         "--port", "11435", "--ctx-size", "512", "--no-warmup", "--fit", "off",
                         "--n-gpu-layers", "0", "--parallel", "1"], dict(os.environ))
        wait_ready(process, "http://127.0.0.1:11435/props")
        env = dict(os.environ, FINRAG_API_TOKEN=token, TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1")
        process = launch("api", [sys.executable, "scripts/serve_web_api.py", *(["--workspace-corpus", args.workspace_corpus] if args.workspace_corpus else ["--source-audit", str(audit)]),
                         "--model-cache", str(cache), "--tokenizer-url", "http://127.0.0.1:11435",
                         "--gguf", str(gguf), "--gguf-sha256", GGUF_SHA256,
                         *(["--gradio-port", str(args.gradio_port)] if args.gradio_port else [])], env)
        wait_ready(process, "http://127.0.0.1:8000/health", token=token)
        env = dict(os.environ, FINRAG_BACKEND_URL="http://127.0.0.1:8000", FINRAG_BACKEND_TOKEN=token,
                   FINRAG_WEB_PORT=str(args.web_port), FINRAG_BACKEND_TIMEOUT_MS="240000")
        process = launch("web", [args.node, "--env-file-if-exists=.env", "dev.mjs"], env, ROOT / "web")
        wait_ready(process, f"http://127.0.0.1:{args.web_port}/api/health")
        # This process manifest contains no secret and does not license killing a reused PID.
        (state / "local-processes.json").write_text(json.dumps({"pids": [p.pid for p in children],
             "scope": "loopback development only; final_experiment_ready false"}, indent=2) + "\n")
        print(f"Local workspace ready: http://127.0.0.1:{args.web_port}/ (final acceptance pending)")
    except BaseException:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()  # only subprocess handles this invocation actually created
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = {
        "ollama": ROOT.parent / "ollama/ollama", "llama-server": ROOT.parent / "ollama/llama-server",
        "models": ROOT.parent / "ollama-models",
        "gguf": ROOT.parent / "ollama-models" / "blobs" / ("sha256-" + GGUF_SHA256),
        "source-audit": ROOT / "output/nov17/canonical_audit.json",
        "model-cache": ROOT / "output/models-http",
    }
    for name, default in defaults.items():
        parser.add_argument("--" + name, default=str(default), help="Existing asset path; override for another machine")
    parser.add_argument("--workspace-corpus", default=str(ROOT / "output/nov17/corpus"), help="Prepared source-checked application corpus")
    parser.add_argument("--status", action="store_true", help="Check the local workspace without starting services")
    parser.add_argument("--node", default="node")
    parser.add_argument("--web-port", type=int, default=4180)
    parser.add_argument("--gradio-port", type=int, help="Optional required Gradio workspace, e.g.7860; loopback only")
    args = parser.parse_args()
    if not 1024 <= args.web_port <= 65535 or args.web_port in {8000, 11434, 11435}:
        parser.error("Choose a separate local web port between1024and65535")
    if args.gradio_port and (not 1024 <= args.gradio_port <= 65535
                            or args.gradio_port in {args.web_port, 8000, 11434, 11435}):
        parser.error("Choose a separate Gradio port between 1024 and 65535")
    if args.status:
        try:
            response = requests.get(f"http://127.0.0.1:{args.web_port}/api/health", timeout=8)
            response.raise_for_status()
            health = response.json()
            if not isinstance(health.get("runtime"), dict):
                raise ValueError("Invalid workspace health")
            print(f"Local workspace: http://127.0.0.1:{args.web_port}/")
            print(json.dumps(health, indent=2))
        except (requests.RequestException, ValueError):
            parser.exit(2, "The local workspace is unavailable. Start it using this script without --status.\n")
        return
    start(args)


if __name__ == "__main__":
    main()
