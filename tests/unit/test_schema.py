from pathlib import Path

import pytest

from pdf_summarizer.core.exceptions import LlmParseError
from pdf_summarizer.core.summary.schema import (
    DEFAULT_USER_PROMPT,
    construir_requisicao_ollama,
    parse_resposta_json,
    validate_resposta_llm,
)


def test_parse_json_puro():
    payload = {"resposta": "ok", "resumo": "meta"}
    result = parse_resposta_json('{"resposta": "ok", "resumo": "meta"}')
    assert result["resposta"] == "ok"


def test_parse_json_com_markdown_fence():
    raw = '```json\n{"resposta": "x", "resumo": "y"}\n```'
    result = parse_resposta_json(raw)
    assert result["resposta"] == "x"


def test_parse_json_invalido_levanta_erro():
    with pytest.raises(Exception):
        parse_resposta_json("{invalid")


def test_validate_resposta_llm_campos_obrigatorios():
    with pytest.raises(LlmParseError):
        validate_resposta_llm({"resposta": "sem resumo"})


def test_construir_requisicao_ollama_usa_prompt_do_usuario():
    prompt = "Extraia apenas valores monetários."
    req = construir_requisicao_ollama("conteúdo", prompt)
    assert req["instrucoes"] == prompt
    assert req["texto"] == "conteúdo"


def test_construir_requisicao_ollama_prompt_padrao():
    req = construir_requisicao_ollama("texto")
    assert req["instrucoes"] == DEFAULT_USER_PROMPT
