"""Cruce del `cliente` (texto libre de Gestión) contra el catálogo de empresas
activas de Siges, para poder contar impresoras por cliente. Medido con datos
reales (2026-08-14, 268 clientes distintos del calendario): exacto normalizado
65%, +contención única llega a ~85%; el resto son alias/anotaciones que se
resuelven con el mapa manual (`ClienteSigesMapRepository`), que siempre gana.

Prioridad de resolución: alias manual > exacto normalizado único >
contención única (≥5 caracteres). Ambiguo o sin candidato → sin cruce
(lista vacía). Un alias puede mapear a varias empresas a la vez (ej.
'Salta Refrescos' son 3 regiones en Siges): el cliente suma todas."""

import re
import unicodedata

from src.modules.contadores.domain.ports.parque_cliente_port import EmpresaSiges

_MIN_LARGO_CONTENCION = 5


def normalizar_nombre(nombre: str) -> str:
    """Case/acentos/puntuación-insensible: 'Aerolíneas  Argentinas S.A.' →
    'AEROLINEAS ARGENTINAS SA'."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    sin_puntuacion = re.sub(r"[.,]", "", sin_acentos).strip().upper()
    return re.sub(r"\s+", " ", sin_puntuacion)


def match_clientes(
    clientes: list[str],
    empresas: list[EmpresaSiges],
    alias: dict[str, list[int]],
) -> dict[str, list[int]]:
    """`cliente` → `ID_Empresa`(s) (lista vacía si no cruza). Los alias se
    comparan también normalizados, para que un mapeo manual sobreviva a
    cambios de mayúsculas/acentos en Gestión."""
    alias_norm = {normalizar_nombre(nombre): ids for nombre, ids in alias.items()}
    por_norm: dict[str, list[EmpresaSiges]] = {}
    for empresa in empresas:
        por_norm.setdefault(normalizar_nombre(empresa.den_comercial), []).append(empresa)
    return {
        cliente: _match_uno(normalizar_nombre(cliente), por_norm, alias_norm)
        for cliente in clientes
    }


def _match_uno(
    norm: str,
    por_norm: dict[str, list[EmpresaSiges]],
    alias_norm: dict[str, list[int]],
) -> list[int]:
    if norm in alias_norm:
        return alias_norm[norm]
    exactos = por_norm.get(norm, [])
    if len(exactos) == 1:
        return [exactos[0].id]
    if len(exactos) > 1:
        return []
    return _match_por_contencion(norm, por_norm)


def _match_por_contencion(norm: str, por_norm: dict[str, list[EmpresaSiges]]) -> list[int]:
    if len(norm) < _MIN_LARGO_CONTENCION:
        return []
    candidatos = [
        empresa
        for otro_norm, empresas in por_norm.items()
        if norm in otro_norm or otro_norm in norm
        for empresa in empresas
    ]
    return [candidatos[0].id] if len(candidatos) == 1 else []
