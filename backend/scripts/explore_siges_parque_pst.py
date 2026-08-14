"""Explora SiGesReadOnly para validar si se puede obtener el parque de impresoras
asignado a un PST (caso concreto: PST Villa Mercedes). Solo SELECTs parametrizados,
misma cuenta de solo lectura y mismo patrón que explore_siges_planificacion.py
(conexión efímera, autocommit=True, close() explícito en finally).

Ronda 1 (hecha): PST Villa Mercedes = ID_Empresa 740 ('PST Villa Mercedes - Infomac',
Estado=0 activo; el 692 es 'NO USAR', Estado=1). Maquina tiene ID_Sucursal,
ID_Estado_Maquina y Estado; Sucursal.ID_Prestador es la asignación al PST.

Ronda 2: catálogo Estado_Maquina + parque real del PST 740 vía
Sucursal.ID_Prestador → Maquina → Articulo → ArtGen.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_parque_pst.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30

_PST_VILLA_MERCEDES = 740

_SQL_ESTADO_MAQUINA = "SELECT Id, Descripcion, Estado FROM dbo.Estado_Maquina ORDER BY Id"

_SQL_SUCURSALES_DEL_PST = """
SELECT COUNT(*) AS total,
       SUM(CASE WHEN S.Estado = 0 THEN 1 ELSE 0 END) AS activas
FROM dbo.Sucursal S
WHERE S.ID_Prestador = ?
"""

_SQL_PARQUE_POR_ESTADO = """
SELECT EM.Id AS id_estado, EM.Descripcion AS estado_maquina,
       M.Estado AS estado_fila, COUNT(*) AS cantidad
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Estado_Maquina EM ON EM.Id = M.ID_Estado_Maquina
WHERE S.ID_Prestador = ? AND S.Estado = 0
GROUP BY EM.Id, EM.Descripcion, M.Estado
ORDER BY cantidad DESC
"""

_SQL_PARQUE_POR_CLIENTE = """
SELECT TOP 15 E.Den_Comercial AS cliente, COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Estado_Maquina EM ON EM.Id = M.ID_Estado_Maquina
WHERE S.ID_Prestador = ? AND S.Estado = 0 AND M.Estado = 0
GROUP BY E.Den_Comercial
ORDER BY maquinas DESC
"""

_SQL_MUESTRA_PARQUE = """
SELECT TOP 10
    M.ID_Maquina, M.Nro_Serie, AG.Descripcion AS modelo,
    E.Den_Comercial AS cliente, S.descripcion AS sucursal,
    EM.Descripcion AS estado_maquina
FROM dbo.Maquina M
INNER JOIN dbo.Articulo A ON A.Id_Articulo = M.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
INNER JOIN dbo.Estado_Maquina EM ON EM.Id = M.ID_Estado_Maquina
WHERE S.ID_Prestador = ? AND S.Estado = 0 AND M.Estado = 0
ORDER BY E.Den_Comercial, S.descripcion
"""


def _catalogo_estado_maquina(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_ESTADO_MAQUINA)
    filas = list(cursor.fetchall())
    print(f"=== Catálogo Estado_Maquina ({len(filas)}) ===")
    for f in filas:
        print(f"  Id={f.Id} {f.Descripcion!r} (Estado={f.Estado})")


def _sucursales_del_pst(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_SUCURSALES_DEL_PST, _PST_VILLA_MERCEDES)
    f = cursor.fetchone()
    print(f"\n=== Sucursales con ID_Prestador={_PST_VILLA_MERCEDES}: {f.total} (activas={f.activas}) ===")


def _parque_por_estado(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_PARQUE_POR_ESTADO, _PST_VILLA_MERCEDES)
    filas = list(cursor.fetchall())
    print("\n=== Máquinas en sucursales activas del PST, por estado ===")
    for f in filas:
        print(
            f"  Estado_Maquina={f.estado_maquina!r} (id={f.id_estado}) "
            f"Maquina.Estado={f.estado_fila}: {f.cantidad}"
        )


def _parque_por_cliente(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_PARQUE_POR_CLIENTE, _PST_VILLA_MERCEDES)
    filas = list(cursor.fetchall())
    print("\n=== Top clientes por máquinas activas (Maquina.Estado=0) ===")
    for f in filas:
        print(f"  {f.cliente!r}: {f.maquinas}")


def _muestra_parque(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_MUESTRA_PARQUE, _PST_VILLA_MERCEDES)
    filas = list(cursor.fetchall())
    print("\n=== Muestra de 10 máquinas del parque ===")
    for f in filas:
        print(
            f"  ID={f.ID_Maquina} Serie={f.Nro_Serie!r} Modelo={f.modelo!r} "
            f"Cliente={f.cliente!r} Sucursal={f.sucursal!r} Estado={f.estado_maquina!r}"
        )


# Ronda 3: el reporte legacy "Maquinas Activas por Prestador" (sitesphp) da 841
# equipos para el PST 740. Hipótesis por aritmética de la ronda 2:
# 841 = todas las Maquina.Estado=0 en sucursales activas, excluyendo
# ID_Estado_Maquina 2 ('De Baja') y 8 ('Backup Fijo'). Se prueba con y sin el
# filtro de sucursal activa para ver cuál matchea exacto.
_SQL_PARIDAD_LEGACY = """
SELECT
    SUM(CASE WHEN S.Estado = 0 THEN 1 ELSE 0 END) AS con_sucursal_activa,
    COUNT(*) AS sin_filtro_sucursal
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
WHERE S.ID_Prestador = ? AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
"""


def _paridad_legacy(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_PARIDAD_LEGACY, _PST_VILLA_MERCEDES)
    f = cursor.fetchone()
    print("\n=== Paridad contra reporte legacy (esperado 841) ===")
    print(f"  Estado=0 y NOT IN ('De Baja','Backup Fijo'), sucursales activas: {f.con_sucursal_activa}")
    print(f"  Ídem sin filtrar estado de sucursal: {f.sin_filtro_sucursal}")


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _catalogo_estado_maquina(cursor)
        _sucursales_del_pst(cursor)
        _parque_por_estado(cursor)
        _parque_por_cliente(cursor)
        _muestra_parque(cursor)
        _paridad_legacy(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
