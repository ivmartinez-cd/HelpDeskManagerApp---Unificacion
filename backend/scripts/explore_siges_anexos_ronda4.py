"""Ronda 4 de exploración AnexosNoFacturados (rondas 1-3 en
explore_siges_anexos_no_facturados.py / explore_siges_anexos_ronda3.py).

Objetivos:
1. ¿El importe "USD" del legacy es Anexo.ValorFijo? (COD36CDSI00816 muestra
   745,00 en sus dos filas, FACTURADO 202607 y DEMORADO 202602.)
2. Confirmar la ventana: los 14 pendientes que el legacy excluye deberían
   tener Fecha_Proceso < 2025-08-01 (ref 202608 - 12 meses); los 44 incluidos,
   >= esa fecha.
3. Joins de presentación: E.ADMIN (Contrato.ID_EmpresaAdmin → Empresa),
   VENDEDOR (Contrato.Id_Vendedor → Vendedor), monedas (Anexo.moneda_id /
   moneda_facturacion_id → Moneda).

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_anexos_ronda4.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

# (nombre, importe USD que muestra el legacy 2026-08-14)
_MUESTRA_IMPORTES = [
    ("COD36CDSI00816/Anexo 1", "745,00"),
    ("SUMCDSI0077/C2", "6.472,41"),
    ("SUMCDSI0077/A3", "3.085,13"),
    ("ANEXO A OC 4500334404", "380,01"),
    ("COD48CDSI00677/A", "9.609,64"),
    ("COD36CDSI00674/A/C", "1.044,99"),
    ("COD36CDSI00248/A1", "0,00"),
]

_SQL_VALOR_FIJO = """
SELECT A.NombreAnexo, A.ValorFijo, A.ID_Moneda, A.moneda_id,
       A.moneda_facturacion_id, MO.Descripcion AS moneda,
       MF.Descripcion AS moneda_fact,
       EA.Den_Comercial AS empresa_admin, V.Descripcion AS vendedor
FROM dbo.Anexo A
LEFT JOIN dbo.Contrato C ON C.ID_Contrato = A.ID_Contrato
LEFT JOIN dbo.Empresa EA ON EA.ID_Empresa = C.ID_EmpresaAdmin
LEFT JOIN dbo.Vendedor V ON V.Id_Vendedor = C.Id_Vendedor
LEFT JOIN dbo.Moneda MO ON MO.Id = A.moneda_id
LEFT JOIN dbo.Moneda MF ON MF.Id = A.moneda_facturacion_id
WHERE A.NombreAnexo = ?
"""

# Pendientes (facturado=0, listo=0) que son última fila de su anexo, con
# Fecha_Proceso — para validar la ventana de 12 meses del legacy.
_SQL_PENDIENTES_FECHAS = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, FA.PeriodoFacturacion, FA.Fecha_Proceso,
         FA.ListoParaFacturar, FA.Facturado,
         ROW_NUMBER() OVER (
           PARTITION BY FA.ID_Anexo
           ORDER BY FA.PeriodoFacturacion DESC, FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
)
SELECT u.PeriodoFacturacion AS periodo, u.Fecha_Proceso, A.NombreAnexo
FROM ultimo u
INNER JOIN dbo.Anexo A ON A.ID_Anexo = u.ID_Anexo
WHERE u.rn = 1 AND u.Facturado = 0 AND u.ListoParaFacturar = 0
  AND A.ID_EstadoAnexo = 1
ORDER BY u.Fecha_Proceso
"""

# Pendientes que NO son la última fila (agujeros tipo COD36CDSI00816 202602).
_SQL_AGUJEROS = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, FA.PeriodoFacturacion, FA.Nro_Proceso, FA.Fecha_Proceso,
         FA.ListoParaFacturar, FA.Facturado,
         ROW_NUMBER() OVER (
           PARTITION BY FA.ID_Anexo
           ORDER BY FA.PeriodoFacturacion DESC, FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
)
SELECT u.PeriodoFacturacion AS periodo, u.Fecha_Proceso, u.rn, A.NombreAnexo,
       A.ID_EstadoAnexo
FROM ultimo u
INNER JOIN dbo.Anexo A ON A.ID_Anexo = u.ID_Anexo
WHERE u.rn > 1 AND u.Facturado = 0 AND u.ListoParaFacturar = 0
  AND u.Fecha_Proceso >= ?
ORDER BY u.Fecha_Proceso
"""


def _importes(cursor: pyodbc.Cursor) -> None:
    print("=== ¿USD == Anexo.ValorFijo? + joins de presentación ===")
    for nombre, usd_legacy in _MUESTRA_IMPORTES:
        cursor.execute(_SQL_VALOR_FIJO, nombre)
        filas = list(cursor.fetchall())
        for f in filas:
            print(
                f"  {nombre!r}: legacy={usd_legacy} valor_fijo={f.ValorFijo} "
                f"moneda={f.moneda!r} moneda_fact={f.moneda_fact!r} "
                f"admin={f.empresa_admin!r} vendedor={f.vendedor!r}"
            )
        if not filas:
            print(f"  {nombre!r}: SIN FILA EN Anexo")


def _fechas_pendientes(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_PENDIENTES_FECHAS)
    filas = list(cursor.fetchall())
    print(f"\n=== Pendientes última-fila con anexo Activo ({len(filas)}) por Fecha_Proceso ===")
    for f in filas:
        print(f"  {f.Fecha_Proceso} periodo={f.periodo} {f.NombreAnexo!r}")


def _agujeros(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_AGUJEROS, "2025-08-01")
    filas = list(cursor.fetchall())
    print(f"\n=== Pendientes que no son última fila (agujeros), proceso >= 2025-08 ({len(filas)}) ===")
    for f in filas:
        print(
            f"  {f.Fecha_Proceso} periodo={f.periodo} rn={f.rn} "
            f"estado_anexo={f.ID_EstadoAnexo} {f.NombreAnexo!r}"
        )


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _importes(cursor)
        _fechas_pendientes(cursor)
        _agujeros(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
