from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GrupoEconomicoOption:
    id: int
    descripcion: str


@dataclass(frozen=True, slots=True)
class ProcesoOption:
    nro_proceso: int
    periodo_facturacion: str
    nombre_anexo: str
    periodo_hasta: date
    id_anexo: int


@dataclass(frozen=True, slots=True)
class AnexoOption:
    id_anexo: int
    nombre_anexo: str


class ProcesoEstimacionPort(Protocol):
    """Puerto de solo lectura contra Siges — combos de selección de la
    pantalla principal del Estimador (MODELO_DE_DATOS.md §3.1-§3.3)."""

    async def list_grupos_economicos_activos(self) -> list[GrupoEconomicoOption]:
        """Grupos con al menos un proceso abierto en un anexo activo, con
        actividad en los últimos 2 años."""
        ...

    async def list_procesos_por_grupo(self, id_grupo_economico: int) -> list[ProcesoOption]:
        """Procesos abiertos del grupo, solo en anexos activos."""
        ...

    async def list_anexos_por_grupo(self, id_grupo_economico: int) -> list[AnexoOption]:
        """Anexos activos del grupo — para acotar el alcance de un receso."""
        ...
