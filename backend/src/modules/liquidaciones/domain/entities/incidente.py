"""Incidente cobrado dentro de una liquidación — incidentes.

Los campos `*_cobrado` vienen del CSV del prestador; los `*_esperado` los calcula el
motor de reglas al validar (quedan `None` hasta la primera corrida). `estado_validacion`
lo fija `ejecutar_motor`: "con_alertas" si generó al menos una `Alerta`, "ok" si no.
"""

import uuid
from dataclasses import dataclass
from datetime import date

ESTADO_VALIDACION_PENDIENTE = "pendiente"
ESTADO_VALIDACION_OK = "ok"
ESTADO_VALIDACION_CON_ALERTAS = "con_alertas"


@dataclass(frozen=True)
class Incidente:
    id: uuid.UUID
    liquidacion_id: uuid.UUID
    numero_incidente: str
    rubro: str | None
    tipo: str
    empresa_nombre: str | None
    sucursal_nombre: str | None
    nro_serie: str | None
    fecha_cierre: date | None
    costo_servicio_cobrado: float
    cant_km_cobrado: float
    costo_km_cobrado: float
    total_viaje_cobrado: float
    costo_total_cobrado: float
    pasa_it: bool
    costo_servicio_esperado: float | None
    cant_km_esperado: float | None
    costo_km_esperado: float | None
    estado_validacion: str
