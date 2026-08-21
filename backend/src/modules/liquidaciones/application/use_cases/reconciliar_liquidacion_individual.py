"""ReconciliarLiquidacionIndividual — dispara `ReconciliarLiquidacion` para una
sola liquidación, desde la pantalla de detalle al abrirla (a diferencia de
`SincronizarLiquidaciones`, que recorre todos los prestadores vinculados).

Best-effort a propósito: si la liquidación no tiene vínculo AyC, el prestador
no está vinculado, AyC ya no la reporta, o el SOAP de incidentes falla, no hace
nada y no propaga error — abrir el detalle nunca debe fallar por esto, es un
refresh silencioso, no una acción explícita del usuario.

Si la liquidación está en estado terminal (aprobada/cerrada) se salta el
listado de incidentes (`get_incidentes`, no hace falta, `ReconciliarLiquidacion`
lo ignoraría igual) pero se delega igual — el extra/factura sí se intenta traer
para liquidaciones terminales, ver docstring de `ReconciliarLiquidacion`.
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._cd_mapping import a_importado
from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacion,
    ReconciliarLiquidacionResultado,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_APROBADA, ESTADO_CERRADA
from src.modules.liquidaciones.domain.repositories.cd_liquidaciones_gateway import (
    CdLiquidacionesGateway,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.shared.domain.errors import ExternalServiceError

_ESTADOS_TERMINALES = frozenset({ESTADO_APROBADA, ESTADO_CERRADA})
_SIN_RECONCILIAR = ReconciliarLiquidacionResultado(reconciliada=False)


@dataclass(frozen=True)
class ReconciliarLiquidacionIndividualPorts:
    liquidaciones: LiquidacionRepository
    prestadores: PrestadorRepository
    cd_gateway: CdLiquidacionesGateway
    reconciliar: ReconciliarLiquidacion


class ReconciliarLiquidacionIndividual:
    def __init__(self, ports: ReconciliarLiquidacionIndividualPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID) -> ReconciliarLiquidacionResultado:
        liquidacion = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liquidacion is None or not liquidacion.numero_liquidacion:
            return _SIN_RECONCILIAR

        prestador = await self._ports.prestadores.get_by_id(liquidacion.prestador_id)
        if prestador is None or prestador.cd_prestador_id is None:
            return _SIN_RECONCILIAR

        cd_liqs = await self._ports.cd_gateway.get_liquidaciones(prestador.cd_prestador_id)
        cd_liq = next(
            (c for c in cd_liqs if c.numero_liquidacion == liquidacion.numero_liquidacion), None
        )
        if cd_liq is None:
            return _SIN_RECONCILIAR

        if liquidacion.estado in _ESTADOS_TERMINALES:
            return await self._ports.reconciliar.execute(liquidacion, cd_liq, [])

        try:
            filas_cd = await self._ports.cd_gateway.get_incidentes(cd_liq.id)
        except ExternalServiceError:
            return _SIN_RECONCILIAR

        remotos = [a_importado(r) for r in filas_cd]
        return await self._ports.reconciliar.execute(liquidacion, cd_liq, remotos)
