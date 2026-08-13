"""Prestador de Servicio Técnico (PST) — prestadores.

Los 4 PST reales del negocio (Pentacom/Córdoba, Pertex-Supernova/Rosario,
Infomac/Villa Mercedes+Gral. Roca-Neuquén, Gestión Integral/San Juan) — ver
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` en la raíz del repo para el contexto
funcional completo.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Prestador:
    id: uuid.UUID
    nombre: str
    nombre_corto: str
    cuit: str | None
    region: str | None
    activo: bool
    created_at: datetime
    updated_at: datetime
    # Vínculo a `dbo.Empresa` de Siges (ADR-014) — None = sin vincular, fuera
    # del sync. Con default para no romper los constructores existentes.
    siges_empresa_id: int | None = None
