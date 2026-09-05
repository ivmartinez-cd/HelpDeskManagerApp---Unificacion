"""Caso de uso de vínculo Tabla KM ↔ SPST por coincidencia de localidad — ver
`domain/services/vincular_tabla_km_spst.py` para el motivo. Dry-run first-class,
mismo patrón que el sync de tarifarios de Siges (ADR-014)."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.vincular_tabla_km_spst import (
    CRITERIO_PROVINCIA,
    PropuestaVinculoSpst,
    proponer_vinculos_spst,
)

_MAX_EJEMPLOS = 20


@dataclass(frozen=True)
class VincularTablaKmSpstPorts:
    tabla_km: TablaKmRepository
    spsts: SpstRepository


@dataclass(frozen=True)
class ResultadoVinculoTablaKmSpst:
    dry_run: bool
    total_sin_vincular: int
    con_propuesta: int
    sin_propuesta: int
    vinculadas: int
    ejemplos: list[PropuestaVinculoSpst]
    # Propuestas que salieron solo por provincia — se aplican únicamente con
    # `incluir_provincia=True` (decisión de la TL por prestador, ver dominio).
    por_provincia: int = 0


class VincularTablaKmSpst:
    def __init__(self, ports: VincularTablaKmSpstPorts) -> None:
        self._ports = ports

    async def execute(
        self, prestador_id: UUID, *, dry_run: bool, incluir_provincia: bool = False
    ) -> ResultadoVinculoTablaKmSpst:
        filas = await self._ports.tabla_km.list_by_prestador(prestador_id)
        spsts = await self._ports.spsts.list_by_prestador(prestador_id)
        propuestas = proponer_vinculos_spst(filas, spsts)
        por_provincia = [p for p in propuestas if p.criterio == CRITERIO_PROVINCIA]
        con_propuesta = [
            p
            for p in propuestas
            if p.spst_id is not None and (incluir_provincia or p.criterio != CRITERIO_PROVINCIA)
        ]

        vinculadas = 0
        if not dry_run:
            for propuesta in con_propuesta:
                await self._ports.tabla_km.update_vinculo_spst(
                    propuesta.tabla_km_id, spst_id=propuesta.spst_id
                )
                vinculadas += 1

        return ResultadoVinculoTablaKmSpst(
            dry_run=dry_run,
            total_sin_vincular=len(propuestas),
            con_propuesta=len(con_propuesta),
            sin_propuesta=len(propuestas) - len(con_propuesta),
            vinculadas=vinculadas,
            ejemplos=propuestas[:_MAX_EJEMPLOS],
            por_provincia=len(por_provincia),
        )
