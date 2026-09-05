"""Resultado de correr el motor de reglas sobre una liquidación.

`Hallazgo` es la salida cruda de un evaluador (descripción + contexto); el orquestador
la envuelve en `AlertaGenerada` con el código/riesgo de la regla. `IncidenteEvaluado`
es el enriquecimiento de "esperado" que el legacy aplicaba mutando el ORM in-place
(`incidente.costo_servicio_esperado = ...`) — acá se devuelve como dato porque las
entidades de dominio son inmutables; la aplicación decide cómo persistirlo.
"""

import uuid
from dataclasses import dataclass, field
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
    # Ex `ObservacionGenerada` (ver `domain/entities/alerta.py`) — hoy solo lo
    # arma `alt005_ruta.py::evaluar_grupo_alt005`.
    es_grupo: bool = False
    grupo_incidente_ids: tuple[uuid.UUID, ...] = field(default_factory=tuple)
    monto_cobrado: float | None = None
    monto_esperado: float | None = None
    diferencia: float | None = None


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
