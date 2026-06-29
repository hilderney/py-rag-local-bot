import shutil
from pathlib import Path

import pytest

from pdf_summarizer.core.artifacts import scan_generated_files


def test_scan_generated_files(tmp_path: Path, fixtures_dir: Path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    resultados = output_dir / "resultados"
    tabelas = output_dir / "tabelas"
    respostas = output_dir / "respostas"
    resultados.mkdir(parents=True)
    tabelas.mkdir(parents=True)
    respostas.mkdir(parents=True)

    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "doc.pdf")
    shutil.copy(fixtures_dir / "sample.txt", resultados / "doc.txt")
    (tabelas / "doc.csv").write_text("a,b\n1,2", encoding="utf-8")
    (respostas / "doc.json").write_text("{}", encoding="utf-8")

    artifacts = scan_generated_files(input_dir, output_dir)
    assert len(artifacts) == 1
    assert artifacts[0].stem == "doc"
    assert artifacts[0].txt is not None
    assert artifacts[0].csv is not None
    assert artifacts[0].json is not None


def test_scan_generated_files_sem_pdfs(tmp_path: Path):
    assert scan_generated_files(tmp_path / "missing", tmp_path / "out") == []
