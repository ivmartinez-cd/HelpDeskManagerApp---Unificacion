"""Sub-Prestador de Servicio Técnico (SPST) — spsts.

Sucursal/filial de un `Prestador` (ej. las distintas bases de INFOMAC en Villa Mercedes
y Gral. Roca/Neuquén) — resuelve el domicilio real usado por `TablaKM`, y es la fila que
`Tarifario.spst_id` referencia directamente para el precio (ya no hay un campo "zona"
intermedio compartido entre las dos entidades).
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
    # Texto libre, SOLO para que "Vincular SPST" sugiera coincidencias por
    # localidad al alta de una fila de Tabla KM — no tiene ningún efecto sobre
    # qué tarifa se le cobra a un incidente (eso lo decide `Tarifario.spst_id`
    # directo). Se llamó "zona" hasta 2026-09; se renombró para que no se
    # confunda con eso.
    zona_cobertura: str | None
    activo: bool
    created_at: datetime
    # Vínculo a `dbo.Empresa` de Siges (ADR-014) — None = sin vincular.
    siges_empresa_id: int | None = None
    # Sucursal propia del PST desde la que este SPST despacha — determina el
    # origen de las distancias en el recálculo por fila. None = usa base default del PST.
    siges_base_sucursal_id: int | None = None
