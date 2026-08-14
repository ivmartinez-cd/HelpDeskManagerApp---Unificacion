"""Ronda 3 de exploración AnexosNoFacturados (ver
explore_siges_anexos_no_facturados.py para rondas 1-2). Objetivos:

1. Paridad del universo pendiente: mi corte da 56+ filas con
   Facturado=0/Listo=0 vs 44 DEMORADO del legacy — encontrar el filtro extra
   (¿ID_EstadoAnexo? ¿Contrato.Estado? ¿GrupoEconomico.Estado?).
2. Origen del importe USD del reporte (Factura_Renta / Factura_Detalle /
   Factura_Cabecera / Informe_Factura, vía Nro_Proceso).
3. Joins de presentación: GrupoEconomico, Contrato, Empresa admin (¿de dónde
   sale 'CDSISA'?), Vendedor, Moneda.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_anexos_ronda3.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

_SQL_PENDIENTES = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, FA.PeriodoFacturacion, FA.Nro_Proceso, FA.Fecha_Proceso,
         FA.ListoParaFacturar, FA.Facturado,
         ROW_NUMBER() OVER (
           PARTITION BY FA.ID_Anexo
           ORDER BY FA.PeriodoFacturacion DESC, FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
)
SELECT u.PeriodoFacturacion AS periodo, u.Nro_Proceso, A.NombreAnexo,
       A.ID_EstadoAnexo, A.discriminador, A.ID_GrupoE,
       C.NombreContrato, C.Estado AS contrato_estado,
       G.descripcion AS grupo, G.Estado AS grupo_estado
FROM ultimo u
INNER JOIN dbo.Anexo A ON A.ID_Anexo = u.ID_Anexo
LEFT JOIN dbo.Contrato C ON C.ID_Contrato = A.ID_Contrato
LEFT JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
WHERE u.rn = 1 AND u.Facturado = 0 AND u.ListoParaFacturar = 0
  AND u.PeriodoFacturacion < ?
ORDER BY u.PeriodoFacturacion DESC, A.NombreAnexo
"""

_SQL_COLUMNAS = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
"""

_TABLAS_IMPORTE = ["Factura_Renta", "Factura_Detalle", "Factura_Cabecera", "Informe_Factura", "Moneda", "Empresa"]

# Roemmers SUMCDSI0077/C2: DEMORADO 202607, USD 6.472,41 en el legacy.
_SQL_RENTA_PROCESO = """
SELECT TOP 20 FR.*
FROM dbo.Factura_Renta FR
INNER JOIN dbo.Factura_Anexo FA ON FA.Nro_Proceso = FR.Nro_Proceso
INNER JOIN dbo.Anexo A ON A.ID_Anexo = FA.ID_Anexo
WHERE A.NombreAnexo = ?
  AND FA.Facturado = 0 AND FA.ListoParaFacturar = 0
"""


def _pendientes(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_PENDIENTES, "202608")
    filas = list(cursor.fetchall())
    print(f"=== Pendientes (facturado=0, listo=0, periodo<202608): {len(filas)} ===")
    for f in filas:
        print(
            f"  {f.periodo} {f.NombreAnexo!r} estado_anexo={f.ID_EstadoAnexo} "
            f"disc={f.discriminador!r} contrato={f.NombreContrato!r} "
            f"c_estado={f.contrato_estado} grupo={f.grupo!r} g_estado={f.grupo_estado}"
        )


def _columnas(cursor: pyodbc.Cursor) -> None:
    for tabla in _TABLAS_IMPORTE:
        cursor.execute(_SQL_COLUMNAS, tabla)
        filas = list(cursor.fetchall())
        print(f"\n=== {tabla} ({len(filas)} columnas) ===")
        for f in filas:
            print(f"  {f.COLUMN_NAME} ({f.DATA_TYPE})")


def _renta_roemmers(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_RENTA_PROCESO, "SUMCDSI0077/C2")
    cols = [d[0] for d in cursor.description]
    filas = list(cursor.fetchall())
    print(f"\n=== Factura_Renta del proceso pendiente de 'SUMCDSI0077/C2' ({len(filas)} filas) ===")
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
        _pendientes(cursor)
        _columnas(cursor)
        _renta_roemmers(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
