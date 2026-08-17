"""BackfillEstadoLiquidaciones — actualiza `estado` de las liquidaciones `abierta`
con su estado real en wsAyC.

Reutiliza getTopLiquidations (ya usado por el sync), que devuelve el campo `Estado`
para cada liquidación. No hay llamadas SOAP adicionales por liquidación.

Solo actualiza liquidaciones con `estado='abierta'` — respeta cualquier estado que
la TL haya asignado manualmente. Ver ADR-016.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.backfill_estado import (
    BackfillEstadoPrestadorResultado,
    BackfillEstadoResultado,
)
from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_ABIERTA,
    Liquidacion,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.repositories.cd_liquidaciones_gateway import (
    CdLiquidacionesGateway,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.services.numeracion_ayc import numero_liquidacion

logger = logging.getLogger(__name__)

_ESTADOS_AYC_VALIDOS = frozenset(
    {"preliquidada", "recibida", "observada", "aprobada", "cerrada"}
)


@dataclass(frozen=True)
class BackfillEstadoLiquidacionesPorts:
    cd_gateway: CdLiquidacionesGateway
    prestadores: PrestadorRepository
    liquidaciones: LiquidacionRepository


class BackfillEstadoLiquidaciones:
    def __init__(self, ports: BackfillEstadoLiquidacionesPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        *,
        dry_run: bool,
        prestador_id: UUID | None = None,
    ) -> BackfillEstadoResultado:
        todos = await self._ports.prestadores.list_con_cd_id()
        prestadores = (
            [p for p in todos if p.id == prestador_id] if prestador_id else todos
        )
        resultado = BackfillEstadoResultado(dry_run=dry_run)
        for pst in prestadores:
            resultado.prestadores.append(
                await self._backfill_prestador(pst, resultado, dry_run=dry_run)
            )
        return resultado

    async def _backfill_prestador(
        self, pst: Prestador, resultado: BackfillEstadoResultado, *, dry_run: bool
    ) -> BackfillEstadoPrestadorResultado:
        pst_res = BackfillEstadoPrestadorResultado(
            prestador_id=str(pst.id), prestador_nombre=pst.nombre
        )
        ayc_map = await self._estados_ayc(pst)
        locales = await self._ports.liquidaciones.list_filtered(
            prestador_id=pst.id, estado=ESTADO_ABIERTA
        )
        for liq in locales:
            await self._aplicar_estado(liq, ayc_map, pst_res, resultado, dry_run=dry_run)
        logger.info(
            "backfill_estado(pst=%s, dry_run=%s): procesadas=%d actualizadas=%d "
            "saltadas=%d sin_match=%d",
            pst.nombre, dry_run, pst_res.procesadas,
            pst_res.actualizadas, pst_res.saltadas, pst_res.sin_match,
        )
        return pst_res

    async def _estados_ayc(self, pst: Prestador) -> dict[str, str]:
        """Mapa numero_liquidacion → estado AyC en minúsculas."""
        assert pst.cd_prestador_id is not None  # garantizado por list_con_cd_id()
        cd_liqs = await self._ports.cd_gateway.get_liquidaciones(
            pst.cd_prestador_id, top=500
        )
        return {
            numero_liquidacion(liq.id): liq.estado.lower()
            for liq in cd_liqs
            if liq.estado
        }

    async def _aplicar_estado(
        self,
        liq: Liquidacion,
        ayc_map: dict[str, str],
        pst_res: BackfillEstadoPrestadorResultado,
        resultado: BackfillEstadoResultado,
        *,
        dry_run: bool,
    ) -> None:
        pst_res.procesadas += 1
        numero = liq.numero_liquidacion
        nuevo_estado = ayc_map.get(numero) if numero else None
        if not nuevo_estado:
            pst_res.sin_match += 1
            return
        if nuevo_estado not in _ESTADOS_AYC_VALIDOS:
            logger.warning(
                "backfill_estado: estado AyC desconocido %r para %s — saltando",
                nuevo_estado, numero,
            )
            pst_res.saltadas += 1
            return
        if not dry_run:
            await self._ports.liquidaciones.update_estado(liq.id, nuevo_estado)
        pst_res.actualizadas += 1
        resultado.por_estado_destino[nuevo_estado] = (
            resultado.por_estado_destino.get(nuevo_estado, 0) + 1
        )
