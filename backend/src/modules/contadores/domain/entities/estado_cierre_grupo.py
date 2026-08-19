"""Estado real de cierre por grupo económico de Siges: misma definición de
"pendiente" que `AnexoPendiente` (Facturado=0 AND ListoParaFacturar=0 —
regla de la TL, 2026-08-14), pero SIN dejar afuera el mes en curso: acá
interesa el grupo aunque su período abierto ya sea el actual, porque eso es
justo lo que indica que el cliente avanzó y no sigue "sin cerrar". Es la
señal para decidir si un cliente del backlog de calendario sigue sin cerrar
o ya cerró/rodó al mes en curso."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EstadoCierreGrupo:
    grupo: str
    # True si al menos uno de sus anexos de Impresión activos sigue
    # pendiente (mismo criterio que el reporte de anexos sin facturar) de un
    # período anterior al mes en curso.
    sin_cerrar: bool


@dataclass(frozen=True)
class EstadoCierreGruposSnapshot:
    """Universo completo de grupos con anexos de Impresión activos — no solo
    los pendientes. Se sirve cacheado (TTL en el gateway)."""

    grupos: list[EstadoCierreGrupo]
    consultado_en: datetime
