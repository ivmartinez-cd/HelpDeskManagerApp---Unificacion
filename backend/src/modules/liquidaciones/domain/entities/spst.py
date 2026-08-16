"""Sub-Prestador de Servicio Técnico (SPST) — spsts.

Sucursal/filial de un `Prestador` (ej. las distintas bases de INFOMAC en Villa Mercedes
y Gral. Roca/Neuquén) — resuelve la zona/domicilio real usada por `TablaKM` y por el
motor de reglas para elegir tarifario.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Spst:
    id: uuid.UUID
    prestador_id: uuid.UUID
    nombre: str
    domicilio: str | None
    localidad: str | None
    provincia: str | None
    zona: str | None
    activo: bool
    created_at: datetime
    # Vínculo a `dbo.Empresa` de Siges (ADR-014) — None = sin vincular.
    siges_empresa_id: int | None = None
    # Sucursal propia del PST desde la que este SPST despacha — determina el
    # origen de las distancias en el recálculo por fila. None = usa base default del PST.
    siges_base_sucursal_id: int | None = None
