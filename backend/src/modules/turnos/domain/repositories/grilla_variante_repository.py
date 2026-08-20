import uuid
from datetime import date
from typing import Protocol

from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante


class GrillaVarianteRepository(Protocol):
    """Puerto de persistencia de grillas variantes (modo vacaciones, ADR-025)."""

    async def create(self, variante: GrillaVariante) -> None: ...

    async def update(self, variante: GrillaVariante) -> None:
        """Reemplaza cabecera, franjas y asignaciones (mismo `id`). No toca
        `created_by_user_id` ni `estado` -- la única transición es `cancelar`."""
        ...

    async def get_by_id(self, variante_id: uuid.UUID) -> GrillaVariante | None: ...

    async def list_all(self) -> list[GrillaVariante]: ...

    async def list_activas(self) -> list[GrillaVariante]:
        """Variantes con estado ACTIVA sin filtrar por fecha -- catálogo chico,
        el filtro de vigencia lo hacen las reglas de dominio."""
        ...

    async def find_vigente(self, fecha: date) -> GrillaVariante | None:
        """Variante ACTIVA con `desde <= fecha <= hasta`. Las reglas de alta
        garantizan que haya a lo sumo una."""
        ...

    async def cancelar(self, variante_id: uuid.UUID) -> None: ...
