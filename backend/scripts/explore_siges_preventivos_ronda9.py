"""Ronda 9: Garbarino pasa el filtro porque su anexo está 'Activo' (estado 1)
pero con FechaFinalizacion 2023-05-22 ya vencida — baja de facto no registrada
en Gestión. Se mide si "anexo activo pero vencido por fecha" separa bajas
reales de clientes vigentes (¿o hay clientes vivos con anexo vencido en
tácita reconducción?), y qué pinta tiene el estado 100 'No Facturable' por
fecha. Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda9.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 120

_FILTRO_BASE = """
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
LEFT JOIN dbo.Anexo A ON A.ID_Anexo = M.ID_Anexo
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina = 1
  AND E.Estado = 0 AND E.ID_Tipo_Empresa IN (101, 102)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
"""

_SQL_ESTADO1_POR_VIGENCIA = f"""
SELECT CASE WHEN A.FechaFinalizacion >= GETDATE() THEN 'vigente'
            ELSE 'vencido' END AS vigencia,
       COUNT(*) AS maquinas, COUNT(DISTINCT E.ID_Empresa) AS empresas
{_FILTRO_BASE}
  AND A.ID_EstadoAnexo = 1
GROUP BY CASE WHEN A.FechaFinalizacion >= GETDATE() THEN 'vigente' ELSE 'vencido' END
"""

# Empresas con anexo ACTIVO pero VENCIDO por fecha: ¿son bajas de facto
# (Garbarino) o clientes vivos renegociando?
_SQL_ESTADO1_VENCIDAS = f"""
SELECT TOP 30 E.ID_Empresa, E.Den_Comercial, MAX(A.FechaFinalizacion) AS fin_max,
       COUNT(*) AS maquinas
{_FILTRO_BASE}
  AND A.ID_EstadoAnexo = 1 AND A.FechaFinalizacion < GETDATE()
GROUP BY E.ID_Empresa, E.Den_Comercial
ORDER BY maquinas DESC
"""

# ¿Esas empresas "vencidas" tienen OTRO anexo activo vigente por fecha
# (renovación en curso — empresa viva, máquina colgada de un anexo viejo)?
_SQL_ESTADO1_VENCIDAS_FLAG = f"""
SELECT TOP 30 E.ID_Empresa, E.Den_Comercial, MAX(A.FechaFinalizacion) AS fin_max,
       COUNT(*) AS maquinas,
       (SELECT COUNT(*) FROM dbo.Anexo A3
        INNER JOIN dbo.Contrato C3 ON C3.ID_Contrato = A3.ID_Contrato
        WHERE C3.ID_Empresa = E.ID_Empresa AND A3.ID_EstadoAnexo = 1
          AND A3.FechaFinalizacion >= GETDATE()) AS anexos_vigentes_empresa
{_FILTRO_BASE}
  AND A.ID_EstadoAnexo = 1 AND A.FechaFinalizacion < GETDATE()
GROUP BY E.ID_Empresa, E.Den_Comercial
ORDER BY maquinas DESC
"""

_SQL_ESTADO100_POR_VIGENCIA = f"""
SELECT CASE WHEN A.FechaFinalizacion >= GETDATE() THEN 'vigente'
            ELSE 'vencido' END AS vigencia,
       COUNT(*) AS maquinas, COUNT(DISTINCT E.ID_Empresa) AS empresas
{_FILTRO_BASE}
  AND A.ID_EstadoAnexo = 100
GROUP BY CASE WHEN A.FechaFinalizacion >= GETDATE() THEN 'vigente' ELSE 'vencido' END
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
        _dump(cursor, "Anexo estado 1 por vigencia de fecha", _SQL_ESTADO1_POR_VIGENCIA)
        _dump(cursor, "Empresas con anexo activo VENCIDO (top 30)", _SQL_ESTADO1_VENCIDAS)
        _dump(
            cursor,
            "Ídem con flag de otro anexo vigente en la empresa",
            _SQL_ESTADO1_VENCIDAS_FLAG,
        )
        _dump(cursor, "Estado 100 (No Facturable) por vigencia", _SQL_ESTADO100_POR_VIGENCIA)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
