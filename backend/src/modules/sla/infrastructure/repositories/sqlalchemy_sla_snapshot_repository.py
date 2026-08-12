"""Implementación Postgres del snapshot cacheado de SLA (ver
domain/repositories/sla_snapshot_repository.py). Los incidentes vencidos y el
desglose por técnico se guardan como JSONB — no ameritan tablas propias, se
reescriben enteros en cada refresh (ver upsert)."""

from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.entities.sla_snapshot import SlaSnapshot, TecnicoVencidos
from src.modules.sla.infrastructure.models.sla_periodo_snapshot_model import (
    SlaPeriodoSnapshotModel,
)

_SNAPSHOT_FIELDS = (
    "total",
    "correctos",
    "vencidos",
    "pct_correctos",
    "pct_vencidos",
    "vencidos_por_tecnico",
    "incidentes_vencidos",
    "updated_at",
)


def _incidente_to_json(i: IncidenteSla) -> dict[str, object]:
    return {
        "id_incidente": i.id_incidente,
        "fecha_ingreso": i.fecha_ingreso.isoformat() if i.fecha_ingreso else None,
        "tipo": i.tipo,
        "estado": i.estado,
        "cliente": i.cliente,
        "sucursal": i.sucursal,
        "nro_serie": i.nro_serie,
        "modelo": i.modelo,
        "tecnico": i.tecnico,
        "id_tecnico": i.id_tecnico,
        "region": i.region,
        "fecha_operativo": i.fecha_operativo.isoformat() if i.fecha_operativo else None,
        "periodo": i.periodo,
        "tiempo": i.tiempo,
        "rango": i.rango,
        "sla_horas": i.sla_horas,
        "horas_vencido": i.horas_vencido,
        "resultado": i.resultado,
    }


def _json_to_incidente(d: dict[str, object]) -> IncidenteSla:
    fecha_ingreso = d["fecha_ingreso"]
    fecha_operativo = d["fecha_operativo"]
    return IncidenteSla(
        id_incidente=d["id_incidente"],  # type: ignore[arg-type]
        fecha_ingreso=datetime.fromisoformat(fecha_ingreso) if fecha_ingreso else None,  # type: ignore[arg-type]
        tipo=d["tipo"],  # type: ignore[arg-type]
        estado=d["estado"],  # type: ignore[arg-type]
        cliente=d["cliente"],  # type: ignore[arg-type]
        sucursal=d["sucursal"],  # type: ignore[arg-type]
        nro_serie=d["nro_serie"],  # type: ignore[arg-type]
        modelo=d["modelo"],  # type: ignore[arg-type]
        tecnico=d["tecnico"],  # type: ignore[arg-type]
        id_tecnico=d["id_tecnico"],  # type: ignore[arg-type]
        region=d["region"],  # type: ignore[arg-type]
        fecha_operativo=datetime.fromisoformat(fecha_operativo) if fecha_operativo else None,  # type: ignore[arg-type]
        periodo=d["periodo"],  # type: ignore[arg-type]
        tiempo=d["tiempo"],  # type: ignore[arg-type]
        rango=d["rango"],  # type: ignore[arg-type]
        sla_horas=d["sla_horas"],  # type: ignore[arg-type]
        horas_vencido=d["horas_vencido"],  # type: ignore[arg-type]
        resultado=d["resultado"],  # type: ignore[arg-type]
    )


def _row_to_snapshot(row: SlaPeriodoSnapshotModel) -> SlaSnapshot:
    return SlaSnapshot(
        periodo=row.periodo,
        total=row.total,
        correctos=row.correctos,
        vencidos=row.vencidos,
        pct_correctos=row.pct_correctos,
        pct_vencidos=row.pct_vencidos,
        vencidos_por_tecnico=[TecnicoVencidos(**t) for t in row.vencidos_por_tecnico],  # type: ignore[arg-type]
        incidentes_vencidos=[_json_to_incidente(i) for i in row.incidentes_vencidos],
        updated_at=row.updated_at,
    )


def _snapshot_to_values(snapshot: SlaSnapshot) -> dict[str, object]:
    return {
        "periodo": snapshot.periodo,
        "total": snapshot.total,
        "correctos": snapshot.correctos,
        "vencidos": snapshot.vencidos,
        "pct_correctos": snapshot.pct_correctos,
        "pct_vencidos": snapshot.pct_vencidos,
        "vencidos_por_tecnico": [
            {
                "tecnico": t.tecnico,
                "id_tecnico": t.id_tecnico,
                "cantidad": t.cantidad,
                "ids_incidente": t.ids_incidente,
            }
            for t in snapshot.vencidos_por_tecnico
        ],
        "incidentes_vencidos": [_incidente_to_json(i) for i in snapshot.incidentes_vencidos],
        "updated_at": snapshot.updated_at,
    }


class SqlAlchemySlaSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, periodo: int) -> SlaSnapshot | None:
        row = await self._session.get(SlaPeriodoSnapshotModel, periodo)
        return _row_to_snapshot(row) if row else None

    async def upsert(self, snapshot: SlaSnapshot) -> None:
        stmt = insert(SlaPeriodoSnapshotModel).values(**_snapshot_to_values(snapshot))
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=[SlaPeriodoSnapshotModel.periodo],
                set_={field: getattr(stmt.excluded, field) for field in _SNAPSHOT_FIELDS},
            )
        )
