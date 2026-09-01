"""Investiga el incidente 844650 en SigesReadOnly — reporte del usuario de "carga
fantasma": el 24/8 se cargó un incidente idéntico para el mismo cliente y se resolvió,
y ahora se repite. El técnico va y el cliente dice que no lo cargó.

Solo SELECTs parametrizados. Cuenta SiGesReadOnly, autocommit=True, close() explícito
en finally. Mismo patrón que explore_siges_incidentes_sin_cerrar.py.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_incidente_844650_carga_fantasma.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60
_ID_INCIDENTE = 844650

_SQL_COLUMNAS_INCIDENTE = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Incidente'
ORDER BY ORDINAL_POSITION
"""

_SQL_INCIDENTE_DETALLE = """
SELECT
    I.ID_Incidente,
    I.ID_Empresa,
    E.Den_Comercial AS cliente,
    I.ID_Sucursal,
    S.Descripcion AS sucursal,
    I.ID_Sector,
    I.ID_Maquina,
    M.Nro_Serie,
    I.ID_Tipo_Incidente,
    TI.Descripcion AS tipo,
    I.ID_Estado_Incidente,
    EI.Descripcion AS estado,
    I.ID_Tecnico,
    E1.Den_Comercial AS tecnico,
    I.ID_Origen,
    IO.Descripcion AS origen,
    I.ID_Causa,
    IC.Descripcion AS causa,
    I.Nro_Incidente_Cliente,
    I.NroIncidente,
    I.Fecha_Ingreso,
    I.Fecha_Vto,
    I.Fecha_Cierre,
    I.Solicitante,
    I.emailSolicitante,
    I.telefonoSolicitante,
    I.Visita_a,
    I.Conforme,
    I.PlanillaIncompleta,
    I.Usuario_Mod,
    I.Fecha_Mod,
    I.UsuarioSync,
    I.FechaSync
FROM dbo.Incidente I
LEFT JOIN dbo.Empresa E ON I.ID_Empresa = E.ID_Empresa
LEFT JOIN dbo.Sucursal S ON I.ID_Sucursal = S.ID_Sucursal
LEFT JOIN dbo.Maquina M ON I.ID_Maquina = M.ID_Maquina
LEFT JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
LEFT JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
LEFT JOIN dbo.Empresa E1 ON I.ID_Tecnico = E1.ID_Empresa
LEFT JOIN dbo.IncidenteOrigen IO ON I.ID_Origen = IO.Id
LEFT JOIN dbo.IncidenteCausa IC ON I.ID_Causa = IC.Id
WHERE I.ID_Incidente = ?
"""

# Otros incidentes del mismo equipo/cliente en los últimos 60 días — para encontrar el
# del 24/8 que el usuario dice que es "el mismo con todo igual" y ver el patrón.
_SQL_HISTORIAL_MAQUINA = """
SELECT
    I.ID_Incidente,
    I.Fecha_Ingreso,
    I.Fecha_Cierre,
    TI.Descripcion AS tipo,
    EI.Descripcion AS estado,
    I.ID_Origen,
    IO.Descripcion AS origen,
    I.Nro_Incidente_Cliente,
    I.Solicitante,
    I.Usuario_Mod
FROM dbo.Incidente I
LEFT JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
LEFT JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
LEFT JOIN dbo.IncidenteOrigen IO ON I.ID_Origen = IO.Id
WHERE I.ID_Maquina = ?
  AND I.Fecha_Ingreso >= DATEADD(DAY, -60, GETDATE())
ORDER BY I.Fecha_Ingreso DESC
"""

# Catálogo de origen — para saber qué valores existen (Web, App, Proactivo, Telefono...)
_SQL_CATALOGO_ORIGEN = """
SELECT Id, Descripcion FROM dbo.IncidenteOrigen ORDER BY Id
"""

# Todos los incidentes recientes del mismo cliente con el mismo Falla/patrón, por si el
# "mismo con todo igual" es otra máquina de la misma sucursal, no la misma máquina.
_SQL_HISTORIAL_CLIENTE_RECIENTE = """
SELECT TOP 30
    I.ID_Incidente,
    I.ID_Maquina,
    M.Nro_Serie,
    I.ID_Sucursal,
    I.Fecha_Ingreso,
    I.Fecha_Cierre,
    TI.Descripcion AS tipo,
    EI.Descripcion AS estado,
    I.ID_Origen,
    IO.Descripcion AS origen,
    I.Nro_Incidente_Cliente,
    I.Solicitante
FROM dbo.Incidente I
LEFT JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
LEFT JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
LEFT JOIN dbo.IncidenteOrigen IO ON I.ID_Origen = IO.Id
LEFT JOIN dbo.Maquina M ON I.ID_Maquina = M.ID_Maquina
WHERE I.ID_Empresa = ?
  AND I.Fecha_Ingreso >= DATEADD(DAY, -60, GETDATE())
ORDER BY I.Fecha_Ingreso DESC
"""


def _columnas_incidente(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_COLUMNAS_INCIDENTE)
    filas = list(cursor.fetchall())
    print(f"\n=== Columnas de dbo.Incidente ({len(filas)}) ===")
    for f in filas:
        print(f"  {f.COLUMN_NAME}  ({f.DATA_TYPE})")


def _catalogo_origen(cursor: pyodbc.Cursor) -> None:
    try:
        cursor.execute(_SQL_CATALOGO_ORIGEN)
        filas = list(cursor.fetchall())
        print(f"\n=== Catálogo IncidenteOrigen ({len(filas)}) ===")
        for f in filas:
            print(f"  Id={f.Id}  {f.Descripcion!r}")
    except pyodbc.Error as e:
        print(f"\n=== IncidenteOrigen — error: {e} ===")


def _incidente_detalle(cursor: pyodbc.Cursor) -> dict | None:
    cursor.execute(_SQL_INCIDENTE_DETALLE, _ID_INCIDENTE)
    fila = cursor.fetchone()
    if fila is None:
        print(f"\n=== ID_Incidente={_ID_INCIDENTE} — NO ENCONTRADO en SigesReadOnly ===")
        return None
    cols = [d[0] for d in cursor.description]
    datos = dict(zip(cols, fila, strict=True))
    print(f"\n=== Detalle ID_Incidente={_ID_INCIDENTE} ===")
    for k, v in datos.items():
        print(f"  {k}: {v!r}")
    return datos


def _historial_maquina(cursor: pyodbc.Cursor, id_maquina: int | None) -> None:
    if id_maquina is None:
        print("\n=== Historial por máquina — sin ID_Maquina, se omite ===")
        return
    cursor.execute(_SQL_HISTORIAL_MAQUINA, id_maquina)
    filas = list(cursor.fetchall())
    print(
        f"\n=== Historial de incidentes de la máquina {id_maquina} "
        f"(últimos 60 días, {len(filas)}) ==="
    )
    for f in filas:
        print(
            f"  ID={f.ID_Incidente}  Ingreso={f.Fecha_Ingreso}  Cierre={f.Fecha_Cierre}  "
            f"Tipo={f.tipo!r}  Estado={f.estado!r}  Origen={f.ID_Origen}={f.origen!r}  "
            f"NroIncCliente={f.Nro_Incidente_Cliente!r}  "
            f"Solicitante={f.Solicitante!r}  UsuarioMod={f.Usuario_Mod!r}"
        )


def _historial_cliente(cursor: pyodbc.Cursor, id_empresa: int | None) -> None:
    if id_empresa is None:
        print("\n=== Historial por cliente — sin ID_Empresa, se omite ===")
        return
    cursor.execute(_SQL_HISTORIAL_CLIENTE_RECIENTE, id_empresa)
    filas = list(cursor.fetchall())
    print(
        f"\n=== Historial de incidentes del cliente {id_empresa} "
        f"(últimos 60 días, {len(filas)}) ==="
    )
    for f in filas:
        print(
            f"  ID={f.ID_Incidente}  Maquina={f.ID_Maquina}({f.Nro_Serie!r})  "
            f"Sucursal={f.ID_Sucursal}  "
            f"Ingreso={f.Fecha_Ingreso}  Cierre={f.Fecha_Cierre}  Tipo={f.tipo!r}  "
            f"Estado={f.estado!r}  "
            f"Origen={f.ID_Origen}={f.origen!r}  "
            f"NroIncCliente={f.Nro_Incidente_Cliente!r}  Solicitante={f.Solicitante!r}"
        )


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit(
            "Falta SLA_MERCURIO_HOST en .env — no hay acceso a MERCURIO desde este entorno."
        )

    conn_str = build_mercurio_connection_string(settings)
    print("Conectando a MERCURIO…")
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _columnas_incidente(cursor)
        _catalogo_origen(cursor)
        datos = _incidente_detalle(cursor)
        if datos is not None:
            _historial_maquina(cursor, datos.get("ID_Maquina"))
            _historial_cliente(cursor, datos.get("ID_Empresa"))
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
