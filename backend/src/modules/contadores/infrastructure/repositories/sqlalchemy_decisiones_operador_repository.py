from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionManualDto,
    DecisionOperadorDto,
)
from src.modules.contadores.infrastructure.models.decision_operador_model import (
    DecisionOperadorModel,
)


class SqlAlchemyDecisionesOperadorRepository:
    """Sin commit: el límite transaccional vive en `get_db` (scope="function",
    ADR-030). `_upsert` centraliza el patrón (una fila por equipo+clase, se
    pisa) que usan las cuatro acciones."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar_todas(self) -> dict[tuple[int, str], DecisionOperadorDto]:
        rows = (await self._session.execute(select(DecisionOperadorModel))).scalars().all()
        return {(row.id_maquina, row.clase): _to_dto(row) for row in rows}

    async def marcar_pendiente(self, id_maquina: int, clase: str) -> None:
        actual = await self._obtener(id_maquina, clase)
        await self._upsert(
            id_maquina, clase,
            pendiente=True, nota=actual.nota if actual else None,
            manual=actual.manual if actual else None,
        )

    async def agregar_nota(self, id_maquina: int, clase: str, nota: str) -> None:
        actual = await self._obtener(id_maquina, clase)
        await self._upsert(
            id_maquina, clase,
            pendiente=actual.pendiente if actual else False, nota=nota,
            manual=actual.manual if actual else None,
        )

    async def aceptar(
        self, id_maquina: int, clase: str, manual: DecisionManualDto | None = None
    ) -> None:
        if manual is None:
            await self._session.execute(
                delete(DecisionOperadorModel).where(
                    DecisionOperadorModel.id_maquina == id_maquina,
                    DecisionOperadorModel.clase == clase,
                )
            )
            return
        actual = await self._obtener(id_maquina, clase)
        await self._upsert(
            id_maquina, clase,
            pendiente=False, nota=actual.nota if actual else None, manual=manual,
        )

    async def _obtener(self, id_maquina: int, clase: str) -> DecisionOperadorDto | None:
        row = await self._session.get(DecisionOperadorModel, (id_maquina, clase))
        return _to_dto(row) if row is not None else None

    async def _upsert(
        self,
        id_maquina: int,
        clase: str,
        *,
        pendiente: bool,
        nota: str | None,
        manual: DecisionManualDto | None,
    ) -> None:
        valores = _valores_de(pendiente, nota, manual)
        stmt = pg_insert(DecisionOperadorModel).values(
            id_maquina=id_maquina, clase=clase, **valores
        )
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=[DecisionOperadorModel.id_maquina, DecisionOperadorModel.clase],
                set_=valores,
            )
        )


def _valores_de(
    pendiente: bool, nota: str | None, manual: DecisionManualDto | None
) -> dict[str, Any]:
    return {
        "pendiente": pendiente,
        "nota": nota,
        "manual_contador_propuesto": manual.contador_propuesto if manual else None,
        "manual_tipo_toma": manual.tipo_toma if manual else None,
        "manual_fuente": manual.fuente if manual else None,
        "manual_metodo_detalle": manual.metodo_detalle if manual else None,
        "actualizado_en": datetime.now(UTC),
    }


def _to_dto(row: DecisionOperadorModel) -> DecisionOperadorDto:
    manual = None
    if row.manual_fuente is not None:
        manual = DecisionManualDto(
            contador_propuesto=(
                float(row.manual_contador_propuesto)
                if row.manual_contador_propuesto is not None
                else None
            ),
            tipo_toma=row.manual_tipo_toma,
            fuente=row.manual_fuente,
            metodo_detalle=row.manual_metodo_detalle or "",
        )
    return DecisionOperadorDto(pendiente=row.pendiente, nota=row.nota, manual=manual)
