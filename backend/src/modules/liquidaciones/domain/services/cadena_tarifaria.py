"""Cadena temporal de vigencias de tarifarios — port de `_rebuild_temporal_chain` del
legacy (`backend/app/api/routers/tarifarios.py`).

Dentro de un grupo (prestador, tipo_servicio, zona) cada tarifa debe cerrarse el día
anterior a la `vigencia_desde` de la siguiente; la última conserva la `vigencia_hasta`
que tenga (None = abierta). Sin esto se generan vigencias solapadas, que es justo lo
que ALT001/ALT008 usan para resolver el precio esperado."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tarifario import Tarifario


@dataclass(frozen=True)
class AjusteVigencia:
    tarifario_id: UUID
    vigencia_hasta: date


def recalcular_cadena(tarifas: list[Tarifario]) -> list[AjusteVigencia]:
    """Devuelve solo los ajustes necesarios (filas cuya `vigencia_hasta` cambia).

    Precondición: `tarifas` es un único grupo prestador+tipo_servicio+zona; acá no
    se re-agrupa."""
    ordenadas = sorted(tarifas, key=lambda t: t.vigencia_desde)
    ajustes = []
    for actual, siguiente in zip(ordenadas, ordenadas[1:], strict=False):
        nueva = siguiente.vigencia_desde - timedelta(days=1)
        if actual.vigencia_hasta != nueva:
            ajustes.append(AjusteVigencia(tarifario_id=actual.id, vigencia_hasta=nueva))
    return ajustes
