from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.ports.estim_log_port import EntradaEstimLog
from src.modules.contadores.infrastructure.models.estim_log_model import EstimLogModel


class SqlAlchemyEstimLogRepository:
    """Sin commit: el límite transaccional vive en `get_db` (scope="function",
    ADR-030) — ver `src/shared/infrastructure/database/session.py`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(self, entrada: EntradaEstimLog) -> None:
        self._session.add(
            EstimLogModel(
                operador_user_id=entrada.operador_user_id,
                operador_email=entrada.operador_email,
                nro_proceso=entrada.nro_proceso,
                id_maquina=entrada.id_maquina,
                clase=entrada.clase,
                fecha_objetivo=entrada.fecha_objetivo,
                accion=entrada.accion,
                contador_anterior=entrada.contador_anterior,
                contador_propuesto=entrada.contador_propuesto,
                tipo_toma_grabado=entrada.tipo_toma_grabado,
                fuente=entrada.fuente,
                metodo_detalle=entrada.metodo_detalle,
                observacion=entrada.observacion,
                detalle=entrada.detalle or None,
            )
        )
        await self._session.flush()
