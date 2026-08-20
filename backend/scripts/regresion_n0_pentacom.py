"""Fase 3 del plan de matching+geovalidacion: regresión de N0. Confirma que
el matching N1/N2 agregado no cambió el comportamiento de `normalizar_nombre`
(RefrescarDatosSiges) para un PST de control — read-only, no llama a
`RefrescarDatosSiges.execute()` (que escribe), solo reproduce su criterio de
match exacto para contar no_encontradas, comparando contra el número de
referencia mencionado en el plan (PENTACOM 247/276).

Uso (dentro del contenedor backend):
    uv run python scripts/regresion_n0_pentacom.py
"""

import asyncio

import pyodbc
from sqlalchemy import text

from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre
from src.modules.liquidaciones.infrastructure.siges.query import SUCURSALES_DE_PRESTADOR_SQL
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_PRESTADOR_ID = "9f39c270-6f4a-4cc4-96d8-2300a63ed782"  # Cordoba - Pentacom S.A.
_SIGES_EMPRESA_ID = 137
_TIMEOUT_SECONDS = 30


async def _locales() -> list[tuple[str, str]]:
    async with get_sessionmaker()() as db:
        rows = await db.execute(
            text("SELECT empresa_nombre, sucursal_nombre FROM tabla_kms WHERE prestador_id = :p"),
            {"p": _PRESTADOR_ID},
        )
        return [(r.empresa_nombre, r.sucursal_nombre) for r in rows]


def _siges_sucursales() -> list[tuple[str, str]]:
    settings = get_settings()
    conn = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        conn.timeout = _TIMEOUT_SECONDS
        cursor = conn.cursor()
        cursor.execute(SUCURSALES_DE_PRESTADOR_SQL, _SIGES_EMPRESA_ID)
        return [(str(r.Den_Comercial), str(r.descripcion)) for r in cursor.fetchall()]
    finally:
        conn.close()


def main() -> None:
    locales = asyncio.run(_locales())
    siges = _siges_sucursales()
    claves_siges = {(normalizar_nombre(e), normalizar_nombre(s)) for e, s in siges}
    encontradas = sum(
        1 for e, s in locales if (normalizar_nombre(e), normalizar_nombre(s)) in claves_siges
    )
    no_encontradas = len(locales) - encontradas

    print(f"PENTACOM — filas locales tabla_kms: {len(locales)}")
    print(f"Sucursales activas en Siges: {len(siges)}")
    print(f"N0 encontradas (match exacto normalizar_nombre): {encontradas}")
    print(f"N0 no_encontradas: {no_encontradas}")
    print("\nReferencia del plan: PENTACOM 247/276 (matched/total esperado, verificar orden)")


if __name__ == "__main__":
    main()
