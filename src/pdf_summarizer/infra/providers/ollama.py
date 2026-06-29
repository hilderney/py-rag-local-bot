import json
from urllib.error import URLError
from urllib.request import urlopen

from ollama import chat

from pdf_summarizer.core.exceptions import LlmError
from pdf_summarizer.core.models import LlmResponse, ProviderResult
from pdf_summarizer.core.summary.schema import (
    FORMATO_RESPOSTA_LLM,
    construir_requisicao_ollama,
    parse_resposta_json,
)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_OPTIONS = {
    "temperature": 0.2,
    "num_predict": 4096,
    "num_ctx": 32768,
}
MAX_JSON_RETRIES = 5
FALLBACK_TEXT_LIMITS = (4000, 2000)


def _extrair_conteudo_resposta(response: object) -> str:
    """Extrai o texto da resposta do Ollama (dict legado ou ChatResponse 0.6+)."""
    message = getattr(response, "message", None)
    if message is not None:
        return getattr(message, "content", "") or ""

    chunks = response if isinstance(response, list) else [response]
    resposta_completa = ""
    for chunk in chunks:
        if isinstance(chunk, dict) and "message" in chunk:
            resposta_completa += chunk["message"].get("content", "")
        elif getattr(chunk, "message", None) is not None:
            resposta_completa += getattr(chunk.message, "content", "") or ""
        if isinstance(chunk, dict) and chunk.get("done", False):
            break
    return resposta_completa


def _texto_lengths(texto: str) -> list[int]:
    lengths = [len(texto)]
    for limit in FALLBACK_TEXT_LIMITS:
        if len(texto) > limit:
            lengths.append(limit)
    return sorted(set(lengths), reverse=True)


def _to_provider_result(
    model: str,
    requisicao: dict,
    parsed: dict,
) -> ProviderResult:
    return ProviderResult(
        modelo=model,
        provedor="ollama",
        requisicao=requisicao,
        llm_response=LlmResponse(
            resposta=str(parsed.get("resposta", "")),
            resumo=str(parsed.get("resumo", "")),
        ),
    )


class OllamaProvider:
    """Provider LLM via Ollama local."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def health_check(self) -> bool:
        try:
            with urlopen(f"{self._base_url}/", timeout=3) as response:
                return response.status == 200
        except (URLError, OSError, TimeoutError):
            return False

    def summarize(self, texto: str, model: str, user_prompt: str) -> ProviderResult:
        last_error: LlmError | None = None
        for size in _texto_lengths(texto):
            try:
                return self._summarize_texto(texto[:size], model, user_prompt)
            except LlmError as exc:
                last_error = exc

        assert last_error is not None
        raise last_error

    def _summarize_texto(self, texto: str, model: str, user_prompt: str) -> ProviderResult:
        requisicao = construir_requisicao_ollama(texto, user_prompt)
        mensagem = json.dumps(requisicao, ensure_ascii=False)
        last_json_error: json.JSONDecodeError | None = None

        try:
            for _ in range(MAX_JSON_RETRIES):
                response = chat(
                    model=model,
                    messages=[{"role": "user", "content": mensagem}],
                    stream=False,
                    format=FORMATO_RESPOSTA_LLM,
                    options=OLLAMA_CHAT_OPTIONS,
                )
                resposta_completa = _extrair_conteudo_resposta(response)
                if not resposta_completa.strip():
                    raise LlmError("Resposta vazia do Ollama")

                try:
                    parsed = parse_resposta_json(resposta_completa)
                    return _to_provider_result(model, requisicao, parsed)
                except json.JSONDecodeError as exc:
                    last_json_error = exc

            raise LlmError(
                f"Resposta JSON inválida do Ollama após {MAX_JSON_RETRIES} tentativas: "
                f"{last_json_error}"
            ) from last_json_error
        except LlmError:
            raise
        except Exception as exc:
            raise LlmError(f"Erro na chamada Ollama: {exc}") from exc
