import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.dtos.create_asignacion_override_request import (
    CreateAsignacionOverrideRequest,
)
from src.modules.contadores.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.errors import (
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
)

_AUSENTE = "mjvela"
_REEMPLAZANTE = "vipaez"


def _request(**overrides: object) -> CreateAsignacionOverrideRequest:
    base = {
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "vigente_desde": date(2026, 8, 1),
        "vigente_hasta": date(2026, 8, 15),
        "clientes": None,
        "motivo": "vacaciones",
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return CreateAsignacionOverrideRequest(**base)  # type: ignore[arg-type]


def _existente(**overrides: object) -> AsignacionOverride:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "vigente_desde": date(2026, 8, 1),
        "vigente_hasta": date(2026, 8, 15),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": None,
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


def _deps(existentes: list[AsignacionOverride]) -> CreateAsignacionOverrideDependencies:
    overrides = AsyncMock()
    overrides.list_activos_por_ausente.return_value = existentes
    calendar = AsyncMock()
    calendar.list_operadores.return_value = [
        Operador(id=_AUSENTE, nombre="Maria Jose Vela"),
        Operador(id=_REEMPLAZANTE, nombre="Victor Paez"),
    ]
    return CreateAsignacionOverrideDependencies(overrides=overrides, calendar=calendar)


@pytest.mark.asyncio
async def test_crea_override_alcance_total() -> None:
    deps = _deps([])

    dto = await CreateAsignacionOverride(deps).execute(_request())

    assert dto.alcance_total is True
    assert dto.clientes == []
    assert dto.operador_ausente_nombre == "Maria Jose Vela"
    assert dto.operador_reemplazante_nombre == "Victor Paez"
    assert dto.estado == "ACTIVA"
    deps.overrides.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_crea_override_alcance_por_cliente() -> None:
    deps = _deps([])

    dto = await CreateAsignacionOverride(deps).execute(
        _request(clientes=["NEUMATICOS ROSMI SRL"])
    )

    assert dto.alcance_total is False
    assert dto.clientes == ["NEUMATICOS ROSMI SRL"]


@pytest.mark.asyncio
async def test_rechaza_rango_invalido() -> None:
    deps = _deps([])

    with pytest.raises(InvalidOverrideRangeError):
        await CreateAsignacionOverride(deps).execute(
            _request(vigente_desde=date(2026, 8, 15), vigente_hasta=date(2026, 8, 1))
        )


@pytest.mark.asyncio
async def test_rechaza_mismo_operador_como_ausente_y_reemplazante() -> None:
    deps = _deps([])

    with pytest.raises(OverrideMismoOperadorError):
        await CreateAsignacionOverride(deps).execute(
            _request(operador_reemplazante_id=_AUSENTE)
        )


@pytest.mark.asyncio
async def test_rechaza_solapamiento_con_override_total_existente() -> None:
    deps = _deps([_existente()])

    with pytest.raises(OverlappingOverrideError):
        await CreateAsignacionOverride(deps).execute(
            _request(vigente_desde=date(2026, 8, 10), vigente_hasta=date(2026, 8, 20))
        )


@pytest.mark.asyncio
async def test_permite_overrides_puntuales_de_clientes_distintos_con_fechas_solapadas() -> None:
    deps = _deps([_existente(alcance=frozenset({"CLIENTE A"}))])

    dto = await CreateAsignacionOverride(deps).execute(
        _request(clientes=["CLIENTE B"])
    )

    assert dto.estado == "ACTIVA"
