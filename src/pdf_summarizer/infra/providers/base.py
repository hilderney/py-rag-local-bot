from typing import Protocol

from pdf_summarizer.core.models import JobConfig, ProviderResult


class LLMProvider(Protocol):
    def summarize(self, texto: str, model: str, user_prompt: str) -> ProviderResult: ...

    def health_check(self) -> bool: ...


def create_provider(config: JobConfig) -> LLMProvider:
    from pdf_summarizer.core.exceptions import ConfigError
    from pdf_summarizer.infra.providers.ollama import OllamaProvider
    from pdf_summarizer.infra.providers.openrouter import OpenRouterProvider

    if config.provider == "ollama":
        return OllamaProvider()
    if config.provider == "openrouter":
        if not config.api_key:
            raise ConfigError("API key obrigatória para provider openrouter")
        return OpenRouterProvider(api_key=config.api_key)
    raise ConfigError(f"Provider desconhecido: {config.provider}")
