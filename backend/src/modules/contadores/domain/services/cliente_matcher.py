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
_SEPARADORES_RE = re.compile(r"\s*[-–/|]\s*")


def normalizar_nombre(nombre: str) -> str:
    """Case/acentos/puntuación-insensible: 'Aerolíneas  Argentinas S.A.' →
    'AEROLINEAS ARGENTINAS SA'."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    sin_puntuacion = re.sub(r"[.,]", "", sin_acentos).strip().upper()
    return re.sub(r"\s+", " ", sin_puntuacion)


# El cruce automático (exacto/flex/contención ≥5 caracteres) no resuelve
# siglas cortas ni abreviaturas: "JBS" (3) y "Arag"/"ELEA" (4) quedan bajo el
# mínimo de contención, y "HOSP. ITALIANO..." no comparte prefijo tokenizado
# con "Hospital Italiano...". Verificado a mano contra Siges (2026-08-19).
# Mismo criterio que `contadores_cliente_siges_map`: alias manual solo para
# lo que el cruce automático no resuelve. Compartido entre
# FiltrarPendientesPorPeriodoReal (cliente → ¿tiene grupo sin cerrar?) y
# FiltrarPendientesPeriodoPorOperador (grupo → ¿es de este operador?).
ALIAS_CLIENTE_GRUPO_NORM: dict[str, str] = {
    normalizar_nombre(cliente): normalizar_nombre(grupo)
    for cliente, grupo in {
        "JBS": "JBS Leather Argentina S.A.",
        "ELEA": "Laboratorio Elea Phoenix SA",
        "Arag": "Arag S.R.L.",
        "HOSP. ITALIANO DE LA PLATA": "Hospital Italiano De La Plata",
    }.items()
}


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


def flex_nombre(normalizado: str) -> str:
    """Sobre un nombre ya pasado por `normalizar_nombre`, equipara
    separadores tipográficos a un espacio: 'ROEMMERS - MAPRIMED' ≈
    'ROEMMERS / MAPRIMED'."""
    return re.sub(r"\s+", " ", _SEPARADORES_RE.sub(" ", normalizado)).strip()


class IndiceNombres[T]:
    """Índice de nombres libres (claves ya normalizadas con
    `normalizar_nombre`) con su variante flex precalculada, para cruzar
    contra otro nombre libre por exacto/flex/contención única
    (`buscar_por_nombre`) sin repetir el armado por cada búsqueda."""

    def __init__(self, valores: dict[str, T]) -> None:
        self.exacto = valores
        self.flex = {flex_nombre(k): v for k, v in valores.items()}


def buscar_por_nombre[T](nombre: str | None, indice: IndiceNombres[T]) -> T | None:
    """Exacto normalizado > flex (separadores equivalentes) > contención
    única (≥5 caracteres). Ambiguo, corto o sin candidato → sin cruce."""
    if not nombre or not indice.exacto:
        return None
    norm = normalizar_nombre(nombre)
    if norm in indice.exacto:
        return indice.exacto[norm]
    flex = flex_nombre(norm)
    if flex in indice.flex:
        return indice.flex[flex]
    if len(flex) < _MIN_LARGO_CONTENCION:
        return None
    candidatos = [v for k, v in indice.flex.items() if flex in k or k in flex]
    return candidatos[0] if len(candidatos) == 1 else None
