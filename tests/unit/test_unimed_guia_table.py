from pathlib import Path

import pytest

from pdf_summarizer.core.tables.csv_export import write_table_csv
from pdf_summarizer.core.tables.extractor import extract_tables_from_text
from pdf_summarizer.core.tables.unimed_guia import extract_unimed_guia_rows


@pytest.fixture
def unimed_sample_text(fixtures_dir: Path) -> str:
    return (fixtures_dir / "unimed_guia_sample.txt").read_text(encoding="utf-8")


def test_extract_unimed_guia_rows(unimed_sample_text: str):
    rows = extract_unimed_guia_rows(unimed_sample_text)
    assert len(rows) == 2
    assert rows[0]["guia"] == "7063165"
    assert rows[0]["beneficiario"] == "INGRID PINHEIRO ACIOLI"
    assert rows[0]["codigo_procedimento"] == "50000470"
    assert rows[1]["guia"] == "7079846"


def test_extract_tables_from_text_retorna_formato(unimed_sample_text: str):
    result = extract_tables_from_text(unimed_sample_text)
    assert result is not None
    assert result.format_name == "unimed_guia"
    assert result.row_count == 2


def test_extract_tables_texto_sem_tabela():
    assert extract_tables_from_text("apenas texto livre sem cabeçalho") is None


def test_write_table_csv(tmp_path: Path, unimed_sample_text: str):
    table = extract_tables_from_text(unimed_sample_text)
    assert table is not None
    csv_path = tmp_path / "saida.csv"
    write_table_csv(csv_path, table)
    content = csv_path.read_text(encoding="utf-8-sig")
    assert "guia,dt_emis,beneficiario" in content
    assert "7063165" in content
