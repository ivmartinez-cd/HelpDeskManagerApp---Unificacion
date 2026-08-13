"""Puertos de auditoría. El de escritura (`RegistradorAuditoria`) va bound al
usuario actuante (lo construye presentation); los use cases solo dicen QUÉ
pasó. Nunca debe lanzar: la auditoría no puede romper el flujo principal
(paridad con recordAudit del legacy) — el contrato exige que la implementación
atrape y loguee sus propios errores.
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

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


class AuditoriaRepository(Protocol):
    async def list_pagina(
        self, filtros: FiltrosAuditoria, *, offset: int, limit: int
    ) -> tuple[list[RegistroAuditoria], int]:
        """Página ordenada por created_at desc + total de la consulta."""
        ...
