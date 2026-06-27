import pytest

from pdf_summarizer.core.exceptions import LlmParseError
from pdf_summarizer.core.summary.schema import DEFAULT_USER_PROMPT
from pdf_summarizer.core.models import SummaryResult
from pdf_summarizer.core.summary.summarizer import Summarizer


def test_trunca_texto_acima_max_chars(mock_llm_provider):
    summarizer = Summarizer(mock_llm_provider, max_chars=10)
    long_text = "a" * 100
    outcome = summarizer.summarize(long_text, "test-model", DEFAULT_USER_PROMPT)
    assert outcome.truncated is True
    called_text = mock_llm_provider.summarize.call_args[0][0]
    assert len(called_text) == 10


def test_summarize_delega_provider(mock_llm_provider):
    summarizer = Summarizer(mock_llm_provider, max_chars=8000)
    outcome = summarizer.summarize("texto curto", "test-model", DEFAULT_USER_PROMPT)
    mock_llm_provider.summarize.assert_called_once_with(
        "texto curto", "test-model", DEFAULT_USER_PROMPT
    )
    assert outcome.result.modelo == "test-model"


def test_summarize_campos_obrigatorios(mocker):
    provider = mocker.Mock()
    provider.summarize.return_value = SummaryResult(
        modelo="m",
        requisicao={},
        resposta={"resumo": "ok"},
    )
    summarizer = Summarizer(provider)
    with pytest.raises(LlmParseError):
        summarizer.summarize("texto", "m", DEFAULT_USER_PROMPT)
