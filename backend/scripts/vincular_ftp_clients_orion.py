"""Vincula los clientes FTP de HDM a su grupo económico de Siges/ORION (migración
d6b2e8f4a1c7). Vincula solo los casos sin ambigüedad: el usuario coincide con un
único grupo, la contraseña es la misma y el servidor es el de la empresa. Al
vincular, la contraseña local se borra (se lee de Siges al procesar). El resto se
lista para revisarlo a mano y queda con sus datos locales.

Solo SELECTs contra ORION. Sin --aplicar no escribe nada.

Uso (dentro del contenedor backend):
    uv run python scripts/vincular_ftp_clients_orion.py            # muestra el plan
    uv run python scripts/vincular_ftp_clients_orion.py --aplicar  # lo ejecuta
"""

import asyncio
import sys
from collections import defaultdict

import pyodbc
from sqlalchemy import text

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_engine
from src.shared.infrastructure.orion.connection import build_orion_connection_string

_SQL_ORION = """
SELECT id, descripcion, LTRIM(RTRIM(userftp)) AS usuario, passftp
FROM dbo.GrupoEconomico WHERE ISNULL(LTRIM(RTRIM(userftp)), '') <> ''
"""
_SQL_LOCALES = (
    'SELECT id, name, host, "user", password FROM ftp_clients WHERE grupo_economico_id IS NULL'
)
_SQL_VINCULAR = (
    'UPDATE ftp_clients SET grupo_economico_id = :grupo, "user" = :usuario, password = NULL '
    "WHERE id = :id"
)


def _grupos_por_usuario() -> dict[str, list[tuple[int, str, str, str]]]:
    conn = pyodbc.connect(
        build_orion_connection_string(get_settings()), timeout=30, autocommit=True
    )
    try:
        rows = conn.cursor().execute(_SQL_ORION).fetchall()
    finally:
        conn.close()
    grupos: dict[str, list[tuple[int, str, str, str]]] = defaultdict(list)
    for r in rows:
        grupos[r.usuario.lower()].append((r.id, r.descripcion.strip(), r.usuario, r.passftp or ""))
    return grupos


def _motivo_para_no_vincular(local, candidatos, host: str) -> str | None:
    if not candidatos:
        return "su usuario no está en Siges"
    if len(candidatos) > 1:
        return "el usuario aparece en varios grupos: " + ", ".join(c[1] for c in candidatos)
    if local.host != host:
        return f"usa otro servidor ({local.host})"
    if (local.password or "").strip() != candidatos[0][3].strip():
        return f"la contraseña difiere de la de Siges ({candidatos[0][1]})"
    return None


async def main(aplicar: bool) -> None:
    host = get_settings().contadores_ftp_host
    grupos = _grupos_por_usuario()
    async with get_engine().begin() as conn:
        locales = (await conn.execute(text(_SQL_LOCALES))).all()
        vinculables, revisar = [], []
        for local in locales:
            candidatos = grupos.get(local.user.strip().lower(), [])
            motivo = _motivo_para_no_vincular(local, candidatos, host)
            (revisar if motivo else vinculables).append((local, candidatos, motivo))
        print(f"{len(vinculables)} para vincular, {len(revisar)} para revisar a mano:")
        for local, _, motivo in revisar:
            print(f"  - {local.name}: {motivo}")
        if not aplicar:
            print("\nSin --aplicar: no se escribió nada.")
            return
        for local, candidatos, _ in vinculables:
            grupo_id, _, usuario, _ = candidatos[0]
            await conn.execute(
                text(_SQL_VINCULAR), {"grupo": grupo_id, "usuario": usuario, "id": local.id}
            )
        print(f"\nVinculados {len(vinculables)} clientes.")


if __name__ == "__main__":
    asyncio.run(main("--aplicar" in sys.argv))
