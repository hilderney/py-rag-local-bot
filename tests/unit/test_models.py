from pathlib import Path

import pytest

from pdf_summarizer.core.models import JobConfig, LlmDocument, ProgressEvent


def test_job_config_defaults():
    config = JobConfig(
        input_dir=Path("."),
        output_dir=Path("."),
        provider="ollama",
        model="gemma3:270m",
    )
    assert config.provider == "ollama"


def test_progress_event():
    event = ProgressEvent(stage="extract", filename="a.pdf", message="msg")
    assert event.stage == "extract"


def test_llm_document_to_dict():
    doc = LlmDocument(
        modelo="m",
        provedor="ollama",
        texto="t",
        requisitado="r",
        resposta="resp",
        resumo="meta",
        arquivos={"txt": "/path/txt"},
    )
    data = doc.to_dict()
    assert data["resposta"] == "resp"
    assert data["arquivos"]["txt"] == "/path/txt"
