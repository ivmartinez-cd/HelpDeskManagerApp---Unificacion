"""Ronda 8: la señal de baja de Garbarino es contractual — sus anexos están
todos en ID_EstadoAnexo=3 (Inactivo/Cancelado) y `Maquina.ID_Anexo` vincula
máquina→anexo. Se mide el universo local por estado de anexo (¿cuántas
máquinas 'Activa en Cliente' cuelgan de anexos muertos?), se valida que
Garbarino cae entero, y se muestrean las empresas que caerían con el filtro
para detectar falsos positivos. Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda8.py
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

_SQL_POR_ESTADO_ANEXO = f"""
SELECT COALESCE(CAST(A.ID_EstadoAnexo AS VARCHAR), 'sin anexo') AS estado_anexo,
       COUNT(*) AS maquinas, COUNT(DISTINCT E.ID_Empresa) AS empresas
{_FILTRO_BASE}
GROUP BY COALESCE(CAST(A.ID_EstadoAnexo AS VARCHAR), 'sin anexo')
ORDER BY maquinas DESC
"""

_SQL_GARBARINO = f"""
SELECT COALESCE(CAST(A.ID_EstadoAnexo AS VARCHAR), 'sin anexo') AS estado_anexo,
       COUNT(*) AS maquinas
{_FILTRO_BASE}
  AND E.ID_Empresa = 99
GROUP BY COALESCE(CAST(A.ID_EstadoAnexo AS VARCHAR), 'sin anexo')
"""

# Empresas cuyas máquinas caerían con "solo anexo activo": top por máquinas
# excluidas — para chequear a ojo que sean bajas reales y no falsos positivos.
_SQL_EXCLUIDAS = f"""
SELECT TOP 25 E.ID_Empresa, E.Den_Comercial,
       COALESCE(CAST(A.ID_EstadoAnexo AS VARCHAR), 'sin anexo') AS estado_anexo,
       COUNT(*) AS maquinas
{_FILTRO_BASE}
  AND (A.ID_EstadoAnexo IS NULL OR A.ID_EstadoAnexo <> 1)
GROUP BY E.ID_Empresa, E.Den_Comercial,
         COALESCE(CAST(A.ID_EstadoAnexo AS VARCHAR), 'sin anexo')
ORDER BY maquinas DESC
"""

# Y las que quedarían: sanity check de que los clientes vigentes conocidos
# (Hospital Italiano, Celulosa Campana de los casos de paridad) siguen.
_SQL_VIGENTES_MUESTRA = f"""
SELECT TOP 10 E.ID_Empresa, E.Den_Comercial, COUNT(*) AS maquinas
{_FILTRO_BASE}
  AND A.ID_EstadoAnexo = 1
GROUP BY E.ID_Empresa, E.Den_Comercial
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
        _dump(cursor, "Universo local por estado de anexo de la máquina", _SQL_POR_ESTADO_ANEXO)
        _dump(cursor, "Garbarino (ID 99) por estado de anexo", _SQL_GARBARINO)
        _dump(cursor, "Empresas que caerían con 'solo anexo activo' (top 25)", _SQL_EXCLUIDAS)
        _dump(cursor, "Top empresas que quedarían (anexo activo)", _SQL_VIGENTES_MUESTRA)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
