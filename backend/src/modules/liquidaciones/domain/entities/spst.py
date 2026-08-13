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
    # Vínculo a `dbo.Empresa` de Siges (ADR-014) — None = sin vincular, fuera
    # del sync. Con default para no romper los constructores existentes.
    siges_empresa_id: int | None = None
