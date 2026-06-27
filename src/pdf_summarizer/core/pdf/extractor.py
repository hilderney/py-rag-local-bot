from pathlib import Path

import pdfplumber

from pdf_summarizer.core.exceptions import PdfExtractError


class PdfExtractor:
    """Extrai texto de arquivos PDF via pdfplumber."""

    def extract_page(self, page) -> str:
        """Extrai todo o texto da página como texto puro."""
        return (page.extract_text() or "").strip()

    def extract(self, pdf_path: Path) -> str:
        """Extrai todo o texto de um PDF."""
        if not pdf_path.is_file():
            raise PdfExtractError(f"Arquivo não encontrado: {pdf_path}")

        try:
            partes: list[str] = []
            with pdfplumber.open(pdf_path) as pdf:
                for pagina in pdf.pages:
                    conteudo = self.extract_page(pagina)
                    if conteudo:
                        partes.append(conteudo)
            return "\n\n".join(partes)
        except PdfExtractError:
            raise
        except Exception as exc:
            raise PdfExtractError(f"Erro ao extrair PDF {pdf_path.name}: {exc}") from exc
