"""Los routers del apartado "Administración" de Insumos (Clientes, Configuración,
Estadísticas) exigen la función `insumos-administracion` a nivel router
(ADR-032): sin ella, 403 aunque se tenga `insumos.view`."""

import uuid

import pytest
from fastapi import APIRouter

from src.modules.auth.application.dtos.results import Identity, UserView
from src.modules.auth.domain.errors import ForbiddenError
from src.modules.insumos.domain.well_known_features import ADMINISTRACION
from src.modules.insumos.presentation import config_router, customers_router, statistics_router

_ROUTERS = [customers_router.router, config_router.router, statistics_router.router]


def _identity(*features: str) -> Identity:
    return Identity(
        user=UserView(
            id=uuid.uuid4(),
            email="op@example.com",
            full_name="Op",
            is_superadmin=False,
            color=None,
        ),
        permissions=frozenset({("insumos", "view"), ("insumos", "update")}),
        session_id=uuid.uuid4(),
        features=frozenset(features),
    )


async def _run_router_dependencies(router: APIRouter, identity: Identity) -> None:
    assert router.dependencies, "el router tiene que exigir la función a nivel router"
    for dep in router.dependencies:
        await dep.dependency(identity=identity)  # type: ignore[misc]


@pytest.mark.parametrize("router", _ROUTERS, ids=["customers", "config", "statistics"])
async def test_sin_la_funcion_es_403_aunque_tenga_view(router: APIRouter) -> None:
    with pytest.raises(ForbiddenError):
        await _run_router_dependencies(router, _identity())


@pytest.mark.parametrize("router", _ROUTERS, ids=["customers", "config", "statistics"])
async def test_con_la_funcion_pasa(router: APIRouter) -> None:
    await _run_router_dependencies(router, _identity(ADMINISTRACION.value))
