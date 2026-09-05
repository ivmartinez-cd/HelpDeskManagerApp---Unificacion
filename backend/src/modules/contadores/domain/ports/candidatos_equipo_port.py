from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LecturaCandidataSiges:
    fecha: date
    tipo_toma: int
    valor: float
    para_facturar: bool


@dataclass(frozen=True, slots=True)
class MetadataEquipoSiges:
    nro_serie: str
    empresa: str
    sucursal: str
    sector: str | None
    modelo: str
    id_tecnologia: int
    velocidad: float | None


class CandidatosEquipoPort(Protocol):
    """Puerto de solo lectura contra Siges para el panel de candidatos
    manuales del Estimador (MODELO_DE_DATOS.md §3.6)."""

    async def fetch_lecturas(
        self, id_maquina: int, id_clase_contador: int
    ) -> list[LecturaCandidataSiges]:
        """Últimas 24 lecturas del equipo/clase, más recientes primero."""
        ...

    async def fetch_metadata_equipo(self, id_maquina: int) -> MetadataEquipoSiges | None:
        """Identidad del equipo (ubicación y modelo actuales) — `None` si el
        `ID_Maquina` no existe en Siges."""
        ...
