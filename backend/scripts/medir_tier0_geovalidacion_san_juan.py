"""Fase 0 de la geovalidación (Fase 2 del plan): corre Tier 0 REAL
(dominio de producción) sobre TODAS las sucursales activas de SAN JUAN.
Solo lectura, cero llamadas a Georef/Nominatim/Google.

Uso (dentro del contenedor backend):
    uv run python scripts/medir_tier0_geovalidacion_san_juan.py
"""

import pyodbc

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    parse_latlon_siges,
)
from src.modules.liquidaciones.domain.services.geovalidacion_tier0 import (
    SucursalParaValidar,
    evaluar_tier0,
)
from src.modules.liquidaciones.infrastructure.siges.query import (
    SUCURSALES_DE_EMPRESA_SQL,
    SUCURSALES_DE_PRESTADOR_SQL,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30
_SIGES_EMPRESA_ID = 504  # San Juan - Gestion Integral
_BASE_SUCURSAL_ID = 2649  # prestadores.siges_base_sucursal_id de San Juan - Gestion Integral


def _conectar() -> pyodbc.Connection:
    settings = get_settings()
    conn = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    conn.timeout = _TIMEOUT_SECONDS
    return conn


def _sucursales_cliente(conn: pyodbc.Connection) -> list[SucursalParaValidar]:
    cursor = conn.cursor()
    cursor.execute(SUCURSALES_DE_PRESTADOR_SQL, _SIGES_EMPRESA_ID)
    resultado = []
    for r in cursor.fetchall():
        coords = parse_latlon_siges(r.Latitud, r.Longitud)
        resultado.append(SucursalParaValidar(
            siges_sucursal_id=int(r.Id_Sucursal),
            empresa_nombre=str(r.Den_Comercial),
            sucursal_nombre=str(r.descripcion),
            domicilio=r.Domicilio,
            provincia=r.DesProvincia,
            latitud=coords[0] if coords else None,
            longitud=coords[1] if coords else None,
        ))
    return resultado


def _base_despacho(conn: pyodbc.Connection) -> tuple[float, float] | None:
    if _BASE_SUCURSAL_ID is None:
        return None
    cursor = conn.cursor()
    cursor.execute(SUCURSALES_DE_EMPRESA_SQL, _SIGES_EMPRESA_ID)
    for r in cursor.fetchall():
        if int(r.Id_Sucursal) == _BASE_SUCURSAL_ID:
            return parse_latlon_siges(r.Latitud, r.Longitud)
    return None


def main() -> None:
    conn = _conectar()
    try:
        sucursales = _sucursales_cliente(conn)
        base = _base_despacho(conn)
    finally:
        conn.close()

    print(f"Sucursales activas evaluadas (SAN JUAN, empresa {_SIGES_EMPRESA_ID}): {len(sucursales)}")
    print(f"Base de despacho: {base if base else 'no configurada — distancia a base NO evaluada'}")

    hallazgos = evaluar_tier0(sucursales, base=base)
    por_codigo: dict[str, int] = {}
    for h in hallazgos:
        por_codigo[h.codigo] = por_codigo.get(h.codigo, 0) + 1

    afectadas = {h.siges_sucursal_id for h in hallazgos}
    print(f"\nTotal hallazgos: {len(hallazgos)} sobre {len(afectadas)} sucursales distintas")
    for codigo, n in sorted(por_codigo.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {codigo}")

    print("\n=== Muestra por código (hasta 10 c/u) ===")
    por_id = {s.siges_sucursal_id: s for s in sucursales}
    for codigo in por_codigo:
        muestra = [h for h in hallazgos if h.codigo == codigo][:10]
        print(f"\n-- {codigo} --")
        for h in muestra:
            s = por_id[h.siges_sucursal_id]
            print(f"  [{h.severidad}] {s.empresa_nombre} | {s.sucursal_nombre} — {h.detalle}")


if __name__ == "__main__":
    main()
