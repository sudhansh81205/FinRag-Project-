"""R4/R12: count the installed generator's tokens and reject oversized prompts.

The local llama.cpp tokenizer reads the same hash-pinned GGUF as Ollama; no
substitute BGE tokenizer or character estimate can license a model call.
"""

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


class GGUFTokenCounter:
    def __init__(self, url, model_path, expected_sha256, *, server_root=None):
        parsed = urlparse(url)
        if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in {"", "/"}):
            raise ValueError("Tokenizer must be an explicit loopback HTTP service")
        self.url = url.rstrip("/")
        self.model_path = Path(model_path).resolve()
        self.server_root = Path(server_root or Path.cwd()).resolve()
        h = hashlib.sha256()
        with self.model_path.open("rb") as f:
            for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != expected_sha256:
            raise ValueError("GGUF tokenizer source does not match the pinned model bytes")
        self.identity = "llama.cpp:gguf-sha256:" + h.hexdigest()
        self._verify_server()

    def _verify_server(self):
        response = requests.get(self.url + "/props", timeout=15)
        response.raise_for_status()
        path = Path(response.json()["model_path"])
        actual = (self.server_root / path).resolve() if not path.is_absolute() else path.resolve()
        if actual != self.model_path:
            raise ValueError("Tokenizer service loaded a different model file")

    def __call__(self, text):
        if not isinstance(text, str):
            raise ValueError("Token counter requires text")
        self._verify_server()  # a restarted server must not inherit a cached identity
        response = requests.post(self.url + "/tokenize",
                                 json={"content": text, "add_special": True, "parse_special": False},
                                 timeout=15)
        response.raise_for_status()
        tokens = response.json().get("tokens")
        if not isinstance(tokens, list) or any(type(t) is not int for t in tokens):
            raise ValueError("Tokenizer returned invalid token IDs")
        return len(tokens)


class BudgetedClient:
    """Enforce the full planner/answer prompt budget before any generation call."""

    def __init__(self, client, counter, *, input_tokens=3000, context_tokens=4096,
                 output_tokens=768, template_reserve=32):
        values = [input_tokens, context_tokens, output_tokens, template_reserve]
        if any(type(v) is not int or v < 1 for v in values):
            raise ValueError("Token budgets must be positive integers")
        if input_tokens + output_tokens + template_reserve > context_tokens:
            raise ValueError("Prompt/output/template token budgets exceed the model context")
        self.client, self.counter = client, counter
        self.input_tokens = input_tokens

    def __getattr__(self, name):
        return getattr(self.client, name)

    def generate(self, prompt, *, images=None, response_format=None):
        try:
            if images is not None:
                return self.client._failure("unmeasured_image_budget", "Image tokens require a separately measured vision budget.")
            count = self.counter(prompt)
            if type(count) is not int or count < 0:
                raise ValueError("Invalid token count")
            if count > self.input_tokens:
                return self.client._failure("prompt_token_budget", "The complete prompt exceeds the fixed input budget; no model call made.")
        except Exception:
            return self.client._failure("tokenizer_failed", "The pinned generator tokenizer could not validate the prompt.")
        result = self.client.generate(prompt, response_format=response_format)
        result["prompt_budget"] = {"used": count, "limit": self.input_tokens,
                                   "scope": "complete prompt before model chat template"}
        return result
