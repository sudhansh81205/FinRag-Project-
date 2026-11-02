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

    @property
    def model(self) -> str:
        if self.provider == "ollama":
            return self.ollama_model
        if self.provider == "gemini":
            return self.gemini_model
        return "offline-ci-mock" if self.provider == "mock" else ""

    @classmethod
    def from_settings(cls, settings):
        return cls(provider=settings.provider, ollama_model=settings.model,
                   ollama_url=settings.ollama_url, gemini_api_key=settings.gemini_api_key,
                   gemini_model=settings.model)

    def _failure(self, code: str, message: str) -> dict[str, Any]:
        # Never expose exception strings, response bodies, URLs or keys in logs/UI.
        return {"success": False, "status": "service_error", "provider": self.provider,
                "model": self.model, "text": "", "error_code": code, "error": message}

    def _success(self, text: Any) -> dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            return self._failure("empty_response", "The provider returned no answer text.")
        return {"success": True, "status": "ok", "provider": self.provider,
                "model": self.model, "text": text.strip()}

    def generate(self, prompt: str) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            return self._failure("empty_prompt", "A nonempty prompt is required.")
        if self.provider == "mock":
            return {"success": True, "status": "test_only", "provider": "mock",
                    "model": self.model, "text": "TEST ONLY: synthetic provider response."}
        if self.provider == "unconfigured" or not self.model:
            return self._failure("not_configured", "Configure one real provider and model.")
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        return self._call_gemini(prompt)

    def _call_ollama(self, prompt: str) -> dict[str, Any]:
        try:
            import requests
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False,
                      "think": False, "options": {"temperature": 0}},
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                return self._failure("provider_http_error", "Ollama rejected the request; check its model and service.")
            data = response.json()
            if not isinstance(data, dict) or data.get("error") or data.get("done") is not True:
                return self._failure("invalid_response", "Ollama returned an invalid or incomplete response.")
            if data.get("model") != self.model:
                return self._failure("model_mismatch", "Ollama returned a different model than configured.")
            return self._success(data.get("response"))
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
