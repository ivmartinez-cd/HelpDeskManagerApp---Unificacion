import uuid
from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class Prestador:
    """Un Prestador de Servicio Técnico (PST) — vinculado a Siges por
    `siges_empresa_id` (el mismo `ID_Empresa`/`ID_Tecnico` que usa el módulo
    sla), no por nombre: la denominación comercial de Siges no coincide con
    el nombre de contacto que se maneja puertas adentro."""

    id: uuid.UUID
    siges_empresa_id: int
    den_comercial: str
    razon_social: str | None
    cuit: str | None
    equipos: int | None
    operador_id: uuid.UUID | None
    is_active: bool

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Prestador) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
