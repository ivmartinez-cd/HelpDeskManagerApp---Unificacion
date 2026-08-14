"""Smoke de lectura del refactor de integraciones externas (SOLO LECTURA).

Ejercita la misma operación de lectura por cada gateway Siges/wsAyC, antes y
después del refactor: si los números coinciden, el refactor fue conductual-
neutro. Ninguna operación de escritura (getTopLiquidations es lectura; Siges
se consulta con la cuenta read-only).

Uso: uv run python scripts/smoke_integraciones_lectura.py
"""

import asyncio
import time

from sqlalchemy import text

from src.modules.contadores.presentation.dependencies import (
    get_equipos_sin_real_gateway,
    get_parque_cliente_gateway,
)
from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)
from src.modules.liquidaciones.presentation.dependencies.siges import _gateway
from src.modules.prestadores.presentation.dependencies import get_prestador_siges_gateway
from src.modules.sla.domain.value_objects.periodo import Periodo
from src.modules.sla.presentation.dependencies import get_sla_query_gateway
from src.shared.infrastructure.database.engine import get_engine

EMPRESA_CD_ID = 1303  # BAHIA
PERIODO = 202608


async def _siges_ids_de_prestadores() -> list[int]:
    engine = get_engine()
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT siges_empresa_id FROM prestadores "
                "WHERE siges_empresa_id IS NOT NULL ORDER BY siges_empresa_id"
            )
        )
        return [int(r[0]) for r in rows]


async def main() -> None:  # noqa: PLR0914 - script de verificación, no producción
    t0 = time.perf_counter()
    incidentes = await get_sla_query_gateway().find_incidentes(Periodo(PERIODO))
    print(f"sla.find_incidentes({PERIODO}): {len(incidentes)} filas "
          f"({time.perf_counter() - t0:.1f}s)")

    siges_ids = await _siges_ids_de_prestadores()
    prestador_gw = get_prestador_siges_gateway()
    info = await prestador_gw.find_by_siges_ids(siges_ids)
    equipos = await prestador_gw.count_equipos_by_siges_ids(siges_ids)
    print(f"prestadores.find_by_siges_ids({len(siges_ids)} ids): {len(info)} filas; "
          f"count_equipos: {sum(equipos.values())} equipos en {len(equipos)} PST")

    parque = get_parque_cliente_gateway()
    empresas = await parque.list_empresas_activas()
    print(f"contadores.parque.list_empresas_activas: {len(empresas)} empresas")

    t0 = time.perf_counter()
    snapshot = await get_equipos_sin_real_gateway().list_equipos(force_refresh=True)
    print(f"contadores.equipos_sin_real.list_equipos: {len(snapshot.equipos)} equipos "
          f"({time.perf_counter() - t0:.1f}s)")

    catalogo = _gateway()
    pst = await catalogo.list_empresas_activas()
    costos = await catalogo.list_costos_habilitados([e.siges_empresa_id for e in pst])
    print(f"liquidaciones.siges.list_empresas_activas: {len(pst)} PST/SPST; "
          f"costos_habilitados: {len(costos)} filas")

    liqs = await ZeepCdLiquidacionesGateway().get_liquidaciones(EMPRESA_CD_ID, top=5)
    print(f"liquidaciones.wsayc.get_liquidaciones({EMPRESA_CD_ID}, top=5): "
          f"{len(liqs)} liquidaciones; ids={sorted(liq.id for liq in liqs)}")


if __name__ == "__main__":
    asyncio.run(main())
