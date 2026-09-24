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

# (id_maquina, clase) → lecturas del equipo/clase en Siges, por ID_Contador.
ReleerLecturas = Callable[[int, str], Awaitable[dict[int, LecturaElegidaDto]]]


def releer_lecturas_de_siges(port: CandidatosEquipoPort) -> ReleerLecturas:
    """`ReleerLecturas` sobre el panel de candidatos real (mismas 24 lecturas
    que ofrece `GetCandidatos` del legacy)."""

    async def releer(id_maquina: int, clase: str) -> dict[int, LecturaElegidaDto]:
        lecturas = await port.fetch_lecturas(id_maquina, int(clase))
        return {lectura.id_contador: _lectura_elegida(lectura) for lectura in lecturas}

    return releer


async def con_pl_releida(
    clave: tuple[int, str], decision: DecisionOperadorDto, releer: ReleerLecturas
) -> DecisionOperadorDto:
    """Lectura que ya no está en Siges, o P/L guardada sin `ID_Contador`
    → queda sin P/L y la decisión se descarta al resolver (legacy:
    `PartidaIdContador is null` o candidato `null`)."""
    if decision.accion != "PL_Manual":
        return decision
    ids = _ids_pl(decision)
    if ids is None:
        return replace(decision, partida=None, llegada=None)
    lecturas = await _lecturas_o_vacio(releer, clave)
    return replace(decision, partida=lecturas.get(ids[0]), llegada=lecturas.get(ids[1]))


async def _lecturas_o_vacio(
    releer: ReleerLecturas, clave: tuple[int, str]
) -> dict[int, LecturaElegidaDto]:
    try:
        return await releer(*clave)
    except Exception as exc:
        # Mismo manejo que el legacy: sin candidatos no se puede reconstruir
        # la P/L, se descarta esa decisión y el resto sigue.
        logger.warning(
            "No se pudieron releer los candidatos para restaurar una P/L manual",
            extra={"id_maquina": clave[0], "clase": clave[1]},
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
