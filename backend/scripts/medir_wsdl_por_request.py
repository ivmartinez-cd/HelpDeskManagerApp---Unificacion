"""Medición Fase 0.2 del refactor de integraciones externas (SOLO LECTURA).

Cronometra el costo del patrón actual de liquidaciones (gateway nuevo por
request → cliente zeep con WSDL recién descargado y parseado en la primera
llamada) contra el patrón singleton (cliente cacheado). Usa exclusivamente
getTopLiquidations — ninguna operación de escritura.

Uso: uv run python scripts/medir_wsdl_por_request.py
"""

import asyncio
import statistics
import time

from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)

EMPRESA_CD_ID = 1303  # BAHIA — solo lectura, top chico
TOP = 5
RONDAS = 3


async def _medir_una_ronda() -> tuple[float, float]:
    gateway = ZeepCdLiquidacionesGateway()

    t0 = time.perf_counter()
    primera = await gateway.get_liquidaciones(EMPRESA_CD_ID, top=TOP)
    t_primera = time.perf_counter() - t0

    t0 = time.perf_counter()
    repetida = await gateway.get_liquidaciones(EMPRESA_CD_ID, top=TOP)
    t_repetida = time.perf_counter() - t0

    print(
        f"  gateway nuevo: 1ra llamada (WSDL + SOAP) = {t_primera:.3f}s "
        f"({len(primera)} liq) | repetida (cliente cacheado) = {t_repetida:.3f}s "
        f"({len(repetida)} liq)"
    )
    return t_primera, t_repetida


async def main() -> None:
    primeras: list[float] = []
    repetidas: list[float] = []
    for ronda in range(1, RONDAS + 1):
        print(f"Ronda {ronda}:")
        t_primera, t_repetida = await _medir_una_ronda()
        primeras.append(t_primera)
        repetidas.append(t_repetida)

    print()
    print(
        f"Mediana 1ra llamada (patrón actual, gateway por request): "
        f"{statistics.median(primeras):.3f}s"
    )
    print(
        f"Mediana llamada repetida (patrón singleton): {statistics.median(repetidas):.3f}s"
    )
    print(
        f"Sobrecosto del WSDL por request: "
        f"{statistics.median(primeras) - statistics.median(repetidas):.3f}s por request"
    )


if __name__ == "__main__":
    asyncio.run(main())
