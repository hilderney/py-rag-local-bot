import pytest

from pdf_summarizer.core.model_catalog import (
    DEFAULT_MODEL_CATALOG,
    ModelEntry,
    catalog_from_config,
    catalog_to_config,
    ensure_entry_in_catalog,
    format_model_label,
    parse_model_label,
)


def test_format_and_parse_label():
    label = format_model_label("gemma3:270m", "ollama")
    assert label == "gemma3:270m | Ollama"
    entry = parse_model_label(label)
    assert entry.model == "gemma3:270m"
    assert entry.provider == "ollama"


def test_catalog_roundtrip():
    catalog = list(DEFAULT_MODEL_CATALOG)
    restored = catalog_from_config(catalog_to_config(catalog))
    assert restored == catalog


def test_ensure_entry_in_catalog():
    catalog = [ModelEntry("phi3", "ollama")]
    updated = ensure_entry_in_catalog(catalog, "openrouter", "nvidia/test")
    assert len(updated) == 2
    assert ensure_entry_in_catalog(updated, "openrouter", "nvidia/test") == updated


def test_parse_invalid_label():
    with pytest.raises(ValueError):
        parse_model_label("sem-separador")
