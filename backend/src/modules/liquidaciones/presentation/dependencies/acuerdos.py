"""Builders de los casos de uso de acuerdos de precio por cliente."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.config_acuerdos import (
    ConfigAcuerdosPorts,
    CreateAcuerdo,
    DeleteAcuerdo,
    ListAcuerdos,
    UpdateAcuerdo,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_acuerdo_precio_cliente_repository import (  # noqa: E501
    SqlAlchemyAcuerdoPrecioClienteRepository,
)


def _ports(session: AsyncSession) -> ConfigAcuerdosPorts:
    return ConfigAcuerdosPorts(acuerdos=SqlAlchemyAcuerdoPrecioClienteRepository(session))


def build_list_acuerdos(session: AsyncSession) -> ListAcuerdos:
    return ListAcuerdos(_ports(session))


def build_create_acuerdo(session: AsyncSession) -> CreateAcuerdo:
    return CreateAcuerdo(_ports(session))


def build_update_acuerdo(session: AsyncSession) -> UpdateAcuerdo:
    return UpdateAcuerdo(_ports(session))


def build_delete_acuerdo(session: AsyncSession) -> DeleteAcuerdo:
    return DeleteAcuerdo(_ports(session))
