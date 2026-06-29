from openai import OpenAI

from pdf_summarizer.core.exceptions import ConfigError, LlmError
from pdf_summarizer.core.models import LlmResponse, ProviderResult
from pdf_summarizer.core.summary.schema import (
    construir_requisicao_openrouter,
    parse_resposta_json,
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider:
    """Provider LLM via OpenRouter API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = OPENROUTER_BASE_URL,
    ) -> None:
        if not api_key:
            raise ConfigError("API key obrigatória para OpenRouter")
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/ZAPFCOORP/py-rag-local-bot",
                "X-Title": "Py-RAG-Local-Bot",
            },
        )

    def health_check(self) -> bool:
        return bool(self._client.api_key)

    def summarize(self, texto: str, model: str, user_prompt: str) -> ProviderResult:
        prompt = construir_requisicao_openrouter(texto, user_prompt)

        try:
            resposta_api = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
                stream=False,
            )
            conteudo = resposta_api.choices[0].message.content or ""
            parsed = parse_resposta_json(conteudo)
        except Exception as exc:
            raise LlmError(f"Erro na chamada OpenRouter: {exc}") from exc

        return ProviderResult(
            modelo=model,
            provedor="openrouter",
            requisicao=prompt,
            llm_response=LlmResponse(
                resposta=str(parsed.get("resposta", "")),
                resumo=str(parsed.get("resumo", "")),
            ),
        )
