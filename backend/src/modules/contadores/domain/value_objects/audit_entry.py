from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Una fila de la hoja "Auditoria": explica si una lectura se usó (y por
    qué) o se descartó al calcular la proyección de `serie`/`clase`."""

    serie: str
    clase: str
    fecha: date | None
    contador: int | None
    tipo_contador: str | None
    usado: bool
    motivo: str
