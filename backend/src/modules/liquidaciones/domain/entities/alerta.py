"""Alerta generada por el motor de reglas — alertas / alerta_incidentes.

Hasta 2026-09 existían dos entidades separadas para esto: `Alerta` (1:1 con un
incidente) y `Observacion` (agrupaba N incidentes, con su propia máquina de
estados sin justificación obligatoria) — dos vocabularios casi idénticos para
la misma idea (auditoría de liquidaciones, hallazgo "Alertas vs. Observaciones
— dos máquinas de estado parecidas"). Se unificaron en esta sola entidad:
`es_grupo=False` es el caso de siempre (1:1 incidente×regla, `tipo_alerta` es
el código de `ReglaAlerta.codigo`); `es_grupo=True` es lo que antes era una
`Observacion` — hoy solo lo genera ALT005 agrupando por corredor
(`domain/services/motor_reglas/alt005_ruta.py`), con `incidente_id` como el
incidente "principal" del grupo y `grupo_incidente_ids` con todos (incluido el
principal). ALT006/ALT007 son códigos válidos del catálogo pero sin evaluador
implementado (nunca se genera una `Alerta` con esos códigos hoy — ver
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §3).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

ESTADO_PENDIENTE = "pendiente"
ESTADO_EN_REVISION = "en_revision"
ESTADO_RESUELTA = "resuelta"
ESTADO_DESCARTADA = "descartada"

# Rol de cada incidente dentro de un grupo (`es_grupo=True`) — ex `Observacion`.
ROL_PRINCIPAL = "principal"
ROL_REFERENCIA = "referencia"


@dataclass(frozen=True)
class Alerta:
    id: uuid.UUID
    incidente_id: uuid.UUID
    liquidacion_id: uuid.UUID
    tipo_alerta: str
    descripcion: str | None
    datos_contexto: dict[str, Any] | None
    riesgo: float
    estado: str
    fecha_generacion: datetime
    # Motivo de la decisión de la TL — obligatorio al descartar; el re-análisis
    # lo preserva junto con el estado (ver `conciliar_alertas`).
    justificacion: str | None = None
    # Otro incidente de la misma liquidación donde en realidad se cobraron los
    # km de esta ruta compartida — vínculo MANUAL que la TL carga al gestionar
    # una alerta individual (`es_grupo=False`), preservado por el re-análisis
    # igual que justificacion. No confundir con `grupo_incidente_ids`: ese es
    # el agrupamiento que arma el propio motor, no una decisión de la TL.
    incidente_relacionado_id: uuid.UUID | None = None
    es_grupo: bool = False
    # Solo para `es_grupo=True` — todos los incidentes del grupo, incluido el
    # principal (`incidente_id`). Vacía para alertas 1:1.
    grupo_incidente_ids: tuple[uuid.UUID, ...] = field(default_factory=tuple)
    # Solo para `es_grupo=True` (antes exclusivos de `Observacion`) — montos
    # agregados del grupo. `None` para alertas 1:1.
    monto_cobrado: float | None = None
    monto_esperado: float | None = None
    diferencia: float | None = None
