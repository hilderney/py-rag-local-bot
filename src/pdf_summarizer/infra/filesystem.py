import json
from pathlib import Path


class FileSystem:
    """Operações de filesystem para o pipeline."""

    def ensure_output_dirs(self, output_dir: Path) -> tuple[Path, Path]:
        resultados = output_dir / "resultados"
        resumos = output_dir / "resumos"
        resultados.mkdir(parents=True, exist_ok=True)
        resumos.mkdir(parents=True, exist_ok=True)
        return resultados, resumos

    def list_pdfs(self, input_dir: Path) -> list[Path]:
        if not input_dir.is_dir():
            return []
        return sorted(
            arquivo
            for arquivo in input_dir.iterdir()
            if arquivo.is_file() and arquivo.suffix.lower() == ".pdf"
        )

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
