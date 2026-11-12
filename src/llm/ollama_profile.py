"""Resolve an installed Ollama tag to immutable manifest identity before use."""

import re

import requests


def fingerprint(url, model, timeout=15):
    response = requests.get(f"{url.rstrip('/')}/api/tags", timeout=timeout)
    response.raise_for_status()
    matches = [m for m in response.json()["models"] if m.get("name") == model]
    if len(matches) != 1 or not re.fullmatch(r"[a-f0-9]{64}", matches[0].get("digest", "")):
        raise ValueError("Exact model tag is missing or ambiguous.")
    response = requests.post(f"{url.rstrip('/')}/api/show", json={"model": model}, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    details = data.get("details", {})
    return {"model": model, "digest": matches[0]["digest"],
            "family": details.get("family"), "parameter_size": details.get("parameter_size"),
            "quantization_level": details.get("quantization_level"),
            "capabilities": data.get("capabilities", []),
            "model_context_length": next((v for k, v in data.get("model_info", {}).items()
                                           if k.endswith(".context_length")), None)}
