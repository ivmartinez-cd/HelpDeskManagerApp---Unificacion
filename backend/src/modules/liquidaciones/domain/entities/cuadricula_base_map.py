"""Mapeo cuadrícula-Siges → sucursal-base del PST (Cod. Agrupación en Gestión).

Cuando un PST opera desde más de una sede, cada cuadrícula de Siges indica qué
técnico/base cubre ese grupo de sucursales cliente. El mapeo persiste localmente
(Siges no tiene una FK explícita cuadrícula → base); se configura una vez y el
cálculo de distancias lo usa automáticamente."""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CuadriculaBaseMap:
    id: uuid.UUID
    prestador_id: uuid.UUID
    cuadricula: str
    siges_base_sucursal_id: int
    created_at: datetime
