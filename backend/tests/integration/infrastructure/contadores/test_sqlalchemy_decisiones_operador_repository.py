"""Round-trip de la decisión vigente del operador (Proyección) contra Postgres:
una fila por (proceso, equipo, clase), que se pisa en cada acción ("último
gana"). Sin nota: la observación del operador es solo de la auditoría."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_decisiones_operador_repository import (  # noqa: E501
    SqlAlchemyDecisionesOperadorRepository,
)

_CLAVE = ClaveDecisionDto(nro_proceso=5501, id_maquina=777, clase="10")


async def test_pl_manual_se_guarda_con_ids_y_valores(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDecisionesOperadorRepository(db_session)
    partida = LecturaElegidaDto(date(2026, 1, 31), 40_000, 1, id_contador=11)
    llegada = LecturaElegidaDto(date(2026, 3, 2), 43_000, 4, id_contador=12, para_facturar=False)

    await repo.guardar(_CLAVE, DecisionOperadorDto("PL_Manual", partida, llegada))
    guardada = (await repo.listar_por_proceso(5501))[(777, "10")]

    assert guardada.accion == "PL_Manual"
    assert guardada.partida == partida
    assert guardada.llegada == llegada
    assert guardada.actualizado_en is not None


async def test_se_pisa_por_fila(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDecisionesOperadorRepository(db_session)
    partida = LecturaElegidaDto(date(2026, 1, 31), 40_000, 1, id_contador=11)
    llegada = LecturaElegidaDto(date(2026, 3, 2), 43_000, 1, id_contador=12)

    await repo.guardar(_CLAVE, DecisionOperadorDto("PL_Manual", partida, llegada))
    await repo.guardar(_CLAVE, DecisionOperadorDto("AceptarSugerencia"))
    guardada = (await repo.listar_por_proceso(5501))[(777, "10")]

    assert guardada.accion == "AceptarSugerencia"
    assert guardada.partida is None


async def test_decisiones_de_otro_proceso_no_se_listan(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDecisionesOperadorRepository(db_session)

    await repo.guardar(_CLAVE, DecisionOperadorDto("ForzarCascada"))
    await repo.guardar(ClaveDecisionDto(5502, 777, "10"), DecisionOperadorDto("MarcarPendiente"))

    assert list((await repo.listar_por_proceso(5501)).values())[0].accion == "ForzarCascada"
    assert len(await repo.listar_por_proceso(5502)) == 1


async def test_obtener_devuelve_la_decision_de_una_sola_fila(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDecisionesOperadorRepository(db_session)

    await repo.guardar(_CLAVE, DecisionOperadorDto("MarcarPendiente"))

    guardada = await repo.obtener(_CLAVE)
    assert guardada is not None and guardada.accion == "MarcarPendiente"
    assert await repo.obtener(ClaveDecisionDto(5501, 778, "10")) is None
