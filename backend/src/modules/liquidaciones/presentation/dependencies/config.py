"""Factories de los casos de uso de escritura de configuración — arman el
repositorio SQLAlchemy scoped a la sesión del request y lo inyectan en el Ports."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.config_prestadores import (
    ConfigPrestadoresPorts,
    CreatePrestador,
    DeletePrestador,
    TogglePrestadorActivo,
    UpdatePrestador,
)
from src.modules.liquidaciones.application.use_cases.config_spsts import (
    ConfigSpstsPorts,
    CreateSpst,
    DeleteSpst,
    ToggleSpstActivo,
    UpdateSpst,
)
from src.modules.liquidaciones.application.use_cases.config_tabla_km import (
    ConfigTablaKmPorts,
    CreateTablaKm,
    DeleteTablaKm,
    UpdateTablaKm,
)
from src.modules.liquidaciones.application.use_cases.config_tarifarios import (
    ConfigTarifariosPorts,
    CreateTarifario,
    DeleteTarifario,
    UpdateTarifario,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (  # noqa: E501
    SqlAlchemyTarifarioRepository,
)


def _prestadores_ports(session: AsyncSession) -> ConfigPrestadoresPorts:
    return ConfigPrestadoresPorts(prestadores=SqlAlchemyPrestadorRepository(session))


def build_create_prestador(session: AsyncSession) -> CreatePrestador:
    return CreatePrestador(_prestadores_ports(session))


def build_update_prestador(session: AsyncSession) -> UpdatePrestador:
    return UpdatePrestador(_prestadores_ports(session))


def build_toggle_prestador_activo(session: AsyncSession) -> TogglePrestadorActivo:
    return TogglePrestadorActivo(_prestadores_ports(session))


def build_delete_prestador(session: AsyncSession) -> DeletePrestador:
    return DeletePrestador(_prestadores_ports(session))


def _spsts_ports(session: AsyncSession) -> ConfigSpstsPorts:
    return ConfigSpstsPorts(spsts=SqlAlchemySpstRepository(session))


def build_create_spst(session: AsyncSession) -> CreateSpst:
    return CreateSpst(_spsts_ports(session))


def build_update_spst(session: AsyncSession) -> UpdateSpst:
    return UpdateSpst(_spsts_ports(session))


def build_toggle_spst_activo(session: AsyncSession) -> ToggleSpstActivo:
    return ToggleSpstActivo(_spsts_ports(session))


def build_delete_spst(session: AsyncSession) -> DeleteSpst:
    return DeleteSpst(_spsts_ports(session))


def _tarifarios_ports(session: AsyncSession) -> ConfigTarifariosPorts:
    return ConfigTarifariosPorts(tarifarios=SqlAlchemyTarifarioRepository(session))


def build_create_tarifario(session: AsyncSession) -> CreateTarifario:
    return CreateTarifario(_tarifarios_ports(session))


def build_update_tarifario(session: AsyncSession) -> UpdateTarifario:
    return UpdateTarifario(_tarifarios_ports(session))


def build_delete_tarifario(session: AsyncSession) -> DeleteTarifario:
    return DeleteTarifario(_tarifarios_ports(session))


def _tabla_km_ports(session: AsyncSession) -> ConfigTablaKmPorts:
    return ConfigTablaKmPorts(tabla_km=SqlAlchemyTablaKmRepository(session))


def build_create_tabla_km(session: AsyncSession) -> CreateTablaKm:
    return CreateTablaKm(_tabla_km_ports(session))


def build_update_tabla_km(session: AsyncSession) -> UpdateTablaKm:
    return UpdateTablaKm(_tabla_km_ports(session))


def build_delete_tabla_km(session: AsyncSession) -> DeleteTablaKm:
    return DeleteTablaKm(_tabla_km_ports(session))
