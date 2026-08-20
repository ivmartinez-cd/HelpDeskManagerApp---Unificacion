"""CSV de geovalidación para Gestión (Fase 2, cierre del plan): Siges es
read-only, así que la corrección real la hace un humano en Gestión — este
CSV junta TODA la evidencia ya calculada (Tier 0 certeza absoluta, Tier 1b
confirmado por dos fuentes, Tier 2 confirmado por Google) en un solo
listado con Id_Sucursal, pin actual, pin sugerido y evidencia legible.
Read-only: no llama a ningún proveedor, solo combina resultados ya
cacheados/calculados por los use cases de cada tier."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1b import (
    HallazgoTier1b,
    ListarHallazgosTier1b,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_worklist import (
    CalcularWorklistTier2,
    ItemWorklist,
)
from src.modules.liquidaciones.application.use_cases.pines_sospechosos import (
    ListarPinesSospechosos,
    PinSospechoso,
)


@dataclass(frozen=True)
class WorklistCsvPorts:
    calcular_worklist: CalcularWorklistTier2
    listar_tier1b: ListarHallazgosTier1b
    listar_pines: ListarPinesSospechosos


@dataclass(frozen=True)
class FilaWorklistCsv:
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    tier: str
    evidencia: str
    latitud_actual: float | None
    longitud_actual: float | None
    latitud_sugerida: float | None
    longitud_sugerida: float | None


class GenerarWorklistCsv:
    def __init__(self, ports: WorklistCsvPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[FilaWorklistCsv]:
        worklist = await self._ports.calcular_worklist.execute(prestador_id)
        confirmados_1b = await self._ports.listar_tier1b.execute(prestador_id)
        pines = await self._ports.listar_pines.execute(prestador_id)
        return (
            [_fila_tier0(i) for i in worklist.certeza_absoluta]
            + [_fila_tier1b(h) for h in confirmados_1b]
            + [_fila_tier2(p) for p in pines]
        )


def _fila_tier0(i: ItemWorklist) -> FilaWorklistCsv:
    lat_sugerida = lon_sugerida = None
    if "latlon_invertidas" in i.motivos and i.latitud is not None and i.longitud is not None:
        lat_sugerida, lon_sugerida = i.longitud, i.latitud
    return FilaWorklistCsv(
        i.siges_sucursal_id, i.empresa_nombre, i.sucursal_nombre, i.domicilio,
        "0", "Certeza absoluta: " + ", ".join(i.motivos),
        i.latitud, i.longitud, lat_sugerida, lon_sugerida,
    )


def _fila_tier1b(h: HallazgoTier1b) -> FilaWorklistCsv:
    evidencia = (
        f"Georef+Nominatim coinciden: pin en {h.provincia_georef}, "
        f"declarado {h.provincia_declarada or 'sin dato'}"
    )
    return FilaWorklistCsv(
        h.siges_sucursal_id, h.empresa_nombre, h.sucursal_nombre, None,
        "1b", evidencia, h.latitud, h.longitud, None, None,
    )


def _fila_tier2(p: PinSospechoso) -> FilaWorklistCsv:
    evidencia = f"Google: {p.discrepancia_km:.1f} km de discrepancia ({p.location_type})"
    return FilaWorklistCsv(
        p.siges_sucursal_id, p.empresa_nombre, p.sucursal_nombre, p.direccion,
        "2", evidencia, p.latitud_siges, p.longitud_siges,
        p.latitud_geocode, p.longitud_geocode,
    )
