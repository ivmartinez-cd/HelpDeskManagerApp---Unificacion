"""Mapeo zona-Siges → zona-local del tarifario, por prestador (ADR-014).

`CostoServicio.descripcion` de Siges no coincide literalmente con la `zona` local
del tarifario; el sync solo sincroniza descripciones mapeadas acá (la 'Genérica'
mapea implícitamente a zona=None, sin fila). `zona_local=None` en un mapeo
explícito también significa zona genérica — es el caso mayoritario real: la
descripción de la mayoría de los PSTs es su código de tarifa (`TMTB122`, etc.)
y corresponde al grupo local sin zona. El mapeo puede ser N:1 del lado local
(Siges agrupa zonas que la planilla local separa) — cada descripción de Siges
vincula a lo sumo una zona local; las zonas locales extra quedan manuales.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TarifarioZonaMap:
    id: uuid.UUID
    prestador_id: uuid.UUID
    descripcion_siges: str
    zona_local: str | None
    created_at: datetime
