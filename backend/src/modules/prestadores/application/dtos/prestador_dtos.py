import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ContactoDTO:
    id: uuid.UUID
    prestador_id: uuid.UUID
    nombre: str
    telefono: str | None
    email: str | None
    is_principal: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class PrestadorDTO:
    id: uuid.UUID
    siges_empresa_id: int
    den_comercial: str
    razon_social: str | None
    cuit: str | None
    equipos: int | None
    operador_id: uuid.UUID | None
    operador_nombre: str | None
    operador_color: str | None
    is_active: bool
    contactos: list[ContactoDTO]


@dataclass(frozen=True, slots=True)
class OperadorGroupDTO:
    """Un grupo del listado agrupado por operador — `operador_id=None` es el
    grupo "Sin asignar", siempre al final."""

    operador_id: uuid.UUID | None
    operador_nombre: str | None
    operador_color: str | None
    prestadores: list[PrestadorDTO]


@dataclass(frozen=True, slots=True)
class PrestadoresResumenDTO:
    total_prestadores: int
    total_activos: int
    operadores_con_pst: int
    sin_asignar: int
    grupos: list[OperadorGroupDTO]


@dataclass(frozen=True, slots=True)
class AsignacionHistorialDTO:
    id: uuid.UUID
    operador_id: uuid.UUID | None
    operador_nombre: str | None
    desde: date
    hasta: date | None


@dataclass(frozen=True, slots=True)
class CreatePrestadorCommand:
    siges_empresa_id: int
    den_comercial: str
    razon_social: str | None = None
    cuit: str | None = None
    equipos: int | None = None
    operador_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class UpdatePrestadorCommand:
    """Solo los datos propios editables — la asignación de operador tiene su
    propio comando (`AssignOperadorCommand`) porque además escribe historial,
    y `is_active` tiene el suyo porque es una acción de alta/baja, no una
    edición de datos."""

    prestador_id: uuid.UUID
    den_comercial: str
    razon_social: str | None
    cuit: str | None
    equipos: int | None


@dataclass(frozen=True, slots=True)
class SetPrestadorActiveCommand:
    prestador_id: uuid.UUID
    is_active: bool


@dataclass(frozen=True, slots=True)
class AssignOperadorCommand:
    prestador_id: uuid.UUID
    operador_id: uuid.UUID | None
    desde: date


@dataclass(frozen=True, slots=True)
class UpsertContactoCommand:
    contacto_id: uuid.UUID | None
    prestador_id: uuid.UUID
    nombre: str
    telefono: str | None
    email: str | None
    is_principal: bool = False
    sort_order: int = 0


@dataclass(frozen=True, slots=True)
class SyncResultDTO:
    actualizados: list[str]
    sin_cambios: int


@dataclass(frozen=True, slots=True)
class CreateAsignacionOverrideCommand:
    operador_ausente_id: uuid.UUID
    operador_reemplazante_id: uuid.UUID
    desde: date
    hasta: date
    prestador_ids: list[uuid.UUID] | None
    """`None` = alcance TOTAL; lista vacía o con ids = alcance por PST puntual."""
    motivo: str | None
    created_by_user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class AsignacionOverrideDTO:
    id: uuid.UUID
    operador_ausente_id: uuid.UUID
    operador_ausente_nombre: str | None
    operador_reemplazante_id: uuid.UUID
    operador_reemplazante_nombre: str | None
    desde: date
    hasta: date
    alcance_total: bool
    prestador_ids: list[uuid.UUID]
    estado: str
    motivo: str | None
