"""Explicit real-provider client. Provider failures never become mock answers."""

from typing import Any


class UnifiedLLMClient:
    def __init__(
        self,
        provider: str = "unconfigured",
        ollama_model: str = "",
        ollama_url: str = "http://localhost:11434",
        gemini_api_key: str | None = None,
        gemini_model: str = "",
        *,
        allow_mock: bool = False,
        timeout_seconds: float = 60,
        expected_digest: str | None = None,
        ollama_options: dict | None = None,
    ):
        if provider not in {"unconfigured", "ollama", "gemini", "mock"}:
            raise ValueError("Select an explicit provider: ollama or gemini; auto is unsupported.")
        if provider == "mock" and not allow_mock:
            raise ValueError("Mock mode requires explicit test-only allow_mock=True.")
        if timeout_seconds <= 0:
            raise ValueError("Provider timeout must be positive.")
        self.provider = provider
        self.ollama_model = ollama_model.strip()
        self.ollama_url = ollama_url.rstrip("/")
        self.gemini_model = gemini_model.strip()
        self._gemini_api_key = gemini_api_key
        self.timeout_seconds = timeout_seconds
        self._gemini_client = None
        self.expected_digest = expected_digest
        self.ollama_options = dict(ollama_options or {})

    @property
    def model(self) -> str:
        if self.provider == "ollama":
            return self.ollama_model
        if self.provider == "gemini":
            return self.gemini_model
        return "offline-ci-mock" if self.provider == "mock" else ""

    @classmethod
    def from_profile(cls, profile):
        if profile.get("provider") != "ollama" or not profile.get("digest"):
            raise ValueError("An installed, digest-pinned Ollama profile is required.")
        return cls(provider="ollama", ollama_model=profile["model"],
                   ollama_url=profile.get("ollama_url", "http://127.0.0.1:11434"),
                   expected_digest=profile["digest"],
                   timeout_seconds=profile.get("timeout_seconds", 180),
                   ollama_options=profile.get("options", {}))

    @classmethod
    def from_settings(cls, settings):
        return cls(provider=settings.provider, ollama_model=settings.model,
                   ollama_url=settings.ollama_url, gemini_api_key=settings.gemini_api_key,
                   gemini_model=settings.model,
                   expected_digest=getattr(settings, "ollama_digest", "") or None,
                   timeout_seconds=getattr(settings, "provider_timeout", 180),
                   ollama_options={"num_ctx": getattr(settings, "ollama_num_ctx", 4096),
                                   "num_predict": getattr(settings, "ollama_num_predict", 768), "seed": 42})

    def _failure(self, code: str, message: str) -> dict[str, Any]:
        # Never expose exception strings, response bodies, URLs or keys in logs/UI.
        return {"success": False, "status": "service_error", "provider": self.provider,
                "model": self.model, "text": "", "error_code": code, "error": message}

    def _success(self, text: Any) -> dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            return self._failure("empty_response", "The provider returned no answer text.")
        return {"success": True, "status": "ok", "provider": self.provider,
                "model": self.model, "text": text.strip()}

    def generate(self, prompt: str, *, images=None, response_format=None) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            return self._failure("empty_prompt", "A nonempty prompt is required.")
        if (images is not None or response_format is not None) and self.provider != "ollama":
            return self._failure("unsupported_input", "Structured vision requests require Ollama.")
        if self.provider == "mock":
            return {"success": True, "status": "test_only", "provider": "mock",
                    "model": self.model, "text": "TEST ONLY: synthetic provider response."}
        if self.provider == "unconfigured" or not self.model:
            return self._failure("not_configured", "Configure one real provider and model.")
        if self.provider == "ollama":
            return self._call_ollama(prompt, images=images, response_format=response_format)
        return self._call_gemini(prompt)

    def _call_ollama(self, prompt: str, *, images=None, response_format=None) -> dict[str, Any]:
        try:
            import requests

            from .ollama_profile import fingerprint
            snapshot = None
            if self.expected_digest or images is not None:
                snapshot = fingerprint(self.ollama_url, self.model, self.timeout_seconds)
                if self.expected_digest and snapshot["digest"] != self.expected_digest:
                    return self._failure("digest_mismatch", "Installed model differs from the pinned digest.")
            payload = {"model": self.model, "prompt": prompt, "stream": False,
                       "think": False, "options": {"temperature": 0, **self.ollama_options}}
            if images is not None:
                if (not isinstance(images, list) or not 1 <= len(images) <= 4
                        or any(not isinstance(i, str) or len(i) > 12000000 for i in images)):
                    return self._failure("invalid_images", "Provide one to four bounded base64 images.")
                if "vision" not in snapshot["capabilities"]:
                    return self._failure("vision_unsupported", "The configured model does not support images.")
                payload["images"] = images
            if response_format is not None:
                payload["format"] = response_format
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                return self._failure("provider_http_error", "Ollama rejected the request; check its model and service.")
            data = response.json()
            if not isinstance(data, dict) or data.get("error") or data.get("done") is not True:
                return self._failure("invalid_response", "Ollama returned an invalid or incomplete response.")
            if data.get("done_reason") == "length":
                return self._failure("truncated_response", "The model reached its output limit; no partial answer was accepted.")
            if data.get("model") != self.model:
                return self._failure("model_mismatch", "Ollama returned a different model than configured.")
            if snapshot and fingerprint(self.ollama_url, self.model, self.timeout_seconds) != snapshot:
                return self._failure("digest_mismatch", "Model identity changed during generation.")
            result = self._success(data.get("response"))
            if snapshot:
                result["model_fingerprint"] = snapshot
            result["timing"] = {k: data.get(k) for k in (
                "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration",
                "eval_count", "eval_duration")}
            return result
        except ImportError:
            return self._failure("dependency_missing", "Install the provider dependencies.")
        except Exception:
            return self._failure("provider_unavailable", "Ollama is unavailable or returned an unreadable response.")

    def _call_gemini(self, prompt: str) -> dict[str, Any]:
        if not self._gemini_api_key:
            return self._failure("credentials_missing", "Gemini credentials are missing.")
        try:
            from google import genai
            from google.genai import types

            if self._gemini_client is None:
                self._gemini_client = genai.Client(
                    api_key=self._gemini_api_key,
                    http_options=types.HttpOptions(
                        timeout=int(self.timeout_seconds * 1000),
                        retry_options=types.HttpRetryOptions(attempts=1),
                    ),
                )
            response = self._gemini_client.models.generate_content(
                model=self.model, contents=prompt,
                config=types.GenerateContentConfig(temperature=0),
            )
            return self._success(response.text)
        except ImportError:
            return self._failure("dependency_missing", "Install requirements-provider.txt for Gemini.")
        except Exception:
            return self._failure("provider_unavailable", "Gemini failed; check credentials, model, quota and network.")
