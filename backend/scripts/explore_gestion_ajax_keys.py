"""Inspecciona el payload crudo del ajax-by-rango de Gestión para ver si los
eventos traen un id de cliente que hoy no persistimos (el parser de
GestionPlanificacionClient descarta las claves desconocidas). Solo un GET de
lectura — la misma llamada que hace el sync manual del calendario.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_gestion_ajax_keys.py
"""

import asyncio
from datetime import date, timedelta

from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)


async def main() -> None:
    client = GestionPlanificacionClient()
    hoy = date.today()
    params = client._build_params(  # noqa: SLF001 — script de exploración
        hoy.isoformat(), (hoy + timedelta(days=14)).isoformat(), None, None
    )
    response = await client._get(  # noqa: SLF001
        "/planificacion/ajax-by-rango",
        params=params,
        extra_headers={
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    data = list(response.json())
    print(f"Eventos en el rango: {len(data)}")
    if not data:
        return

    claves = sorted({k for item in data for k in item})
    print(f"\nClaves presentes en el payload ({len(claves)}):")
    for k in claves:
        print(f"  {k}")

    ejemplo = next((i for i in data if i.get("cliente")), data[0])
    print("\nEjemplo (campos con 'id' o 'cliente' en el nombre):")
    for k, v in ejemplo.items():
        if "id" in k.lower() or "cliente" in k.lower() or "empresa" in k.lower():
            print(f"  {k} = {v!r}")


if __name__ == "__main__":
    asyncio.run(main())
