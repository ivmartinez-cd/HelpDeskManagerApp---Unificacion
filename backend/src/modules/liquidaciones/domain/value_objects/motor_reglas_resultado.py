"""Resultado de correr el motor de reglas sobre una liquidación.

`Hallazgo` es la salida cruda de un evaluador (descripción + contexto); el orquestador
la envuelve en `AlertaGenerada` con el código/riesgo de la regla. `IncidenteEvaluado`
es el enriquecimiento de "esperado" que el legacy aplicaba mutando el ORM in-place
(`incidente.costo_servicio_esperado = ...`) — acá se devuelve como dato porque las
entidades de dominio son inmutables; la aplicación decide cómo persistirlo.
"""

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Hallazgo:
    descripcion: str
    contexto: dict[str, Any]


@dataclass(frozen=True)
class AlertaGenerada:
    incidente_id: uuid.UUID
    tipo_alerta: str
    descripcion: str
    riesgo: float
    datos_contexto: dict[str, Any]


@dataclass(frozen=True)
class ObservacionGenerada:
    tipo_observacion: str
    severidad: str
    titulo: str
    descripcion: str
    monto_cobrado: float
    monto_esperado: float
    incidentes_relacionados: list[uuid.UUID]
    incidente_principal_id: uuid.UUID
    regla_codigo: str
    datos_contexto: dict[str, Any]


@dataclass(frozen=True)
class IncidenteEvaluado:
    incidente_id: uuid.UUID
    costo_servicio_esperado: float | None
    cant_km_esperado: float | None
    costo_km_esperado: float | None
    estado_validacion: str


@dataclass(frozen=True)
class ResultadoMotorReglas:
    incidentes_evaluados: list[IncidenteEvaluado]
    alertas: list[AlertaGenerada]
    observaciones: list[ObservacionGenerada]
