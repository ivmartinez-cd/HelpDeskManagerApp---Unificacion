"""Constantes, contenedores de fakes y builders de body compartidos por los
tests de routers de turnos (las fixtures viven en conftest.py de este paquete)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionOverrideRepository,
    FakeAsignacionRepository,
    FakeCasillaRepository,
    FakeGrillaVarianteRepository,
    FakeSlotRepository,
    FakeUserProvider,
)

PREFIX = "/api/turnos"
MODULE = "turnos"
PAGE_KEYS = {"items", "total", "page", "size"}
OVERRIDE_KEYS = {
    "id", "operadorAusenteId", "operadorAusenteNombre", "operadorReemplazanteId",
    "operadorReemplazanteNombre", "desde", "hasta", "alcanceTotal", "slotIds", "estado",
    "motivo", "intercambioId",
}


@dataclass
class ReposTitular:
    """Grilla titular mínima: una casilla, una franja de hoy con Luna asignada."""

    casillas: FakeCasillaRepository
    slots: FakeSlotRepository
    asignaciones: FakeAsignacionRepository
    users: FakeUserProvider
    casilla: Casilla
    slot: Slot
    luna: uuid.UUID


@dataclass
class ReposCoberturas:
    """Coberturas/intercambios/grillas variantes: dos operadores y una casilla."""

    overrides: FakeAsignacionOverrideRepository
    variantes: FakeGrillaVarianteRepository
    casilla: Casilla
    majo: uuid.UUID
    luna: uuid.UUID


def override_body(repos: ReposCoberturas, **extra: object) -> dict[str, object]:
    return {
        "operadorAusenteId": str(repos.majo),
        "operadorReemplazanteId": str(repos.luna),
        "desde": "2026-08-24",
        "hasta": "2026-08-28",
        "motivo": "vacaciones",
        **extra,
    }


def variante_slot_body(repos: ReposCoberturas, **extra: object) -> dict[str, object]:
    return {
        "casillaId": str(repos.casilla.id),
        "diaSemana": 0,
        "horaInicio": "08:00",
        "horaFin": "11:00",
        "userIds": [str(repos.luna)],
        **extra,
    }


def variante_body(repos: ReposCoberturas, **extra: object) -> dict[str, object]:
    return {
        "motivo": "Vacaciones M. J. Vela",
        "desde": "2026-08-24",
        "hasta": "2026-08-28",
        "slots": [variante_slot_body(repos)],
        **extra,
    }
