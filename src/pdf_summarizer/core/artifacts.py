from dataclasses import dataclass
from pathlib import Path


@dataclass
class ArtifactPaths:
    stem: str
    pdf: Path | None
    txt: Path | None
    csv: Path | None
    json: Path | None


def scan_generated_files(input_dir: Path, output_dir: Path) -> list[ArtifactPaths]:
    """Lista artefatos gerados por stem de cada PDF na pasta de entrada."""
    if not input_dir.is_dir():
        return []

    from pdf_summarizer.infra.filesystem import FileSystem

    filesystem = FileSystem()
    pdfs = filesystem.list_pdfs(input_dir)
    artifacts: list[ArtifactPaths] = []

    for pdf_path in pdfs:
        stem = pdf_path.stem
        resolved = FileSystem.resolve_artifacts(output_dir, stem, pdf_path)
        txt = Path(resolved["txt"]) if resolved.get("txt") else None
        if txt is None:
            local_txt = pdf_path.with_suffix(".txt")
            txt = local_txt if local_txt.is_file() else None

        csv = Path(resolved["csv"]) if resolved.get("csv") else None
        json_path = Path(resolved["json"]) if resolved.get("json") else None

        artifacts.append(
            ArtifactPaths(
                stem=stem,
                pdf=pdf_path,
                txt=txt,
                csv=csv if csv and csv.is_file() else None,
                json=json_path if json_path and json_path.is_file() else None,
            )
        )

    return artifacts
