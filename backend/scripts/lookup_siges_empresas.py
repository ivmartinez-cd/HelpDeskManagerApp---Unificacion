"""Busca en `dbo.Empresa` (Siges/MERCURIO) candidatos por texto para PST que
todavía no están cargados en `modules/prestadores`. Script operativo de un
solo uso, read-only (misma cuenta `db_datareader` que ya usa el módulo sla —
sin permisos de escritura, verificado en `pyodbc_prestador_gateway.py`).

Uso: `uv run python scripts/lookup_siges_empresas.py`
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TERMINOS = [
    "Formosa",
    "Armoa",
    "Posadas",
    "Godoy",
    "Rio Gallegos",
    "Basiglio",
    "Trelew",
    "Erdozain",
    "Copytec",
    "Tandil",
    "Basili",
    "Tucuman",
    "Naselli",
    "Herculano",
]


def _buscar(cursor: pyodbc.Cursor, termino: str) -> list[pyodbc.Row]:
    sql = (
        "SELECT ID_Empresa, Den_Comercial, razon_social, cuit "
        "FROM dbo.Empresa WHERE Den_Comercial LIKE ? OR razon_social LIKE ?"
    )
    patron = f"%{termino}%"
    cursor.execute(sql, (patron, patron))
    return list(cursor.fetchall())


def main() -> None:
    settings = get_settings()
    conn_str = build_mercurio_connection_string(settings)
    with pyodbc.connect(conn_str, timeout=15) as conn:
        conn.timeout = 15
        cursor = conn.cursor()
        for termino in _TERMINOS:
            filas = _buscar(cursor, termino)
            print(f"\n=== '{termino}' ({len(filas)} resultado/s) ===")
            for fila in filas:
                print(
                    f"  ID_Empresa={fila.ID_Empresa!r} "
                    f"Den_Comercial={fila.Den_Comercial!r} "
                    f"razon_social={fila.razon_social!r} "
                    f"cuit={fila.cuit!r}"
                )


if __name__ == "__main__":
    main()
