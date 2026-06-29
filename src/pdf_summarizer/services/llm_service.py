from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pdf_summarizer.core.exceptions import PdfSummarizerError
from pdf_summarizer.core.models import JobConfig, LlmStats, ProgressEvent
from pdf_summarizer.core.summary.summarizer import Summarizer
from pdf_summarizer.infra.filesystem import FileSystem
from pdf_summarizer.infra.providers.base import create_provider


class LlmService:
    """Envia textos extraídos à LLM e grava respostas/*.json."""

    def __init__(
        self,
        filesystem: FileSystem | None = None,
        on_progress: Callable[[ProgressEvent], None] | None = None,
    ) -> None:
        self._filesystem = filesystem or FileSystem()
        self._on_progress = on_progress

    def _emit(
        self,
        stage: Literal["summarize", "info", "error", "done"],
        filename: str,
        message: str,
    ) -> None:
        if self._on_progress:
            self._on_progress(ProgressEvent(stage=stage, filename=filename, message=message))

    def run(self, config: JobConfig) -> LlmStats:
        stats = LlmStats()
        provider = create_provider(config)
        summarizer = Summarizer(provider, max_chars=config.max_chars)

        txt_files = self._filesystem.list_resultados_txt(config.output_dir)
        stats.files_found = len(txt_files)

        if not txt_files:
            self._emit("info", "", "Nenhum .txt encontrado em resultados/.")
            return stats

        _, _, respostas_dir = self._filesystem.ensure_output_dirs(config.output_dir)
        self._emit("info", "", f"Enviando {len(txt_files)} arquivo(s) à LLM...")

        pdf_by_stem = {
            pdf.stem: pdf for pdf in self._filesystem.list_pdfs(config.input_dir)
        }

        for txt_path in txt_files:
            stem = txt_path.stem
            display_name = f"{stem}.txt"
            texto = self._filesystem.read_text(txt_path).strip()
            if not texto:
                stats.skipped += 1
                self._emit("info", display_name, f"⏭️  {display_name} (vazio, ignorado)")
                continue

            self._emit("summarize", display_name, f"Enviando à LLM: {display_name}")
            json_path = respostas_dir / f"{stem}.json"
            pdf_path = pdf_by_stem.get(stem)

            try:
                outcome = summarizer.process(texto, config, stem, pdf_path)
                if outcome.truncated:
                    self._emit(
                        "info",
                        display_name,
                        f"Aviso: texto truncado para {config.max_chars} caracteres.",
                    )

                document = outcome.document
                document.arquivos["json"] = str(json_path.resolve())
                self._filesystem.write_json(json_path, document.to_dict())
                stats.processed += 1
                self._emit(
                    "info",
                    display_name,
                    (
                        f"── Resposta ({display_name}) ──\n"
                        f"{document.resposta}\n\n"
                        f"── Resumo ──\n"
                        f"{document.resumo}"
                    ),
                )
                self._emit(
                    "info",
                    display_name,
                    f"JSON salvo: respostas/{json_path.name}",
                )
            except PdfSummarizerError as exc:
                stats.failed += 1
                self._emit("error", display_name, f"❌ {display_name}: {exc}")

        self._emit(
            "done",
            "",
            (
                f"── LLM: {stats.processed} processados, "
                f"{stats.skipped} ignorados, {stats.failed} falhas ──"
            ),
        )
        return stats
