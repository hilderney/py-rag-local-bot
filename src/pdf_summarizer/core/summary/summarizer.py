from pathlib import Path

from pdf_summarizer.core.models import JobConfig, LlmDocument, LlmOutcome, ProviderResult
from pdf_summarizer.core.summary.schema import validate_resposta_llm
from pdf_summarizer.infra.filesystem import FileSystem
from pdf_summarizer.infra.providers.base import LLMProvider


class Summarizer:
    """Orquestra truncamento, delegação ao provider e montagem do documento final."""

    def __init__(self, provider: LLMProvider, max_chars: int = 8000) -> None:
        self._provider = provider
        self._max_chars = max_chars

    def process(
        self,
        texto: str,
        config: JobConfig,
        stem: str,
        pdf_path: Path | None = None,
    ) -> LlmOutcome:
        truncated = False
        texto_enviado = texto
        if len(texto) > self._max_chars:
            texto_enviado = texto[: self._max_chars]
            truncated = True

        provider_result = self._provider.summarize(
            texto_enviado,
            config.model,
            config.user_prompt,
        )
        validate_resposta_llm(
            {
                "resposta": provider_result.llm_response.resposta,
                "resumo": provider_result.llm_response.resumo,
            }
        )

        artifacts = FileSystem.resolve_artifacts(config.output_dir, stem, pdf_path)
        document = LlmDocument(
            modelo=config.model,
            provedor=config.provider,
            texto=texto_enviado,
            requisitado=config.user_prompt,
            resposta=provider_result.llm_response.resposta,
            resumo=provider_result.llm_response.resumo,
            arquivos=artifacts,
        )
        return LlmOutcome(document=document, truncated=truncated)
