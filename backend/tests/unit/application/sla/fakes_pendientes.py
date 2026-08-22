"""Fakes en memoria de los puertos de 'incidentes sin cerrar' (pendientes)
para los tests unitarios de sla/application."""

import uuid
from datetime import UTC, datetime

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.domain.entities.pendientes_snapshot import PendientesSnapshot


class FakePendientesQueryGateway:
    def __init__(self, incidentes: list[IncidenteSinCerrar] | None = None) -> None:
        self.incidentes = incidentes or []
        self.meses_consultados: list[int] = []

    async def find_incidentes_sin_cerrar(self, meses_corte: int) -> list[IncidenteSinCerrar]:
        self.meses_consultados.append(meses_corte)
        return list(self.incidentes)


class FakePendientesSnapshotRepository:
    """Vacío por default — ejercita el cold start (cache-miss -> refresh)."""

    def __init__(self, snapshot: PendientesSnapshot | None = None) -> None:
        self.snapshot = snapshot
        self.upserts = 0

    async def get(self) -> PendientesSnapshot | None:
        return self.snapshot

    async def upsert(self, snapshot: PendientesSnapshot) -> None:
        self.snapshot = snapshot
        self.upserts += 1


class FakePrestadorLookup:
    def __init__(
        self,
        pst_ids: list[int] | None = None,
        pst_to_operador: dict[int, str] | None = None,
    ) -> None:
        self.pst_ids = pst_ids or []
        self.pst_to_operador = pst_to_operador or {}

    async def get_siges_ids_por_operador(self, operador_id: uuid.UUID) -> list[int]:
        return []

    async def get_all_pst_siges_ids(self) -> list[int]:
        return list(self.pst_ids)

    async def get_pst_to_operador_mapping(self) -> dict[int, str]:
        return dict(self.pst_to_operador)


def build_sin_cerrar(
    id_incidente: int, id_tecnico: int, tecnico: str, dias_en_estado: int = 1
) -> IncidenteSinCerrar:
    return IncidenteSinCerrar(
        id_incidente=id_incidente,
        fecha_ingreso=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        tipo="Correctivo",
        estado="Finalizado",
        cliente="Cliente SA",
        sucursal="Casa Central",
        nro_serie=f"SERIE{id_incidente}",
        modelo="HP LaserJet",
        tecnico=tecnico,
        id_tecnico=id_tecnico,
        fecha_finalizacion=datetime(2026, 8, 2, 9, 0, tzinfo=UTC),
        dias_en_estado=dias_en_estado,
    )
