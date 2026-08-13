"""DTOs del sync de tarifarios y mapeo de zonas contra Siges (ADR-014, dataset 2)."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class GrupoTarifasCreadas:
    """Altas agregadas por grupo — el detalle fila por fila sería enorme (una
    vigencia por trimestre desde 2014) y no aporta a la decisión del usuario."""

    prestador: str
    tipo_servicio: str
    zona: str | None
    cantidad: int


@dataclass(frozen=True)
class ConflictoTarifario:
    prestador: str
    tipo_servicio: str
    zona: str | None
    vigencia_desde: date
    campo: str
    valor_local: float
    valor_siges: float


@dataclass(frozen=True)
class ZonaSinMapear:
    prestador: str
    descripcion_siges: str
    filas: int


@dataclass(frozen=True)
class SyncTarifariosResultado:
    dry_run: bool
    creados: int
    grupos_creados: list[GrupoTarifasCreadas]
    conflictos: list[ConflictoTarifario]
    sin_cambios: int
    zonas_sin_mapear: list[ZonaSinMapear]
    prestadores_sin_vinculo: list[str]


@dataclass(frozen=True)
class ZonaEstado:
    """Estado de mapeo de una descripción de Siges para un prestador vinculado —
    insumo de la pantalla de confirmación de mapeos. `mapeada` distingue el caso
    "mapeada a la zona genérica" (`mapeada=True, zona_local=None`) del caso
    "sin mapear" (`mapeada=False`)."""

    prestador_id: UUID
    prestador: str
    descripcion_siges: str
    mapeada: bool
    zona_local: str | None
    propuesta: str | None
    zonas_locales: list[str]


@dataclass(frozen=True)
class ZonasSigesResultado:
    zonas: list[ZonaEstado]
