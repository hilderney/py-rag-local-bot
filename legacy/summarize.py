import json
import sys
from pathlib import Path

from ollama import chat

# MODEL_NAME = "phi3"
MODEL_NAME = "gemma3:270m"
# MODEL_NAME = "deepseek-r1:1.5b"

MAX_CHARS = 8000

FORMATO_RESPOSTA = {
    "type": "object",
    "properties": {
        "resumo": {"type": "string"},
        "pontos_principais": {"type": "array", "items": {"type": "string"}},
        "informacoes_importantes": {"type": "array", "items": {"type": "string"}},
        "assuntos": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["resumo", "pontos_principais", "informacoes_importantes", "assuntos"],
}


def construir_requisicao(texto):
    """Monta o payload JSON enviado à LLM."""
    if len(texto) > MAX_CHARS:
        texto = texto[:MAX_CHARS]
        print(f"  Aviso: texto truncado para {MAX_CHARS} caracteres.")

    return {
        "idioma": "pt-BR",
        "tarefa": "resumir_texto",
        "instrucoes": (
            "Faça um resumo conciso e claro do texto fornecido. "
            "Destaque os pontos principais e as informações mais importantes. "
            "Responda em português do Brasil."
            "Crie os assuntos como se fossem tags para um sistema de busca."
        ),
        "formato_resposta": {
            "resumo": "string",
            "pontos_principais": ["string"],
            "informacoes_importantes": ["string"],
            "assuntos": ["string"],
        },
        "texto": texto,
    }


def parse_resposta_json(conteudo):
    """Interpreta a resposta da LLM como JSON."""
    conteudo = conteudo.strip()
    if conteudo.startswith("```"):
        linhas = conteudo.splitlines()
        conteudo = "\n".join(linhas[1:-1] if linhas[-1].strip() == "```" else linhas[1:])
    return json.loads(conteudo)


def resumir_texto(texto, modelo=MODEL_NAME):
    """Envia JSON à LLM com stream=True e retorna requisição + resposta estruturadas."""
    requisicao = construir_requisicao(texto)
    mensagem = json.dumps(requisicao, ensure_ascii=False)

    # Inicializa a string que vai acumular a resposta completa
    resposta_completa = ""

    # Itera sobre cada pedaço (chunk) gerado pela LLM
    for chunk in chat(
        model=modelo,
        messages=[{"role": "user", "content": mensagem}],
        stream=False,          
        format=FORMATO_RESPOSTA,
        options={"temperature": 0.2},
    ):
        # Cada chunk tem a estrutura: {"message": {"content": "texto"}, "done": False/True}
        if "message" in chunk and "content" in chunk["message"]:
            resposta_completa += chunk["message"]["content"]

        # Opcional: se o chunk indicar que acabou, podemos sair do loop mais cedo
        if chunk.get("done", False):
            break

    # Agora que temos o JSON completo, fazemos o parse
    resposta = parse_resposta_json(resposta_completa)

    return {
        "modelo": modelo,
        "requisicao": requisicao,
        "resposta": resposta,
    }


def resumir_arquivos(pasta_entrada="."):
    """Lê cada .txt em resultados/ e grava o resumo JSON em resumos/."""
    pasta_entrada = Path(pasta_entrada)
    pasta_resultados = pasta_entrada / "resultados"
    pasta_resumos = pasta_entrada / "resumos"
    pasta_resumos.mkdir(parents=True, exist_ok=True)

    if not pasta_resultados.is_dir():
        print(f"Pasta não encontrada: {pasta_resultados.resolve()}")
        return

    arquivos = sorted(
        arquivo
        for arquivo in pasta_resultados.iterdir()
        if arquivo.is_file() and arquivo.suffix.lower() == ".txt"
    )

    if not arquivos:
        print(f"Nenhum .txt encontrado em: {pasta_resultados.resolve()}")
        return

    for caminho_txt in arquivos:
        texto = caminho_txt.read_text(encoding="utf-8").strip()
        if not texto:
            print(f"⏭️  {caminho_txt.name} (vazio, ignorado)")
            continue

        print(f"📄 Resumindo: {caminho_txt.name}...")
        try:
            resultado = resumir_texto(texto)
        except json.JSONDecodeError as e:
            print(f"❌ Resposta inválida para {caminho_txt.name}: {e}")
            continue
        except Exception as e:
            print(f"❌ Erro ao resumir {caminho_txt.name}: {e}")
            continue

        caminho_saida = pasta_resumos / f"{caminho_txt.stem}.json"
        caminho_saida.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"✅ {caminho_txt.name} → resumos/{caminho_saida.name}")


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else "."
    resumir_arquivos(pasta)
