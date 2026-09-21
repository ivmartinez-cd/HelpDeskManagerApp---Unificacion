"""Investiga por qué el incidente 842212 no aparece por el web service wsAyC y qué
estado/datos tiene en Orion (SigesReadOnly).

Solo lecturas: getIncidentById contra wsAyC (sin persist*) y SELECTs parametrizados
contra Orion. Mismo patrón que explore_incidente_844650_carga_fantasma.py.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_incidente_842212_no_aparece.py
"""

import asyncio

import pyodbc

from src.modules.insumos.infrastructure.soap import wsayc_parsing as parsing
from src.modules.insumos.infrastructure.soap.zeep_wsayc_gateway import ZeepWsAycGateway
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.orion.connection import build_orion_connection_string

_TIMEOUT_SECONDS = 60
_ID_INCIDENTE = 842212

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


async def _consultar_wsayc() -> None:
    gateway = ZeepWsAycGateway()
    print(f"\n=== wsAyC getIncidentById(id={_ID_INCIDENTE}) — crudo ===")
    raw = await asyncio.to_thread(
        lambda: gateway._service().getIncidentById(id=str(_ID_INCIDENTE))
    )
    print(repr(raw))

    print(f"\n=== wsAyC getIncidentById(id={_ID_INCIDENTE}) — parseado ===")
    parsed = parsing.parse_incident_by_id(raw)
    print(parsed)

    resultado_gateway = await gateway.fetch_incident_by_id(_ID_INCIDENTE)
    print(f"\n=== ZeepWsAycGateway.fetch_incident_by_id({_ID_INCIDENTE}) ===")
    print(resultado_gateway)


def _consultar_orion() -> None:
    settings = get_settings()
    if not settings.orion_host:
        print("\n=== Orion: sin ORION_HOST configurado, se omite ===")
        return

    conn_str = build_orion_connection_string(settings)
    print("\nConectando a ORION…")
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        cursor.execute(_SQL_INCIDENTE_DETALLE, _ID_INCIDENTE)
        fila = cursor.fetchone()
        if fila is None:
            print(f"\n=== ID_Incidente={_ID_INCIDENTE} — NO ENCONTRADO en SigesReadOnly ===")
            return
        cols = [d[0] for d in cursor.description]
        datos = dict(zip(cols, fila, strict=True))
        print(f"\n=== Detalle ID_Incidente={_ID_INCIDENTE} en Orion ===")
        for k, v in datos.items():
            print(f"  {k}: {v!r}")
    finally:
        connection.close()
        print("\nConexión a Orion cerrada explícitamente.")


def main() -> None:
    asyncio.run(_consultar_wsayc())
    _consultar_orion()


if __name__ == "__main__":
    main()
