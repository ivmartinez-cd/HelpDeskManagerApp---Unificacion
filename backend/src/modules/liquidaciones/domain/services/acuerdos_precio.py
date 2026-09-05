"""Resolución del acuerdo de precio que aplica a un incidente (ALT001)."""

import unicodedata
from collections.abc import Sequence
from datetime import date

from src.modules.liquidaciones.domain.entities.acuerdo_precio_cliente import (
    AcuerdoPrecioCliente,
)
from src.modules.liquidaciones.domain.entities.incidente import Incidente


def normalizar_empresa(nombre: str | None) -> str:
    sin_acentos = (
        unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode("ascii")
    )
    return " ".join(sin_acentos.lower().split())


def resolver_acuerdo(
    incidente: Incidente, acuerdos: Sequence[AcuerdoPrecioCliente]
) -> AcuerdoPrecioCliente | None:
    """El acuerdo vigente a la fecha de cierre para el cliente del incidente;
    uno específico del tipo de servicio gana sobre el general, y entre iguales
    el de vigencia más reciente."""
    fecha = incidente.fecha_cierre
    empresa = normalizar_empresa(incidente.empresa_nombre)
    if fecha is None or not empresa:
        return None
    candidatos = [a for a in acuerdos if _aplica(a, empresa, incidente.tipo, fecha)]
    if not candidatos:
        return None
    return max(candidatos, key=lambda a: (a.tipo_servicio is not None, a.vigencia_desde))


def _aplica(a: AcuerdoPrecioCliente, empresa: str, tipo: str, fecha: date) -> bool:
    return (
        normalizar_empresa(a.empresa_nombre) == empresa
        and (a.tipo_servicio is None or a.tipo_servicio == tipo)
        and a.vigencia_desde <= fecha
        and (a.vigencia_hasta is None or fecha <= a.vigencia_hasta)
    )
