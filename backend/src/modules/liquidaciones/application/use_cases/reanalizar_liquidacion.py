"""Caso de uso ReanalizarLiquidacion — port de POST /liquidaciones/{id}/reanalize.

Re-corre el motor de reglas sobre una liquidación ya importada. El legacy
(`ejecutar_motor`) solo actualiza `total_alertas` al terminar — `total_incidentes` y
`total_importe` se fijan al importar y no se tocan acá (confirmado leyendo el router
real del legacy, ver la nota en `LiquidacionRepository.update_total_alertas`).

`estado_validacion` del incidente NO sale del `hallazgos` crudo del motor
(`motor.py::_evaluar_incidentes` solo sabe "encontre algo" / "no encontre nada",
ignora el triage previo de la TL) - sale de conciliar ese hallazgo con las alertas
ya resueltas/descartadas (`conciliar_alertas` + `recalcular_estado_incidente`), igual
que hace `ActualizarEstadoAlerta`. Sin esto, re-analizar una liquidacion reabre como
"con_alertas" incidentes que la TL ya habia cerrado - la alerta regenerada arrastra
su `estado` correctamente, pero el incidente quedaba desincronizado.
"""

from collections import defaultdict
from dataclasses import dataclass, replace
from uuid import UUID

from src.modules.liquidaciones.application.dtos.reanalizar_liquidacion import (
    ReanalizarLiquidacionResultado,
)
from src.modules.liquidaciones.domain.entities.incidente import (
    ESTADO_VALIDACION_OK,
    Incidente,
)
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.repositories.alerta_repository import AlertaRepository
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.observacion_repository import (
    ObservacionRepository,
)
from src.modules.liquidaciones.domain.repositories.regla_alerta_repository import (
    ReglaAlertaRepository,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.repositories.tarifario_repository import (
    TarifarioRepository,
)
from src.modules.liquidaciones.domain.services.conciliar_alertas import (
    AlertaConciliada,
    conciliar_alertas,
)
from src.modules.liquidaciones.domain.services.motor_reglas.motor import ejecutar_motor_reglas
from src.modules.liquidaciones.domain.services.triage_alertas import recalcular_estado_incidente
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    IncidenteEvaluado,
    ResultadoMotorReglas,
)


@dataclass(frozen=True)
class ReanalizarLiquidacionPorts:
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    alertas: AlertaRepository
    observaciones: ObservacionRepository
    reglas: ReglaAlertaRepository
    tablas_km: TablaKmRepository
    spsts: SpstRepository
    tarifarios: TarifarioRepository


class ReanalizarLiquidacion:
    def __init__(self, ports: ReanalizarLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID) -> ReanalizarLiquidacionResultado:
        liquidacion = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liquidacion is None:
            raise LiquidacionNoEncontradaError(liquidacion_id)

        incidentes = await self._ports.incidentes.list_by_liquidacion(liquidacion_id)
        resultado = await self._ejecutar_motor(liquidacion.prestador_id, incidentes)
        await self._persistir(liquidacion_id, resultado)

        return ReanalizarLiquidacionResultado(
            total_incidentes=len(incidentes),
            total_alertas=len(resultado.alertas),
            total_observaciones=len(resultado.observaciones),
        )

    async def _ejecutar_motor(
        self, prestador_id: UUID, incidentes: list[Incidente]
    ) -> ResultadoMotorReglas:
        incidentes_prestador = await self._ports.incidentes.list_by_prestador(prestador_id)
        reglas_activas = await self._ports.reglas.list_activas()
        tablas_km = await self._ports.tablas_km.list_by_prestador(prestador_id)
        spsts = await self._ports.spsts.list_by_prestador(prestador_id)
        tarifarios = await self._ports.tarifarios.list_by_prestador(prestador_id)
        return ejecutar_motor_reglas(
            incidentes, incidentes_prestador, reglas_activas, tablas_km, spsts, tarifarios
        )

    async def _persistir(self, liquidacion_id: UUID, resultado: ResultadoMotorReglas) -> None:
        # El triage previo de la TL (estado ≠ pendiente + justificación) sobrevive
        # al reemplazo — ver conciliar_alertas. El estado_validacion del incidente se
        # deriva de las alertas YA conciliadas, no del hallazgo crudo del motor.
        existentes = await self._ports.alertas.list_by_liquidacion(liquidacion_id)
        conciliadas = conciliar_alertas(existentes, resultado.alertas)
        incidentes_evaluados = _conciliar_estado_incidentes(
            resultado.incidentes_evaluados, conciliadas
        )
        await self._ports.incidentes.apply_evaluacion(incidentes_evaluados)
        await self._ports.alertas.replace_for_liquidacion(liquidacion_id, conciliadas)
        await self._ports.observaciones.replace_for_liquidacion(
            liquidacion_id, resultado.observaciones
        )
        await self._ports.liquidaciones.update_total_alertas(liquidacion_id, len(resultado.alertas))


def _conciliar_estado_incidentes(
    incidentes_evaluados: list[IncidenteEvaluado], conciliadas: list[AlertaConciliada]
) -> list[IncidenteEvaluado]:
    estados_por_incidente: dict[UUID, list[str]] = defaultdict(list)
    for c in conciliadas:
        estados_por_incidente[c.generada.incidente_id].append(c.estado)
    resultado = []
    for evaluado in incidentes_evaluados:
        estados = estados_por_incidente.get(evaluado.incidente_id, [])
        nuevo_estado = (
            recalcular_estado_incidente(estados) if estados else ESTADO_VALIDACION_OK
        )
        resultado.append(replace(evaluado, estado_validacion=nuevo_estado))
    return resultado
