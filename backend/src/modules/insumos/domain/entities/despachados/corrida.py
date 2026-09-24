"""Una ejecución del job de Despachados, programada o disparada con "Actualizar ahora"
(tabla `insumos_despacho_corrida`)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class OrigenCorrida(StrEnum):
    PROGRAMADA = "programada"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class ResumenCorrida:
    envios_nuevos: int = 0
    consultas_ok: int = 0
    consultas_error: int = 0
    error: str | None = None
    """Error que cortó la corrida entera (p. ej. Siges caído); None si terminó."""


@dataclass(frozen=True, slots=True)
class Corrida:
    id: int
    origen: OrigenCorrida
    iniciada_en: datetime
    usuario_nombre: str | None
    """Quién apretó "Actualizar ahora"; None en las programadas."""
    terminada_en: datetime | None = None
    """None mientras corre."""
    resumen: ResumenCorrida = field(default_factory=ResumenCorrida)
