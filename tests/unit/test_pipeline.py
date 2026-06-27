import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pdf_summarizer.core.exceptions import LlmError
from pdf_summarizer.core.models import JobConfig, ProgressEvent, SummaryResult
from pdf_summarizer.core.pdf.extractor import PdfExtractor
from pdf_summarizer.core.summary.summarizer import Summarizer
from pdf_summarizer.infra.filesystem import FileSystem
from pdf_summarizer.services.pipeline import PipelineService


def _make_config(input_dir: Path, output_dir: Path) -> JobConfig:
    return JobConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        provider="ollama",
        model="test-model",
        max_chars=8000,
    )


def _copy_sample_pdfs(input_dir: Path, fixtures_dir: Path) -> None:
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc_a.pdf")
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc_b.pdf")


def test_run_sem_pdfs(tmp_path: Path):
    events: list[ProgressEvent] = []
    pipeline = PipelineService(on_progress=events.append)
    config = _make_config(tmp_path / "in", tmp_path / "out")
    stats = pipeline.run(config)
    assert stats.pdfs_found == 0
    assert any(e.stage == "info" for e in events)


def test_run_extrai_e_resume(tmp_path: Path, fixtures_dir: Path, mock_llm_provider, mocker):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _copy_sample_pdfs(input_dir, fixtures_dir)

    mocker.patch(
        "pdf_summarizer.services.pipeline.create_provider",
        return_value=mock_llm_provider,
    )

    pipeline = PipelineService()
    stats = pipeline.run(_make_config(input_dir, output_dir))

    assert stats.pdfs_found == 2
    assert stats.extracted == 2
    assert stats.summarized == 2
    assert (output_dir / "resultados" / "doc_a.txt").is_file()
    assert (input_dir / "doc_a.txt").is_file()
    assert (output_dir / "resumos" / "doc_a.json").is_file()


def test_run_falha_em_um_arquivo_continua(tmp_path: Path, fixtures_dir: Path, mocker):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _copy_sample_pdfs(input_dir, fixtures_dir)

    provider = MagicMock()
    provider.summarize.side_effect = [
        LlmError("falha"),
        SummaryResult(
            modelo="m",
            requisicao={},
            resposta={
                "resumo": "ok",
                "pontos_principais": [],
                "informacoes_importantes": [],
                "assuntos": [],
            },
        ),
    ]
    mocker.patch(
        "pdf_summarizer.services.pipeline.create_provider",
        return_value=provider,
    )

    pipeline = PipelineService()
    stats = pipeline.run(_make_config(input_dir, output_dir))

    assert stats.summarized == 1
    assert stats.failed == 1


def test_run_emite_progress_events(tmp_path: Path, fixtures_dir: Path, mock_llm_provider, mocker):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc.pdf")

    mocker.patch(
        "pdf_summarizer.services.pipeline.create_provider",
        return_value=mock_llm_provider,
    )

    events: list[ProgressEvent] = []
    pipeline = PipelineService(on_progress=events.append)
    pipeline.run(_make_config(input_dir, output_dir))

    stages = [e.stage for e in events]
    assert "extract" in stages
    assert "summarize" in stages
    assert "done" in stages


def test_run_cria_subpastas(tmp_path: Path, fixtures_dir: Path, mock_llm_provider, mocker):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc.pdf")

    mocker.patch(
        "pdf_summarizer.services.pipeline.create_provider",
        return_value=mock_llm_provider,
    )

    pipeline = PipelineService()
    pipeline.run(_make_config(input_dir, output_dir))

    assert (output_dir / "resultados").is_dir()
    assert (output_dir / "resumos").is_dir()
