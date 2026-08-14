"""Factories de wiring de sla: el gateway exige MERCURIO configurado (chequeo
centralizado en `require_mercurio_runner`, ADR-018) y los builders arman el
grafo de use cases sin tocar la DB."""

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import src.modules.sla.presentation.dependencies as deps_module
import src.shared.infrastructure.mercurio.factories as mercurio_factories
from src.modules.sla.application.use_cases.get_sla_compliance import GetSlaCompliance
from src.modules.sla.application.use_cases.list_incidentes_vencidos import (
    ListIncidentesVencidos,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.shared.domain.errors import ExternalServiceError
from tests.unit.infrastructure.contadores.settings_stub import make_settings

_SESSION = cast(AsyncSession, object())  # los builders solo lo inyectan, no lo usan


@pytest.fixture(autouse=True)
def _reset_gateway_cache() -> None:
    deps_module.get_sla_query_gateway.cache_clear()
    mercurio_factories.require_mercurio_runner.cache_clear()


def test_gateway_sin_mercurio_configurado_falla_con_mensaje_claro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mercurio_factories, "get_settings", lambda: make_settings(sla_mercurio_host="")
    )
    with pytest.raises(ExternalServiceError, match="SLA_MERCURIO_HOST"):
        deps_module.get_sla_query_gateway()


def test_builders_arman_el_grafo_de_use_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mercurio_factories,
        "get_settings",
        lambda: make_settings(
            sla_mercurio_host="mercurio.test",
            sla_mercurio_user="u",
            sla_mercurio_password="p",
        ),
    )

    assert isinstance(deps_module.build_refresh_sla_snapshot(_SESSION), RefreshSlaSnapshot)
    assert isinstance(deps_module.build_get_sla_compliance(_SESSION), GetSlaCompliance)
    assert isinstance(
        deps_module.build_list_incidentes_vencidos(_SESSION), ListIncidentesVencidos
    )
