"""Fakes en memoria del puerto de Incidentes Derivados para los tests
unitarios de sla/application."""

from datetime import UTC, date, datetime

from src.modules.sla.domain.entities.incidente_derivado import IncidenteDerivado


class FakeDerivadosQueryGateway:
    def __init__(self, incidentes: list[IncidenteDerivado] | None = None) -> None:
        self.incidentes = incidentes or []
        self.rangos_consultados: list[tuple[date, date]] = []

    async def find_incidentes_derivados(
        self, desde: date, hasta: date
    ) -> list[IncidenteDerivado]:
        self.rangos_consultados.append((desde, hasta))
        return list(self.incidentes)


def build_derivado(
    id_incidente: int, id_tecnico: int, tecnico: str, dias_desde_ingreso: int = 1
) -> IncidenteDerivado:
    return IncidenteDerivado(
        id_incidente=id_incidente,
        fecha_ingreso=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        tipo="Correctivo",
        estado="Derivado",
        cliente="Cliente SA",
        sucursal="Casa Central",
        nro_serie=f"SERIE{id_incidente}",
        modelo="HP LaserJet",
        tecnico=tecnico,
        id_tecnico=id_tecnico,
        dias_desde_ingreso=dias_desde_ingreso,
    )
