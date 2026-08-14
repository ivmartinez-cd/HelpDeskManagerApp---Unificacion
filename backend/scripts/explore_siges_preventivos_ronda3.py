"""Ronda 3 de exploración para "preventivos por zona". Hallazgos previos:
zona = `Sucursal.Cuadricula` (texto libre, sin catálogo); frecuencia =
`Sucursal.TipoPreventivo` → `TipoPreventivo.Dias`; preventivo = Tipo_Incidente
102; estados "hecho" candidatos: 500/600/700/710 (excluye 900 Anulado).

Esta ronda:
  1. ¿`Empresa.ID_DomicilioFactur` apunta a `Sucursal`? (explicaría "la zona por
     empresa" que se ve en Gestión sin columna propia).
  2. Semántica de fechas en Incidente 102 cerrado: ¿Fecha_Cierre es real o
     sentinel? Muestra de filas recientes.
  3. Casos de paridad: 3 máquinas activas de la zona SUR con su último
     preventivo (NroIncidente incluido para contrastar en Gestión).
  4. MEDICIÓN: 3 corridas de la consulta candidata completa por zona
     (parque activo + último preventivo + frecuencia).

Solo SELECTs. Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda3.py
"""

import time

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 120

_SQL_DOMICILIO_ES_SUCURSAL = """
SELECT COUNT(*) AS empresas_activas,
       SUM(CASE WHEN S.Id_Sucursal IS NOT NULL THEN 1 ELSE 0 END) AS con_sucursal_match,
       SUM(CASE WHEN S.Id_Sucursal IS NOT NULL AND S.Id_Empresa = E.ID_Empresa
                THEN 1 ELSE 0 END) AS match_misma_empresa
FROM dbo.Empresa E
LEFT JOIN dbo.Sucursal S ON S.Id_Sucursal = E.ID_DomicilioFactur
WHERE E.Estado = 0
"""

_SQL_MUESTRA_DOMICILIO = """
SELECT TOP 5 E.ID_Empresa, E.Den_Comercial, E.ID_DomicilioFactur,
       S.descripcion AS sucursal_factur, S.Cuadricula AS zona_factur
FROM dbo.Empresa E
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = E.ID_DomicilioFactur
WHERE E.Estado = 0
ORDER BY E.ID_Empresa
"""

_SQL_FECHAS_102 = """
SELECT TOP 10 I.ID_Incidente, I.NroIncidente, I.Fecha_Ingreso, I.Fecha_Cierre,
       I.ID_Estado_Incidente, I.ID_Maquina
FROM dbo.Incidente I
WHERE I.ID_Tipo_Incidente = 102 AND I.ID_Estado_Incidente = 600
ORDER BY I.ID_Incidente DESC
"""

_SQL_CASOS_PARIDAD = """
SELECT TOP 3
    M.ID_Maquina, M.Nro_Serie, AG.Descripcion AS modelo,
    E.Den_Comercial AS cliente, S.descripcion AS sucursal, S.Cuadricula AS zona,
    S.TipoPreventivo AS tipo_prev, TP.Dias AS frecuencia_dias,
    UP.fecha_ultimo_preventivo, UP.nro_incidente
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Articulo A ON A.Id_Articulo = M.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
LEFT JOIN dbo.TipoPreventivo TP ON TP.Tipo = S.TipoPreventivo
OUTER APPLY (
    SELECT TOP 1 I.Fecha_Cierre AS fecha_ultimo_preventivo, I.NroIncidente AS nro_incidente
    FROM dbo.Incidente I
    WHERE I.ID_Maquina = M.ID_Maquina AND I.ID_Tipo_Incidente = 102
      AND I.ID_Estado_Incidente IN (500, 600, 700, 710)
    ORDER BY I.Fecha_Cierre DESC
) UP
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula = ?
  AND UP.fecha_ultimo_preventivo IS NOT NULL
ORDER BY UP.fecha_ultimo_preventivo DESC
"""

# Consulta candidata completa para la pantalla: parque activo de UNA zona con
# frecuencia y último preventivo (agregado por máquina, sin TOP).
_SQL_CANDIDATA_ZONA = """
SELECT
    M.ID_Maquina, M.Nro_Serie, AG.Descripcion AS modelo,
    E.Den_Comercial AS cliente, S.descripcion AS sucursal, S.Cuadricula AS zona,
    TP.Dias AS frecuencia_dias,
    UP.fecha_ultimo_preventivo
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Articulo A ON A.Id_Articulo = M.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
LEFT JOIN dbo.TipoPreventivo TP ON TP.Tipo = S.TipoPreventivo
LEFT JOIN (
    SELECT I.ID_Maquina, MAX(I.Fecha_Cierre) AS fecha_ultimo_preventivo
    FROM dbo.Incidente I
    WHERE I.ID_Tipo_Incidente = 102
      AND I.ID_Estado_Incidente IN (500, 600, 700, 710)
    GROUP BY I.ID_Maquina
) UP ON UP.ID_Maquina = M.ID_Maquina
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula = ?
"""

_ZONAS_MEDICION = ["SUR", "CABA-N", "NORTE2"]


def _dump(cursor: pyodbc.Cursor, titulo: str, sql: str, *params: object) -> None:
    cursor.execute(sql, *params) if params else cursor.execute(sql)
    columnas = [d[0] for d in cursor.description]
    filas = list(cursor.fetchall())
    print(f"\n=== {titulo} ({len(filas)} filas) ===")
    print(f"  columnas: {columnas}")
    for f in filas:
        print(f"  {tuple(f)}")


def _medir(cursor: pyodbc.Cursor) -> None:
    print("\n=== Medición consulta candidata por zona (3 corridas c/u) ===")
    for zona in _ZONAS_MEDICION:
        tiempos = []
        filas_totales = 0
        for _ in range(3):
            inicio = time.perf_counter()
            cursor.execute(_SQL_CANDIDATA_ZONA, zona)
            filas_totales = len(cursor.fetchall())
            tiempos.append(time.perf_counter() - inicio)
        tiempos_txt = ", ".join(f"{t:.2f}s" for t in tiempos)
        print(f"  zona {zona!r}: {filas_totales} filas — corridas: {tiempos_txt}")


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _dump(cursor, "Empresa.ID_DomicilioFactur vs Sucursal", _SQL_DOMICILIO_ES_SUCURSAL)
        _dump(cursor, "Muestra domicilio facturación → zona", _SQL_MUESTRA_DOMICILIO)
        _dump(cursor, "Incidentes 102 Cerrados recientes: fechas", _SQL_FECHAS_102)
        _dump(cursor, "Casos de paridad zona SUR", _SQL_CASOS_PARIDAD, "SUR")
        _medir(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
