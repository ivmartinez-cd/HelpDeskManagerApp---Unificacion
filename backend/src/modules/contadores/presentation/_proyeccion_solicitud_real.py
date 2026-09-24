"""Compartido por los endpoints de `proyeccion_candidatos_router.py`: decide si
una acción es sobre un equipo real de Siges (trae la selección completa y la
clase es numérica) o sobre uno de ejemplo, contra qué calcula (la grilla ya
cargada del proceso o los datos de ejemplo) y dónde se guarda su decisión."""

from datetime import date, datetime
from typing import Protocol

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.dtos.decision_operador_dto import ClaveDecisionDto
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo import (
    buscar_equipo_y_clase,
    entrada_ejemplo,
)
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    NRO_PROCESO_EJEMPLO,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    get_decisiones_operador_store,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_decisiones_operador_repository import (  # noqa: E501
    SqlAlchemyDecisionesOperadorRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_recesos_repository import (
    SqlAlchemyRecesosRepository,
)
from src.modules.contadores.presentation._proyeccion_contexto_ejemplo import contexto_ejemplo
from src.modules.contadores.presentation.dependencies import get_grilla_estimacion_gateway

_SELECCION_INCOMPLETA = (
    "Para un proceso real hacen falta grupo económico, anexo, fecha objetivo y clase numérica"
)


class SeleccionProceso(Protocol):
    """Atributos como `@property` read-only: lo implementan tanto bodies
    pydantic como dataclasses `frozen=True` (`ForzarMetodoRequest`), y mypy
    exige que el Protocol calce esa mutabilidad."""

    @property
    def nro_proceso(self) -> int | None: ...
    @property
    def id_grupo_economico(self) -> int | None: ...
    @property
    def id_anexo(self) -> int | None: ...
    @property
    def fecha_objetivo(self) -> date | None: ...
    @property
    def descartar_hasta(self) -> datetime | None: ...


def solicitud_real_de(
    seleccion: SeleccionProceso, clase: str, operador: str | None = None
) -> SolicitudRecalculoSigesDto | None:
    """`None` = modo ejemplo (sin `nro_proceso`). Con `nro_proceso` la
    selección tiene que estar completa (422): el legacy opera siempre sobre
    la grilla del proceso cargado — la que cargó ESE `operador`."""
    nro, grupo, anexo = seleccion.nro_proceso, seleccion.id_grupo_economico, seleccion.id_anexo
    if nro is None:
        return None
    fecha = seleccion.fecha_objetivo
    if not clase.isdigit() or grupo is None or anexo is None or fecha is None:
        raise HTTPException(status_code=422, detail=_SELECCION_INCOMPLETA)
    return SolicitudRecalculoSigesDto(
        nro_proceso=nro,
        id_grupo_economico=grupo,
        id_anexo=anexo,
        fecha_objetivo=fecha,
        operador=operador,
    )


def operador_de(identity: Identity) -> str:
    """Cada operador trabaja sobre SU última carga de la grilla (en v1.7, la
    lista en memoria de su circuito): es la clave con que el gateway la
    recuerda."""
    return str(identity.user.id)


def clave_decision_de(id_maquina: int, clase: str, nro_proceso: int | None) -> ClaveDecisionDto:
    """La decisión es del proceso (`Estim_Log.NroProceso` del legacy). Sin
    `nro_proceso` solo se acepta un equipo de ejemplo — un equipo real sin
    proceso no se puede atribuir a ninguno."""
    if nro_proceso is not None:
        return ClaveDecisionDto(nro_proceso, id_maquina, clase)
    equipo, _ = buscar_equipo_y_clase(id_maquina, clase)
    if equipo is None:
        raise HTTPException(422, detail="nro_proceso es requerido para un equipo real")
    return ClaveDecisionDto(NRO_PROCESO_EJEMPLO, id_maquina, clase)


def decisiones_de(nro_proceso: int | None, db: AsyncSession) -> DecisionesOperadorPort:
    """Proceso real → Postgres; modo ejemplo (sin `nro_proceso`) → store en
    memoria, como sus recesos."""
    if nro_proceso is None:
        return get_decisiones_operador_store()
    return SqlAlchemyDecisionesOperadorRepository(db)


async def entrada_de(
    id_maquina: int,
    clase: str,
    seleccion: SeleccionProceso,
    db: AsyncSession,
    operador: str | None = None,
) -> EstimacionInput | None:
    """La fila (equipo, clase) del proceso tal como la calcula el tablero:
    sobre la grilla ya cargada del proceso real (el legacy opera sobre la
    lista que tiene en pantalla) o sobre los datos de ejemplo. `None` si la
    fila no existe."""
    solicitud = solicitud_real_de(seleccion, clase, operador)
    if solicitud is None:
        return entrada_ejemplo(id_maquina, clase, await contexto_ejemplo(seleccion.fecha_objetivo))
    constructor = ConstructorEntradaSiges(
        get_grilla_estimacion_gateway(), SqlAlchemyRecesosRepository(db)
    )
    construida = await constructor.construir(id_maquina, clase, solicitud)
    return construida[0] if construida is not None else None
