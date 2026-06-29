import json

FORMATO_RESPOSTA_LLM = {
    "type": "object",
    "properties": {
        "resposta": {"type": "string"},
        "resumo": {"type": "string"},
    },
    "required": ["resposta", "resumo"],
}

REQUIRED_LLM_FIELDS = FORMATO_RESPOSTA_LLM["required"]

FORMATO_RESPOSTA_DESCRICAO = {
    "resposta": "string (resposta completa ao pedido do usuário)",
    "resumo": (
        "string (explicação ultra resumida do que foi entendido da requisição, "
        "da resposta e por que essa resposta foi escolhida)"
    ),
}

DEFAULT_USER_PROMPT = (
    "Analise o texto fornecido e responda ao pedido do usuário em português do Brasil."
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
        "resposta": "string (resposta completa ao pedido)",
        "resumo": (
            "string (explicação ultra resumida do que entendeu da requisição, "
            "da resposta e por que escolheu essa resposta)"
        ),
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


def validate_resposta_llm(resposta: dict) -> None:
    """Valida presença dos campos obrigatórios na resposta da LLM."""
    from pdf_summarizer.core.exceptions import LlmParseError

    for campo in REQUIRED_LLM_FIELDS:
        if campo not in resposta:
            raise LlmParseError(f"Campo obrigatório ausente na resposta: {campo}")
