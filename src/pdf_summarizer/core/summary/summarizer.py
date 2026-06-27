from pdf_summarizer.core.models import SummaryResult, SummarizeOutcome
from pdf_summarizer.core.summary.schema import validate_resposta
from pdf_summarizer.infra.providers.base import LLMProvider


class Summarizer:
    """Orquestra truncamento e delegação ao provider LLM."""

    def __init__(self, provider: LLMProvider, max_chars: int = 8000) -> None:
        self._provider = provider
        self._max_chars = max_chars

    def summarize(self, texto: str, model: str, user_prompt: str) -> SummarizeOutcome:
        truncated = False
        if len(texto) > self._max_chars:
            texto = texto[: self._max_chars]
            truncated = True

        result = self._provider.summarize(texto, model, user_prompt)
        validate_resposta(result.resposta)
        return SummarizeOutcome(result=result, truncated=truncated)
