"""Ronda 11 (final): criterio candidato de "cliente vivo" = la empresa tuvo
alguna toma de contador O algún incidente en los últimos N meses (empresa-
level; una máquina puntual puede pasar meses sin actividad estando viva).
Se valida contra los corporativos sin tomas (¿SC JOHNSON tiene incidentes
recientes?), se parte el universo con N=3, se listan las empresas que caen,
y se cronometra la consulta candidata final por zona. Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda11.py
"""

import time

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 120

_ACTIVIDAD_JOIN = """
LEFT JOIN (
    SELECT M2.ID_Empresa, MAX(CT.FechaTomaContador) AS ultima_toma
    FROM dbo.Contadores CT
    INNER JOIN dbo.Maquina M2 ON M2.ID_Maquina = CT.ID_Maquina
    WHERE CT.Estado = 0
    GROUP BY M2.ID_Empresa
) TOMA ON TOMA.ID_Empresa = E.ID_Empresa
LEFT JOIN (
    SELECT I.ID_Empresa, MAX(I.Fecha_Ingreso) AS ultimo_incidente
    FROM dbo.Incidente I
    GROUP BY I.ID_Empresa
) INC ON INC.ID_Empresa = E.ID_Empresa
"""

_FILTRO_UNIVERSO = f"""
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
{_ACTIVIDAD_JOIN}
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0 AND E.ID_Tipo_Empresa IN (101, 102)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
"""

_SQL_PARTICION = f"""
SELECT CASE WHEN TOMA.ultima_toma >= DATEADD(month, -3, GETDATE())
              OR INC.ultimo_incidente >= DATEADD(month, -3, GETDATE())
            THEN 'viva' ELSE 'sin actividad 3m' END AS grupo,
       COUNT(*) AS maquinas, COUNT(DISTINCT E.ID_Empresa) AS empresas
{_FILTRO_UNIVERSO}
GROUP BY CASE WHEN TOMA.ultima_toma >= DATEADD(month, -3, GETDATE())
              OR INC.ultimo_incidente >= DATEADD(month, -3, GETDATE())
            THEN 'viva' ELSE 'sin actividad 3m' END
"""

_SQL_EXCLUIDAS = f"""
SELECT E.ID_Empresa, E.Den_Comercial, COUNT(*) AS maquinas,
       MAX(TOMA.ultima_toma) AS ultima_toma, MAX(INC.ultimo_incidente) AS ultimo_incidente
{_FILTRO_UNIVERSO}
  AND NOT (TOMA.ultima_toma >= DATEADD(month, -3, GETDATE())
           OR INC.ultimo_incidente >= DATEADD(month, -3, GETDATE()))
GROUP BY E.ID_Empresa, E.Den_Comercial
ORDER BY maquinas DESC
"""

# Consulta candidata final por zona (con el filtro de actividad) para medir.
_SQL_CANDIDATA_SUR = f"""
SELECT M.ID_Maquina
{_FILTRO_UNIVERSO}
  AND S.Cuadricula = 'SUR'
  AND (TOMA.ultima_toma >= DATEADD(month, -3, GETDATE())
       OR INC.ultimo_incidente >= DATEADD(month, -3, GETDATE()))
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
        _dump(cursor, "Partición viva / sin actividad 3m", _SQL_PARTICION)
        _dump(cursor, "Empresas excluidas (toma+incidente)", _SQL_EXCLUIDAS)
        for _ in range(3):
            inicio = time.perf_counter()
            cursor.execute(_SQL_CANDIDATA_SUR)
            filas = len(cursor.fetchall())
            print(f"candidata SUR: {filas} filas en {time.perf_counter() - inicio:.2f}s")
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
