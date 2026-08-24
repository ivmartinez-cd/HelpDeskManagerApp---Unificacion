"""Factories del vínculo Empleado↔Siges — gateway y casos de uso. Singleton
de proceso (`lru_cache`) para el gateway, como el resto de los módulos que
consultan Mercurio. El chequeo de host y el runner con su semáforo viven en
`require_mercurio_runner` (ADR-018)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.application.use_cases.siges_vinculo import (
    ProponerVinculosSigesEmpleados,
    SigesVinculoPorts,
    VincularEmpleadoSiges,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.siges.pyodbc_siges_tecnico_gateway import (
    PyodbcSigesTecnicoGateway,
)
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner


@lru_cache
def get_siges_tecnico_gateway() -> PyodbcSigesTecnicoGateway:
    return PyodbcSigesTecnicoGateway(require_mercurio_runner())


def _ports(db: AsyncSession) -> SigesVinculoPorts:
    return SigesVinculoPorts(
        empleados=SqlAlchemyEmpleadoRepository(db), siges=get_siges_tecnico_gateway()
    )


def build_proponer_vinculos_siges(db: AsyncSession) -> ProponerVinculosSigesEmpleados:
    return ProponerVinculosSigesEmpleados(_ports(db))


def build_vincular_empleado_siges(db: AsyncSession) -> VincularEmpleadoSiges:
    return VincularEmpleadoSiges(_ports(db))
