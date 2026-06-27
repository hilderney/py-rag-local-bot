from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from pdf_summarizer.core.exceptions import PdfExtractError, PdfSummarizerError
from pdf_summarizer.core.models import JobConfig, PipelineStats, ProgressEvent
from pdf_summarizer.core.pdf.extractor import PdfExtractor
from pdf_summarizer.core.summary.summarizer import Summarizer
from pdf_summarizer.infra.filesystem import FileSystem
from pdf_summarizer.infra.providers.base import create_provider


class PipelineService:
    """Orquestra extração de PDF e geração de resumos JSON."""

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
        stage: Literal["extract", "summarize", "info", "error", "done"],
        filename: str,
        message: str,
    ) -> None:
        if self._on_progress:
            self._on_progress(ProgressEvent(stage=stage, filename=filename, message=message))

    def run(self, config: JobConfig) -> PipelineStats:
        stats = PipelineStats()
        provider = create_provider(config)
        summarizer = Summarizer(provider, max_chars=config.max_chars)

        pdfs = self._filesystem.list_pdfs(config.input_dir)
        stats.pdfs_found = len(pdfs)

        if not pdfs:
            self._emit("info", "", "Nenhum PDF encontrado na pasta de entrada.")
            return stats

        resultados_dir, resumos_dir = self._filesystem.ensure_output_dirs(config.output_dir)

        extracted_items: list[tuple[Path, Path]] = []

        for pdf_path in pdfs:
            self._emit("extract", pdf_path.name, f"Extraindo PDF: {pdf_path.name}")
            txt_path = resultados_dir / f"{pdf_path.stem}.txt"
            try:
                texto = self._extractor.extract(pdf_path)
                self._filesystem.write_text(txt_path, texto)
                self._filesystem.write_text(pdf_path.with_suffix(".txt"), texto)
                stats.extracted += 1
                extracted_items.append((pdf_path, txt_path))
            except PdfExtractError as exc:
                stats.failed += 1
                self._emit("error", pdf_path.name, f"❌ {pdf_path.name}: {exc}")

        for pdf_path, txt_path in extracted_items:
            texto = self._filesystem.read_text(txt_path).strip()
            if not texto:
                stats.skipped += 1
                self._emit(
                    "info",
                    pdf_path.name,
                    f"⏭️  {pdf_path.name} (texto vazio após extração, ignorado)",
                )
                continue

            self._emit("summarize", pdf_path.name, f"Enviando à LLM: {pdf_path.name}")
            json_path = resumos_dir / f"{pdf_path.stem}.json"

            try:
                outcome = summarizer.summarize(texto, config.model, config.user_prompt)
                if outcome.truncated:
                    self._emit(
                        "info",
                        pdf_path.name,
                        f"Aviso: texto truncado para {config.max_chars} caracteres.",
                    )

                payload = asdict(outcome.result)
                self._filesystem.write_json(json_path, payload)
                stats.summarized += 1
                rel_path = f"resumos/{json_path.name}"
                self._emit(
                    "info",
                    pdf_path.name,
                    f"✅ {pdf_path.name} → {rel_path}",
                )
            except PdfSummarizerError as exc:
                stats.failed += 1
                self._emit("error", pdf_path.name, f"❌ {pdf_path.name}: {exc}")

        self._emit(
            "done",
            "",
            (
                f"── Concluído: {stats.extracted} extraídos, "
                f"{stats.summarized} resumos, {stats.skipped} ignorados, "
                f"{stats.failed} falhas ──"
            ),
        )
        return stats
