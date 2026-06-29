import json
from pathlib import Path

from pdf_summarizer.core.tables.csv_export import write_table_csv
from pdf_summarizer.core.tables.extractor import TableExtractionResult


class FileSystem:
    """Operações de filesystem para o pipeline."""

    def ensure_output_dirs(self, output_dir: Path) -> tuple[Path, Path, Path]:
        resultados = output_dir / "resultados"
        tabelas = output_dir / "tabelas"
        respostas = output_dir / "respostas"
        resultados.mkdir(parents=True, exist_ok=True)
        tabelas.mkdir(parents=True, exist_ok=True)
        respostas.mkdir(parents=True, exist_ok=True)
        return resultados, tabelas, respostas

    def list_pdfs(self, input_dir: Path) -> list[Path]:
        if not input_dir.is_dir():
            return []
        return sorted(
            arquivo
            for arquivo in input_dir.iterdir()
            if arquivo.is_file() and arquivo.suffix.lower() == ".pdf"
        )

    def list_resultados_txt(self, output_dir: Path) -> list[Path]:
        resultados = output_dir / "resultados"
        if not resultados.is_dir():
            return []
        return sorted(
            arquivo
            for arquivo in resultados.iterdir()
            if arquivo.is_file() and arquivo.suffix.lower() == ".txt"
        )

    @staticmethod
    def resolve_artifacts(
        output_dir: Path,
        stem: str,
        pdf_path: Path | None = None,
    ) -> dict[str, str | None]:
        txt_path = output_dir / "resultados" / f"{stem}.txt"
        csv_path = output_dir / "tabelas" / f"{stem}.csv"
        json_path = output_dir / "respostas" / f"{stem}.json"

        artifacts: dict[str, str | None] = {
            "pdf": str(pdf_path.resolve()) if pdf_path and pdf_path.is_file() else None,
            "txt": str(txt_path.resolve()) if txt_path.is_file() else None,
            "csv": str(csv_path.resolve()) if csv_path.is_file() else None,
            "json": str(json_path.resolve()) if json_path.is_file() else None,
        }
        return artifacts

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_table_csv(self, path: Path, table: TableExtractionResult) -> None:
        write_table_csv(path, table)
