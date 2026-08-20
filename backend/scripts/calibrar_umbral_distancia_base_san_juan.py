"""Fase 0.3 de Tier 0: distribución real de distancia base→sucursal para
calibrar `umbral_distancia_base_km` (300 km era provisorio, sin evidencia).
Cruza contra los hallazgos YA confirmados (Tier0 certeza absoluta, Tier1b,
Tier2/pines sospechosos) para separar "lejos pero real" de "pin roto
confirmado" — read-only, no llama a ningún proveedor nuevo.

Uso (dentro del contenedor backend):
    uv run python scripts/calibrar_umbral_distancia_base_san_juan.py
"""

import pyodbc

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    parse_latlon_siges,
)
from src.modules.liquidaciones.domain.services.geolocalizacion import haversine_km
from src.modules.liquidaciones.infrastructure.siges.query import (
    SUCURSALES_DE_EMPRESA_SQL,
    SUCURSALES_DE_PRESTADOR_SQL,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_SIGES_EMPRESA_ID = 504
_BASE_SUCURSAL_ID = 2649
_TIMEOUT_SECONDS = 30


def _conectar() -> pyodbc.Connection:
    settings = get_settings()
    conn = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    conn.timeout = _TIMEOUT_SECONDS
    return conn


def main() -> None:
    conn = _conectar()
    try:
        cur = conn.cursor()
        cur.execute(SUCURSALES_DE_PRESTADOR_SQL, _SIGES_EMPRESA_ID)
        sucursales = [
            (int(r.Id_Sucursal), str(r.Den_Comercial), str(r.descripcion), r.Latitud, r.Longitud)
            for r in cur.fetchall()
        ]
        cur.execute(SUCURSALES_DE_EMPRESA_SQL, _SIGES_EMPRESA_ID)
        base = next(
            (r for r in cur.fetchall() if int(r.Id_Sucursal) == _BASE_SUCURSAL_ID), None
        )
    finally:
        conn.close()

    if base is None:
        print("Base no encontrada")
        return
    base_coords = parse_latlon_siges(base.Latitud, base.Longitud)
    print(f"Base: {base_coords}")

    distancias = []
    for sid, empresa, sucursal, lat, lon in sucursales:
        coords = parse_latlon_siges(lat, lon)
        if coords is None or base_coords is None:
            continue
        d = haversine_km(*base_coords, *coords)
        distancias.append((d, sid, empresa, sucursal))
    distancias.sort()

    print(f"\nTotal con coordenadas válidas: {len(distancias)}")
    print("\n=== Percentiles de distancia a la base (km) ===")
    for p in (50, 75, 90, 95, 97, 98, 99, 100):
        idx = min(len(distancias) - 1, int(len(distancias) * p / 100))
        print(f"  p{p}: {distancias[idx][0]:.0f} km")

    print("\n=== Histograma por rango ===")
    rangos = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 250), (250, 300),
              (300, 400), (400, 600), (600, 1000), (1000, 2000), (2000, 100000)]
    for lo, hi in rangos:
        n = sum(1 for d, *_ in distancias if lo <= d < hi)
        print(f"  [{lo:5d}, {hi:6d}) km: {n:4d} sucursales")

    print("\n=== Detalle 200-450 km (zona del posible umbral) ===")
    for d, sid, empresa, sucursal in distancias:
        if 200 <= d <= 450:
            print(f"  {d:6.0f} km  id={sid}  {empresa} | {sucursal}")


if __name__ == "__main__":
    main()
