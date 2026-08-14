"""Explora SiGesReadOnly para recrear el reporte legacy "FACTURACION ANEXOS"
(`sitesphp/.../SiGes/AnexosNoFacturados/RUN.php`). Solo SELECTs parametrizados,
misma cuenta de solo lectura y mismo patrón que explore_siges_parque_pst.py
(conexión efímera, autocommit=True, close() explícito en finally).

Ronda 1 (hecha): Estado_Anexo es ciclo de vida del anexo (Activo/En Demo/...),
no el estado de facturación del reporte. El estado por período tiene que salir
de Factura_Anexo (PeriodoFacturacion, ListoParaFacturar, Facturado, Estado).

Ronda 2: mapear estados del legacy contra flags de Factura_Anexo usando filas
reales capturadas del reporte (2026-08-14, ref=202608):
  - 'COD48CDSI00677/A'  → 202607 LIBERADO   (fecha 03/08/26, USD 9.609,64)
  - 'COD36CDSI00684/A/C'→ 202607 FACTURADO  (fecha 27/07/26)
  - 'COD36CDSI00797/B'  → 202607 A LIBERAR  (fecha 06/08/26)
  - 'COD36CDSI00248/A1' → 202607 DEMORADO   (fecha 14/08/26, 0,00)
  - 'COD36CDSI00707/B'  → 202608 EN PROCESO (fecha 14/08/26, 0,00)
  - 'COD36CDSI00674/A1 OC 4500008054' → 202606 DEMORADO (12/08/26)

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_anexos_no_facturados.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30

_ANEXOS_MUESTRA = [
    ("COD48CDSI00677/A", "LIBERADO 202607"),
    ("COD36CDSI00684/A/C", "FACTURADO 202607"),
    ("COD36CDSI00797/B", "A LIBERAR 202607"),
    ("COD36CDSI00248/A1", "DEMORADO 202607"),
    ("COD36CDSI00707/B", "EN PROCESO 202608"),
    ("COD36CDSI00674/A1 OC 4500008054", "DEMORADO 202606"),
]

_SQL_FACTURA_ANEXO_POR_NOMBRE = """
SELECT TOP 4 A.ID_Anexo, A.NombreAnexo, A.ID_EstadoAnexo, A.discriminador,
       FA.Nro_Proceso, FA.PeriodoFacturacion, FA.Fecha_Proceso,
       FA.ListoParaFacturar, FA.FechaListoParaFacturar,
       FA.Facturado, FA.Estado, FA.Fecha_Mod, FA.ImpresionesAnexo
FROM dbo.Anexo A
INNER JOIN dbo.Factura_Anexo FA ON FA.ID_Anexo = A.ID_Anexo
WHERE A.NombreAnexo = ?
ORDER BY FA.PeriodoFacturacion DESC, FA.Nro_Proceso DESC
"""

_SQL_COMBOS_ULTIMO_PERIODO = """
WITH ultimo AS (
  SELECT FA.*, ROW_NUMBER() OVER (
           PARTITION BY FA.ID_Anexo
           ORDER BY FA.PeriodoFacturacion DESC, FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
  WHERE FA.PeriodoFacturacion >= ?
)
SELECT u.PeriodoFacturacion, u.Facturado, u.ListoParaFacturar, u.Estado,
       COUNT(*) AS cantidad
FROM ultimo u
WHERE u.rn = 1
GROUP BY u.PeriodoFacturacion, u.Facturado, u.ListoParaFacturar, u.Estado
ORDER BY u.PeriodoFacturacion DESC, cantidad DESC
"""


def _muestra_por_nombre(cursor: pyodbc.Cursor) -> None:
    for nombre, esperado in _ANEXOS_MUESTRA:
        cursor.execute(_SQL_FACTURA_ANEXO_POR_NOMBRE, nombre)
        filas = list(cursor.fetchall())
        print(f"\n=== {nombre!r} (legacy: {esperado}) — {len(filas)} filas ===")
        for f in filas:
            print(
                f"  periodo={f.PeriodoFacturacion} proceso={f.Nro_Proceso} "
                f"fecha_proceso={f.Fecha_Proceso} listo={f.ListoParaFacturar} "
                f"fecha_listo={f.FechaListoParaFacturar} facturado={f.Facturado} "
                f"estado={f.Estado} fecha_mod={f.Fecha_Mod} "
                f"impresiones={f.ImpresionesAnexo} estado_anexo={f.ID_EstadoAnexo}"
            )


def _combos_ultimo_periodo(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_COMBOS_ULTIMO_PERIODO, "202601")
    filas = list(cursor.fetchall())
    print("\n=== Último período por anexo desde 202601: combos de flags ===")
    print("  (legacy ref=202608: FACTURADO 423, LIBERADO 154, DEMORADO 44, A LIBERAR 26, EN PROCESO 8)")
    for f in filas:
        print(
            f"  periodo={f.PeriodoFacturacion} facturado={f.Facturado} "
            f"listo={f.ListoParaFacturar} estado={f.Estado}: {f.cantidad}"
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
        _muestra_por_nombre(cursor)
        _combos_ultimo_periodo(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
