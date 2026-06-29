from dataclasses import dataclass, field

from pdf_summarizer.core.tables.unimed_guia import UNIMED_COLUMNS, extract_unimed_guia_rows


@dataclass
class TableExtractionResult:
    format_name: str
    columns: list[str]
    rows: list[dict[str, str]] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.rows)


def extract_tables_from_text(texto: str) -> TableExtractionResult | None:
    """Tenta extrair tabela estruturada do texto; retorna None se não reconhecer."""
    unimed_rows = extract_unimed_guia_rows(texto)
    if unimed_rows:
        return TableExtractionResult(
            format_name="unimed_guia",
            columns=list(UNIMED_COLUMNS),
            rows=unimed_rows,
        )
    return None
