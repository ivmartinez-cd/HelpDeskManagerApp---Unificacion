"""Propuesta de vínculo Empleado ↔ técnico de Siges por matching de nombre
normalizado — mismo criterio que `liquidaciones/domain/services/
vinculacion_siges.py` (ADR-014): solo matches de alta confianza (igualdad
normalizada o contención, nunca con ambigüedad), la confirmación es siempre
manual en la UI. Duplicado a propósito en vez de importado desde
`liquidaciones`: los módulos de negocio son independientes entre sí (ver
`.importlinter`) y la lógica es genérica y chica.
"""

import unicodedata
from dataclasses import dataclass
from uuid import UUID

_PREFIJOS = ("cd",)


@dataclass(frozen=True)
class SigesTecnicoInfo:
    siges_empresa_id: int
    den_comercial: str


def normalizar_nombre(nombre: str) -> str:
    """Minúsculas sin acentos ni puntuación, sin el prefijo `CD -` inicial
    (`Den_Comercial` de Siges siempre lo lleva para técnicos de planta)."""
    sin_acentos = "".join(
        ch for ch in unicodedata.normalize("NFD", nombre) if not unicodedata.combining(ch)
    )
    alfanumerico = "".join(ch if ch.isalnum() else " " for ch in sin_acentos.lower())
    tokens = alfanumerico.split()
    if tokens and tokens[0] in _PREFIJOS:
        tokens = tokens[1:]
    return " ".join(tokens)


def nombres_compatibles(a: str, b: str) -> bool:
    """Compara nombres ya normalizados, sin espacios: tolera orden de tokens
    igual pero abreviaturas o un nombre compuesto extra en un lado."""
    a_compacto = a.replace(" ", "")
    b_compacto = b.replace(" ", "")
    if not a_compacto or not b_compacto:
        return False
    return a_compacto in b_compacto or b_compacto in a_compacto


def _candidato_unico(nombre_local: str, candidatos: list[SigesTecnicoInfo]) -> int | None:
    matches = [
        c
        for c in candidatos
        if nombres_compatibles(nombre_local, normalizar_nombre(c.den_comercial))
    ]
    return matches[0].siges_empresa_id if len(matches) == 1 else None


def proponer_vinculos(
    locales: list[tuple[UUID, str]], candidatos: list[SigesTecnicoInfo]
) -> dict[UUID, int]:
    """`locales`: (id, nombre_completo) de empleados sin vincular; `candidatos`:
    técnicos de Siges todavía no vinculados a ningún empleado. Devuelve solo
    matches inequívocos en ambas direcciones (un empleado ↔ un técnico)."""
    por_local = {
        local_id: propuesto
        for local_id, nombre in locales
        if (propuesto := _candidato_unico(normalizar_nombre(nombre), candidatos)) is not None
    }
    usos: dict[int, int] = {}
    for propuesto in por_local.values():
        usos[propuesto] = usos.get(propuesto, 0) + 1
    return {
        local_id: propuesto for local_id, propuesto in por_local.items() if usos[propuesto] == 1
    }
