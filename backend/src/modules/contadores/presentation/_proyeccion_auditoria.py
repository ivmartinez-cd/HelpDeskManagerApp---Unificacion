"""Auditoría de acciones sobre el tablero de Proyección (REGLAS_DE_NEGOCIO
§11) — un INSERT append-only por acción del operador, en paralelo a lo que
ya hace cada endpoint (no reemplaza `DecisionesOperadorStore`, que sigue
siendo la fuente del "estado vigente" en memoria; ver docstring de
`EstimLogModel`)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.domain.ports.estim_log_port import EntradaEstimLog
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
