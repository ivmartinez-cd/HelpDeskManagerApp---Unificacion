"""Casos de uso del vínculo Empleado↔técnico de Siges (mismo criterio que
`liquidaciones/application/use_cases/siges_config.py`, ADR-014, adaptado a un
solo tipo de entidad local): la propuesta es solo matching de alta confianza,
la confirmación de cada vínculo es siempre manual."""

import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.siges_vinculo_dtos import (
    PropuestasVinculoEmpleadoResultado,
    PropuestaVinculoEmpleado,
    SigesTecnicoDisponibleDTO,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.errors import EmpleadoNoEncontradoError
from src.modules.vacaciones.domain.repositories.empleado_repository import (
    EmpleadoRepository,
    FiltrosEmpleados,
)
from src.modules.vacaciones.domain.repositories.siges_tecnico_gateway import SigesTecnicoGateway
from src.modules.vacaciones.domain.services.vinculacion_siges import (
    SigesTecnicoInfo,
    proponer_vinculos,
)


@dataclass(frozen=True)
class SigesVinculoPorts:
    empleados: EmpleadoRepository
    siges: SigesTecnicoGateway


class ProponerVinculosSigesEmpleados:
    def __init__(self, ports: SigesVinculoPorts) -> None:
        self._ports = ports

    async def execute(self) -> PropuestasVinculoEmpleadoResultado:
        tecnicos = await self._ports.siges.list_tecnicos_activos()
        empleados = await self._ports.empleados.list_filtrados(FiltrosEmpleados())
        vinculados = {e.siges_empresa_id for e in empleados if e.siges_empresa_id is not None}
        candidatos = [t for t in tecnicos if t.siges_empresa_id not in vinculados]
        sin_vinculo = [e for e in empleados if e.siges_empresa_id is None]

        propuestas = _construir_propuestas(sin_vinculo, candidatos)
        disponibles = _construir_disponibles(candidatos, propuestas)
        return PropuestasVinculoEmpleadoResultado(propuestas=propuestas, disponibles=disponibles)


class VincularEmpleadoSiges:
    def __init__(self, ports: SigesVinculoPorts) -> None:
        self._ports = ports

    async def execute(
        self, empleado_id: uuid.UUID, *, siges_empresa_id: int | None
    ) -> Empleado:
        actualizado = await self._ports.empleados.vincular_siges(
            empleado_id, siges_empresa_id=siges_empresa_id
        )
        if actualizado is None:
            raise EmpleadoNoEncontradoError(empleado_id)
        return actualizado


def _construir_propuestas(
    sin_vinculo: list[Empleado], candidatos: list[SigesTecnicoInfo]
) -> list[PropuestaVinculoEmpleado]:
    matches = proponer_vinculos([(e.id, e.nombre_completo) for e in sin_vinculo], candidatos)
    nombres = {e.id: e.nombre_completo for e in sin_vinculo}
    den_por_id = {t.siges_empresa_id: t.den_comercial for t in candidatos}
    return [
        PropuestaVinculoEmpleado(
            empleado_id=eid,
            empleado_nombre=nombres[eid],
            siges_empresa_id=sid,
            siges_den_comercial=den_por_id[sid],
        )
        for eid, sid in matches.items()
    ]


def _construir_disponibles(
    candidatos: list[SigesTecnicoInfo], propuestas: list[PropuestaVinculoEmpleado]
) -> list[SigesTecnicoDisponibleDTO]:
    propuestos = {p.siges_empresa_id for p in propuestas}
    return [
        SigesTecnicoDisponibleDTO(
            siges_empresa_id=t.siges_empresa_id, den_comercial=t.den_comercial
        )
        for t in candidatos
        if t.siges_empresa_id not in propuestos
    ]
