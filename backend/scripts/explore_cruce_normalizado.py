"""Ronda 2 del cruce clientes-calendario vs Empresa de Siges: mide cuánto
mejora el match con normalización (case/acentos/trim) y con contención
(nombre del evento contenido en Den_Comercial o al revés). Solo lectura.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_cruce_normalizado.py
"""

import asyncio
import re
import unicodedata

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
"""

_SQL_EMPRESAS_ACTIVAS = """
SELECT ID_Empresa, Den_Comercial
FROM dbo.Empresa
WHERE Estado = 0
"""


def _normalizar(nombre: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    # colapsa espacios y saca puntuación menor para comparar "S.A." vs "SA"
    limpio = re.sub(r"[.,]", "", sin_acentos).strip().upper()
    return re.sub(r"\s+", " ", limpio)


async def _clientes_locales() -> list[str]:
    async with get_sessionmaker()() as db:
        rows = await db.execute(text(_SQL_CLIENTES_LOCALES))
        return [r.cliente for r in rows]


def _empresas() -> list[tuple[int, str]]:
    settings = get_settings()
    connection = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        cursor.execute(_SQL_EMPRESAS_ACTIVAS)
        return [(int(r.ID_Empresa), str(r.Den_Comercial)) for r in cursor.fetchall()]
    finally:
        connection.close()


def main() -> None:
    clientes = asyncio.run(_clientes_locales())
    empresas = _empresas()
    por_norm: dict[str, list[tuple[int, str]]] = {}
    for id_empresa, den in empresas:
        por_norm.setdefault(_normalizar(den), []).append((id_empresa, den))

    exactos = 0
    contenidos = 0
    ambiguos = 0
    sin_match: list[str] = []
    for cliente in clientes:
        norm = _normalizar(cliente)
        candidatos = por_norm.get(norm, [])
        if len(candidatos) == 1:
            exactos += 1
            continue
        if len(candidatos) > 1:
            ambiguos += 1
            continue
        # contención en ambos sentidos (>=5 chars para evitar falsos positivos)
        contencion = [
            (i, d)
            for n, lst in por_norm.items()
            for (i, d) in lst
            if len(norm) >= 5 and (norm in n or n in norm)
        ]
        if len(contencion) == 1:
            contenidos += 1
        elif len(contencion) > 1:
            ambiguos += 1
        else:
            sin_match.append(cliente)

    total = len(clientes)
    print(f"Clientes distintos: {total}")
    print(f"  Exacto normalizado y único: {exactos}")
    print(f"  Único por contención: {contenidos}")
    print(f"  Ambiguos: {ambiguos}")
    print(f"  Sin match: {len(sin_match)}")
    print(f"  Cobertura (exacto+contención): {(exactos + contenidos) / total:.1%}")
    print("\n=== Sin match (muestra) ===")
    for nombre in sin_match[:25]:
        print(f"  {nombre!r}")


if __name__ == "__main__":
    main()
