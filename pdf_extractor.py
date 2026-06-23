import sys
from pathlib import Path

import pdfplumber


def tabela_para_markdown(dados):
    """Converte dados tabulares em tabela Markdown."""
    if not dados:
        return ""

    num_colunas = max(len(linha) for linha in dados)
    linhas = []

    for i, linha in enumerate(dados):
        celulas = [(celula or "").replace("\n", " ").strip() for celula in linha]
        while len(celulas) < num_colunas:
            celulas.append("")
        linhas.append("| " + " | ".join(celulas) + " |")
        if i == 0:
            linhas.append("| " + " | ".join(["---"] * num_colunas) + " |")

    return "\n".join(linhas)


def extrair_pagina(pagina):
    """Extrai texto da página, ignorando imagens e convertendo tabelas para Markdown."""
    tabelas = pagina.find_tables()
    if not tabelas:
        return (pagina.extract_text() or "").strip()

    tabelas_ordenadas = sorted(tabelas, key=lambda t: t.bbox[1])
    partes = []
    x0, topo_pagina, x1, base_pagina = pagina.bbox
    y_atual = topo_pagina

    for tabela in tabelas_ordenadas:
        _, top, _, bottom = tabela.bbox

        if top > y_atual:
            regiao = (x0, y_atual, x1, top)
            texto = pagina.crop(regiao).extract_text()
            if texto and texto.strip():
                partes.append(texto.strip())

        markdown = tabela_para_markdown(tabela.extract())
        if markdown:
            partes.append(markdown)

        y_atual = max(y_atual, bottom)

    if y_atual < base_pagina:
        regiao = (x0, y_atual, x1, base_pagina)
        texto = pagina.crop(regiao).extract_text()
        if texto and texto.strip():
            partes.append(texto.strip())

    return "\n\n".join(partes)


def extrair_pdf(caminho_pdf):
    """Extrai todo o texto de um PDF (sem imagens, tabelas em Markdown)."""
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
