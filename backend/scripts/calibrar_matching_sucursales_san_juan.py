"""Calibración Fase 0.3: corre el matching N1/N2 REAL de producción
(`matching_sucursales_tabla_km.py`) contra las 151 filas sin match de SAN
JUAN, para revisar la calidad de las propuestas antes de cerrar Fase 1.
Solo lectura, sin Google. Uso (dentro del contenedor backend):
    uv run python scripts/calibrar_matching_sucursales_san_juan.py
"""

import asyncio
from uuid import uuid4

import pyodbc
from sqlalchemy import text

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.matching_sucursales_tabla_km import (
    FilaSinMatch,
    proponer_matches_tabla_km,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre
from src.modules.liquidaciones.infrastructure.siges.query import SUCURSALES_DE_PRESTADOR_SQL
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_PRESTADOR_ID = "eda1e000-b50f-4475-bf2c-4d1bc3cf116e"
_SIGES_EMPRESA_ID = 504
_TIMEOUT_SECONDS = 30


async def _locales() -> list[tuple[str, str]]:
    async with get_sessionmaker()() as db:
        rows = await db.execute(
            text("SELECT empresa_nombre, sucursal_nombre FROM tabla_kms WHERE prestador_id = :p"),
            {"p": _PRESTADOR_ID},
        )
        return [(r.empresa_nombre, r.sucursal_nombre) for r in rows]


def _siges_sucursales() -> list[SigesSucursalCliente]:
    settings = get_settings()
    connection = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        cursor.execute(SUCURSALES_DE_PRESTADOR_SQL, _SIGES_EMPRESA_ID)
        return [
            SigesSucursalCliente(
                siges_sucursal_id=int(r.Id_Sucursal),
                empresa_nombre=str(r.Den_Comercial),
                sucursal_nombre=str(r.descripcion),
                domicilio=r.Domicilio,
                localidad=r.DesCiudad,
                provincia=r.DesProvincia,
            )
            for r in cursor.fetchall()
        ]
    finally:
        connection.close()


def main() -> None:
    locales = asyncio.run(_locales())
    siges = _siges_sucursales()
    claves_siges = {(normalizar_nombre(s.empresa_nombre), normalizar_nombre(s.sucursal_nombre)) for s in siges}
    no_encontradas = [
        (e, s) for e, s in locales if (normalizar_nombre(e), normalizar_nombre(s)) not in claves_siges
    ]

    filas = [FilaSinMatch(uuid4(), e, s) for e, s in no_encontradas]
    propuestas = proponer_matches_tabla_km(filas, siges)

    por_id = {f.id: (f.empresa_nombre, f.sucursal_nombre) for f in filas}
    n1 = n2 = sin_candidato = 0
    for fila in filas:
        cands = propuestas.get(fila.id, [])
        if not cands:
            sin_candidato += 1
            continue
        if cands[0].nivel == "N1":
            n1 += 1
        else:
            n2 += 1

    print(f"Total no_encontradas: {len(filas)}")
    print(f"  N1 (auto-vinculable, top-1): {n1}")
    print(f"  N2 (con candidato, requiere confirmacion): {n2}")
    print(f"  Sin candidato (ninguno de la empresa o bajo umbral): {sin_candidato}")

    print("\n=== N2: todas las propuestas (revisar motivo/score) ===")
    for fila in filas:
        cands = propuestas.get(fila.id, [])
        if not cands or cands[0].nivel != "N2":
            continue
        empresa, sucursal = por_id[fila.id]
        print(f"LOCAL: {empresa!r} | {sucursal!r}")
        for c in cands:
            siges_nombre = next(s.sucursal_nombre for s in siges if s.siges_sucursal_id == c.siges_sucursal_id)
            print(f"  -> [{c.nivel} score={c.score:.3f}] {siges_nombre!r}  ({c.motivo})")
        print()

    print("=== SIN candidato (top motivo: no hay nada de la empresa o todo < umbral) ===")
    for fila in filas:
        if fila.id not in propuestas:
            empresa, sucursal = por_id[fila.id]
            print(f"  {empresa!r} | {sucursal!r}")


if __name__ == "__main__":
    main()
