from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pdf_summarizer.core.exceptions import ConfigError
from pdf_summarizer.core.summary.schema import DEFAULT_USER_PROMPT
from pdf_summarizer.core.models import JobConfig
from pdf_summarizer.infra.providers.base import create_provider
from pdf_summarizer.infra.providers.openrouter import OpenRouterProvider


def test_summarize_sem_api_key_levanta_erro():
    with pytest.raises(ConfigError):
        OpenRouterProvider(api_key="")


def test_create_provider_openrouter_sem_key():
    config = JobConfig(
        input_dir=Path("."),
        output_dir=Path("."),
        provider="openrouter",
        model="test",
        api_key=None,
    )
    with pytest.raises(ConfigError):
        create_provider(config)


def test_summarize_chama_openai_client(mocker):
    valid_json = (
        '{"resumo":"r","pontos_principais":[],"informacoes_importantes":[],"assuntos":[]}'
    )
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = valid_json
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch(
        "pdf_summarizer.infra.providers.openrouter.OpenAI",
        return_value=mock_client,
    )

    provider = OpenRouterProvider(api_key="sk-test")
    result = provider.summarize("texto", "nvidia/test", DEFAULT_USER_PROMPT)
    mock_client.chat.completions.create.assert_called_once()
    assert result.resposta["resumo"] == "r"
