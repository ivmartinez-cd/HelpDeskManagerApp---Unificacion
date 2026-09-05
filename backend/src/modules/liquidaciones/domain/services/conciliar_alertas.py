"""Conciliación de alertas entre re-análisis.

El motor regenera el set completo de alertas en cada corrida
(`replace_for_liquidacion` borra y crea). Sin conciliación, el triage de la TL
(resolver/descartar con justificación) se perdería en cada "Re-analizar". Regla:

- La alerta equivalente conserva `estado` y `justificacion` si la TL ya la
  trabajó (estado ≠ pendiente). La clave de equivalencia es `(tipo_alerta,
  incidente_id)` para una alerta 1:1, o `(tipo_alerta, frozenset(incidentes
  del grupo))` para una alerta agrupada (`es_grupo=True`, ex `Observacion` —
  ver `domain/entities/alerta.py`): si el grupo exacto vuelve a formarse, es
  "la misma" alerta; si cambia un miembro, es una alerta nueva (mismo criterio
  que ya regía para las 1:1, ahora extendido).
- Una alerta trabajada que el motor ya no genera PORQUE SU REGLA SIGUE ACTIVA
  desaparece: el dato que la causaba se corrigió, así que la decisión quedó
  obsoleta. Pero si dejó de generarse porque la regla se desactivó (no porque
  el dato cambió), la alerta trabajada se preserva tal cual — desactivar una
  regla no debe borrar el triage ya hecho sobre alertas que siguen siendo
  válidas, solo evita que se generen alertas nuevas de ese tipo.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from src.modules.liquidaciones.domain.entities.alerta import ESTADO_PENDIENTE, Alerta
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada

_Clave = tuple[str, uuid.UUID | frozenset[uuid.UUID]]


@dataclass(frozen=True)
class AlertaConciliada:
    """Alerta del motor + la decisión previa de la TL que sobrevive al re-análisis."""

    generada: AlertaGenerada
    estado: str
    justificacion: str | None
    incidente_relacionado_id: uuid.UUID | None = None


def _clave(
    tipo_alerta: str,
    incidente_id: uuid.UUID,
    es_grupo: bool,
    grupo_incidente_ids: Sequence[uuid.UUID],
) -> _Clave:
    if es_grupo:
        return (tipo_alerta, frozenset(grupo_incidente_ids))
    return (tipo_alerta, incidente_id)


def conciliar_alertas(
    existentes: list[Alerta],
    nuevas: Sequence[AlertaGenerada],
    codigos_reglas_activas: set[str] | None = None,
) -> list[AlertaConciliada]:
    trabajadas = {
        _clave(a.tipo_alerta, a.incidente_id, a.es_grupo, a.grupo_incidente_ids): a
        for a in existentes
        if a.estado != ESTADO_PENDIENTE
    }
    conciliadas, claves_nuevas = _conciliar_nuevas(nuevas, trabajadas)
    if codigos_reglas_activas is not None:
        conciliadas.extend(
            _preservar_desactivadas(trabajadas, claves_nuevas, codigos_reglas_activas)
        )
    return conciliadas


def _conciliar_nuevas(
    nuevas: Sequence[AlertaGenerada], trabajadas: dict[_Clave, Alerta]
) -> tuple[list[AlertaConciliada], set[_Clave]]:
    conciliadas = []
    claves_nuevas: set[_Clave] = set()
    for nueva in nuevas:
        clave = _clave(
            nueva.tipo_alerta, nueva.incidente_id, nueva.es_grupo, nueva.grupo_incidente_ids
        )
        claves_nuevas.add(clave)
        previa = trabajadas.get(clave)
        conciliadas.append(AlertaConciliada(
            generada=nueva,
            estado=previa.estado if previa else ESTADO_PENDIENTE,
            justificacion=previa.justificacion if previa else None,
            incidente_relacionado_id=previa.incidente_relacionado_id if previa else None,
        ))
    return conciliadas, claves_nuevas


def _regenerar(previa: Alerta) -> AlertaConciliada:
    return AlertaConciliada(
        generada=AlertaGenerada(
            incidente_id=previa.incidente_id,
            tipo_alerta=previa.tipo_alerta,
            descripcion=previa.descripcion or "",
            riesgo=previa.riesgo,
            datos_contexto=previa.datos_contexto or {},
            es_grupo=previa.es_grupo,
            grupo_incidente_ids=previa.grupo_incidente_ids,
            monto_cobrado=previa.monto_cobrado,
            monto_esperado=previa.monto_esperado,
            diferencia=previa.diferencia,
        ),
        estado=previa.estado,
        justificacion=previa.justificacion,
        incidente_relacionado_id=previa.incidente_relacionado_id,
    )


def _preservar_desactivadas(
    trabajadas: dict[_Clave, Alerta],
    claves_nuevas: set[_Clave],
    codigos_reglas_activas: set[str],
) -> list[AlertaConciliada]:
    return [
        _regenerar(previa)
        for clave, previa in trabajadas.items()
        if clave not in claves_nuevas and previa.tipo_alerta not in codigos_reglas_activas
    ]
