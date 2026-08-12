"""Fakes en memoria del puerto de sla para tests unitarios."""

from datetime import datetime

from src.modules.sla.domain.entities.incidente_sla import (
    RESULTADO_CORRECTO,
    IncidenteSla,
)
from src.modules.sla.domain.entities.sla_snapshot import SlaSnapshot
from src.modules.sla.domain.value_objects.periodo import Periodo


class FakeSlaQueryGateway:
    def __init__(self, incidentes: list[IncidenteSla] | None = None) -> None:
        self.incidentes = incidentes or []
        self.periodos_consultados: list[Periodo] = []

    async def find_incidentes(self, periodo: Periodo) -> list[IncidenteSla]:
        self.periodos_consultados.append(periodo)
        return list(self.incidentes)


class FakeSlaSnapshotRepository:
    """En memoria, vacío por default — ejercita el camino de cold-start
    (cache-miss -> refresh en vivo) que usan GetSlaCompliance/ListIncidentesVencidos."""

    def __init__(self) -> None:
        self._snapshots: dict[int, SlaSnapshot] = {}

    async def get(self, periodo: int) -> SlaSnapshot | None:
        return self._snapshots.get(periodo)

    async def upsert(self, snapshot: SlaSnapshot) -> None:
        self._snapshots[snapshot.periodo] = snapshot


def build_incidente(id_incidente: int, tecnico: str, resultado: str) -> IncidenteSla:
    """Incidente con los campos que no importan al caso fijados en valores neutros."""
    return IncidenteSla(
        id_incidente=id_incidente,
        fecha_ingreso=datetime(2026, 8, 3, 10, 0),
        tipo="Correctivo",
        estado="Cerrado",
        cliente="Cliente SA",
        sucursal="Casa Central",
        nro_serie="XYZ123",
        modelo="HP LaserJet",
        tecnico=tecnico,
        region="LOCAL",
        fecha_operativo=datetime(2026, 8, 4, 15, 30),
        periodo=202608,
        tiempo="12:30",
        rango="0 a 24",
        sla_horas=24,
        horas_vencido=0 if resultado == RESULTADO_CORRECTO else 5,
        resultado=resultado,
    )
