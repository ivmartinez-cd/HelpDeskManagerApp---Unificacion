"""Jefe de sector: en Personas solo ve y toca gente de su sector."""

import uuid
from dataclasses import replace

from src.modules.personas.application.use_cases.alcance_sector import PersonasDelSector
from src.modules.personas.domain.entities.persona import Persona
from src.modules.personas.domain.repositories.persona_repository import (
    FiltrosPersonas,
    OrdenPersonas,
)
from tests.unit.application.personas.fakes import make_persona

TALLER = uuid.uuid4()
MESA = uuid.uuid4()


class _RepoQueFiltraPorSector:
    def __init__(self, personas: list[Persona]) -> None:
        self._personas = personas

    async def list_page(
        self, filtros: FiltrosPersonas, orden: OrdenPersonas, *, page: int, size: int
    ) -> tuple[list[Persona], int]:
        todas = [p for p in self._personas if filtros.sector_id in (None, p.sector_id)]
        return todas, len(todas)

    async def get(self, persona_id: uuid.UUID) -> Persona | None:
        return next((p for p in self._personas if p.id == persona_id), None)


def _mundo() -> tuple[Persona, Persona, _RepoQueFiltraPorSector]:
    del_taller = replace(make_persona(email="t@canal.com"), sector_id=TALLER)
    de_mesa = replace(make_persona(email="m@canal.com"), sector_id=MESA)
    return del_taller, de_mesa, _RepoQueFiltraPorSector([del_taller, de_mesa])


async def test_sin_sector_ve_a_todos() -> None:
    del_taller, de_mesa, base = _mundo()
    repo = PersonasDelSector(base, None)

    personas, total = await repo.list_page(FiltrosPersonas(), OrdenPersonas(), page=1, size=50)

    assert total == 2
    assert await repo.get(de_mesa.id) is de_mesa


async def test_jefe_lista_solo_su_sector() -> None:
    del_taller, _, base = _mundo()
    repo = PersonasDelSector(base, TALLER)

    personas, total = await repo.list_page(FiltrosPersonas(), OrdenPersonas(), page=1, size=50)

    assert personas == [del_taller] and total == 1


async def test_jefe_que_filtra_por_otro_sector_no_ve_nada() -> None:
    _, _, base = _mundo()
    repo = PersonasDelSector(base, TALLER)

    filtros = FiltrosPersonas(sector_id=MESA)
    assert await repo.list_page(filtros, OrdenPersonas(), page=1, size=50) == ([], 0)


async def test_persona_de_otro_sector_es_inexistente_para_el_jefe() -> None:
    del_taller, de_mesa, base = _mundo()
    repo = PersonasDelSector(base, TALLER)

    assert await repo.get(de_mesa.id) is None
    assert await repo.get(del_taller.id) is del_taller
