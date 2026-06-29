from unittest.mock import MagicMock, patch

import json
import pytest

from pdf_summarizer.core.exceptions import ConfigError
from pdf_summarizer.core.models import ProviderResult, LlmResponse
from pdf_summarizer.core.summary.schema import DEFAULT_USER_PROMPT
from pdf_summarizer.infra.providers.base import create_provider
from pdf_summarizer.infra.providers.ollama import OllamaProvider


def test_health_check_ok(mocker):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mocker.patch("pdf_summarizer.infra.providers.ollama.urlopen", return_value=mock_response)

    provider = OllamaProvider()
    assert provider.health_check() is True


def test_health_check_offline(mocker):
    mocker.patch(
        "pdf_summarizer.infra.providers.ollama.urlopen",
        side_effect=OSError("offline"),
    )
    provider = OllamaProvider()
    assert provider.health_check() is False


def test_summarize_chama_ollama_chat(mocker):
    valid_json = '{"resposta":"r","resumo":"meta"}'
    mocker.patch(
        "pdf_summarizer.infra.providers.ollama.chat",
        return_value={
            "message": {"content": valid_json},
            "done": True,
        },
    )

    provider = OllamaProvider()
    result = provider.summarize("texto", "gemma3:270m", DEFAULT_USER_PROMPT)
    assert result.modelo == "gemma3:270m"
    assert result.llm_response.resposta == "r"
    assert result.llm_response.resumo == "meta"


def test_summarize_ollama_chat_response_object(mocker):
    valid_json = '{"resposta":"r","resumo":"meta"}'
    message = MagicMock()
    message.content = valid_json
    response = MagicMock()
    response.message = message
    mocker.patch(
        "pdf_summarizer.infra.providers.ollama.chat",
        return_value=response,
    )

    provider = OllamaProvider()
    result = provider.summarize("texto", "gemma3:270m", DEFAULT_USER_PROMPT)
    assert result.llm_response.resposta == "r"


def test_summarize_repete_ate_json_valido(mocker):
    valid_json = '{"resposta":"r","resumo":"meta"}'
    invalid_response = {"message": {"content": "{"}, "done": True}
    valid_response = {"message": {"content": valid_json}, "done": True}
    chat_mock = mocker.patch("pdf_summarizer.infra.providers.ollama.chat")
    chat_mock.side_effect = [invalid_response, valid_response]

    provider = OllamaProvider()
    result = provider.summarize("texto", "gemma3:270m", DEFAULT_USER_PROMPT)
    assert result.llm_response.resposta == "r"
    assert chat_mock.call_count == 2


def test_summarize_usa_texto_menor_apos_falhas(mocker):
    valid_json = '{"resposta":"r","resumo":"meta"}'
    invalid_response = {"message": {"content": "{"}, "done": True}
    valid_response = {"message": {"content": valid_json}, "done": True}
    texto_longo = "x" * 5000
    chat_mock = mocker.patch("pdf_summarizer.infra.providers.ollama.chat")
    chat_mock.side_effect = [invalid_response] * 5 + [valid_response]

    provider = OllamaProvider()
    result = provider.summarize(texto_longo, "gemma3:270m", DEFAULT_USER_PROMPT)
    assert result.llm_response.resposta == "r"
    assert chat_mock.call_count == 6
    ultima_mensagem = chat_mock.call_args_list[-1].kwargs["messages"][0]["content"]
    assert len(json.loads(ultima_mensagem)["texto"]) == 4000


def test_create_provider_ollama():
    from pdf_summarizer.core.models import JobConfig
    from pathlib import Path

    config = JobConfig(
        input_dir=Path("."),
        output_dir=Path("."),
        provider="ollama",
        model="gemma3:270m",
    )
    provider = create_provider(config)
    assert isinstance(provider, OllamaProvider)
