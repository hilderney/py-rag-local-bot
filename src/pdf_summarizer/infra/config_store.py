import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from pdf_summarizer.core.model_catalog import DEFAULT_MODEL_CATALOG, catalog_to_config
from pdf_summarizer.core.models import (
    DEFAULT_MAX_CHARS_OLLAMA,
    DEFAULT_MAX_CHARS_OPENROUTER,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENROUTER_MODEL,
)
from pdf_summarizer.core.summary.schema import DEFAULT_USER_PROMPT

CONFIG_DIR_NAME = "PDFSummarizer"
CONFIG_FILE_NAME = "config.json"


class ConfigStore:
    """Persistência de configuração em %APPDATA%/PDFSummarizer/config.json."""

    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is None:
            appdata = os.environ.get("APPDATA")
            if not appdata:
                config_dir = Path.home() / CONFIG_DIR_NAME
            else:
                config_dir = Path(appdata) / CONFIG_DIR_NAME
        self._config_dir = config_dir
        self._config_path = self._config_dir / CONFIG_FILE_NAME

    @property
    def config_path(self) -> Path:
        return self._config_path

    def _defaults(self) -> dict[str, Any]:
        return {
            "input_dir": "",
            "output_dir": "",
            "provider": "ollama",
            "model": DEFAULT_OLLAMA_MODEL,
            "api_key": "",
            "max_chars": DEFAULT_MAX_CHARS_OLLAMA,
            "model_catalog": catalog_to_config(list(DEFAULT_MODEL_CATALOG)),
            "user_prompt": DEFAULT_USER_PROMPT,
        }

    def _apply_provider_defaults(self, data: dict[str, Any]) -> dict[str, Any]:
        provider = data.get("provider", "ollama")
        if provider == "openrouter":
            if not data.get("model"):
                data["model"] = DEFAULT_OPENROUTER_MODEL
            if not data.get("max_chars"):
                data["max_chars"] = DEFAULT_MAX_CHARS_OPENROUTER
        else:
            if not data.get("model"):
                data["model"] = DEFAULT_OLLAMA_MODEL
            if not data.get("max_chars"):
                data["max_chars"] = DEFAULT_MAX_CHARS_OLLAMA
        return data

    def load(self) -> dict[str, Any]:
        load_dotenv()
        data = self._defaults()

        if self._config_path.is_file():
            stored = json.loads(self._config_path.read_text(encoding="utf-8"))
            data.update({k: v for k, v in stored.items() if v is not None})

        env_key = os.environ.get("OPENROUTER_API_KEY", "")
        if env_key and not data.get("api_key"):
            data["api_key"] = env_key

        return self._apply_provider_defaults(data)

    def save(self, data: dict[str, Any]) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        to_save = self._apply_provider_defaults({**self._defaults(), **data})
        self._config_path.write_text(
            json.dumps(to_save, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
