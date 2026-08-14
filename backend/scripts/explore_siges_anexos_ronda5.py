"""Ronda 5 de exploración AnexosNoFacturados (rondas previas en
explore_siges_anexos_no_facturados.py / _ronda3.py / _ronda4.py).

Objetivos:
1. Historia completa de Factura_Anexo para 'COD36CDSI00816/Anexo 1' — el
   legacy lo muestra dos veces (FACTURADO 202607 y DEMORADO 202602) pero la
   query de "agujeros" de ronda 4 no lo encontró.
2. Origen del importe USD: columnas de Factura_SubProceso, Factura_Contador,
   Renta, Factura_Escala_C/D, Factura_Empresa, Factura_Impresion_Concepto y
   búsqueda del 6.472,41 de 'SUMCDSI0077/C2' por Nro_Proceso.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_anexos_ronda5.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

_SQL_HISTORIA_816 = """
SELECT FA.PeriodoFacturacion, FA.Nro_Proceso, FA.Fecha_Proceso,
       FA.ListoParaFacturar, FA.Facturado, FA.Estado, FA.ImpresionesAnexo
FROM dbo.Factura_Anexo FA
INNER JOIN dbo.Anexo A ON A.ID_Anexo = FA.ID_Anexo
WHERE A.NombreAnexo = ?
ORDER BY FA.PeriodoFacturacion DESC, FA.Nro_Proceso DESC
"""

_SQL_COLUMNAS = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
"""

_TABLAS = [
    "Factura_SubProceso",
    "Factura_Contador",
    "Renta",
    "Factura_Escala_C",
    "Factura_Escala_D",
    "Factura_Empresa",
    "Factura_Impresion_Concepto",
]

_SQL_SUBPROCESO_ROEMMERS = """
SELECT TOP 10 FS.*
FROM dbo.Factura_SubProceso FS
WHERE FS.Nro_Proceso IN (
  SELECT FA.Nro_Proceso
  FROM dbo.Factura_Anexo FA
  INNER JOIN dbo.Anexo A ON A.ID_Anexo = FA.ID_Anexo
  WHERE A.NombreAnexo = ? AND FA.Facturado = 0
)
"""


def _historia_816(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_HISTORIA_816, "COD36CDSI00816/Anexo 1")
    filas = list(cursor.fetchall())
    print(f"=== Historia Factura_Anexo de 'COD36CDSI00816/Anexo 1' ({len(filas)}) ===")
    for f in filas:
        print(
            f"  periodo={f.PeriodoFacturacion} proceso={f.Nro_Proceso} "
            f"fecha={f.Fecha_Proceso} listo={f.ListoParaFacturar} "
            f"facturado={f.Facturado} estado={f.Estado} impresiones={f.ImpresionesAnexo}"
        )


def _columnas(cursor: pyodbc.Cursor) -> None:
    for tabla in _TABLAS:
        cursor.execute(_SQL_COLUMNAS, tabla)
        filas = list(cursor.fetchall())
        print(f"\n=== {tabla} ({len(filas)} columnas) ===")
        for f in filas:
            print(f"  {f.COLUMN_NAME} ({f.DATA_TYPE})")


def _subproceso_roemmers(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_SUBPROCESO_ROEMMERS, "SUMCDSI0077/C2")
    cols = [d[0] for d in cursor.description]
    filas = list(cursor.fetchall())
    print(f"\n=== Factura_SubProceso del pendiente de 'SUMCDSI0077/C2' ({len(filas)}) ===")
    print(f"  columnas: {cols}")
    for f in filas:
        print(f"  {tuple(f)}")


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _historia_816(cursor)
        _columnas(cursor)
        _subproceso_roemmers(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
