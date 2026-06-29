import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pdf_summarizer.core.models import JobConfig, ProgressEvent
from pdf_summarizer.services.extract_service import ExtractService
from pdf_summarizer.services.llm_service import LlmService
from pdf_summarizer.services.table_service import TableService


def _make_config(input_dir: Path, output_dir: Path) -> JobConfig:
    return JobConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        provider="ollama",
        model="test-model",
        max_chars=8000,
        user_prompt="Analise o texto.",
    )


def _copy_sample_pdfs(input_dir: Path, fixtures_dir: Path) -> None:
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc_a.pdf")
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc_b.pdf")


def test_extract_service_sem_pdfs(tmp_path: Path):
    events: list[ProgressEvent] = []
    service = ExtractService(on_progress=events.append)
    stats = service.run(tmp_path / "in", tmp_path / "out")
    assert stats.pdfs_found == 0
    assert any(e.stage == "info" for e in events)


def test_extract_service_extrai_txt(tmp_path: Path, fixtures_dir: Path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _copy_sample_pdfs(input_dir, fixtures_dir)

    stats = ExtractService().run(input_dir, output_dir)

    assert stats.pdfs_found == 2
    assert stats.extracted == 2
    assert (output_dir / "resultados" / "doc_a.txt").is_file()
    assert (input_dir / "doc_a.txt").is_file()


def test_table_service_cria_subpastas(tmp_path: Path, fixtures_dir: Path):
    output_dir = tmp_path / "out"
    resultados = output_dir / "resultados"
    resultados.mkdir(parents=True)
    shutil.copy(
        fixtures_dir / "unimed_guia_sample.txt",
        resultados / "relatorio.txt",
    )

    stats = TableService().run(output_dir)

    assert (output_dir / "tabelas").is_dir()
    assert stats.tables_extracted == 1
    assert (output_dir / "tabelas" / "relatorio.csv").is_file()


def test_llm_service_processa_txt(tmp_path: Path, fixtures_dir: Path, mock_llm_provider, mocker):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    resultados = output_dir / "resultados"
    resultados.mkdir(parents=True)
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc.pdf")
    shutil.copy(fixtures_dir / "sample.txt", resultados / "doc.txt")

    mocker.patch(
        "pdf_summarizer.services.llm_service.create_provider",
        return_value=mock_llm_provider,
    )

    config = _make_config(input_dir, output_dir)
    stats = LlmService().run(config)

    assert stats.processed == 1
    json_path = output_dir / "respostas" / "doc.json"
    assert json_path.is_file()


def test_llm_service_falha_continua(tmp_path: Path, fixtures_dir: Path, mocker):
    from pdf_summarizer.core.exceptions import LlmError
    from pdf_summarizer.core.models import LlmResponse, ProviderResult

    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    resultados = output_dir / "resultados"
    resultados.mkdir(parents=True)
    shutil.copy(fixtures_dir / "sample.txt", resultados / "doc_a.txt")
    shutil.copy(fixtures_dir / "sample.txt", resultados / "doc_b.txt")

    provider = MagicMock()
    provider.summarize.side_effect = [
        LlmError("falha"),
        ProviderResult(
            modelo="m",
            provedor="ollama",
            requisicao={},
            llm_response=LlmResponse(resposta="ok", resumo="meta"),
        ),
    ]
    mocker.patch(
        "pdf_summarizer.services.llm_service.create_provider",
        return_value=provider,
    )

    config = _make_config(input_dir, output_dir)
    stats = LlmService().run(config)

    assert stats.processed == 1
    assert stats.failed == 1


def test_extract_service_emite_progress_events(tmp_path: Path, fixtures_dir: Path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc.pdf")

    events: list[ProgressEvent] = []
    ExtractService(on_progress=events.append).run(input_dir, output_dir)

    stages = [e.stage for e in events]
    assert "extract" in stages
    assert "done" in stages
