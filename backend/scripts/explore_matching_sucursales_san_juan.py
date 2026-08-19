"""Fase 0 del matching sucursales SAN JUAN (ver
docs/MASTER_PROMPT_MATCHING_SUCURSALES_GEOVALIDACION.md): mide el problema
real en las dos puntas del join local<->Siges usando la MISMA normalizar_nombre
que ya usa RefrescarDatosSiges/DiagnosticarAsistenteKm (ADR-014), sin escribir
nada y sin llamar a Google. Para las filas sin match arma un top-1 candidato
por similitud (difflib, solo stdlib) para poder clasificar a mano la causa.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_matching_sucursales_san_juan.py
"""

import asyncio
import difflib
import re
import unicodedata

import pyodbc
from sqlalchemy import text

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    desde_periodo_hace_meses,
    es_empresa_activa,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre
from src.modules.liquidaciones.infrastructure.siges.query import SUCURSALES_DE_PRESTADOR_SQL
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30
_PRESTADOR_ID = "eda1e000-b50f-4475-bf2c-4d1bc3cf116e"  # San Juan - Gestion Integral
_SIGES_EMPRESA_ID = 504

_SQL_TABLA_KM_LOCAL = """
SELECT empresa_nombre, sucursal_nombre
FROM tabla_kms
WHERE prestador_id = :prestador_id
"""

_SQL_ACTIVIDAD_RECIENTE = """
SELECT DISTINCT i.empresa_nombre
FROM incidentes i
JOIN liquidaciones l ON l.id = i.liquidacion_id
WHERE l.prestador_id = :prestador_id AND l.periodo >= :desde_periodo
"""


async def _datos_locales() -> tuple[list[tuple[str, str]], set[str]]:
    async with get_sessionmaker()() as db:
        filas = await db.execute(text(_SQL_TABLA_KM_LOCAL), {"prestador_id": _PRESTADOR_ID})
        locales = [(r.empresa_nombre, r.sucursal_nombre) for r in filas]
        activos = await db.execute(
            text(_SQL_ACTIVIDAD_RECIENTE),
            {"prestador_id": _PRESTADOR_ID, "desde_periodo": desde_periodo_hace_meses(24)},
        )
        return locales, {r.empresa_nombre for r in activos}


def _sucursales_siges() -> list[tuple[str, str]]:
    settings = get_settings()
    connection = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        cursor.execute(SUCURSALES_DE_PRESTADOR_SQL, _SIGES_EMPRESA_ID)
        return [(str(r.Den_Comercial), str(r.descripcion)) for r in cursor.fetchall()]
    finally:
        connection.close()


def _clave(empresa: str, sucursal: str) -> tuple[str, str]:
    return (normalizar_nombre(empresa), normalizar_nombre(sucursal))


def _mejor_candidato(
    local: tuple[str, str], candidatos: list[tuple[str, str]]
) -> tuple[tuple[str, str], float]:
    local_compacto = f"{normalizar_nombre(local[0])} {normalizar_nombre(local[1])}"
    mejor = max(
        candidatos,
        key=lambda c: difflib.SequenceMatcher(
            None, local_compacto, f"{normalizar_nombre(c[0])} {normalizar_nombre(c[1])}"
        ).ratio(),
    )
    ratio = difflib.SequenceMatcher(
        None, local_compacto, f"{normalizar_nombre(mejor[0])} {normalizar_nombre(mejor[1])}"
    ).ratio()
    return mejor, ratio


def _mejor_candidato_anclado_empresa(
    local: tuple[str, str], candidatos: list[tuple[str, str]]
) -> tuple[tuple[str, str], float, bool]:
    """Restringe candidatos a la MISMA empresa normalizada cuando existe al
    menos una empresa exacta en Siges; si no hay ninguna, cae al catálogo
    completo. Devuelve (candidato, ratio_sucursal, empresa_exacta_encontrada)."""
    empresa_norm = normalizar_nombre(local[0])
    mismos_empresa = [c for c in candidatos if normalizar_nombre(c[0]) == empresa_norm]
    universo = mismos_empresa if mismos_empresa else candidatos
    sucursal_norm = normalizar_nombre(local[1])
    mejor = max(
        universo,
        key=lambda c: difflib.SequenceMatcher(
            None, sucursal_norm, normalizar_nombre(c[1])
        ).ratio(),
    )
    ratio = difflib.SequenceMatcher(None, sucursal_norm, normalizar_nombre(mejor[1])).ratio()
    return mejor, ratio, bool(mismos_empresa)


_RE_NUMERO = re.compile(r"(?i)\bN[.\sºR°oO]{0,5}(\d+)\b")
_ABREVIATURAS = (
    "sec", "sup", "pcia", "prov", "nac", "prim", "rep", "pte", "tec", "gral",
    "esc", "eee", "eni", "jinz", "epet", "sta", "sto", "dpto", "bo", "b",
)


def _numero(texto: str) -> str | None:
    m = _RE_NUMERO.search(texto)
    return m.group(1).lstrip("0") or "0" if m else None


def _normalizar_fuerte(texto: str) -> str:
    """NFKD (mapea º/ª a letra ASCII, a diferencia de la NFD de normalizar_nombre)."""
    sin_compat = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(ch for ch in sin_compat if not unicodedata.combining(ch))
    alfanumerico = "".join(ch if ch.isalnum() else " " for ch in sin_acentos.lower())
    return " ".join(alfanumerico.split())


def _clasificar_causa(local_suc: str, siges_suc: str, ratio: float) -> str:
    num_local, num_siges = _numero(local_suc), _numero(siges_suc)
    if num_local is not None and num_siges is not None:
        if num_local != num_siges:
            return "numero_distinto (candidato dudoso, NO auto-vincular)"
        fuerte_local = _normalizar_fuerte(local_suc).replace(" ", "")
        fuerte_siges = _normalizar_fuerte(siges_suc).replace(" ", "")
        debil_local = normalizar_nombre(local_suc).replace(" ", "")
        debil_siges = normalizar_nombre(siges_suc).replace(" ", "")
        if fuerte_local == fuerte_siges and debil_local != debil_siges:
            return "solo simbolo (º/°/ª) o puntuacion"
        tokens_local = set(_normalizar_fuerte(local_suc).split())
        tokens_siges = set(_normalizar_fuerte(siges_suc).split())
        if any(t in _ABREVIATURAS for t in tokens_local ^ tokens_siges):
            return "abreviatura de palabra (Sec/Sup/Pcia/Prim/...)"
        return "mismo numero, variante descriptiva (texto extra/orden)"
    if ratio >= 0.85:
        return "alta similitud sin numero identificable"
    return "sin candidato confiable (revisar a mano)"


def main() -> None:
    locales, activos_raw = asyncio.run(_datos_locales())
    activos_norm = {normalizar_nombre(n) for n in activos_raw}
    siges = _sucursales_siges()

    claves_locales = {_clave(e, s) for e, s in locales}
    claves_siges = {_clave(e, s) for e, s in siges}

    no_encontradas = [(e, s) for e, s in locales if _clave(e, s) not in claves_siges]
    nuevas = [(e, s) for e, s in siges if _clave(e, s) not in claves_locales]
    nuevas_activas = [(e, s) for e, s in nuevas if es_empresa_activa(e, activos_norm)]
    nuevas_ex_cliente = [n for n in nuevas if n not in nuevas_activas]

    print(f"Filas tabla_km locales (SAN JUAN): {len(locales)}")
    print(f"Sucursales activas en Siges (SAN JUAN, ID_Prestador={_SIGES_EMPRESA_ID}): {len(siges)}")
    print(f"\nno_encontradas_en_siges (local sin match): {len(no_encontradas)}")
    print(f"sucursales_nuevas_por_importar (Siges sin fila local): {len(nuevas)}")
    print(f"  activas (con actividad reciente 24m): {len(nuevas_activas)}")
    print(f"  ex-clientes: {len(nuevas_ex_cliente)}")

    print("\n=== TODAS las no_encontradas (151): top-1 anclado por empresa exacta ===")
    print("(ratio solo sobre sucursal, cuando la empresa normalizada matchea exacto)\n")
    con_empresa_exacta = sin_empresa_exacta = 0
    ratios_con_empresa = []
    categorias: dict[str, int] = {}
    for empresa, sucursal in no_encontradas:
        candidato, ratio, empresa_exacta = _mejor_candidato_anclado_empresa(
            (empresa, sucursal), siges
        )
        if empresa_exacta:
            con_empresa_exacta += 1
            ratios_con_empresa.append(ratio)
            causa = _clasificar_causa(sucursal, candidato[1], ratio)
        else:
            sin_empresa_exacta += 1
            causa = "sin empresa exacta (posible renombre de empresa/inexistente)"
        categorias[causa] = categorias.get(causa, 0) + 1
        print(f"LOCAL : {empresa!r} | {sucursal!r}")
        marca = "" if empresa_exacta else "  [SIN empresa exacta en Siges]"
        print(
            f"SIGES : {candidato[0]!r} | {candidato[1]!r}  (ratio_sucursal={ratio:.3f}){marca}"
            f"  -> {causa}"
        )
        print()

    print(f"=== Composicion de causas ({len(no_encontradas)} filas, Fase 0.2) ===")
    total = len(no_encontradas)
    for causa, n in sorted(categorias.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d} ({n/total:5.1%})  {causa}")

    print(f"\n=== Resumen anclaje por empresa ({len(no_encontradas)} filas) ===")
    print(f"  con empresa exacta en Siges (compara solo sucursal): {con_empresa_exacta}")
    print(f"  sin empresa exacta en Siges (empresa también difiere/no existe): {sin_empresa_exacta}")
    if ratios_con_empresa:
        rs = sorted(ratios_con_empresa, reverse=True)
        print("\n=== Distribución de ratio_sucursal (solo con empresa exacta, calibración N2) ===")
        print(f"max={rs[0]:.3f} p10={rs[len(rs)//10]:.3f} p25={rs[len(rs)//4]:.3f} "
              f"mediana={rs[len(rs)//2]:.3f} p75={rs[3*len(rs)//4]:.3f} min={rs[-1]:.3f}")

    print(f"\n=== Muestra sucursales_nuevas activas (primeras 20 de {len(nuevas_activas)}) ===")
    for empresa, sucursal in nuevas_activas[:20]:
        print(f"  {empresa!r} | {sucursal!r}")


if __name__ == "__main__":
    main()
