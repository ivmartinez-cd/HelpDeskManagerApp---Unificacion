"""Estado real de cierre por grupo económico de Siges: a diferencia del
universo de `AnexoPendiente` (que a propósito deja afuera el mes en curso y
lo `A LIBERAR`, para el reporte que se imprime), acá interesa saber si el
grupo tiene TODAVÍA algún anexo de Impresión activo sin facturar de un
período anterior al actual — sin importar si ya está `A LIBERAR` o no. Es la
señal para decidir si un cliente sigue "sin cerrar" o ya cerró/rodó al mes
en curso."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EstadoCierreGrupo:
    grupo: str
    # True si al menos uno de sus anexos de Impresión activos tiene un
    # período abierto anterior al mes en curso y todavía no se facturó.
    sin_cerrar: bool


@dataclass(frozen=True)
class EstadoCierreGruposSnapshot:
    """Universo completo de grupos con anexos de Impresión activos — no solo
    los pendientes. Se sirve cacheado (TTL en el gateway)."""

    grupos: list[EstadoCierreGrupo]
    consultado_en: datetime
