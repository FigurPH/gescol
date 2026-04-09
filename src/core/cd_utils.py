"""Utilitários para formatação e validação de CDs (centros de distribuição).

Regra canônica:
  - Mínimo 3 dígitos (preenchido com zeros à esquerda).
  - Máximo 4 dígitos (truncado se necessário).

Use sempre ``format_cd`` no lugar de ``str(x).zfill(3)`` avulso.
"""


def format_cd(value: int | str) -> str:
    """Formata um valor de CD para a representação canônica (3–4 dígitos).

    Examples:
        >>> format_cd(5)
        '005'
        >>> format_cd('290')
        '290'
        >>> format_cd('12345')
        '1234'
    """
    clean = str(value).strip()
    if len(clean) < 3:
        return clean.zfill(3)
    return clean[:4]


def same_cd(a: int | str, b: int | str) -> bool:
    """Retorna True se dois valores de CD são equivalentes após formatação."""
    return format_cd(a) == format_cd(b)
