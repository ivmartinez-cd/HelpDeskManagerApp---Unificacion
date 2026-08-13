"""DTOs del vínculo y sync de configuración contra Siges (ADR-014)."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    TipoEmpresaSiges,
)

EntidadVinculable = Literal["prestador", "spst"]


@dataclass(frozen=True)
class SigesEmpresaDisponible:
    """Empresa activa en Siges sin vínculo local (reporte "disponible, no
    vinculada" del ADR-014 — nunca se auto-crea)."""

    siges_empresa_id: int
    den_comercial: str
    razon_social: str | None
    cuit: str | None
    tipo: TipoEmpresaSiges


@dataclass(frozen=True)
class PropuestaVinculo:
    entidad: EntidadVinculable
    local_id: UUID
    local_nombre: str
    siges_empresa_id: int
    siges_den_comercial: str


@dataclass(frozen=True)
class PropuestasVinculoResultado:
    propuestas: list[PropuestaVinculo]
    disponibles: list[SigesEmpresaDisponible]


@dataclass(frozen=True)
class SyncCambio:
    """Cambio de un campo espejo (hoy solo `cuit`) — aplicado, o a aplicar si
    el resultado es de un dry-run."""

    local_id: UUID
    local_nombre: str
    campo: str
    valor_anterior: str | None
    valor_nuevo: str | None


@dataclass(frozen=True)
class SyncDiferenciaNombre:
    """Nombre local ≠ Den_Comercial de Siges — informativo, nunca se pisa
    (el nombre local es curado a mano; ver política de conflictos del ADR-014)."""

    local_id: UUID
    local_nombre: str
    siges_den_comercial: str


@dataclass(frozen=True)
class SyncSigesResultado:
    dry_run: bool
    cambios: list[SyncCambio]
    nombres_distintos: list[SyncDiferenciaNombre]
    sin_cambios: int
    sin_vinculo: list[str]
    vinculo_roto: list[str]
