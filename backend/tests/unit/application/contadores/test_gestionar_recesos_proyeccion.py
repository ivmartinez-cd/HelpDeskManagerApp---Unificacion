from dataclasses import replace
from datetime import date

import pytest

from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.use_cases.gestionar_recesos_proyeccion import (
    CrearRecesoRequest,
    GestionarRecesosProyeccionUseCase,
)
from src.modules.contadores.domain.errors import RecesoRangoInvalidoError


class _StoreEnMemoria:
    def __init__(self) -> None:
        self.recesos: list[RecesoDto] = []

    async def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        return [r for r in self.recesos if r.id_grupo_economico == id_grupo_economico]

    async def crear(self, receso_sin_id: RecesoDto) -> RecesoDto:
        receso = replace(receso_sin_id, id=len(self.recesos) + 1)
        self.recesos.append(receso)
        return receso

    async def eliminar(self, id_receso: int) -> None:
        self.recesos = [r for r in self.recesos if r.id != id_receso]


def _request(desde: date, hasta: date) -> CrearRecesoRequest:
    return CrearRecesoRequest(
        id_grupo_economico=417,
        id_anexo=None,
        fecha_desde=desde,
        fecha_hasta=hasta,
        descripcion="Receso de verano",
    )


async def test_crea_receso_de_un_dia_o_de_varios() -> None:
    store = _StoreEnMemoria()
    use_case = GestionarRecesosProyeccionUseCase(store)

    un_dia = await use_case.crear(_request(date(2026, 12, 26), date(2026, 12, 26)))
    varios = await use_case.crear(_request(date(2026, 12, 26), date(2027, 1, 5)))

    assert un_dia.id == 1
    assert varios.id == 2
    assert len(await use_case.listar(417)) == 2


async def test_rechaza_receso_con_fecha_desde_posterior_a_fecha_hasta() -> None:
    store = _StoreEnMemoria()

    with pytest.raises(RecesoRangoInvalidoError):
        await GestionarRecesosProyeccionUseCase(store).crear(
            _request(date(2026, 12, 28), date(2026, 12, 26))
        )

    assert store.recesos == []
