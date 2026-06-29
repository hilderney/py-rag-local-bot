import json
import shutil
from pathlib import Path

from pdf_summarizer.core.models import JobConfig
from pdf_summarizer.services.llm_service import LlmService


def test_llm_service_e2e(tmp_path: Path, fixtures_dir: Path, mock_llm_provider, mocker):
    input_dir = tmp_path / "pdfs"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    resultados = output_dir / "resultados"
    resultados.mkdir(parents=True)
    shutil.copy(fixtures_dir / "sample.pdf", input_dir / "documento.pdf")
    shutil.copy(fixtures_dir / "sample.txt", resultados / "documento.txt")

    mocker.patch(
        "pdf_summarizer.services.llm_service.create_provider",
        return_value=mock_llm_provider,
    )

    config = JobConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        provider="ollama",
        model="test-model",
        max_chars=8000,
        user_prompt="Analise o texto.",
    )

    stats = LlmService().run(config)

    assert stats.processed == 1
    json_path = output_dir / "respostas" / "documento.json"
    assert json_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["modelo"] == "test-model"
    assert data["provedor"] == "ollama"
    assert "texto" in data
    assert data["requisitado"] == "Analise o texto."
    assert "resposta" in data
    assert "resumo" in data
    assert "arquivos" in data
