"""Ronda 7: Garbarino sigue apareciendo en preventivos pese a los filtros de
ronda 5/6 (empresa activa, tipo cliente, máquina 'Activa en Cliente'). Se busca
qué dato de SigesReadOnly lo marca como baja para generalizar el filtro:
`Empresa.FechaRestriccionServicio`, estado de sus anexos/contratos, situación
contractual o cobertura (Mantenimiento) de sus máquinas. Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda7.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

_SQL_EMPRESA = """
SELECT ID_Empresa, Den_Comercial, Estado, ID_Tipo_Empresa,
       FechaRestriccionServicio, sla, slaSeteado, Observ, Fecha_Mod
FROM dbo.Empresa
WHERE Den_Comercial LIKE '%Garbarino%' OR razon_social LIKE '%Garbarino%'
ORDER BY ID_Empresa
"""

# Máquinas de Garbarino que hoy pasan el filtro del módulo, por zona/estado.
_SQL_MAQUINAS = """
SELECT E.ID_Empresa, E.Den_Comercial, S.Cuadricula, EM.Descripcion AS estado_maquina,
       COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Estado_Maquina EM ON EM.Id = M.ID_Estado_Maquina
WHERE (E.Den_Comercial LIKE '%Garbarino%' OR E.razon_social LIKE '%Garbarino%')
  AND S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina = 1 AND E.Estado = 0
GROUP BY E.ID_Empresa, E.Den_Comercial, S.Cuadricula, EM.Descripcion
ORDER BY maquinas DESC
"""

# Contratos y anexos de Garbarino: ¿están cancelados/vencidos?
_SQL_ANEXOS = """
SELECT C.ID_Empresa, C.ID_Contrato, C.NombreContrato, C.Estado AS estado_contrato,
       A.ID_Anexo, A.NombreAnexo, A.ID_EstadoAnexo, A.FechaInicio, A.FechaFinalizacion,
       A.ID_Mantenimiento
FROM dbo.Contrato C
INNER JOIN dbo.Empresa E ON E.ID_Empresa = C.ID_Empresa
LEFT JOIN dbo.Anexo A ON A.ID_Contrato = C.ID_Contrato
WHERE E.Den_Comercial LIKE '%Garbarino%' OR E.razon_social LIKE '%Garbarino%'
ORDER BY C.ID_Contrato, A.ID_Anexo
"""

# ¿La máquina tiene vínculo directo a anexo/situación contractual?
_SQL_MAQ_COLUMNAS_ANEXO = """
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE (TABLE_NAME = 'Maquina' AND (COLUMN_NAME LIKE '%Anexo%' OR COLUMN_NAME LIKE '%Contra%'
       OR COLUMN_NAME LIKE '%Mantenim%' OR COLUMN_NAME LIKE '%Situacion%'))
   OR TABLE_NAME = 'MaquinaSituacionContractual'
ORDER BY TABLE_NAME, ORDINAL_POSITION
"""

_SQL_SITUACION_MUESTRA = "SELECT TOP 5 * FROM dbo.MaquinaSituacionContractual"

# ¿Cuántas empresas del universo local tienen FechaRestriccionServicio?
_SQL_RESTRICCION_UNIVERSO = """
SELECT CASE WHEN E.FechaRestriccionServicio IS NULL THEN 'sin restriccion'
            ELSE 'con restriccion' END AS grupo,
       COUNT(DISTINCT E.ID_Empresa) AS empresas, COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0 AND E.ID_Tipo_Empresa IN (101, 102)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
GROUP BY CASE WHEN E.FechaRestriccionServicio IS NULL THEN 'sin restriccion'
              ELSE 'con restriccion' END
"""

_SQL_RESTRINGIDAS = """
SELECT TOP 20 E.ID_Empresa, E.Den_Comercial, E.FechaRestriccionServicio,
       COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0 AND E.ID_Tipo_Empresa IN (101, 102)
  AND E.FechaRestriccionServicio IS NOT NULL
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
GROUP BY E.ID_Empresa, E.Den_Comercial, E.FechaRestriccionServicio
ORDER BY maquinas DESC
"""


def _dump(cursor: pyodbc.Cursor, titulo: str, sql: str) -> None:
    cursor.execute(sql)
    columnas = [d[0] for d in cursor.description]
    filas = list(cursor.fetchall())
    print(f"\n=== {titulo} ({len(filas)} filas) ===")
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
        _dump(cursor, "Empresa(s) Garbarino", _SQL_EMPRESA)
        _dump(cursor, "Máquinas de Garbarino que pasan el filtro actual", _SQL_MAQUINAS)
        _dump(cursor, "Contratos/anexos de Garbarino", _SQL_ANEXOS)
        _dump(cursor, "Columnas de vínculo máquina↔contrato", _SQL_MAQ_COLUMNAS_ANEXO)
        _dump(cursor, "MaquinaSituacionContractual TOP 5", _SQL_SITUACION_MUESTRA)
        _dump(cursor, "Universo local por FechaRestriccionServicio", _SQL_RESTRICCION_UNIVERSO)
        _dump(cursor, "Empresas restringidas en el universo (top 20)", _SQL_RESTRINGIDAS)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
