"""La fila efectiva sobre la que opera el panel de candidatos
(`GrillaEstimacion.EquipoEfectivo` del legacy): el cálculo automático con la
decisión vigente del proceso, igual que la muestra el tablero — corte de
"Descartar y empezar limpio" incluido, y la P/L manual releída de Siges por
`ID_Contador`. Lo usan los botones que ofrece el panel y todas las acciones
del operador (`_proyeccion_acciones.py`), para que ninguna decida ni audite
sobre una fila distinta de la que el operador tiene en pantalla."""

from dataclasses import dataclass, replace

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionOperadorDto,
    ParPartidaLlegadaDto,
)
from src.modules.contadores.application.use_cases._releer_pl_manual import (
    ReleerLecturas,
    con_pl_releida,
    releer_lecturas_de_siges,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    decision_no_descartada,
    resolver_resultado_final,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.presentation._proyeccion_solicitud_real import (
    SeleccionProceso,
    clave_decision_de,
    decisiones_de,
    entrada_de,
    solicitud_real_de,
)
from src.modules.contadores.presentation.dependencies import get_candidatos_equipo_gateway

_SIN_ID_CONTADOR = "En un proceso real la Partida y la Llegada necesitan su ID de contador"
_LECTURA_INEXISTENTE = "La Partida o la Llegada no está entre las lecturas del equipo en Siges"


@dataclass(frozen=True, slots=True)
class FilaVigente:
    """`entrada` es la fila original (sobre ella se calculan las
    alternativas, como `OnOjoClick`); `resultado`, lo que la grilla muestra."""

    entrada: EstimacionInput
    resultado: EstimacionResultado


async def fila_vigente(
    id_maquina: int,
    clase: str,
    seleccion: SeleccionProceso,
    db: AsyncSession,
    operador: str | None = None,
) -> FilaVigente | None:
    """`None` si la fila no existe en el proceso (o en el ejemplo). 422 si
    la selección de un proceso real está incompleta."""
    solicitud_real_de(seleccion, clase)
    entrada = await entrada_de(id_maquina, clase, seleccion, db, operador)
    if entrada is None:
        return None
    decision = await _decision_vigente(id_maquina, clase, seleccion, db)
    return FilaVigente(entrada, resolver_resultado_final(entrada, decision).resultado)


async def par_de_siges(
    par: ParPartidaLlegadaDto, seleccion: SeleccionProceso
) -> ParPartidaLlegadaDto:
    """En el modo real la P/L es la de Siges (`CandidatoContador` de
    `GetCandidatosAsync`), buscada por `ID_Contador`: lo que mande el
    cliente (valor, fecha, tipo, `Para_Facturar`) no cuenta. 422 sin
    `ID_Contador` o si la lectura no está entre los candidatos del equipo."""
    if solicitud_real_de(seleccion, par.clase) is None:
        return par
    id_partida, id_llegada = par.partida.id_contador, par.llegada.id_contador
    if id_partida is None or id_llegada is None:
        raise HTTPException(status_code=422, detail=_SIN_ID_CONTADOR)
    lecturas = await _releer()(par.id_maquina, par.clase)
    partida, llegada = lecturas.get(id_partida), lecturas.get(id_llegada)
    if partida is None or llegada is None:
        raise HTTPException(status_code=422, detail=_LECTURA_INEXISTENTE)
    return replace(par, partida=partida, llegada=llegada)


async def _decision_vigente(
    id_maquina: int, clase: str, seleccion: SeleccionProceso, db: AsyncSession
) -> DecisionOperadorDto | None:
    clave = clave_decision_de(id_maquina, clase, seleccion.nro_proceso)
    decision = await decisiones_de(seleccion.nro_proceso, db).obtener(clave)
    if decision is None or not decision_no_descartada(decision, seleccion.descartar_hasta):
        return None
    if solicitud_real_de(seleccion, clase) is None:
        return decision
    return await con_pl_releida((id_maquina, clase), decision, _releer())


def _releer() -> ReleerLecturas:
    return releer_lecturas_de_siges(get_candidatos_equipo_gateway())
