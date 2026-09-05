"""Auditoría de acciones sobre el tablero de Proyección (REGLAS_DE_NEGOCIO
§11) — un INSERT append-only por acción del operador, en paralelo a lo que
ya hace cada endpoint (no reemplaza `DecisionesOperadorStore`, que sigue
siendo la fuente del "estado vigente" en memoria; ver docstring de
`EstimLogModel`)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.dtos.forzar_metodo_request import ForzarMetodoRequest
from src.modules.contadores.application.dtos.recalcular_candidato_request import (
    RecalcularCandidatoRequest,
)
from src.modules.contadores.domain.ports.estim_log_port import EntradaEstimLog
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_estim_log_repository import (
    SqlAlchemyEstimLogRepository,
)


async def registrar_accion(
    db: AsyncSession, identity: Identity, id_maquina: int, clase: str, accion: str, **campos: Any
) -> None:
    entrada = EntradaEstimLog(
        operador_user_id=identity.user.id,
        operador_email=identity.user.email,
        id_maquina=id_maquina,
        clase=clase,
        accion=accion,
        **campos,
    )
    await SqlAlchemyEstimLogRepository(db).registrar(entrada)


async def registrar_pl_manual(
    db: AsyncSession,
    identity: Identity,
    request: RecalcularCandidatoRequest,
    resultado: EstimacionResultado,
) -> None:
    await registrar_accion(
        db, identity, request.id_maquina, request.clase, "pl_manual",
        fecha_objetivo=request.fecha_objetivo, nro_proceso=request.nro_proceso,
        contador_propuesto=resultado.estim_propuesto, tipo_toma_grabado=resultado.tipo_toma,
        fuente=resultado.fuente, metodo_detalle=resultado.metodo_detalle,
        detalle={
            "partida_valor": request.partida_valor, "partida_fecha": str(request.partida_fecha),
            "llegada_valor": request.llegada_valor, "llegada_fecha": str(request.llegada_fecha),
        },
    )


async def registrar_metodo_forzado(
    db: AsyncSession,
    identity: Identity,
    request: ForzarMetodoRequest,
    resultado: EstimacionResultado,
) -> None:
    await registrar_accion(
        db, identity, request.id_maquina, request.clase, f"forzar_{request.metodo}",
        fecha_objetivo=request.fecha_objetivo, nro_proceso=request.nro_proceso,
        contador_propuesto=resultado.estim_propuesto, tipo_toma_grabado=resultado.tipo_toma,
        fuente=resultado.fuente, metodo_detalle=resultado.metodo_detalle,
    )
