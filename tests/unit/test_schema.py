import json

import pytest

from pdf_summarizer.core.exceptions import LlmParseError
from pdf_summarizer.core.summary.schema import (
    DEFAULT_USER_PROMPT,
    construir_requisicao_ollama,
    parse_resposta_json,
    validate_resposta,
)


def test_parse_json_puro():
    payload = {"resumo": "ok", "pontos_principais": [], "informacoes_importantes": [], "assuntos": []}
    result = parse_resposta_json(json.dumps(payload))
    assert result["resumo"] == "ok"


def test_parse_json_com_markdown_fence():
    raw = '```json\n{"resumo": "x", "pontos_principais": [], "informacoes_importantes": [], "assuntos": []}\n```'
    result = parse_resposta_json(raw)
    assert result["resumo"] == "x"


def test_parse_json_invalido_levanta_erro():
    with pytest.raises(json.JSONDecodeError):
        parse_resposta_json("{invalid")


def test_validate_resposta_campos_obrigatorios():
    with pytest.raises(LlmParseError):
        validate_resposta({"resumo": "sem demais campos"})


def test_construir_requisicao_ollama_usa_prompt_do_usuario():
    prompt = "Extraia apenas valores monetários."
    req = construir_requisicao_ollama("conteúdo", prompt)
    assert req["instrucoes"] == prompt
    assert req["texto"] == "conteúdo"
    assert req["formato_resposta"]


def test_construir_requisicao_ollama_prompt_padrao():
    req = construir_requisicao_ollama("texto")
    assert req["instrucoes"] == DEFAULT_USER_PROMPT
