from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.domain.entities.pendientes_snapshot import (
    PendientesSnapshot,
    PrestadorPendientes,
)
from src.modules.sla.infrastructure.models.pendientes_snapshot_model import (
    PendientesSnapshotModel,
)

_VERSION = 1
_SNAPSHOT_FIELDS = ("total", "incidentes", "por_prestador", "updated_at")


def _incidente_to_json(i: IncidenteSinCerrar) -> dict[str, object]:
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
        "fecha_finalizacion": i.fecha_finalizacion.isoformat() if i.fecha_finalizacion else None,
        "dias_en_estado": i.dias_en_estado,
    }


def _json_to_incidente(d: dict[str, object]) -> IncidenteSinCerrar:
    fecha_ingreso = d["fecha_ingreso"]
    fecha_fin = d["fecha_finalizacion"]
    return IncidenteSinCerrar(
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
        fecha_finalizacion=datetime.fromisoformat(fecha_fin) if fecha_fin else None,  # type: ignore[arg-type]
        dias_en_estado=d["dias_en_estado"],  # type: ignore[arg-type]
    )


def _row_to_snapshot(row: PendientesSnapshotModel) -> PendientesSnapshot:
    return PendientesSnapshot(
        total=row.total,
        incidentes=[_json_to_incidente(i) for i in row.incidentes],
        por_prestador=[PrestadorPendientes(**p) for p in row.por_prestador],  # type: ignore[arg-type]
        updated_at=row.updated_at,
    )


def _snapshot_to_values(snapshot: PendientesSnapshot) -> dict[str, object]:
    return {
        "version": _VERSION,
        "total": snapshot.total,
        "incidentes": [_incidente_to_json(i) for i in snapshot.incidentes],
        "por_prestador": [
            {
                "id_tecnico": p.id_tecnico,
                "tecnico": p.tecnico,
                "cantidad": p.cantidad,
                "ids_incidente": p.ids_incidente,
            }
            for p in snapshot.por_prestador
        ],
        "updated_at": snapshot.updated_at,
    }


class SqlAlchemyPendientesSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> PendientesSnapshot | None:
        row = await self._session.get(PendientesSnapshotModel, _VERSION)
        return _row_to_snapshot(row) if row else None

    async def upsert(self, snapshot: PendientesSnapshot) -> None:
        stmt = insert(PendientesSnapshotModel).values(**_snapshot_to_values(snapshot))
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=[PendientesSnapshotModel.version],
                set_={field: getattr(stmt.excluded, field) for field in _SNAPSHOT_FIELDS},
            )
        )
