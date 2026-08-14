"""Ronda 10: ni Empresa.Estado, ni estado/fecha del anexo, ni
FechaRestriccionServicio distinguen la baja de facto de Garbarino (rondas
7-9). Última señal candidata: ACTIVIDAD — el precedente del módulo contadores
es "sigue facturando" = alguna toma de contador en el último mes (ver
equipos_sin_real_query.py). Se contrasta Garbarino vs clientes vivos con
anexo también vencido (Hospital Italiano, Aerolíneas, Natura) por última toma
y último incidente, y se mide cómo partiría el universo. Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda10.py
"""

import time

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 120

# Garbarino (baja de facto) vs vivos con anexo vencido por fecha.
_EMPRESAS = "(99, 1065, 715, 945, 817, 974, 450)"

_SQL_ACTIVIDAD_POR_EMPRESA = f"""
SELECT E.ID_Empresa, E.Den_Comercial,
       (SELECT MAX(CT.FechaTomaContador)
        FROM dbo.Contadores CT
        INNER JOIN dbo.Maquina M ON M.ID_Maquina = CT.ID_Maquina
        WHERE M.ID_Empresa = E.ID_Empresa AND CT.Estado = 0) AS ultima_toma,
       (SELECT MAX(I.Fecha_Ingreso)
        FROM dbo.Incidente I
        WHERE I.ID_Empresa = E.ID_Empresa) AS ultimo_incidente
FROM dbo.Empresa E
WHERE E.ID_Empresa IN {_EMPRESAS}
"""

_FILTRO_UNIVERSO = """
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0 AND E.ID_Tipo_Empresa IN (101, 102)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
"""

# Partición del universo por última toma de la MÁQUINA (ventanas de 1/3/6 m).
_SQL_UNIVERSO_POR_TOMA = f"""
SELECT CASE
         WHEN UT.ultima_toma >= DATEADD(month, -1, GETDATE()) THEN '1: ultimo mes'
         WHEN UT.ultima_toma >= DATEADD(month, -3, GETDATE()) THEN '2: 1-3 meses'
         WHEN UT.ultima_toma >= DATEADD(month, -6, GETDATE()) THEN '3: 3-6 meses'
         WHEN UT.ultima_toma IS NOT NULL THEN '4: mas de 6 meses'
         ELSE '5: sin tomas'
       END AS ventana,
       COUNT(*) AS maquinas, COUNT(DISTINCT E.ID_Empresa) AS empresas
{_FILTRO_UNIVERSO.replace("WHERE", '''LEFT JOIN (
    SELECT CT.ID_Maquina, MAX(CT.FechaTomaContador) AS ultima_toma
    FROM dbo.Contadores CT WHERE CT.Estado = 0 GROUP BY CT.ID_Maquina
) UT ON UT.ID_Maquina = M.ID_Maquina
WHERE''')}
GROUP BY CASE
         WHEN UT.ultima_toma >= DATEADD(month, -1, GETDATE()) THEN '1: ultimo mes'
         WHEN UT.ultima_toma >= DATEADD(month, -3, GETDATE()) THEN '2: 1-3 meses'
         WHEN UT.ultima_toma >= DATEADD(month, -6, GETDATE()) THEN '3: 3-6 meses'
         WHEN UT.ultima_toma IS NOT NULL THEN '4: mas de 6 meses'
         ELSE '5: sin tomas'
       END
ORDER BY 1
"""

# Empresas que caerían con "sin toma en 3 meses en NINGUNA de sus máquinas
# del universo" (muestra) — bajas de facto esperadas.
_SQL_EMPRESAS_SIN_TOMA_3M = f"""
SELECT TOP 25 E.ID_Empresa, E.Den_Comercial, COUNT(*) AS maquinas,
       MAX(UT.ultima_toma) AS ultima_toma_empresa
{_FILTRO_UNIVERSO.replace("WHERE", '''LEFT JOIN (
    SELECT CT.ID_Maquina, MAX(CT.FechaTomaContador) AS ultima_toma
    FROM dbo.Contadores CT WHERE CT.Estado = 0 GROUP BY CT.ID_Maquina
) UT ON UT.ID_Maquina = M.ID_Maquina
WHERE''')}
GROUP BY E.ID_Empresa, E.Den_Comercial
HAVING MAX(UT.ultima_toma) < DATEADD(month, -3, GETDATE())
    OR MAX(UT.ultima_toma) IS NULL
ORDER BY maquinas DESC
"""


def _dump(cursor: pyodbc.Cursor, titulo: str, sql: str) -> None:
    inicio = time.perf_counter()
    cursor.execute(sql)
    columnas = [d[0] for d in cursor.description]
    filas = list(cursor.fetchall())
    print(f"\n=== {titulo} ({len(filas)} filas, {time.perf_counter() - inicio:.1f}s) ===")
    print(f"  columnas: {columnas}")
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
        _dump(cursor, "Actividad por empresa (Garbarino vs vivos)", _SQL_ACTIVIDAD_POR_EMPRESA)
        _dump(cursor, "Universo por ventana de última toma", _SQL_UNIVERSO_POR_TOMA)
        _dump(cursor, "Empresas sin toma en 3+ meses (top 25)", _SQL_EMPRESAS_SIN_TOMA_3M)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
