"""ReanalizarLiquidacionesAbiertas — re-corre el motor de reglas sobre todas las
liquidaciones no terminales (de un prestador, o de todos) después de un cambio de
configuración que altera lo que el motor ve: tarifarios, Tabla KM o el vínculo
Tabla KM ↔ SPST.

Hasta 2026-09 el único disparador era el botón "Reanalizar" del detalle: cargar
una tarifa o vincular un SPST desde una alerta ALT008 dejaba la alerta colgada
hasta que alguien volvía a apretarlo (caso INFOMAC 3952-5, 2026-09-04 — ver
`docs/liquidaciones/REDISENO_REVISION_LIQUIDACIONES.md`). Las aprobadas/cerradas
quedan congeladas, mismo guard que la reconciliación contra AyC."""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
)
from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_APROBADA,
    ESTADO_CERRADA,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)

logger = logging.getLogger(__name__)

_TERMINALES = frozenset({ESTADO_APROBADA, ESTADO_CERRADA})


@dataclass(frozen=True)
class ReanalizarLiquidacionesAbiertasPorts:
    liquidaciones: LiquidacionRepository
    reanalizar: ReanalizarLiquidacion


@dataclass(frozen=True)
class ReanalizarAbiertasResultado:
    reanalizadas: int
    total_alertas: int


class ReanalizarLiquidacionesAbiertas:
    def __init__(self, ports: ReanalizarLiquidacionesAbiertasPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID | None) -> ReanalizarAbiertasResultado:
        """`prestador_id=None` = todas las abiertas (sync de tarifarios sin filtro,
        import CSV sin saber qué prestadores tocó)."""
        todas = await self._ports.liquidaciones.list_filtered(prestador_id=prestador_id)
        abiertas = [liq for liq in todas if liq.estado not in _TERMINALES]
        total_alertas = 0
        for liq in abiertas:
            resultado = await self._ports.reanalizar.execute(liq.id)
            total_alertas += resultado.total_alertas
        logger.info(
            "reanalizar_abiertas: %d liquidacion(es) reanalizada(s), %d alerta(s)",
            len(abiertas),
            total_alertas,
            extra={"prestador_id": str(prestador_id)},
        )
        return ReanalizarAbiertasResultado(len(abiertas), total_alertas)
