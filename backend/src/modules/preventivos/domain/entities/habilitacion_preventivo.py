import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, eq=False)
class HabilitacionPreventivo:
    """Marca LOCAL de "equipo habilitado para despachar preventivo" — no
    escribe nada en Gestión/Siges (decisión de alcance v1, ver ADR del módulo).
    El FK a la máquina es lógico (`siges_maquina_id`, int de Siges): no hay
    tabla local de máquinas. `habilitado_por_nombre` es snapshot del nombre al
    momento de habilitar, para mostrar la auditoría sin join contra auth.
    Se desactiva a mano (queda `deshabilitado_por` con el nombre del usuario)
    o sola cuando aparece un preventivo cerrado posterior a la habilitación
    (`deshabilitado_por` = etiqueta de sistema)."""

    id: uuid.UUID
    siges_maquina_id: int
    habilitado_por_user_id: uuid.UUID
    habilitado_por_nombre: str
    habilitado_en: datetime
    nota: str | None
    activa: bool
    deshabilitado_en: datetime | None
    deshabilitado_por: str | None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, HabilitacionPreventivo) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
