import re
from typing import Any

UNIMED_HEADER_MARKERS = ("Guia", "Beneficiário", "Procedimento")
UNIMED_COLUMNS = [
    "guia",
    "dt_emis",
    "beneficiario",
    "id",
    "pl",
    "medico",
    "requisicao",
    "codigo_procedimento",
    "procedimento",
    "qt",
]

_RE_GUIA = re.compile(
    r"^(\d+)\s+"
    r"(\d{2}/\d{2}/\d{2,4})\s+"
    r"(.+)\s+"
    r"REQUISIÇÃO:\s*(\d+)\s*$",
    re.IGNORECASE,
)
_RE_MIDDLE = re.compile(r"^(.+?)\s+(\d{1,4})\s+(\d{1,4})\s+(.+)$")
_RE_PROCEDIMENTO = re.compile(r"^(\d{5,8})\s+(.+?)\s+(\d+)\s*$")


def is_unimed_guia_header(line: str) -> bool:
    return all(marker in line for marker in UNIMED_HEADER_MARKERS)


def is_unimed_footer(line: str) -> bool:
    normalized = line.strip().lower()
    return (
        normalized.startswith("total")
        or "página" in normalized
        or "impresso em" in normalized.replace(" ", "")
    )


def parse_guia_line(line: str) -> dict[str, str] | None:
    match = _RE_GUIA.match(line.strip())
    if not match:
        return None

    guia, dt_emis, middle, requisicao = match.groups()
    middle_match = _RE_MIDDLE.match(middle.strip())
    if not middle_match:
        return None

    beneficiario, id_plano, pl, medico = middle_match.groups()
    return {
        "guia": guia,
        "dt_emis": dt_emis,
        "beneficiario": beneficiario.strip(),
        "id": id_plano,
        "pl": pl,
        "medico": medico.strip(),
        "requisicao": requisicao,
    }


def parse_procedimento_line(line: str) -> dict[str, str] | None:
    match = _RE_PROCEDIMENTO.match(line.strip())
    if not match:
        return None
    codigo, procedimento, qt = match.groups()
    return {
        "codigo_procedimento": codigo,
        "procedimento": procedimento.strip(),
        "qt": qt,
    }


def extract_unimed_guia_rows(texto: str) -> list[dict[str, str]]:
    """Extrai linhas da tabela de guias Unimed (cabeçalho + pares de linhas)."""
    lines = [line.strip() for line in texto.splitlines() if line.strip()]
    if not any(is_unimed_guia_header(line) for line in lines):
        return []

    rows: list[dict[str, str]] = []
    pending_guia: dict[str, str] | None = None

    for line in lines:
        if is_unimed_guia_header(line) or is_unimed_footer(line):
            continue

        guia = parse_guia_line(line)
        if guia is not None:
            if pending_guia is not None:
                rows.append(_finalize_row(pending_guia))
            pending_guia = guia
            continue

        procedimento = parse_procedimento_line(line)
        if procedimento is not None and pending_guia is not None:
            pending_guia.update(procedimento)
            rows.append(_finalize_row(pending_guia))
            pending_guia = None

    if pending_guia is not None:
        rows.append(_finalize_row(pending_guia))

    return rows


def _finalize_row(partial: dict[str, str]) -> dict[str, str]:
    return {column: partial.get(column, "") for column in UNIMED_COLUMNS}
