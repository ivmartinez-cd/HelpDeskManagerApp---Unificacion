"""Migra a Postgres los datos reales de producción del legacy Liquidacion-Prestadores
(SQLite, sin Alembic). Script operativo de un solo uso (Fase 3,
`INTEGRACION_APPS_PLAN.md`) -- no forma parte del flujo de negocio de la app, por eso
vive en `scripts/` y no en `infrastructure/`. Solo lee del snapshot SQLite (nunca
escribe ahí) e inserta usando los modelos SQLAlchemy reales del módulo, para no
duplicar el mapeo columna->entidad. Ver `_migrate_liquidaciones_specs.py` para el
detalle de qué columnas viajan y cómo se convierten.

Fuente: snapshot READ-ONLY del volumen del contenedor productivo
`liquidacion-prestadores-backend-1` (nunca un `cp` del archivo en caliente -- usar la
API de backup de SQLite, ver `LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`). El
snapshot NO se commitea al repo: es un archivo temporal con datos reales de
producción, se pasa por argumento y se descarta después de correr el script.

Todas las 11 tablas legacy usan `id INTEGER` autoincrement; las nuevas usan
`id UUID`. Se generan UUIDs nuevos en Python (no `RETURNING`) y se remapean las FKs
con un diccionario `{tabla: {id_legacy: uuid_nuevo}}` construido en el mismo orden
topológico en que se insertan las filas -- el destino sí enforza las FKs, el legacy no.
`reglas_alerta` NO se toca acá: es catálogo, se siembra por Alembic
(`17663a83c3fd_seed_liquidaciones_reglas_alerta.py`).

Columnas `ayc_*`/WS AyC del legacy se descartan a propósito (fuera de alcance, ver
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md`) -- ninguna existe físicamente en la
SQLite real (el legacy usa `create_all`, que nunca las agregó a la tabla ya creada),
así que ni siquiera se seleccionan: un `SELECT *` derivado de los modelos del legacy
rompería con `no such column`.

No idempotente a propósito: aborta si alguna tabla destino ya tiene filas, en vez de
mezclar una migración parcial con una re-corrida.

Uso: `uv run python scripts/migrate_liquidaciones_data_from_sqlite.py <snapshot.db>`
"""

import asyncio
import json
import sqlite3
import sys
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scripts._migrate_liquidaciones_specs import ORDEN_TOPOLOGICO, TablaSpec
from src.shared.infrastructure.database.session import get_sessionmaker


def _parse_timestamp(raw: str) -> datetime:
    """Naive 'YYYY-MM-DD HH:MM:SS' de SQLite: viene de `CURRENT_TIMESTAMP`, que en
    SQLite es UTC (ningún timestamp del legacy lo pone la app -- todos son
    `server_default`). Etiquetarlo aware evita un corrimiento de 3 h al insertar en
    una columna `timestamptz`."""
    return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)


def _convertir_valor(
    spec: TablaSpec, col: str, raw: Any, mapas: dict[str, dict[int, UUID]]
) -> Any:
    if col in spec.fks:
        return mapas[spec.fks[col]][raw] if raw is not None else None
    if col in spec.bools:
        return bool(raw) if raw is not None else spec.bool_defaults.get(col, False)
    if col in spec.jsons:
        return json.loads(raw) if raw is not None else spec.json_defaults.get(col)
    if col in spec.fechas:
        return date.fromisoformat(raw) if raw is not None else None
    if col in spec.timestamps:
        return _parse_timestamp(raw) if raw is not None else None
    return raw


def _construir_fila(
    spec: TablaSpec, row: sqlite3.Row, mapas: dict[str, dict[int, UUID]]
) -> tuple[int, UUID, Any]:
    kwargs: dict[str, Any] = {"id": uuid4()}
    for col in spec.columnas:
        kwargs[col] = _convertir_valor(spec, col, row[col], mapas)
    if spec.post_procesar is not None:
        spec.post_procesar(kwargs, row, mapas)
    return row["id"], kwargs["id"], spec.modelo(**kwargs)


def _leer_filas(con: sqlite3.Connection, spec: TablaSpec) -> list[sqlite3.Row]:
    presentes = {r[1] for r in con.execute(f"PRAGMA table_info([{spec.origen}])")}
    faltantes = [c for c in spec.columnas if c not in presentes]
    if faltantes:
        raise RuntimeError(
            f"{spec.origen}: columnas esperadas ausentes en el snapshot: {faltantes}"
        )
    cols_sql = ", ".join(("id", *spec.columnas))
    return con.execute(f"SELECT {cols_sql} FROM [{spec.origen}]").fetchall()


async def _tablas_destino_vacias(session: AsyncSession) -> bool:
    for spec in ORDEN_TOPOLOGICO:
        total = await session.scalar(select(func.count()).select_from(spec.modelo))
        if total:
            return False
    return True


async def _migrar(con: sqlite3.Connection) -> None:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        if not await _tablas_destino_vacias(session):
            raise RuntimeError(
                "Alguna tabla destino ya tiene filas -- este script no es idempotente, "
                "correrlo solo contra un destino vacío."
            )

        mapas: dict[str, dict[int, UUID]] = {}
        conteos: dict[str, int] = {}

        for spec in ORDEN_TOPOLOGICO:
            filas = _leer_filas(con, spec)
            mapa_tabla: dict[int, UUID] = {}
            for row in filas:
                id_legacy, id_nuevo, instancia = _construir_fila(spec, row, mapas)
                mapa_tabla[id_legacy] = id_nuevo
                session.add(instancia)
            # Flush explícito por tabla (no commit: la transacción sigue abierta) para
            # que el orden de INSERT en Postgres respete el orden topológico exacto,
            # en vez de confiar en que el unit-of-work de SQLAlchemy lo infiera solo.
            await session.flush()
            mapas[spec.origen] = mapa_tabla
            conteos[spec.origen] = len(filas)

        await session.commit()

    for tabla, n in conteos.items():
        print(f"{tabla}: {n} filas migradas")


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: uv run python scripts/migrate_liquidaciones_data_from_sqlite.py <snapshot.db>")
        raise SystemExit(1)

    con = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        asyncio.run(_migrar(con))
    finally:
        con.close()


if __name__ == "__main__":
    main()
