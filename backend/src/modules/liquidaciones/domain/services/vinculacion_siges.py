"""Propuesta de vínculo local ↔ Siges por matching de nombre normalizado (ADR-014).

Es solo una *propuesta* (la confirmación es manual en la UI), pero igual se
proponen únicamente matches de alta confianza: igualdad normalizada o
contención, y nunca con ambigüedad — un candidato conflictivo se descarta en
silencio antes que proponer un vínculo equivocado.
"""

import unicodedata
from uuid import UUID

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import SigesEmpresaInfo

_PREFIJOS = ("spst", "pst", "pr")


def normalizar_nombre(nombre: str) -> str:
    """Minúsculas sin acentos ni puntuación, sin prefijo PST/SPST/PR inicial."""
    sin_acentos = "".join(
        ch for ch in unicodedata.normalize("NFD", nombre) if not unicodedata.combining(ch)
    )
    alfanumerico = "".join(ch if ch.isalnum() else " " for ch in sin_acentos.lower())
    tokens = alfanumerico.split()
    if tokens and tokens[0] in _PREFIJOS:
        tokens = tokens[1:]
    return " ".join(tokens)


def nombres_compatibles(a: str, b: str) -> bool:
    """Compara nombres ya normalizados, sin espacios: 'supernova servicios s r l'
    tiene que matchear 'rosario supernova servicios srl' aunque la sigla tokenice
    distinto. También la usa el mapeo de zonas de tarifarios (ADR-014 dataset 2)."""
    a_compacto = a.replace(" ", "")
    b_compacto = b.replace(" ", "")
    if not a_compacto or not b_compacto:
        return False
    return a_compacto in b_compacto or b_compacto in a_compacto


def _candidato_unico(nombre_local: str, candidatos: list[SigesEmpresaInfo]) -> int | None:
    matches = [
        c
        for c in candidatos
        if nombres_compatibles(nombre_local, normalizar_nombre(c.den_comercial))
    ]
    return matches[0].siges_empresa_id if len(matches) == 1 else None


def proponer_vinculos(
    locales: list[tuple[UUID, str]], candidatos: list[SigesEmpresaInfo]
) -> dict[UUID, int]:
    """`locales`: (id, nombre) de filas sin vincular; `candidatos`: empresas de
    Siges del tipo correspondiente todavía no vinculadas. Devuelve solo matches
    inequívocos en ambas direcciones (un local ↔ un candidato)."""
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
