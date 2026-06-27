from pathlib import Path

import pytest

from pdf_summarizer.core.exceptions import PdfExtractError
from pdf_summarizer.core.pdf.extractor import PdfExtractor


def test_extrair_pdf_com_texto(sample_pdf_path: Path):
    extractor = PdfExtractor()
    texto = extractor.extract(sample_pdf_path)
    assert "Sample text" in texto


def test_extrair_pdf_vazio(empty_pdf_path: Path):
    extractor = PdfExtractor()
    texto = extractor.extract(empty_pdf_path)
    assert texto == ""


def test_extrair_arquivo_inexistente(tmp_path: Path):
    extractor = PdfExtractor()
    with pytest.raises(PdfExtractError):
        extractor.extract(tmp_path / "missing.pdf")
