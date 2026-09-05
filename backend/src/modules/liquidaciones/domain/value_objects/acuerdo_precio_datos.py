"""Datos editables de un acuerdo de precio por cliente (alta y edición)."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AcuerdoPrecioDatos:
    empresa_nombre: str
    tipo_servicio: str | None
    factor: float | None
    precio_fijo: float | None
    motivo: str
    vigencia_desde: date
    vigencia_hasta: date | None
