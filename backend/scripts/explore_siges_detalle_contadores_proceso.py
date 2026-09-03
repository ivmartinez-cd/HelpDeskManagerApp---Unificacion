"""Explora SiGesReadOnly para encontrar el origen de datos del reporte legacy
SSRS "Impresión/Detalle de contadores por nro de proceso" (parámetro
NroProceso, ej. 99070 — captura real compartida por el usuario 2026-09-01),
de cara a automatizar "Estimación en 0" (hoy CSV manual subido a mano).

Solo SELECTs de solo lectura contra SiGesReadOnly, mismo patrón que
explore_siges_contadores_reales.py. No escribe nada.

Ronda 1 (2026-09-01) — CONFIRMADO contra Nro_Proceso=99070 real:
- El reporte sale de `dbo.Factura_Contador` (una fila por máquina+clase de
  contador dentro de un `Nro_Proceso`), no de `dbo.Contadores` directamente.
  Columnas verificadas 1:1 contra la captura del reporte: `Serie` viene de
  `dbo.Maquina.Nro_Serie` (join por `ID_Maquina`, confirmado exacto para
  ID_Maquina=20310 → Nro_Serie=07QWB9UG3A004KV); `Contador Ant.` es
  literalmente `Factura_Contador.ImpreContadorAnterior` — coincide con el
  alias que YA usa `CsvFaltaContadorReader._CONTADOR_ALIASES`, no es
  casualidad: el CSV legacy es un export directo de esta columna. `Clase`
  es `ID_ClaseContador` (10=Mono, 20=Color, misma convención que
  `EQUIPOS_SIN_REAL_SQL`).
- Hipótesis fuerte para "Tipo = FALTA CONTADOR" (no confirmada contra el
  RDL, sí contra 41 filas reales): `Factura_Contador.ID_ContadorActual =
  Factura_Contador.ID_ContadorAnterior` — es decir, no se registró ninguna
  toma nueva en `dbo.Contadores` para esa máquina/clase en este período, y
  el FK "actual" simplemente reapunta a la última toma conocida. Distinto
  de "ImpresionesReales=0" a secas: hay casos (ID_Maquina=37866) con toma
  real nueva pero delta 0, que el reporte marcaría "Automatico", no "Falta
  Contador" — usar el ID compartido, no el importe.
- `dbo.Contadores.ID_TipoToma=14` = "Estimado" (catálogo `dbo.Tipo_Toma`) es
  literalmente el resultado de una corrida previa de Estimación en 0 —
  coincide con `_TIPO_SALIDA = "14"` en `estimation_zero_builder.py`. Ojo:
  esto implica que el output de esta herramienta se reimporta a Siges por
  algún proceso fuera de este repo (no identificado todavía) — la
  automatización que se está evaluando solo cubriría la mitad "lectura" del
  flujo, no el reimport.
- Pendiente, no resuelto en esta ronda: cómo mapear "cliente" → Nro_Proceso
  activo. `Factura_Contador.ID_Empresa` es la empresa/sucursal del parque,
  pero el criterio de "proceso pendiente" que ya usa este módulo
  (`anexos_pendientes_query.py`: última fila de `Factura_Anexo` por
  `ID_Anexo` con `Facturado=0 AND ListoParaFacturar=0`) cuelga del lado de
  `Anexo`/`Contrato` (`Contrato.ID_EmpresaAdmin`), no necesariamente de la
  empresa "cliente" tal como la ve el usuario en el picker. Falta
  confirmar con el usuario cuál de las dos entidades es la que se elige.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_detalle_contadores_proceso.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 120
_NRO_PROCESO_MUESTRA = 99070

_SQL_COLUMNAS_PROCESO = """
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%Proceso%'
ORDER BY TABLE_NAME, COLUMN_NAME
"""

_SQL_COLUMNAS_CONTADORES = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Contadores'
ORDER BY ORDINAL_POSITION
"""

_SQL_TIPOTOMA_CATALOGO = """
SELECT * FROM dbo.TipoToma
"""

_SQL_COLUMNAS_FACTURA_CONTADOR = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Factura_Contador'
ORDER BY ORDINAL_POSITION
"""

_SQL_TABLAS_TOMA_MOTIVO = """
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE '%Toma%' OR TABLE_NAME LIKE '%Motivo%' OR TABLE_NAME LIKE '%Estimad%'
ORDER BY TABLE_NAME
"""

_SQL_FACTURA_CONTADOR_MUESTRA = """
SELECT TOP 10 *
FROM dbo.Factura_Contador
WHERE Nro_Proceso = ?
"""

_SQL_MAQUINA_SERIE = """
SELECT ID_Maquina, Nro_Serie FROM dbo.Maquina
WHERE ID_Maquina IN (18661, 18667, 18681, 18965, 19667, 20277, 20310, 20340, 21062, 26399)
"""

_SQL_TIPO_TOMA_CATALOGO = "SELECT * FROM dbo.Tipo_Toma"
_SQL_MOTIVO_CONTADOR_ESTIMADO = "SELECT * FROM dbo.Motivo_ContadorEstimado"

_SQL_CONTADORES_ACTUAL_VS_ANTERIOR = """
SELECT FC.ID_Maquina, FC.ID_ClaseContador, FC.ImpresionesReales,
       FC.ID_ContadorActual, FC.ID_ContadorAnterior,
       CA.ID_TipoToma AS tipo_toma_actual, CA.ID_MotivoEstimado AS motivo_actual,
       CAnt.ID_TipoToma AS tipo_toma_anterior
FROM dbo.Factura_Contador FC
INNER JOIN dbo.Contadores CA ON CA.ID_Contador = FC.ID_ContadorActual
INNER JOIN dbo.Contadores CAnt ON CAnt.ID_Contador = FC.ID_ContadorAnterior
WHERE FC.Nro_Proceso = ?
"""


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()

        print("=== Columnas con 'Proceso' en el nombre (todas las tablas) ===")
        cursor.execute(_SQL_COLUMNAS_PROCESO)
        for f in cursor.fetchall():
            print(f"  {f.TABLE_NAME}.{f.COLUMN_NAME} ({f.DATA_TYPE})")

        print("\n=== Columnas de dbo.Contadores ===")
        cursor.execute(_SQL_COLUMNAS_CONTADORES)
        for f in cursor.fetchall():
            print(f"  {f.COLUMN_NAME} ({f.DATA_TYPE})")

        print("\n=== Catálogo dbo.TipoToma (si existe) ===")
        try:
            cursor.execute(_SQL_TIPOTOMA_CATALOGO)
            for f in cursor.fetchall():
                print(f"  {f}")
        except pyodbc.Error as exc:
            print(f"  (no existe o falló: {exc})")

        print("\n=== Columnas de dbo.Factura_Contador ===")
        cursor.execute(_SQL_COLUMNAS_FACTURA_CONTADOR)
        for f in cursor.fetchall():
            print(f"  {f.COLUMN_NAME} ({f.DATA_TYPE})")

        print("\n=== Tablas candidatas a catálogo (Toma/Motivo/Estimad) ===")
        cursor.execute(_SQL_TABLAS_TOMA_MOTIVO)
        for f in cursor.fetchall():
            print(f"  {f.TABLE_NAME}")

        print(f"\n=== Muestra dbo.Factura_Contador WHERE Nro_Proceso={_NRO_PROCESO_MUESTRA} ===")
        cursor.execute(_SQL_FACTURA_CONTADOR_MUESTRA, _NRO_PROCESO_MUESTRA)
        cols = [c[0] for c in cursor.description]
        for f in cursor.fetchall():
            print("  " + ", ".join(f"{c}={getattr(f, c)!r}" for c in cols))

        print("\n=== dbo.Maquina.Nro_Serie de la muestra ===")
        cursor.execute(_SQL_MAQUINA_SERIE)
        for f in cursor.fetchall():
            print(f"  ID_Maquina={f.ID_Maquina} Nro_Serie={f.Nro_Serie}")

        print("\n=== dbo.Tipo_Toma ===")
        try:
            cursor.execute(_SQL_TIPO_TOMA_CATALOGO)
            for f in cursor.fetchall():
                print(f"  {f}")
        except pyodbc.Error as exc:
            print(f"  (falló: {exc})")

        print("\n=== dbo.Motivo_ContadorEstimado ===")
        try:
            cursor.execute(_SQL_MOTIVO_CONTADOR_ESTIMADO)
            for f in cursor.fetchall():
                print(f"  {f}")
        except pyodbc.Error as exc:
            print(f"  (falló: {exc})")

        print(f"\n=== TipoToma actual/anterior por fila (Nro_Proceso={_NRO_PROCESO_MUESTRA}) ===")
        cursor.execute(_SQL_CONTADORES_ACTUAL_VS_ANTERIOR, _NRO_PROCESO_MUESTRA)
        for f in cursor.fetchall():
            print(
                f"  ID_Maquina={f.ID_Maquina} clase={f.ID_ClaseContador} "
                f"impresiones_reales={f.ImpresionesReales} "
                f"actual==anterior_id={f.ID_ContadorActual == f.ID_ContadorAnterior} "
                f"tipo_toma_actual={f.tipo_toma_actual} motivo_actual={f.motivo_actual} "
                f"tipo_toma_anterior={f.tipo_toma_anterior}"
            )
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
