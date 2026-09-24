"""`RecesosEjemploStore`: mismo contrato que `SqlAlchemyRecesosRepository`
(`ListarParaProcesoAsync` y `ActualizarAsync` del legacy)."""

from datetime import date

from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.infrastructure.ejemplo.recesos_store import RecesosEjemploStore


def _receso(grupo: int, anexo: int | None) -> RecesoDto:
    return RecesoDto(0, grupo, anexo, date(2026, 4, 10), date(2026, 4, 12), "")


async def test_para_proceso_trae_los_del_anexo_aunque_sean_de_otro_grupo() -> None:
    """Receso cargado cuando el anexo 44 era del grupo 1; hoy es del 2."""
    store = RecesosEjemploStore()
    del_anexo = await store.crear(_receso(1, 44))
    del_grupo = await store.crear(_receso(2, None))
    await store.crear(_receso(3, 55))

    assert await store.listar_para_proceso(44, [2]) == [del_anexo, del_grupo]
    assert await store.listar(2) == [del_grupo]


async def test_actualizar_pisa_el_receso_y_sin_id_devuelve_none() -> None:
    store = RecesosEjemploStore()
    creado = await store.crear(_receso(2, None))
    editado = RecesoDto(creado.id, 2, 44, date(2026, 4, 1), date(2026, 4, 5), "Vacaciones")

    assert await store.actualizar(editado) == editado
    assert await store.listar(2) == [editado]
    inexistente = RecesoDto(99, 2, None, date(2026, 4, 1), date(2026, 4, 1), "")
    assert await store.actualizar(inexistente) is None
