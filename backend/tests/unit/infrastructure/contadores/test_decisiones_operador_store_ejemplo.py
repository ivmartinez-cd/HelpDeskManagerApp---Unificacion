"""Store en memoria de decisiones del modo ejemplo: una decisión vigente por
(proceso, equipo, clase) — no se arrastra a otro proceso — sin nota (la
observación del operador es solo de la auditoría, como el legacy). Porta
`SqliteAuditResumeTests` del legacy (`GetUltimasDecisionesProcesoAsync`:
último gana, una fila por equipo y clase, aislado por proceso)."""

from datetime import date

from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    DecisionesOperadorStore,
)

_CLAVE = ClaveDecisionDto(nro_proceso=1001, id_maquina=1, clase="10")


async def test_la_decision_es_del_proceso_y_no_aparece_en_otro() -> None:
    store = DecisionesOperadorStore()

    await store.guardar(_CLAVE, DecisionOperadorDto(accion="MarcarPendiente"))

    assert list(await store.listar_por_proceso(1001)) == [(1, "10")]
    assert await store.listar_por_proceso(1002) == {}


async def test_guardar_marca_el_momento_de_la_decision() -> None:
    """`actualizado_en` es lo que compara "Descartar y empezar limpio"."""
    store = DecisionesOperadorStore()

    await store.guardar(_CLAVE, DecisionOperadorDto(accion="ForzarCascada"))

    decision = (await store.listar_por_proceso(1001))[(1, "10")]
    assert decision.accion == "ForzarCascada"
    assert decision.actualizado_en is not None


async def test_roundtrip_pl_manual_persiste_accion_y_par() -> None:
    store = DecisionesOperadorStore()
    partida = LecturaElegidaDto(date(2026, 1, 31), 1_000, 1, id_contador=111)
    llegada = LecturaElegidaDto(date(2026, 3, 2), 1_500, 1, id_contador=222)

    await store.guardar(_CLAVE, DecisionOperadorDto("PL_Manual", partida=partida, llegada=llegada))

    decision = await store.obtener(_CLAVE)
    assert decision is not None
    assert decision.accion == "PL_Manual"
    assert decision.partida is not None and decision.partida.id_contador == 111
    assert decision.llegada is not None and decision.llegada.id_contador == 222


async def test_ultima_decision_gana_por_equipo() -> None:
    store = DecisionesOperadorStore()
    await store.guardar(_CLAVE, DecisionOperadorDto("PL_Manual"))

    await store.guardar(_CLAVE, DecisionOperadorDto("ForzarCascada"))

    assert [d.accion for d in (await store.listar_por_proceso(1001)).values()] == ["ForzarCascada"]


async def test_una_decision_por_equipo_y_clase() -> None:
    store = DecisionesOperadorStore()
    await store.guardar(ClaveDecisionDto(1001, 50, "10"), DecisionOperadorDto("PL_Manual"))
    await store.guardar(ClaveDecisionDto(1001, 50, "20"), DecisionOperadorDto("ForzarCascada"))
    await store.guardar(ClaveDecisionDto(1001, 51, "10"), DecisionOperadorDto("MarcarPendiente"))
    await store.guardar(ClaveDecisionDto(1001, 50, "10"), DecisionOperadorDto("MarcarPendiente"))

    decisiones = await store.listar_por_proceso(1001)

    assert set(decisiones) == {(50, "10"), (50, "20"), (51, "10")}
    assert decisiones[(50, "10")].accion == "MarcarPendiente"


async def test_obtener_sin_decision_devuelve_none() -> None:
    assert await DecisionesOperadorStore().obtener(_CLAVE) is None
