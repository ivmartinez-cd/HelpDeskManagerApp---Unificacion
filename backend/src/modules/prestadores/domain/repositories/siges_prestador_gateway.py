from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SigesPrestadorInfo:
    """Lo que Siges (`dbo.Empresa`) sabe de un PST — solo lectura, la misma
    cuenta `db_datareader` que ya usa sla."""

    siges_empresa_id: int
    den_comercial: str
    razon_social: str | None
    cuit: str | None


class SigesPrestadorGateway(Protocol):
    """Puerto de sync: trae el estado actual en Siges de los PST ya conocidos
    por `siges_empresa_id`. No descubre PST nuevos — el alta es explícita
    desde la UI (ver ADR de diseño en el plan: evitar el problema del legacy,
    donde el sync creó automáticamente ~29 prestadores fuera de alcance)."""

    async def find_by_siges_ids(self, siges_empresa_ids: list[int]) -> list[SigesPrestadorInfo]: ...

    async def count_equipos_by_siges_ids(self, siges_empresa_ids: list[int]) -> dict[int, int]:
        """Parque de equipos activos por PST (`Sucursal.ID_Prestador` →
        `Maquina`), con la misma definición de "activo" que el reporte legacy
        'Maquinas Activas por Prestador' — paridad exacta verificada, ver
        docs/siges/SIGES_READONLY_CATALOGO_DATOS.md §3. Un PST sin equipos
        puede no aparecer en el dict: tratar ausencia como 0."""
        ...
