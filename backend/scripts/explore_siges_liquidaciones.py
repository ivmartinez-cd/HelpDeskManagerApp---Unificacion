"""Fase 1 (ronda 2) de MASTER_PROMPT_AUTOMATIZACION_FUENTES_LIQUIDACIONES.md.

Ronda 1 confirmó: CostoServicio = tarifario por PST (wide, por tipo de servicio),
Empresa contiene PST y SPST (prefijo en Den_Comercial), Sucursal.ID_Prestador vincula
sucursal de cliente con su PST, IncidenteCosto tiene CantidadKm/CostoKm. Esta ronda
verifica vigencias contra el tarifario local, cobertura por PST y el sentido de las FKs.

Solo lectura, SQL parametrizado, conexión efímera. Uso (contenedor backend):
    uv run python scripts/explore_siges_liquidaciones.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 20
_PENTACOM_ID = 137  # dbo.Empresa 'PST Cordoba - Pentacom S.A.' (ronda 1)

_SQL_TARIFAS_PENTACOM = """
SELECT TOP 6 id, correctivo, preventivo, instalacion, PreCorrectivo, CostoKm,
       fecha_vigencia, prestador_id, habilitado
FROM dbo.CostoServicio WHERE ID_Empresa = ? ORDER BY fecha_vigencia DESC
"""

_SQL_COBERTURA_COSTOS = """
SELECT TOP 40 ID_Empresa, Nombre_Empresa, COUNT(*) AS filas,
       MAX(fecha_vigencia) AS ultima_vigencia
FROM dbo.CostoServicio
GROUP BY ID_Empresa, Nombre_Empresa
ORDER BY MAX(fecha_vigencia) DESC
"""

_SQL_COSTOS_TOTAL = "SELECT COUNT(*) AS total FROM dbo.CostoServicio"

_SQL_INCIDENTE_COSTO_COLS = """
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'IncidenteCosto' ORDER BY ORDINAL_POSITION
"""

_SQL_INCIDENTE_COSTO_MUESTRA = "SELECT TOP 2 * FROM dbo.IncidenteCosto ORDER BY ID_Incidente DESC"

_SQL_EMPRESA_PST_INVENTARIO = """
SELECT
    CASE WHEN Den_Comercial LIKE 'PST %' THEN 'PST'
         WHEN Den_Comercial LIKE 'SPST%' THEN 'SPST'
         ELSE 'otro_match' END AS tipo,
    Estado, COUNT(*) AS cantidad
FROM dbo.Empresa
WHERE Den_Comercial LIKE 'PST %' OR Den_Comercial LIKE 'SPST%'
GROUP BY CASE WHEN Den_Comercial LIKE 'PST %' THEN 'PST'
              WHEN Den_Comercial LIKE 'SPST%' THEN 'SPST'
              ELSE 'otro_match' END, Estado
ORDER BY tipo, Estado
"""

_SQL_PST_ACTIVOS = """
SELECT ID_Empresa, Den_Comercial, ID_Tipo_Empresa
FROM dbo.Empresa
WHERE Den_Comercial LIKE 'PST %' AND Estado = 1
ORDER BY Den_Comercial
"""

_SQL_SUCURSALES_DE_PST = """
SELECT COUNT(*) AS pares FROM dbo.Sucursal WHERE ID_Prestador = ? AND Estado = 1
"""

_SQL_SUCURSALES_MUESTRA = """
SELECT TOP 6 S.Id_Sucursal, S.descripcion, S.Domicilio, E.Den_Comercial AS cliente
FROM dbo.Sucursal S JOIN dbo.Empresa E ON E.ID_Empresa = S.Id_Empresa
WHERE S.ID_Prestador = ? AND S.Estado = 1
ORDER BY E.Den_Comercial
"""

_SQL_LIQ_RECIENTES = """
SELECT TOP 3 L.ID_Liquidacion, L.ID_Costo, L.ID_Prestador, E.Den_Comercial AS prestador,
       EL.Descripcion AS estado, L.FacturaNro, L.Fecha_Mod, L.Usuario_Mod
FROM dbo.Liquidacion L
JOIN dbo.Empresa E ON E.ID_Empresa = L.ID_Prestador
JOIN dbo.Estado_Liquidacion EL ON EL.ID = L.ID_Estado_Liquidacion
ORDER BY L.Fecha_Mod DESC
"""

_SQL_LIQ_TOTAL = "SELECT COUNT(*) AS total, MAX(Fecha_Mod) AS ultima FROM dbo.Liquidacion"


def _imprimir(cursor: pyodbc.Cursor, titulo: str, sql: str, *params: object) -> None:
    print(f"\n=== {titulo} ===")
    cursor.execute(sql, *params) if params else cursor.execute(sql)
    columnas = [d[0] for d in cursor.description]
    for fila in cursor.fetchall():
        pares = ", ".join(f"{c}={v!r}" for c, v in zip(columnas, fila, strict=True))
        print(f"  {pares[:420]}")


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env")
    connection = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _imprimir(cursor, "CostoServicio PENTACOM (últimas vigencias)", _SQL_TARIFAS_PENTACOM, _PENTACOM_ID)
        _imprimir(cursor, "CostoServicio total", _SQL_COSTOS_TOTAL)
        _imprimir(cursor, "CostoServicio cobertura por empresa (top 40 por vigencia)", _SQL_COBERTURA_COSTOS)
        _imprimir(cursor, "IncidenteCosto columnas", _SQL_INCIDENTE_COSTO_COLS)
        _imprimir(cursor, "IncidenteCosto muestra", _SQL_INCIDENTE_COSTO_MUESTRA)
        _imprimir(cursor, "Empresa: inventario PST/SPST por Estado", _SQL_EMPRESA_PST_INVENTARIO)
        _imprimir(cursor, "Empresa: PST activos", _SQL_PST_ACTIVOS)
        _imprimir(cursor, "Sucursal: pares cliente-sucursal de PENTACOM", _SQL_SUCURSALES_DE_PST, _PENTACOM_ID)
        _imprimir(cursor, "Sucursal: muestra pares PENTACOM", _SQL_SUCURSALES_MUESTRA, _PENTACOM_ID)
        _imprimir(cursor, "Liquidacion recientes", _SQL_LIQ_RECIENTES)
        _imprimir(cursor, "Liquidacion total", _SQL_LIQ_TOTAL)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
