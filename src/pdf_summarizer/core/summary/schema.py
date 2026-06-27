import json

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

REQUIRED_RESPONSE_FIELDS = FORMATO_RESPOSTA["required"]

FORMATO_RESPOSTA_DESCRICAO = {
    "resumo": "string",
    "pontos_principais": ["string"],
    "informacoes_importantes": ["string"],
    "assuntos": ["string"],
}

DEFAULT_USER_PROMPT = (
    "Faça um resumo conciso e claro do texto fornecido. "
    "Destaque os pontos principais e as informações mais importantes. "
    "Responda em português do Brasil. "
    "Crie os assuntos como se fossem tags para um sistema de busca. "
    "Limite cada lista (pontos_principais, informacoes_importantes, assuntos) "
    "a no máximo 10 itens. "
    "Para textos tabulares ou listas longas, agrupe em categorias em vez de "
    "enumerar cada linha."
)


def construir_requisicao_ollama(texto: str, instrucoes: str = DEFAULT_USER_PROMPT) -> dict:
    """Monta o payload JSON enviado à LLM Ollama."""
    return {
        "idioma": "pt-BR",
        "tarefa": "processar_texto",
        "instrucoes": instrucoes.strip(),
        "formato_resposta": FORMATO_RESPOSTA_DESCRICAO,
        "texto": texto,
    }


def construir_requisicao_openrouter(
    texto: str,
    instrucoes: str = DEFAULT_USER_PROMPT,
) -> str:
    """Monta o prompt em linguagem natural para OpenRouter."""
    schema = {
        "resumo": "string (resumo ou síntese da análise)",
        "pontos_principais": "array de strings (principais tópicos)",
        "informacoes_importantes": "array de strings (detalhes relevantes)",
        "assuntos": "array de strings (tags para busca)",
    }

    prompt = f"""
{instrucoes.strip()}

Texto:
{texto}

Responda **exclusivamente** em JSON, seguindo este esquema:
{json.dumps(schema, ensure_ascii=False, indent=2)}
"""
    return prompt.strip()


def parse_resposta_json(conteudo: str) -> dict:
    """Interpreta a resposta da LLM como JSON."""
    conteudo = conteudo.strip()
    if conteudo.startswith("```"):
        linhas = conteudo.splitlines()
        if len(linhas) >= 2 and linhas[-1].strip() == "```":
            conteudo = "\n".join(linhas[1:-1])
        else:
            conteudo = "\n".join(linhas[1:])
    return json.loads(conteudo)


def validate_resposta(resposta: dict) -> None:
    """Valida presença dos campos obrigatórios na resposta."""
    from pdf_summarizer.core.exceptions import LlmParseError

    for campo in REQUIRED_RESPONSE_FIELDS:
        if campo not in resposta:
            raise LlmParseError(f"Campo obrigatório ausente na resposta: {campo}")
