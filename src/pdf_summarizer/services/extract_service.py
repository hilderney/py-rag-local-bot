from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pdf_summarizer.core.exceptions import PdfExtractError
from pdf_summarizer.core.models import ExtractStats, ProgressEvent
from pdf_summarizer.core.pdf.extractor import PdfExtractor
from pdf_summarizer.infra.filesystem import FileSystem


class ExtractService:
    """Extrai texto de PDFs e grava arquivos .txt."""

    def __init__(
        self,
        extractor: PdfExtractor | None = None,
        filesystem: FileSystem | None = None,
        on_progress: Callable[[ProgressEvent], None] | None = None,
    ) -> None:
        self._extractor = extractor or PdfExtractor()
        self._filesystem = filesystem or FileSystem()
        self._on_progress = on_progress

    def _emit(
        self,
        stage: Literal["extract", "info", "error", "done"],
        filename: str,
        message: str,
    ) -> None:
        if self._on_progress:
            self._on_progress(ProgressEvent(stage=stage, filename=filename, message=message))

    def run(self, input_dir: Path, output_dir: Path) -> ExtractStats:
        stats = ExtractStats()
        pdfs = self._filesystem.list_pdfs(input_dir)
        stats.pdfs_found = len(pdfs)

        if not pdfs:
            self._emit("info", "", "Nenhum PDF encontrado na pasta de entrada.")
            return stats

        resultados_dir, _, _ = self._filesystem.ensure_output_dirs(output_dir)
        self._emit("info", "", f"Iniciando extração de {len(pdfs)} PDF(s)...")

        for pdf_path in pdfs:
            self._emit("extract", pdf_path.name, f"Extraindo PDF: {pdf_path.name}")
            txt_path = resultados_dir / f"{pdf_path.stem}.txt"
            try:
                texto = self._extractor.extract(pdf_path)
                self._filesystem.write_text(txt_path, texto)
                self._filesystem.write_text(pdf_path.with_suffix(".txt"), texto)
                stats.extracted += 1
                self._emit(
                    "info",
                    pdf_path.name,
                    f"TXT salvo: resultados/{txt_path.name}",
                )
            except PdfExtractError as exc:
                stats.failed += 1
                self._emit("error", pdf_path.name, f"❌ {pdf_path.name}: {exc}")

        self._emit(
            "done",
            "",
            (
                f"── Extração: {stats.extracted} extraídos, "
                f"{stats.failed} falhas de {stats.pdfs_found} PDF(s) ──"
            ),
        )
        return stats
