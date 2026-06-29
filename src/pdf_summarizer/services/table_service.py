from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pdf_summarizer.core.models import ProgressEvent, TableStats
from pdf_summarizer.core.tables.extractor import extract_tables_from_text
from pdf_summarizer.infra.filesystem import FileSystem


class TableService:
    """Gera CSVs a partir dos .txt em resultados/."""

    def __init__(
        self,
        filesystem: FileSystem | None = None,
        on_progress: Callable[[ProgressEvent], None] | None = None,
    ) -> None:
        self._filesystem = filesystem or FileSystem()
        self._on_progress = on_progress

    def _emit(
        self,
        stage: Literal["table", "info", "error", "done"],
        filename: str,
        message: str,
    ) -> None:
        if self._on_progress:
            self._on_progress(ProgressEvent(stage=stage, filename=filename, message=message))

    def run(self, output_dir: Path, input_dir: Path | None = None) -> TableStats:
        stats = TableStats()
        txt_files = self._filesystem.list_resultados_txt(output_dir)
        stats.files_found = len(txt_files)

        if not txt_files:
            self._emit("info", "", "Nenhum .txt encontrado em resultados/.")
            return stats

        _, tabelas_dir, _ = self._filesystem.ensure_output_dirs(output_dir)
        self._emit("info", "", f"Gerando tabelas a partir de {len(txt_files)} arquivo(s)...")

        for txt_path in txt_files:
            stem = txt_path.stem
            self._emit("table", txt_path.name, f"Analisando: {txt_path.name}")
            texto = self._filesystem.read_text(txt_path).strip()
            if not texto:
                stats.skipped += 1
                self._emit("info", txt_path.name, f"⏭️  {txt_path.name} (vazio, ignorado)")
                continue

            table = extract_tables_from_text(texto)
            if table is None:
                stats.skipped += 1
                self._emit(
                    "info",
                    txt_path.name,
                    f"⏭️  {txt_path.name} (formato de tabela não reconhecido)",
                )
                continue

            try:
                csv_path = tabelas_dir / f"{stem}.csv"
                self._filesystem.write_table_csv(csv_path, table)
                if input_dir is not None:
                    pdf_path = input_dir / f"{stem}.pdf"
                    if pdf_path.is_file():
                        self._filesystem.write_table_csv(pdf_path.with_suffix(".csv"), table)
                stats.tables_extracted += 1
                self._emit(
                    "info",
                    txt_path.name,
                    f"CSV salvo: tabelas/{csv_path.name} ({table.row_count} linhas)",
                )
            except OSError as exc:
                stats.failed += 1
                self._emit("error", txt_path.name, f"❌ {txt_path.name}: {exc}")

        self._emit(
            "done",
            "",
            (
                f"── Tabelas: {stats.tables_extracted} geradas, "
                f"{stats.skipped} ignorados, {stats.failed} falhas ──"
            ),
        )
        return stats
