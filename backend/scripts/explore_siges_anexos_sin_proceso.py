"""Explora SiGesReadOnly para validar los supuestos del KPI "Anexos sin
procesar" (ver /home/ivan/.claude/plans/lovely-wandering-lightning.md, Paso 0)
antes de escribir la query productiva. Solo SELECTs, misma cuenta de solo
lectura y mismo patrón que explore_siges_anexos_no_facturados.py (conexión
efímera, autocommit=True, close() explícito en finally).

Preguntas a responder:
1. R1 (bloqueante): ¿el período YYYYMM se nombra por el mes en que ARRANCA
   el ciclo (20/mes-1 a 20/mes) o por el mes en que CIERRA? Se resuelve con
   la historia de un cliente real citado por el usuario (United Logistic,
   proceso 99003) y con la distancia entre Fecha_Proceso y los bordes del
   período declarado.
2. R2: ¿existen filas de Factura_Anexo con Nro_Proceso IS NULL, o "sin
   procesar" es siempre ausencia total de fila?
3. Sanity de volumen: anexos activos de Impresión agrupados por último
   período que llegó a tener Nro_Proceso — se esperan decenas en el bucket
   viejo, no miles.
4. R3/R4: columnas de dbo.Anexo relacionadas a fecha de alta / frecuencia de
   facturación, para descartar falsos positivos por anexos nuevos o no
   mensuales.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_anexos_sin_proceso.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30

_SQL_UNITED_LOGISTIC = """
SELECT TOP 20 G.descripcion AS grupo, A.ID_Anexo, A.NombreAnexo,
       FA.Nro_Proceso, FA.PeriodoFacturacion, FA.Fecha_Proceso,
       FA.Facturado, FA.ListoParaFacturar, FA.Estado
FROM dbo.Anexo A
INNER JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
LEFT JOIN dbo.Factura_Anexo FA ON FA.ID_Anexo = A.ID_Anexo
WHERE G.descripcion LIKE '%United Logistic%'
ORDER BY A.ID_Anexo, FA.PeriodoFacturacion DESC, FA.Nro_Proceso DESC
"""

_SQL_PROCESO_99003 = """
SELECT G.descripcion AS grupo, A.NombreAnexo, FA.Nro_Proceso,
       FA.PeriodoFacturacion, FA.Fecha_Proceso, FA.Facturado, FA.ListoParaFacturar
FROM dbo.Factura_Anexo FA
INNER JOIN dbo.Anexo A ON A.ID_Anexo = FA.ID_Anexo
INNER JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
WHERE FA.Nro_Proceso = 99003
"""

_SQL_NRO_PROCESO_NULL = """
SELECT COUNT(*) AS total,
       SUM(CASE WHEN Nro_Proceso IS NULL THEN 1 ELSE 0 END) AS sin_nro_proceso
FROM dbo.Factura_Anexo
"""

_SQL_DISTANCIA_FECHA_PROCESO = """
SELECT TOP 30 FA.PeriodoFacturacion, FA.Fecha_Proceso, FA.Nro_Proceso,
       DATEDIFF(day,
         CAST(LEFT(FA.PeriodoFacturacion, 4) + '-'
           + SUBSTRING(FA.PeriodoFacturacion, 5, 2) + '-20' AS date),
         FA.Fecha_Proceso) AS dias_desde_dia20_del_periodo
FROM dbo.Factura_Anexo FA
WHERE FA.Fecha_Proceso IS NOT NULL AND FA.Nro_Proceso IS NOT NULL
ORDER BY FA.Fecha_Proceso DESC
"""

_SQL_VOLUMEN_ULTIMO_PERIODO = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, MAX(FA.PeriodoFacturacion) AS ultimo_periodo
  FROM dbo.Factura_Anexo FA
  WHERE FA.Nro_Proceso IS NOT NULL
  GROUP BY FA.ID_Anexo
)
SELECT ISNULL(u.ultimo_periodo, 'SIN_HISTORIAL') AS ultimo_periodo, COUNT(*) AS cantidad
FROM dbo.Anexo A
LEFT JOIN ultimo u ON u.ID_Anexo = A.ID_Anexo
WHERE A.ID_EstadoAnexo = 1 AND A.discriminador = 'I'
GROUP BY u.ultimo_periodo
ORDER BY ultimo_periodo DESC
"""

_SQL_COLUMNAS_ANEXO = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Anexo'
ORDER BY ORDINAL_POSITION
"""

_SQL_TABLA_FRECUENCIA = """
SELECT * FROM dbo.Frecuencia
"""

_SQL_ANEXO_TIENE_FRECUENCIA = """
SELECT TOP 1 COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Anexo' AND COLUMN_NAME LIKE '%Frecuencia%'
"""


def _united_logistic(cursor: pyodbc.Cursor) -> None:
    print("\n=== Anexos de 'United Logistic' (historia completa por anexo) ===")
    cursor.execute(_SQL_UNITED_LOGISTIC)
    for f in cursor.fetchall():
        print(
            f"  grupo={f.grupo!r} anexo={f.NombreAnexo!r} id_anexo={f.ID_Anexo} "
            f"periodo={f.PeriodoFacturacion} proceso={f.Nro_Proceso} "
            f"fecha_proceso={f.Fecha_Proceso} facturado={f.Facturado} "
            f"listo={f.ListoParaFacturar} estado={f.Estado}"
        )

    print("\n=== Proceso Nro_Proceso=99003 (el que citó el usuario) ===")
    cursor.execute(_SQL_PROCESO_99003)
    filas = list(cursor.fetchall())
    if not filas:
        print("  (sin filas — el proceso 99003 no existe con ese ID exacto)")
    for f in filas:
        print(
            f"  grupo={f.grupo!r} anexo={f.NombreAnexo!r} periodo={f.PeriodoFacturacion} "
            f"fecha_proceso={f.Fecha_Proceso} facturado={f.Facturado} listo={f.ListoParaFacturar}"
        )


def _nro_proceso_null(cursor: pyodbc.Cursor) -> None:
    print("\n=== R2: Nro_Proceso IS NULL en Factura_Anexo ===")
    cursor.execute(_SQL_NRO_PROCESO_NULL)
    f = cursor.fetchone()
    print(f"  total_filas={f.total} sin_nro_proceso={f.sin_nro_proceso}")


def _distancia_fecha_proceso(cursor: pyodbc.Cursor) -> None:
    print("\n=== R1: días entre el día 20 DEL MES DEL PERÍODO declarado y Fecha_Proceso ===")
    print("  (si el período se nombra por el mes en que ARRANCA, Fecha_Proceso debería")
    print("   caer DESPUÉS del día 20 del mes de PeriodoFacturacion, típicamente +0 a +20 días;")
    print("   si se nombra por el mes en que CIERRA, debería caer ANTES, típicamente negativo)")
    cursor.execute(_SQL_DISTANCIA_FECHA_PROCESO)
    for f in cursor.fetchall():
        print(
            f"  periodo={f.PeriodoFacturacion} fecha_proceso={f.Fecha_Proceso} "
            f"proceso={f.Nro_Proceso} dias_desde_dia20={f.dias_desde_dia20_del_periodo}"
        )


def _volumen(cursor: pyodbc.Cursor) -> None:
    print("\n=== Sanity de volumen: anexos activos 'I' por último período CON proceso ===")
    cursor.execute(_SQL_VOLUMEN_ULTIMO_PERIODO)
    for f in cursor.fetchall():
        print(f"  ultimo_periodo={f.ultimo_periodo} cantidad={f.cantidad}")


def _columnas_anexo(cursor: pyodbc.Cursor) -> None:
    print("\n=== R3/R4: columnas de dbo.Anexo (buscando fecha de alta / frecuencia) ===")
    cursor.execute(_SQL_COLUMNAS_ANEXO)
    for f in cursor.fetchall():
        print(f"  {f.COLUMN_NAME} ({f.DATA_TYPE})")

    print("\n=== ¿dbo.Anexo tiene alguna columna 'Frecuencia*'? ===")
    cursor.execute(_SQL_ANEXO_TIENE_FRECUENCIA)
    fila = cursor.fetchone()
    print(f"  {'SI: ' + fila.COLUMN_NAME if fila else 'NO — ninguna columna coincide'}")

    print("\n=== Contenido de dbo.Frecuencia (por si algo más la referencia) ===")
    try:
        cursor.execute(_SQL_TABLA_FRECUENCIA)
        for f in cursor.fetchall():
            print(f"  {tuple(f)}")
    except pyodbc.Error as exc:
        print(f"  (no se pudo leer: {exc})")


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _united_logistic(cursor)
        _nro_proceso_null(cursor)
        _distancia_fecha_proceso(cursor)
        _volumen(cursor)
        _columnas_anexo(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
