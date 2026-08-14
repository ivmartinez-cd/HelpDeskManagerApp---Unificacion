"""Ronda 2 de paridad: getMachineIncidents no trajo los preventivos recientes
en el top 10 sin filtro — hipótesis: el servicio filtra/ordena por tipo.
Se prueba el parámetro `tipo` con variantes (id 102 y texto) para la máquina
31852 (serie ZELLBJEJ400020A, preventivo 842633 cerrado hoy en la réplica).
SOLO lecturas SOAP.

Uso: uv run python scripts/explore_preventivos_paridad_ronda2.py
"""

import asyncio

from src.modules.insumos.infrastructure.soap import wsayc_parsing as parsing
from src.shared.infrastructure.wsayc.client_provider import get_wsayc_client_provider

# (serie, nro_incidente esperado según la réplica) — casos de la ronda 3.
_CASOS = [
    ("ZELLBJEJ400020A", "842633"),
    ("07QWB9UG3A005LX", "842630"),
    ("076UBJFH30002MT", "842708"),
]


async def main() -> None:
    provider = get_wsayc_client_provider()
    service = provider.service()
    for serie, nro_esperado in _CASOS:
        raw_machine = await asyncio.to_thread(
            lambda s=serie: service.getMachineBySerial(SerialNumber=s)
        )
        machine = parsing.parse_machine(raw_machine)
        if machine is None:
            print(f"\n=== {serie}: no encontrada en wsAyC ===")
            continue
        raw = await asyncio.to_thread(
            lambda m=machine: service.getMachineIncidents(
                IdMaquina=m.machine_id,
                IdEmpresa="",
                IdSucursal="",
                IdSector="",
                top="3",
                estado="",
                tipo="102",
            )
        )
        incidentes = parsing.parse_incidents(raw)
        print(f"\n=== {serie} (machine_id={machine.machine_id}) tipo=102 ===")
        for i in incidentes:
            marca = "  <-- esperado" if i.numero == nro_esperado else ""
            print(f"  {i.numero} {i.estado!r} fecha={i.fecha!r} cierre={i.fecha_cierre!r}{marca}")


if __name__ == "__main__":
    asyncio.run(main())
