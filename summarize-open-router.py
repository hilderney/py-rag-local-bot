import json
import sys
import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

load_dotenv()

OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
MAX_CHARS = 10000

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/ZAPFCOORP/py-rag-local-bot",
        "X-Title": "Py-RAG-Local-Bot",
    },
)

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
    """
        Constrói o prompt em linguagem natural para enviar à LLM.
        Inclui o texto e o schema JSON esperado.
    """
    if len(texto) > MAX_CHARS:
        texto = texto[:MAX_CHARS]
        print(f"  Aviso: texto truncado para {MAX_CHARS} caracteres.")

    schema = {
        "resumo": "string (resumo conciso)",
        "pontos_principais": "array de strings (principais tópicos)",
        "informacoes_importantes": "array de strings (detalhes relevantes)",
        "assuntos": "array de strings (tags para busca)"
    }

    prompt = f"""
    Faça um resumo conciso e claro do texto fornecido abaixo.
    Destaque os pontos principais e as informações mais importantes.
    Responda em português do Brasil.
    Crie assuntos (tags) para facilitar a busca.

    Texto:
    {texto}

    Responda **exclusivamente** em JSON, seguindo este esquema:
    {json.dumps(schema, ensure_ascii=False, indent=2)}
    """
    return prompt.strip()


def parse_resposta_json(conteudo):
    """
    Interpreta a resposta da LLM como JSON.
    Remove blocos de código markdown (```json ... ```) se presentes.
    """
    conteudo = conteudo.strip()
    # Se começa com ```, provavelmente é um bloco de código
    if conteudo.startswith("```"):
        linhas = conteudo.splitlines()
        # Caso a primeira linha seja ```json ou ``` e a última seja ```, remove ambas
        if len(linhas) >= 2 and linhas[-1].strip() == "```":
            # Pega todas as linhas entre a primeira e a última
            conteudo = "\n".join(linhas[1:-1])
        else:
            # Se não houver fechamento, remove só a primeira linha
            conteudo = "\n".join(linhas[1:])
    return json.loads(conteudo)


def resumir_texto(texto, modelo=OPENROUTER_MODEL, stream=False):
    """
    Envia o prompt para o OpenRouter via cliente OpenAI.
    Se stream=True, faz streaming e acumula a resposta; caso contrário, recebe completa.
    Retorna dicionário com modelo, prompt (requisicao) e resposta parseada.
    """
    prompt = construir_requisicao(texto)

    try:
        if stream:
            resposta_completa = ""
            stream_resp = client.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
                stream=False,
            )
            for chunk in stream_resp:
                # Extrai o conteúdo do delta
                if chunk.choices and chunk.choices[0].delta.content:
                    resposta_completa += chunk.choices[0].delta.content
            # Ao final, parseia o JSON completo
            dados = parse_resposta_json(resposta_completa)
        else:
            resposta_api = client.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
                stream=False,
            )
            conteudo = resposta_api.choices[0].message.content
            dados = parse_resposta_json(conteudo)
    except Exception as e:
        raise RuntimeError(f"Erro na chamada da API OpenRouter: {e}")

    # Garante que todos os campos obrigatórios existam
    for campo in FORMATO_RESPOSTA["required"]:
        if campo not in dados:
            dados[campo] = None  # ou levantar exceção, dependendo da sua preferência

    return {
        "modelo": modelo,
        "requisicao": prompt,        # agora é o prompt, não o dicionário antigo
        "resposta": dados,
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
