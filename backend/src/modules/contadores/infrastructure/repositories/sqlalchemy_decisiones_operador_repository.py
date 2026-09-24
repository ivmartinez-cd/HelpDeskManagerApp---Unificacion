from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.application.dtos.decision_operador_dto import (
    AccionDecision,
    ClaveDecisionDto,
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.infrastructure.models.decision_operador_model import (
    DecisionOperadorModel,
)

_M = DecisionOperadorModel


class SqlAlchemyDecisionesOperadorRepository:
    """Sin commit: el límite transaccional vive en `get_db` (scope="function",
    ADR-030). `_upsert` centraliza el patrón (una fila por proceso+equipo+clase,
    se pisa) que usan todas las acciones."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar_por_proceso(
        self, nro_proceso: int
    ) -> dict[tuple[int, str], DecisionOperadorDto]:
        stmt = select(_M).where(_M.nro_proceso == nro_proceso)
        rows = (await self._session.execute(stmt)).scalars().all()
        return {(row.id_maquina, row.clase): _a_dto(row) for row in rows}

    async def guardar(self, clave: ClaveDecisionDto, decision: DecisionOperadorDto) -> None:
        await self._upsert(clave, decision)

    async def obtener(self, clave: ClaveDecisionDto) -> DecisionOperadorDto | None:
        stmt = select(_M).where(
            _M.nro_proceso == clave.nro_proceso,
            _M.id_maquina == clave.id_maquina,
            _M.clase == clave.clase,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _a_dto(row) if row is not None else None

    async def _upsert(self, clave: ClaveDecisionDto, decision: DecisionOperadorDto) -> None:
        valores = _valores_de(decision)
        stmt = pg_insert(_M).values(
            nro_proceso=clave.nro_proceso, id_maquina=clave.id_maquina, clase=clave.clase, **valores
        )
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=[_M.nro_proceso, _M.id_maquina, _M.clase], set_=valores
            )
        )


def _valores_de(decision: DecisionOperadorDto) -> dict[str, Any]:
    return {
        "accion": decision.accion,
        **_columnas_lectura("partida", decision.partida),
        **_columnas_lectura("llegada", decision.llegada),
        "actualizado_en": datetime.now(UTC),
    }


def _columnas_lectura(prefijo: str, lectura: LecturaElegidaDto | None) -> dict[str, Any]:
    return {
        f"{prefijo}_id_contador": lectura.id_contador if lectura else None,
        f"{prefijo}_fecha": lectura.fecha if lectura else None,
        f"{prefijo}_valor": lectura.valor if lectura else None,
        f"{prefijo}_tipo_toma": lectura.tipo_toma if lectura else None,
        f"{prefijo}_para_facturar": lectura.para_facturar if lectura else None,
    }


def _a_dto(row: DecisionOperadorModel) -> DecisionOperadorDto:
    return DecisionOperadorDto(
        accion=cast(AccionDecision, row.accion),
        partida=_partida_de(row),
        llegada=_llegada_de(row),
        actualizado_en=row.actualizado_en,
    )


def _partida_de(row: DecisionOperadorModel) -> LecturaElegidaDto | None:
    if row.partida_fecha is None or row.partida_valor is None or row.partida_tipo_toma is None:
        return None
    return LecturaElegidaDto(
        fecha=row.partida_fecha,
        valor=float(row.partida_valor),
        tipo_toma=row.partida_tipo_toma,
        id_contador=row.partida_id_contador,
        para_facturar=row.partida_para_facturar is not False,
    )


def _llegada_de(row: DecisionOperadorModel) -> LecturaElegidaDto | None:
    if row.llegada_fecha is None or row.llegada_valor is None or row.llegada_tipo_toma is None:
        return None
    return LecturaElegidaDto(
        fecha=row.llegada_fecha,
        valor=float(row.llegada_valor),
        tipo_toma=row.llegada_tipo_toma,
        id_contador=row.llegada_id_contador,
        para_facturar=row.llegada_para_facturar is not False,
    )
