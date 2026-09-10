"""Registro histórico de un cambio que el prestador aplicó sobre una liquidación
ya importada — modificaciones_prestador (ver ADR-038).

A diferencia de una `Alerta` (un hallazgo recalculable que el motor de reglas
regenera entera en cada corrida, ver `domain/entities/alerta.py`), esto es un
evento que ya no es derivable del estado actual: el valor anterior desaparece en
cuanto `IncidenteRepository.update_cobrados`/`delete_by_ids` lo pisan o lo borran.
Por eso vive en tabla propia y nadie lo borra ni lo regenera — solo se marca
`vista_en` cuando la TL lo revisa."""

import uuid
from dataclasses import dataclass
from datetime import datetime

TIPO_ALTA = "alta"
TIPO_BAJA = "baja"
TIPO_MODIFICACION = "modificacion"


@dataclass(frozen=True)
class ModificacionPrestador:
    id: uuid.UUID
    liquidacion_id: uuid.UUID
    # Desnormalizado a propósito, sin FK al incidente: el registro de una `baja`
    # tiene que sobrevivir al borrado del incidente (`delete_by_ids`).
    numero_incidente: str
    tipo_cambio: str
    campo: str | None
    valor_anterior: str | None
    valor_nuevo: str | None
    detectada_en: datetime
    vista_en: datetime | None = None
