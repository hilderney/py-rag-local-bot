import csv
from pathlib import Path

from pdf_summarizer.core.tables.extractor import TableExtractionResult


def write_table_csv(path: Path, table: TableExtractionResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=table.columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(table.rows)
