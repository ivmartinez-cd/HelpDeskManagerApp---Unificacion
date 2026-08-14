"""Valida si el `cliente` (texto) de los eventos del calendario de Contadores
cruza contra `dbo.Empresa.Den_Comercial` de Siges, para poder contar las
impresoras de cada cliente (Maquina por ID_Empresa). Todo solo lectura:
SELECT sobre la DB local y sobre SiGesReadOnly.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_cruce_clientes_contadores_siges.py
"""

import asyncio

import pyodbc
from sqlalchemy import text

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30

_SQL_CLIENTES_LOCALES = """
SELECT DISTINCT cliente
FROM contadores_calendar_events
WHERE cliente IS NOT NULL AND cliente <> ''
ORDER BY cliente
"""

_SQL_EMPRESA_EXACTA = """
SELECT ID_Empresa, Den_Comercial, Estado
FROM dbo.Empresa
WHERE Den_Comercial = ?
"""

# Impresoras activas del cliente (misma definición de "activa" que el parque
# por PST, sin el filtro de prestador).
_SQL_MAQUINAS_DEL_CLIENTE = """
SELECT COUNT(*) AS equipos
FROM dbo.Maquina M
WHERE M.ID_Empresa = ? AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
"""


async def _clientes_locales() -> list[str]:
    async with get_sessionmaker()() as db:
        rows = await db.execute(text(_SQL_CLIENTES_LOCALES))
        return [r.cliente for r in rows]


def _cruzar(clientes: list[str]) -> None:
    settings = get_settings()
    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        exactos: list[tuple[str, int, int]] = []
        sin_match: list[str] = []
        ambiguos: list[str] = []
        for nombre in clientes:
            cursor.execute(_SQL_EMPRESA_EXACTA, nombre)
            filas = list(cursor.fetchall())
            activas = [f for f in filas if f.Estado == 0]
            if len(activas) == 1:
                cursor.execute(_SQL_MAQUINAS_DEL_CLIENTE, activas[0].ID_Empresa)
                equipos = cursor.fetchone().equipos
                exactos.append((nombre, activas[0].ID_Empresa, equipos))
            elif len(activas) > 1:
                ambiguos.append(nombre)
            else:
                sin_match.append(nombre)

        total = len(clientes)
        print(f"Clientes distintos en el calendario local: {total}")
        print(f"  Match exacto y único en Empresa (activa): {len(exactos)}")
        print(f"  Ambiguos (varias Empresa activas con ese nombre): {len(ambiguos)}")
        print(f"  Sin match exacto: {len(sin_match)}")

        print("\n=== Muestra de matcheados (nombre → ID_Empresa, impresoras activas) ===")
        for nombre, id_empresa, equipos in exactos[:15]:
            print(f"  {nombre!r} → {id_empresa}: {equipos}")

        if ambiguos:
            print("\n=== Ambiguos ===")
            for nombre in ambiguos[:10]:
                print(f"  {nombre!r}")

        if sin_match:
            print("\n=== Sin match exacto (muestra) ===")
            for nombre in sin_match[:25]:
                print(f"  {nombre!r}")
    finally:
        connection.close()
        print("\nConexión a Siges cerrada explícitamente.")


def main() -> None:
    clientes = asyncio.run(_clientes_locales())
    _cruzar(clientes)


if __name__ == "__main__":
    main()
