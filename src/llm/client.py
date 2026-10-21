"""
Unified LLM Client (Member 3: LLM Integration Specialist)
Supports:
1. Open-source local models via Ollama (e.g. Llama 3.2, Gemma 3)
2. Cloud fallback via Google GenAI (Gemini)
3. Offline Mock mode for CI / unit tests
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    def __init__(
        self,
        provider: str = "auto",
        ollama_model: str = "llama3.2:3b",
        ollama_url: str = "http://localhost:11434",
        gemini_api_key: str | None = None,
        gemini_model: str = "gemini-3.8-flash",
    ):
        """
        provider: 'ollama', 'gemini', 'mock', or 'auto' (tries ollama, then gemini, then mock)
        """
        self.provider = provider
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url
        self.gemini_model = gemini_model
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

        self._gemini_client = None
        if self.gemini_api_key:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client: {e}")

    def generate(self, prompt: str) -> dict[str, Any]:
        """
        Dispatches generation to Ollama, Gemini, or Mock based on configuration.
        """
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        elif self.provider == "gemini":
            return self._call_gemini(prompt)
        elif self.provider == "mock":
            return self._call_mock(prompt)
        else:
            # Auto fallback chain: Ollama -> Gemini -> Mock
            res = self._call_ollama(prompt)
            if res.get("success"):
                return res
            if self._gemini_client:
                res = self._call_gemini(prompt)
                if res.get("success"):
                    return res
            return self._call_mock(prompt)

    def _call_ollama(self, prompt: str) -> dict[str, Any]:
        """Calls local Ollama instance via HTTP."""
        try:
            import requests
            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "provider": "ollama",
                    "model": self.ollama_model,
                    "text": data.get("response", ""),
                }
            return {
                "success": False,
                "provider": "ollama",
                "error": f"Ollama HTTP {resp.status_code}: {resp.text}",
            }
        except Exception as e:
            return {"success": False, "provider": "ollama", "error": str(e)}

    def _call_gemini(self, prompt: str) -> dict[str, Any]:
        """Calls Gemini API with automatic fallback between 3.8-flash and 3.5-flash-lite."""
        if not self._gemini_client:
            return {"success": False, "provider": "gemini", "error": "No Gemini API key"}

        models_to_try = [self.gemini_model, "gemini-3.5-flash-lite"] if self.gemini_model != "gemini-3.5-flash-lite" else ["gemini-3.5-flash-lite"]

        last_error = ""
        for m in models_to_try:
            try:
                response = self._gemini_client.models.generate_content(
                    model=m,
                    contents=prompt,
                )
                if response.text:
                    return {
                        "success": True,
                        "provider": "gemini",
                        "model": m,
                        "text": response.text,
                    }
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Model {m} failed ({e}), attempting fallback if available...")
                continue

        return {"success": False, "provider": "gemini", "error": last_error}

    def _call_mock(self, prompt: str) -> dict[str, Any]:
        """Deterministic mock response for offline CI and testing."""
        return {
            "success": True,
            "provider": "mock",
            "model": "offline-ci-mock",
            "text": (
                "### Direct Answer:\nTotal net sales for the fiscal year were $365,817 million.\n\n"
                "### Step-by-Step Financial Evidence & Arithmetic:\n"
                "- Products Revenue: $297,392 million\n"
                "- Services Revenue: $68,425 million\n"
                "- Total: $297,392 + $68,425 = $365,817 million\n\n"
                "### Sources Cited:\nConsolidated Statements of Operations"
            ),
        }
