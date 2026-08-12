"""Catálogo de reglas del motor de alertas — reglas_alerta.

Data-driven solo a medias: `activa`/`riesgo_base`/algunos parámetros de
`configuracion` vienen de esta tabla, pero el algoritmo de cada regla es código Python
fijo (un evaluador por código, ver `application/motor_reglas.py` cuando se porte) — no
hay motor de expresiones interpretado. ALT006/ALT007 son códigos válidos sin evaluador
(nunca se ejecutan); ALT005 queda con `activa=False` por default, igual que el legacy —
decisiones de alcance confirmadas por el usuario, ver
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §6.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

CODIGO_ALT001_PRECIO_INCORRECTO = "ALT001"
CODIGO_ALT002_KMS_INCORRECTOS = "ALT002"
CODIGO_ALT003_VIATICO_DUPLICADO = "ALT003"
CODIGO_ALT004_SERVICIO_DUPLICADO = "ALT004"
CODIGO_ALT005_RUTA_COMPARTIDA = "ALT005"
CODIGO_ALT006_SEGUNDA_VISITA = "ALT006"
CODIGO_ALT007_AGRUPACION_INCIDENTES = "ALT007"
CODIGO_ALT008_TARIFARIO_INEXISTENTE = "ALT008"
CODIGO_ALT009_PAR_EMPRESA_SUCURSAL = "ALT009"

# Códigos con evaluador implementado — ALT006/ALT007 quedan afuera a propósito.
CODIGOS_CON_EVALUADOR = frozenset(
    {
        CODIGO_ALT001_PRECIO_INCORRECTO,
        CODIGO_ALT002_KMS_INCORRECTOS,
        CODIGO_ALT003_VIATICO_DUPLICADO,
        CODIGO_ALT004_SERVICIO_DUPLICADO,
        CODIGO_ALT005_RUTA_COMPARTIDA,
        CODIGO_ALT008_TARIFARIO_INEXISTENTE,
        CODIGO_ALT009_PAR_EMPRESA_SUCURSAL,
    }
)


@dataclass(frozen=True)
class ReglaAlerta:
    id: uuid.UUID
    codigo: str
    nombre: str
    descripcion: str | None
    activa: bool
    riesgo_base: float
    configuracion: dict[str, Any]
    created_at: datetime
    updated_at: datetime
