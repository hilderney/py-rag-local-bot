from pathlib import Path

import pytest

from pdf_summarizer.core.models import LlmResponse, ProviderResult


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def sample_pdf_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.pdf"


@pytest.fixture
def empty_pdf_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "empty.pdf"


@pytest.fixture
def sample_txt_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.txt"


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def mock_llm_provider(mocker):
    provider = mocker.Mock()
    provider.health_check.return_value = True
    provider.summarize.return_value = ProviderResult(
        modelo="test-model",
        provedor="ollama",
        requisicao={"texto": "sample"},
        llm_response=LlmResponse(
            resposta="Resposta de teste",
            resumo="Meta resumo",
        ),
    )
    return provider
