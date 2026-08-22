"""Fixtures de los tests de routers de turnos: sesión fake (view / view+manage /
solo sesión) y los repos SQLAlchemy que cada router instancia reemplazados por
los fakes en memoria de tests/unit/domain/turnos. Sin DB."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import date, datetime, time
from types import ModuleType
from zoneinfo import ZoneInfo

import pytest

import src.modules.turnos.presentation.casillas_router as casillas_router
import src.modules.turnos.presentation.grilla_variantes_router as grilla_router
import src.modules.turnos.presentation.intercambios_router as intercambios_router
import src.modules.turnos.presentation.overrides_router as overrides_router
import src.modules.turnos.presentation.slots_router as slots_router
import src.modules.turnos.presentation.turnos_router as turnos_router
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from tests.integration.router_testing import install_session, uninstall_session
from tests.integration.turnos.support import MODULE, ReposCoberturas, ReposTitular
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionOverrideRepository,
    FakeAsignacionRepository,
    FakeAusenciasLookup,
    FakeCasillaRepository,
    FakeGrillaVarianteRepository,
    FakeSlotRepository,
    FakeUserProvider,
)

_HOY = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()


def _patch_repos(
    monkeypatch: pytest.MonkeyPatch, modules: tuple[ModuleType, ...], fakes: dict[str, object]
) -> None:
    for module in modules:
        for name, fake in fakes.items():
            if hasattr(module, name):
                monkeypatch.setattr(module, name, lambda _db, fake=fake: fake)


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, (MODULE, "view"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_manage(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, (MODULE, "view"), (MODULE, "manage"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_solo_sesion(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Sesión válida sin ningún grant de turnos: `/current` igual responde."""
    install_session(monkeypatch, ("insumos", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def repos_titular(monkeypatch: pytest.MonkeyPatch) -> ReposTitular:
    casilla = Casilla(
        id=uuid.uuid4(), nombre="INSUMOS", color="#F7941D", sort_order=0, is_active=True
    )
    slot = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla.id,
        hora_inicio=time(0, 0),
        hora_fin=time(23, 59),
        dia_semana=_HOY.weekday(),
        sort_order=0,
    )
    luna = uuid.uuid4()
    casillas, slots = FakeCasillaRepository(), FakeSlotRepository()
    asignaciones, users = FakeAsignacionRepository(), FakeUserProvider()
    casillas.rows[casilla.id] = casilla
    slots.rows[slot.id] = slot
    asignacion = Asignacion(
        id=uuid.uuid4(), slot_id=slot.id, user_id=luna, vigente_desde=date(2020, 1, 1),
        vigente_hasta=None,
    )
    asignaciones.rows[asignacion.id] = asignacion
    users.users[luna] = UserInfo(id=luna, full_name="Luna Torres", color="#123456")
    users.active_ids.add(luna)
    _patch_repos(
        monkeypatch,
        (turnos_router, casillas_router, slots_router),
        {
            "SqlAlchemyCasillaRepository": casillas,
            "SqlAlchemySlotRepository": slots,
            "SqlAlchemyAsignacionRepository": asignaciones,
            "SqlAlchemyUserProvider": users,
            "SqlAlchemyAsignacionOverrideRepository": FakeAsignacionOverrideRepository(),
            "SqlAlchemyGrillaVarianteRepository": FakeGrillaVarianteRepository(),
            "SqlAlchemyAusenciasLookup": FakeAusenciasLookup(),
        },
    )
    return ReposTitular(casillas, slots, asignaciones, users, casilla, slot, luna)


@pytest.fixture
def repos_coberturas(monkeypatch: pytest.MonkeyPatch) -> ReposCoberturas:
    majo, luna = uuid.uuid4(), uuid.uuid4()
    casilla = Casilla(id=uuid.uuid4(), nombre="INSUMOS", color=None, sort_order=0, is_active=True)
    casillas = FakeCasillaRepository()
    casillas.rows[casilla.id] = casilla
    users = FakeUserProvider()
    users.users[majo] = UserInfo(id=majo, full_name="Maria Jose Vela")
    users.users[luna] = UserInfo(id=luna, full_name="Luna Torres")
    overrides, variantes = FakeAsignacionOverrideRepository(), FakeGrillaVarianteRepository()
    _patch_repos(
        monkeypatch,
        (overrides_router, intercambios_router, grilla_router),
        {
            "SqlAlchemyAsignacionOverrideRepository": overrides,
            "SqlAlchemyUserProvider": users,
            "SqlAlchemyGrillaVarianteRepository": variantes,
            "SqlAlchemyCasillaRepository": casillas,
            "SqlAlchemySlotRepository": FakeSlotRepository(),
            "SqlAlchemyAsignacionRepository": FakeAsignacionRepository(),
            "SqlAlchemyAusenciasLookup": FakeAusenciasLookup(),
        },
    )
    return ReposCoberturas(overrides, variantes, casilla, majo, luna)
