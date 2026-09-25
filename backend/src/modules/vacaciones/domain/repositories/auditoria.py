"""Puertos de auditoría. El de escritura (`RegistradorAuditoria`) va bound al
usuario actuante (lo construye presentation); los use cases solo dicen QUÉ
pasó. Nunca debe lanzar: la auditoría no puede romper el flujo principal
(paridad con recordAudit del legacy) — el contrato exige que la implementación
atrape y loguee sus propios errores.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal, Protocol

from src.modules.vacaciones.domain.entities.registro_auditoria import RegistroAuditoria


class RegistradorAuditoria(Protocol):
    async def registrar(
        self,
        accion: str,
        entidad: str,
        entidad_id: str | None,
        metadata: dict[str, object],
    ) -> None: ...


class RegistradorAuditoriaNulo:
    """Default para tests / contextos sin auditoría."""

    async def registrar(
        self,
        accion: str,
        entidad: str,
        entidad_id: str | None,
        metadata: dict[str, object],
    ) -> None:
        return None


@dataclass(frozen=True, slots=True)
class FiltrosAuditoria:
    """`search` matchea acción, entidad o email del usuario (ilike)."""

    search: str | None = None
    entidad: str | None = None
    accion: str | None = None
    desde: date | None = None
    hasta: date | None = None


CampoOrdenAuditoria = Literal["fecha", "accion", "entidad", "usuario"]


@dataclass(frozen=True, slots=True)
class OrdenAuditoria:
    """Columna de la tabla por la que se ordena. Acción y entidad ordenan por
    su etiqueta en castellano (la que ve el usuario), no por el código legacy;
    los registros sin usuario van al final en ambos sentidos."""

    campo: CampoOrdenAuditoria = "fecha"
    descendente: bool = True


ORDEN_POR_DEFECTO = OrdenAuditoria()


class AuditoriaRepository(Protocol):
    async def list_pagina(
        self,
        filtros: FiltrosAuditoria,
        *,
        offset: int,
        limit: int,
        orden: OrdenAuditoria = ORDEN_POR_DEFECTO,
    ) -> tuple[list[RegistroAuditoria], int]:
        """Página en el orden pedido (empates: más nuevo primero) + total."""
        ...
