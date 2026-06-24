import sys
from pathlib import Path
import pdfplumber


def extrair_pagina(pagina):
    """Extrai todo o texto da página (incluindo o de tabelas) como texto puro."""
    return (pagina.extract_text() or "").strip()


def extrair_pdf(caminho_pdf):
    """Extrai todo o texto de um PDF (sem conversão de tabelas)."""
    partes = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            conteudo = extrair_pagina(pagina)
            if conteudo:
                partes.append(conteudo)
    return "\n\n".join(partes)


def converter_pdfs_para_txt(pasta_entrada="."):
    pasta_entrada = Path(pasta_entrada)
    pasta_saida = pasta_entrada / "resultados"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(
        arquivo
        for arquivo in pasta_entrada.iterdir()
        if arquivo.is_file() and arquivo.suffix.lower() == ".pdf"
    )

    if not pdfs:
        print(f"Nenhum PDF encontrado em: {pasta_entrada.resolve()}")
        return

    for caminho_pdf in pdfs:
        nome_txt = f"{caminho_pdf.stem}.txt"
        caminho_txt = pasta_saida / nome_txt
        texto = extrair_pdf(caminho_pdf)
        caminho_txt.write_text(texto, encoding="utf-8")
        print(f"✅ {caminho_pdf.name} → resultados/{nome_txt}")


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else "."
    converter_pdfs_para_txt(pasta)