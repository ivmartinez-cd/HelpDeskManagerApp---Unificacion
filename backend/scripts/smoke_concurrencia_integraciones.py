"""Prueba de concurrencia del refactor de integraciones (SOLO LECTURA).

Dispara en paralelo consultas MERCURIO (más que el tope del semáforo, para
ejercitar el encolado) y llamadas wsAyC (getTopLiquidations sobre el provider
compartido con Session por llamada) y verifica que todo complete sin deadlock
ni timeouts nuevos.

Uso: uv run python scripts/smoke_concurrencia_integraciones.py
"""

import asyncio
import time

from src.modules.contadores.presentation.dependencies import (
    get_operador_catalog_gateway,
    get_parque_cliente_gateway,
)
from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)
from src.modules.prestadores.presentation.dependencies import get_prestador_siges_gateway

EMPRESAS_CD = [1303, 600, 1285]  # BAHIA, SUPERNOVA, SM TUCUMAN — solo lectura
SIGES_IDS = [1303]


async def _cronometrada(nombre: str, corutina) -> tuple[str, float, int]:
    t0 = time.perf_counter()
    resultado = await corutina
    return nombre, time.perf_counter() - t0, len(resultado)


async def main() -> None:
    parque = get_parque_cliente_gateway()
    operadores = get_operador_catalog_gateway()
    prestadores = get_prestador_siges_gateway()
    cd = ZeepCdLiquidacionesGateway()

    tareas = [
        _cronometrada("mercurio.parque.1", parque.list_empresas_activas()),
        _cronometrada("mercurio.parque.2", parque.list_empresas_activas()),
        _cronometrada("mercurio.operadores.1", operadores.find_by_logins(["vipaez"])),
        _cronometrada("mercurio.operadores.2", operadores.find_by_logins(["vipaez"])),
        _cronometrada("mercurio.prestadores.1", prestadores.find_by_siges_ids(SIGES_IDS)),
        _cronometrada("mercurio.prestadores.2", prestadores.find_by_siges_ids(SIGES_IDS)),
        *[
            _cronometrada(f"wsayc.top.{empresa}", cd.get_liquidaciones(empresa, top=5))
            for empresa in EMPRESAS_CD
        ],
    ]

    t0 = time.perf_counter()
    resultados = await asyncio.gather(*tareas)
    total = time.perf_counter() - t0

    for nombre, duracion, filas in sorted(resultados):
        print(f"  {nombre}: {filas} filas en {duracion:.2f}s")
    print(f"{len(resultados)} operaciones concurrentes completadas en {total:.2f}s "
          "sin deadlock ni timeout")


if __name__ == "__main__":
    asyncio.run(main())
