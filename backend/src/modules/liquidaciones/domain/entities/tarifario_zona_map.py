"""Mapeo descripción-Siges → SPST del tarifario, por prestador (ADR-014).

`CostoServicio.descripcion` de Siges no coincide literalmente con ningún dato
local; el sync solo sincroniza descripciones mapeadas acá (la 'Genérica'
mapea implícitamente a `spst_id=None`, tarifa sin SPST específico). Hasta
2026-09 el destino del mapeo era `zona_local` (texto); ahora es `spst_id`
directo, consistente con `Tarifario.spst_id`. `spst_id=None` en un mapeo
explícito también significa genérica — es el caso mayoritario real: la
descripción de la mayoría de los PSTs es su código de tarifa (`TMTB122`, etc.)
y corresponde al grupo genérico. El mapeo puede ser N:1 del lado local (Siges
agrupa bajo una descripción zonas que acá están separadas en varios SPST) —
cada descripción de Siges vincula a lo sumo un SPST; los SPST extra quedan
manuales. El nombre de la clase quedó de cuando mapeaba a una zona de texto —
no se renombró para no arrastrar el cambio a los 11 archivos que la usan.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TarifarioZonaMap:
    id: uuid.UUID
    prestador_id: uuid.UUID
    descripcion_siges: str
    spst_id: uuid.UUID | None
    created_at: datetime
