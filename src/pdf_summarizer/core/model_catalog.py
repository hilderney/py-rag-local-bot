from dataclasses import dataclass
from typing import Literal

from pdf_summarizer.core.models import DEFAULT_OLLAMA_MODEL, DEFAULT_OPENROUTER_MODEL

ProviderName = Literal["ollama", "openrouter"]

PROVIDER_LABELS: dict[ProviderName, str] = {
    "ollama": "Ollama",
    "openrouter": "OpenRouter",
}


@dataclass(frozen=True)
class ModelEntry:
    model: str
    provider: ProviderName

    @property
    def label(self) -> str:
        return format_model_label(self.model, self.provider)


def format_model_label(model: str, provider: ProviderName) -> str:
    return f"{model} | {PROVIDER_LABELS[provider]}"


def parse_model_label(label: str) -> ModelEntry:
    if " | " not in label:
        raise ValueError(f"Rótulo de modelo inválido: {label!r}")
    model, provider_label = label.rsplit(" | ", 1)
    provider = _provider_from_label(provider_label.strip())
    model = model.strip()
    if not model:
        raise ValueError(f"Rótulo de modelo inválido: {label!r}")
    return ModelEntry(model=model, provider=provider)


def _provider_from_label(label: str) -> ProviderName:
    normalized = label.lower()
    for provider, display in PROVIDER_LABELS.items():
        if normalized == display.lower() or normalized == provider:
            return provider
    raise ValueError(f"Origem desconhecida: {label!r}")


DEFAULT_MODEL_CATALOG: tuple[ModelEntry, ...] = (
    ModelEntry(DEFAULT_OLLAMA_MODEL, "ollama"),
    ModelEntry("phi3", "ollama"),
    ModelEntry("deepseek-r1:1.5b", "ollama"),
    ModelEntry(DEFAULT_OPENROUTER_MODEL, "openrouter"),
)


def catalog_from_config(data: list[dict] | None) -> list[ModelEntry]:
    if not data:
        return list(DEFAULT_MODEL_CATALOG)

    catalog: list[ModelEntry] = []
    for item in data:
        model = str(item.get("model", "")).strip()
        provider = item.get("provider", "ollama")
        if not model or provider not in PROVIDER_LABELS:
            continue
        entry = ModelEntry(model=model, provider=provider)
        if entry not in catalog:
            catalog.append(entry)

    return catalog or list(DEFAULT_MODEL_CATALOG)


def catalog_to_config(catalog: list[ModelEntry]) -> list[dict[str, str]]:
    return [{"model": entry.model, "provider": entry.provider} for entry in catalog]


def ensure_entry_in_catalog(
    catalog: list[ModelEntry],
    provider: ProviderName,
    model: str,
) -> list[ModelEntry]:
    model = model.strip()
    if not model:
        return catalog
    entry = ModelEntry(model=model, provider=provider)
    if entry in catalog:
        return catalog
    return [*catalog, entry]


def find_label(catalog: list[ModelEntry], provider: ProviderName, model: str) -> str | None:
    model = model.strip()
    for entry in catalog:
        if entry.model == model and entry.provider == provider:
            return entry.label
    return None
