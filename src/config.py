"""Load a single validated configuration without changing process credentials."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(ValueError):
    """Safe-to-display configuration error; never includes supplied values."""


@dataclass(frozen=True)
class Settings:
    root: Path
    raw_dir: Path
    index_dir: Path
    collection: str
    embedding_model: str
    reranker_model: str
    provider: str
    model: str
    ollama_url: str
    host: str
    port: int
    top_k_text: int
    top_k_tables: int
    rerank_top_n: int
    chunk_size: int
    chunk_overlap: int
    min_chunk_length: int
    gemini_api_key: str = field(default="", repr=False)


def load_settings(
    config_path: Path | None = None,
    *,
    root: Path = PROJECT_ROOT,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Precedence: process environment > repository .env > YAML.

    Only named settings are used; no upward .env search or mutation.
    Passing environ={} gives tests an isolated environment.
    """
    root = root.resolve()
    path = config_path or root / "configs/config.yaml"
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError
        sections = {key: document[key] for key in ("app", "data", "models", "retrieval")}
        if not all(isinstance(value, dict) for value in sections.values()):
            raise ValueError
    except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        raise ConfigurationError("Cannot read configuration; check configs/config.yaml.") from exc

    env = {**dotenv_values(root / ".env", interpolate=False),
           **(os.environ if environ is None else environ)}

    def value(section, key, env_key=None, *, allow_empty=False):
        result = env.get(env_key, sections[section].get(key)) if env_key else sections[section].get(key)
        if result is None or isinstance(result, (bool, list, dict)):
            raise ConfigurationError(f"Missing or invalid setting: {section}.{key}.")
        result = str(result).strip()
        if not result and not allow_empty:
            raise ConfigurationError(f"Missing or invalid setting: {section}.{key}.")
        return result

    def integer(section, key, env_key=None, minimum=1, maximum=100000):
        try:
            result = int(value(section, key, env_key))
            if not minimum <= result <= maximum:
                raise ValueError
            return result
        except ValueError as exc:
            raise ConfigurationError(f"Invalid integer setting: {section}.{key}.") from exc

    def directory(key, env_key):
        return (root / value("data", key, env_key)).resolve()

    provider = value("models", "provider", "FINRAG_PROVIDER")
    if provider not in {"unconfigured", "gemini", "ollama"}:
        raise ConfigurationError("FINRAG_PROVIDER must be unconfigured, gemini or ollama.")
    chunk_size = integer("retrieval", "chunk_size")
    overlap = integer("retrieval", "chunk_overlap", minimum=0)
    if overlap >= chunk_size:
        raise ConfigurationError("retrieval.chunk_overlap must be smaller than chunk_size.")
    return Settings(
        root=root,
        raw_dir=directory("raw_dir", "FINRAG_RAW_DIR"),
        index_dir=directory("index_dir", "FINRAG_INDEX_DIR"),
        collection=value("data", "collection", "FINRAG_COLLECTION"),
        embedding_model=value("models", "embedding"),
        reranker_model=value("models", "reranker"),
        provider=provider,
        model=value("models", "model", "FINRAG_MODEL", allow_empty=True),
        ollama_url=value("models", "ollama_url", "OLLAMA_BASE_URL"),
        host=value("app", "host", "FINRAG_HOST"),
        port=integer("app", "port", "FINRAG_PORT", maximum=65535),
        top_k_text=integer("retrieval", "top_k_text"),
        top_k_tables=integer("retrieval", "top_k_tables", minimum=0),
        rerank_top_n=integer("retrieval", "rerank_top_n"),
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        min_chunk_length=integer("retrieval", "min_chunk_length"),
        gemini_api_key=str(env.get("GEMINI_API_KEY") or ""),
    )
