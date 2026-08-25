"""Fakes en memoria del puerto de Mesa de Ayuda para los tests unitarios de
sla/application."""

from datetime import UTC, datetime

from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda


class FakeMesaAyudaQueryGateway:
    def __init__(self, incidentes: list[IncidenteMesaAyuda] | None = None) -> None:
        self.incidentes = incidentes or []
        self.ids_tecnico_consultados: list[int] = []

    async def find_incidentes_mesa_ayuda(self, id_tecnico: int) -> list[IncidenteMesaAyuda]:
        self.ids_tecnico_consultados.append(id_tecnico)
        return list(self.incidentes)


def build_mesa_ayuda(
    id_incidente: int,
    operador_login: str = "vipaez",
    operador: str = "Victor Paez",
    dias_transcurridos: int = 1,
) -> IncidenteMesaAyuda:
    return IncidenteMesaAyuda(
        id_incidente=id_incidente,
        fecha_ingreso=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        tipo="Correctivo",
        estado="Demorado",
        cliente="Cliente SA",
        sucursal="Casa Central",
        nro_serie=f"SERIE{id_incidente}",
        modelo="HP LaserJet",
        operador_login=operador_login,
        operador=operador,
        dias_transcurridos=dias_transcurridos,
    )
