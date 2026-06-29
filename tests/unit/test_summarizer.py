from pathlib import Path

import pytest

from pdf_summarizer.core.models import JobConfig, LlmResponse, ProviderResult
from pdf_summarizer.core.summary.summarizer import Summarizer


def test_trunca_texto_acima_max_chars(mock_llm_provider):
    summarizer = Summarizer(mock_llm_provider, max_chars=10)
    long_text = "a" * 100
    config = JobConfig(
        input_dir=Path("."),
        output_dir=Path("."),
        provider="ollama",
        model="test-model",
        user_prompt="prompt",
    )
    outcome = summarizer.process(long_text, config, "doc")
    assert outcome.truncated is True
    called_text = mock_llm_provider.summarize.call_args[0][0]
    assert len(called_text) == 10


def test_process_delega_provider(mock_llm_provider):
    summarizer = Summarizer(mock_llm_provider, max_chars=8000)
    config = JobConfig(
        input_dir=Path("."),
        output_dir=Path("."),
        provider="ollama",
        model="test-model",
        user_prompt="meu prompt",
    )
    outcome = summarizer.process("texto curto", config, "doc")
    mock_llm_provider.summarize.assert_called_once_with(
        "texto curto", "test-model", "meu prompt"
    )
    assert outcome.document.modelo == "test-model"
    assert outcome.document.requisitado == "meu prompt"


def test_process_aceita_resumo_vazio(mocker, tmp_path):
    provider = mocker.Mock()
    provider.summarize.return_value = ProviderResult(
        modelo="m",
        provedor="ollama",
        requisicao={},
        llm_response=LlmResponse(resposta="ok", resumo=""),
    )
    summarizer = Summarizer(provider)
    config = JobConfig(
        input_dir=Path("."),
        output_dir=tmp_path,
        provider="ollama",
        model="m",
        user_prompt="p",
    )
    outcome = summarizer.process("texto", config, "doc")
    assert outcome.document.resumo == ""
