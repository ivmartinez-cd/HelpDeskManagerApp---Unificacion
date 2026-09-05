"""Liquidaciones de abono (`TIPO_ABONO`): contrato mensual donde el prestador
cierra cada incidente a $1 y carga el importe real como ítem extra en AyC
(caso SAN JUAN desde 2026: "Mantenimiento Técnico Centro Cívico", "Recursos
adicionales Escuelas", "Adicional Factura Servicios Cívico" — 31 liquidaciones
reales con exactamente este patrón, ver
`docs/liquidaciones/REDISENO_REVISION_LIQUIDACIONES.md` §6). El legacy ya las
distinguía por el nombre del CSV (`_CC.xls` / `_PRECO.xls`).

Para un abono, las reglas de precio/km por incidente no dicen nada (todo vale
$1 a propósito): generaban 105 ALT001 por mes que nadie miraba. Se apagan; los
duplicados (ALT004/ALT010) siguen, porque un incidente repetido sigue siendo un
error. El monto del abono varía todo el tiempo (decisión del usuario
2026-09-05: no se alerta por monto), así que lo único que se controla es que el
extra esté cargado — eso lo muestra la UI, no el motor.

La detección es automática (decisión 1A del usuario): todos los incidentes a
$1 de servicio."""

from collections.abc import Mapping, Sequence
from typing import Protocol

from src.modules.liquidaciones.domain.entities.liquidacion import TIPO_ABONO, TIPO_REGULAR
from src.modules.liquidaciones.domain.entities.regla_alerta import (
    CODIGO_ALT001_PRECIO_INCORRECTO,
    CODIGO_ALT002_KMS_INCORRECTOS,
    CODIGO_ALT003_VIATICO_DUPLICADO,
    CODIGO_ALT005_RUTA_COMPARTIDA,
    CODIGO_ALT008_TARIFARIO_INEXISTENTE,
    CODIGO_ALT009_PAR_EMPRESA_SUCURSAL,
    ReglaAlerta,
)

COSTO_SERVICIO_ABONO = 1.0

REGLAS_APAGADAS_EN_ABONO = frozenset(
    {
        CODIGO_ALT001_PRECIO_INCORRECTO,
        CODIGO_ALT002_KMS_INCORRECTOS,
        CODIGO_ALT003_VIATICO_DUPLICADO,
        CODIGO_ALT005_RUTA_COMPARTIDA,
        CODIGO_ALT008_TARIFARIO_INEXISTENTE,
        CODIGO_ALT009_PAR_EMPRESA_SUCURSAL,
    }
)


class _ConCostoServicio(Protocol):
    """`Incidente` (entidad) e `IncidenteImportado` (VO del sync), ambos frozen."""

    @property
    def costo_servicio_cobrado(self) -> float: ...


def es_abono(incidentes: Sequence[_ConCostoServicio]) -> bool:
    return bool(incidentes) and all(
        i.costo_servicio_cobrado == COSTO_SERVICIO_ABONO for i in incidentes
    )


def tipo_segun_incidentes(incidentes: Sequence[_ConCostoServicio]) -> str:
    return TIPO_ABONO if es_abono(incidentes) else TIPO_REGULAR


def reglas_aplicables(
    tipo_liquidacion: str, reglas_activas: Mapping[str, ReglaAlerta]
) -> dict[str, ReglaAlerta]:
    """Las reglas activas que corresponde correr para este tipo de liquidación."""
    if tipo_liquidacion != TIPO_ABONO:
        return dict(reglas_activas)
    return {c: r for c, r in reglas_activas.items() if c not in REGLAS_APAGADAS_EN_ABONO}
