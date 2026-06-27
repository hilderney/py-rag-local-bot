import json
import shutil
from pathlib import Path

from pdf_summarizer.core.models import JobConfig
from pdf_summarizer.services.pipeline import PipelineService


def test_pipeline_completo_com_mock_llm(tmp_path: Path, fixtures_dir: Path, mock_llm_provider, mocker):
    input_dir = tmp_path / "pdfs"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "documento.pdf")

    mocker.patch(
        "pdf_summarizer.services.pipeline.create_provider",
        return_value=mock_llm_provider,
    )

    config = JobConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        provider="ollama",
        model="test-model",
        max_chars=8000,
    )

    stats = PipelineService().run(config)

    assert stats.pdfs_found == 1
    assert stats.extracted == 1
    assert stats.summarized == 1

    txt_path = output_dir / "resultados" / "documento.txt"
    json_path = output_dir / "resumos" / "documento.json"
    pdf_txt_path = input_dir / "documento.txt"
    assert txt_path.is_file()
    assert pdf_txt_path.is_file()
    assert json_path.is_file()
    assert txt_path.read_text(encoding="utf-8") == pdf_txt_path.read_text(encoding="utf-8")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "modelo" in data
    assert "requisicao" in data
    assert "resposta" in data
    assert "resumo" in data["resposta"]
