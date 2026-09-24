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

    async def listar_para_proceso(self, id_anexo: int, ids_grupo: list[int]) -> list[RecesoDto]:
        return [
            r for r in self.recesos if r.id_anexo == id_anexo or r.id_grupo_economico in ids_grupo
        ]

    async def actualizar(self, receso: RecesoDto) -> RecesoDto | None:
        if not any(r.id == receso.id for r in self.recesos):
            return None
        self.recesos = [receso if r.id == receso.id else r for r in self.recesos]
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


async def test_editar_pisa_los_campos_y_valida_el_rango() -> None:
    store = _StoreEnMemoria()
    use_case = GestionarRecesosProyeccionUseCase(store)
    creado = await use_case.crear(_request(date(2026, 12, 26), date(2026, 12, 26)))

    editado = await use_case.actualizar(creado.id, _request(date(2026, 12, 20), date(2026, 12, 31)))

    assert editado is not None
    esperado = replace(creado, fecha_desde=date(2026, 12, 20), fecha_hasta=date(2026, 12, 31))
    assert store.recesos == [esperado]
    with pytest.raises(RecesoRangoInvalidoError):
        await use_case.actualizar(creado.id, _request(date(2026, 12, 31), date(2026, 12, 20)))


async def test_editar_un_receso_inexistente_devuelve_none() -> None:
    use_case = GestionarRecesosProyeccionUseCase(_StoreEnMemoria())

    assert await use_case.actualizar(99, _request(date(2026, 12, 26), date(2026, 12, 26))) is None


async def test_descripcion_es_opcional() -> None:
    request = CrearRecesoRequest(417, None, date(2026, 12, 26), date(2026, 12, 26))

    creado = await GestionarRecesosProyeccionUseCase(_StoreEnMemoria()).crear(request)

    assert creado.descripcion == ""
