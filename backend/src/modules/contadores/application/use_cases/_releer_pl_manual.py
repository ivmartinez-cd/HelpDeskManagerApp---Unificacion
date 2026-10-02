"""Relectura de la Partida/Llegada de una P/L manual guardada — lo que
`GrillaEstimacion.ReconstruirOverrideAsync` del legacy hace con
`SiGes.GetCandidatosAsync` + `ID_Contador`: el valor, la fecha, el tipo y el
`Para_Facturar` salen siempre de Siges, no de lo que se guardó o de lo que
manda el cliente. Lo comparten el tablero, el panel y las acciones del
operador."""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import replace

from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    CandidatosEquipoPort,
    LecturaCandidataSiges,
)

logger = logging.getLogger(__name__)

Clave = tuple[int, str]
# (id_maquina, clase) de cada equipo → sus lecturas en Siges, por ID_Contador.
# En lote: el tablero relee todas sus P/L manuales en una sola consulta (una
# por equipo eran ~0,25 s cada una y con 50+ ediciones la grilla tardaba
# tanto que parecía no actualizarse).
ReleerLecturas = Callable[[list[Clave]], Awaitable[dict[Clave, dict[int, LecturaElegidaDto]]]]


def releer_lecturas_de_siges(port: CandidatosEquipoPort) -> ReleerLecturas:
    """`ReleerLecturas` sobre el panel de candidatos real (mismas 24 lecturas
    por equipo que ofrece `GetCandidatos` del legacy)."""

    async def releer(claves: list[Clave]) -> dict[Clave, dict[int, LecturaElegidaDto]]:
        por_equipo = await port.fetch_lecturas_de_equipos([(m, int(c)) for m, c in claves])
        return {
            (m, c): {x.id_contador: _lectura_elegida(x) for x in por_equipo.get((m, int(c)), [])}
            for m, c in claves
        }

    return releer


async def con_pls_releidas(
    decisiones: dict[Clave, DecisionOperadorDto], releer: ReleerLecturas
) -> dict[Clave, DecisionOperadorDto]:
    """Lectura que ya no está en Siges, o P/L guardada sin `ID_Contador`
    → queda sin P/L y la decisión se descarta al resolver (legacy:
    `PartidaIdContador is null` o candidato `null`)."""
    a_releer = [c for c, d in decisiones.items() if d.accion == "PL_Manual" and _ids_pl(d)]
    lecturas = await _lecturas_o_vacio(releer, a_releer)
    return {c: _releida(d, lecturas.get(c, {})) for c, d in decisiones.items()}


async def con_pl_releida(
    clave: Clave, decision: DecisionOperadorDto, releer: ReleerLecturas
) -> DecisionOperadorDto:
    return (await con_pls_releidas({clave: decision}, releer))[clave]


def _releida(
    decision: DecisionOperadorDto, lecturas: dict[int, LecturaElegidaDto]
) -> DecisionOperadorDto:
    if decision.accion != "PL_Manual":
        return decision
    ids = _ids_pl(decision)
    if ids is None:
        return replace(decision, partida=None, llegada=None)
    return replace(decision, partida=lecturas.get(ids[0]), llegada=lecturas.get(ids[1]))


async def _lecturas_o_vacio(
    releer: ReleerLecturas, claves: list[Clave]
) -> dict[Clave, dict[int, LecturaElegidaDto]]:
    if not claves:
        return {}
    try:
        return await releer(claves)
    except Exception as exc:
        # Mismo manejo que el legacy: sin candidatos no se puede reconstruir
        # la P/L, se descartan esas decisiones y el resto sigue.
        logger.warning(
            "No se pudieron releer los candidatos para restaurar una P/L manual",
            extra={"equipos": claves[:20], "cantidad": len(claves)},
            exc_info=exc,
        )
        return {}


def _lectura_elegida(lectura: LecturaCandidataSiges) -> LecturaElegidaDto:
    return LecturaElegidaDto(
        lectura.fecha, lectura.valor, lectura.tipo_toma, lectura.id_contador, lectura.para_facturar
    )


def _ids_pl(decision: DecisionOperadorDto) -> tuple[int, int] | None:
    if decision.partida is None or decision.llegada is None:
        return None
    id_partida, id_llegada = decision.partida.id_contador, decision.llegada.id_contador
    if id_partida is None or id_llegada is None:
        return None
    return id_partida, id_llegada
