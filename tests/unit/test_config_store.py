import json
from pathlib import Path

import pytest

from pdf_summarizer.core.models import DEFAULT_OLLAMA_MODEL
from pdf_summarizer.infra.config_store import ConfigStore


@pytest.fixture
def config_store(tmp_path: Path, monkeypatch) -> ConfigStore:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    return ConfigStore()


def test_load_defaults(config_store: ConfigStore):
    data = config_store.load()
    assert data["provider"] == "ollama"
    assert data["model"] == DEFAULT_OLLAMA_MODEL


def test_save_and_load(config_store: ConfigStore):
    config_store.save(
        {
            "input_dir": "C:/docs/pdfs",
            "output_dir": "C:/docs/saida",
            "provider": "openrouter",
            "model": "nvidia/test",
            "api_key": "sk-test",
        }
    )
    loaded = config_store.load()
    assert loaded["input_dir"] == "C:/docs/pdfs"
    assert loaded["provider"] == "openrouter"
    assert loaded["api_key"] == "sk-test"


def test_env_api_key_fallback(config_store: ConfigStore, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-from-env")
    data = config_store.load()
    assert data["api_key"] == "sk-from-env"


def test_config_file_persisted(config_store: ConfigStore):
    config_store.save({"input_dir": "C:/in"})
    assert config_store.config_path.is_file()
    stored = json.loads(config_store.config_path.read_text(encoding="utf-8"))
    assert stored["input_dir"] == "C:/in"
