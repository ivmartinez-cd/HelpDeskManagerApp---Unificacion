"""Clientes (grupos económicos) con anexo de Impresión activo pendiente
(Facturado=0 AND ListoParaFacturar=0) de EXACTAMENTE el período inmediato
anterior al mes en curso — el arrastre real del cierre que acaba de pasar
para la card de Inicio, independiente del backlog de calendario de Gestión
(ver `get_pending_clients.py`, que sí puede fluctuar por eventos que
entran/salen de su ventana móvil sin relación con facturación)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ClientesPendientesPeriodo:
    periodo: str
    grupos: tuple[str, ...]
    consultado_en: datetime

    @property
    def cantidad(self) -> int:
        return len(self.grupos)
