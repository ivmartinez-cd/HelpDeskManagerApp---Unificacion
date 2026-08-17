"""Smoke read-only de las 5 queries Siges del módulo liquidaciones, vía el
gateway REAL de producción (`PyodbcSigesCatalogoGateway`) — valida el código
que corre en la app, no SQL suelto. Solo SELECT contra SiGesReadOnly; cero
escritura y cero Google.

Uso (dentro del contenedor backend):
    uv run python scripts/smoke_siges_liquidaciones.py
"""

import asyncio

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    parse_latlon_siges,
)
from src.modules.liquidaciones.presentation.dependencies.siges import (
    siges_catalogo_gateway,
)


def _linea(query: str, veredicto: str, detalle: str) -> None:
    print(f"  [{veredicto}] {query}: {detalle}")


async def main() -> None:
    gateway = siges_catalogo_gateway()
    print("Smoke Siges liquidaciones — 5 queries vía el gateway real\n")

    empresas = await gateway.list_empresas_activas()
    psts = [e for e in empresas if e.tipo == "PST"]
    _linea(
        "Q1 EMPRESAS_PST_ACTIVAS",
        "PASS" if empresas else "FAIL",
        f"{len(empresas)} empresas ({len(psts)} PST); "
        f"muestra: {', '.join(e.den_comercial for e in empresas[:3])}",
    )

    ids_muestra = [e.siges_empresa_id for e in psts[:2]]
    costos = await gateway.list_costos_habilitados(ids_muestra)
    _linea(
        "Q2 COSTOS_HABILITADOS",
        "PASS" if costos else "WARN",
        f"{len(costos)} vigencias para empresas {ids_muestra}",
    )

    pst_id = ids_muestra[0]
    clientes = await gateway.list_sucursales_de_prestador(pst_id)
    con_pin = sum(
        1 for s in clientes if parse_latlon_siges(s.latitud, s.longitud) is not None
    )
    con_costo = sum(1 for s in clientes if s.id_costo_servicios is not None)
    _linea(
        "Q3 SUCURSALES_DE_PRESTADOR",
        "PASS" if clientes else "WARN",
        f"empresa {pst_id}: {len(clientes)} sucursales cliente, "
        f"{con_pin} con pin parseable, {con_costo} con IDCostoServicios",
    )

    cuadriculas = await gateway.list_cuadriculas_de_prestador(pst_id)
    _linea(
        "Q4 CUADRICULAS_DE_PRESTADOR",
        "PASS",
        f"empresa {pst_id}: {sorted(cuadriculas)!r}",
    )

    propias = await gateway.list_sucursales_de_empresa(pst_id)
    sin_coords = [
        p.descripcion
        for p in propias
        if parse_latlon_siges(p.latitud, p.longitud) is None
    ]
    _linea(
        "Q5 SUCURSALES_DE_EMPRESA",
        "PASS" if propias and not sin_coords else "WARN",
        f"empresa {pst_id}: {len(propias)} sedes propias"
        + (f"; SIN coordenadas: {sin_coords}" if sin_coords else "; todas con coordenadas"),
    )

    print("\nListo — solo lectura, 0 llamadas a Google.")


if __name__ == "__main__":
    asyncio.run(main())
