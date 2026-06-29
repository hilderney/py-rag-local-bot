import shutil
from pathlib import Path
from unittest.mock import MagicMock

from pdf_summarizer.core.models import JobConfig
from pdf_summarizer.services.extract_service import ExtractService


def test_extract_service_com_unimed_txt(tmp_path: Path, fixtures_dir: Path, mocker):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    shutil.copy(
        fixtures_dir / "unimed_guia_sample.txt",
        input_dir / "relatorio.pdf",
    )

    extractor = MagicMock()
    extractor.extract.return_value = (
        fixtures_dir / "unimed_guia_sample.txt"
    ).read_text(encoding="utf-8")

    stats = ExtractService(extractor=extractor).run(input_dir, output_dir)

    assert stats.extracted == 1
    assert (output_dir / "resultados" / "relatorio.txt").is_file()
