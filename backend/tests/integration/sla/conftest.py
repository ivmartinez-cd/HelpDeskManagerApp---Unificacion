"""Fixtures de los tests de routers de sla: sesión fake (view / view+update /
sin grant) y los factories de ambos routers monkeypatcheados con gateways y
repos en memoria (tests/unit/domain/sla/fakes.py,
tests/unit/application/sla/fakes_pendientes.py). Sin DB ni MERCURIO."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

import src.modules.sla.presentation.mesa_ayuda_router as mesa_ayuda_router
import src.modules.sla.presentation.pendientes_router as pendientes_router
import src.modules.sla.presentation.sla_router as sla_router
from src.modules.sla.application.use_cases.get_pendientes_resumen import GetPendientesResumen
from src.modules.sla.application.use_cases.get_sla_compliance import GetSlaCompliance
from src.modules.sla.application.use_cases.list_incidentes_mesa_ayuda import (
    ListIncidentesMesaAyuda,
)
from src.modules.sla.application.use_cases.list_incidentes_vencidos import (
    ListIncidentesVencidos,
)
from src.modules.sla.application.use_cases.list_pendientes import ListPendientes
from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.domain.entities.incidente_sla import RESULTADO_CORRECTO, RESULTADO_VENCIDO
from tests.integration.router_testing import install_session, uninstall_session
from tests.integration.sla.support import MODULE, PST_AJENO, PST_PROPIO, Lookup
from tests.unit.application.sla.fakes_mesa_ayuda import (
    FakeMesaAyudaQueryGateway,
    build_mesa_ayuda,
)
from tests.unit.application.sla.fakes_pendientes import (
    FakePendientesQueryGateway,
    FakePendientesSnapshotRepository,
    build_sin_cerrar,
)
from tests.unit.domain.sla.fakes import (
    FakeSlaQueryGateway,
    FakeSlaSnapshotRepository,
    build_incidente,
)

MESA_ID_TECNICO = 428


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, (MODULE, "view"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_update(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, (MODULE, "view"), (MODULE, "update"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_sin_grant(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def lookup(monkeypatch: pytest.MonkeyPatch) -> Lookup:
    lk = Lookup()
    monkeypatch.setattr(sla_router, "SqlAlchemyPrestadorLookup", lambda _db: lk)
    monkeypatch.setattr(pendientes_router, "SqlAlchemyPrestadorLookup", lambda _db: lk)
    return lk


@pytest.fixture
def sla_gateway(monkeypatch: pytest.MonkeyPatch) -> FakeSlaQueryGateway:
    gateway = FakeSlaQueryGateway(
        [
            build_incidente(1, "Tecnico Propio", RESULTADO_CORRECTO, id_tecnico=PST_PROPIO),
            build_incidente(2, "Tecnico Propio", RESULTADO_VENCIDO, id_tecnico=PST_PROPIO),
            build_incidente(3, "Tecnico Ajeno", RESULTADO_VENCIDO, id_tecnico=PST_AJENO),
        ]
    )
    repo = FakeSlaSnapshotRepository()
    refresher = RefreshSlaSnapshot(gateway, repo)
    monkeypatch.setattr(sla_router, "build_refresh_sla_snapshot", lambda _db: refresher)
    monkeypatch.setattr(
        sla_router, "build_get_sla_compliance", lambda _db: GetSlaCompliance(repo, refresher)
    )
    monkeypatch.setattr(
        sla_router,
        "build_list_incidentes_vencidos",
        lambda _db: ListIncidentesVencidos(repo, refresher),
    )
    return gateway


@pytest.fixture
def pendientes_gateway(
    monkeypatch: pytest.MonkeyPatch, lookup: Lookup
) -> FakePendientesQueryGateway:
    gateway = FakePendientesQueryGateway(
        [
            build_sin_cerrar(10, PST_PROPIO, "Tecnico Propio", dias_en_estado=3),
            build_sin_cerrar(11, PST_PROPIO, "Tecnico Propio", dias_en_estado=9),
            build_sin_cerrar(12, PST_AJENO, "Tecnico Ajeno", dias_en_estado=1),
            build_sin_cerrar(13, 99, "Sin PST", dias_en_estado=1),  # no es PST: se descarta
        ]
    )
    repo = FakePendientesSnapshotRepository()
    refresher = RefreshPendientesSnapshot(gateway, repo, pst_lookup=lookup, meses_corte=6)
    monkeypatch.setattr(
        pendientes_router, "build_refresh_pendientes_snapshot", lambda _db: refresher
    )
    monkeypatch.setattr(
        pendientes_router,
        "build_get_pendientes_resumen",
        lambda _db: GetPendientesResumen(repo, refresher),
    )
    monkeypatch.setattr(
        pendientes_router, "build_list_pendientes", lambda _db: ListPendientes(repo, refresher)
    )
    return gateway


@pytest.fixture
def mesa_ayuda_gateway(monkeypatch: pytest.MonkeyPatch) -> FakeMesaAyudaQueryGateway:
    gateway = FakeMesaAyudaQueryGateway(
        [
            build_mesa_ayuda(100, operador_login="vipaez", dias_transcurridos=3),
            build_mesa_ayuda(101, operador_login="ltorres", dias_transcurridos=9),
        ]
    )
    use_case = ListIncidentesMesaAyuda(gateway, MESA_ID_TECNICO)
    monkeypatch.setattr(mesa_ayuda_router, "build_list_incidentes_mesa_ayuda", lambda: use_case)
    return gateway
