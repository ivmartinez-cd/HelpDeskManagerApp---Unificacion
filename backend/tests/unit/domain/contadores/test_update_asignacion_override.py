import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.dtos.update_asignacion_override_request import (
    UpdateAsignacionOverrideRequest,
)
from src.modules.contadores.application.use_cases.update_asignacion_override import (
    UpdateAsignacionOverride,
    UpdateAsignacionOverrideDependencies,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.errors import (
    AsignacionOverrideNotFoundError,
    OperadorNoEncontradoError,
    OverlappingOverrideError,
    OverrideNoEditableError,
)

_AUSENTE = "mjvela"
_REEMPLAZANTE = "vipaez"
_OTRO_REEMPLAZANTE = "jlopez"
_CREADOR = uuid.uuid4()


def _existente(**overrides: object) -> AsignacionOverride:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "desde": date(2026, 8, 1),
        "hasta": date(2026, 8, 15),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": "vacaciones",
        "created_by_user_id": _CREADOR,
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


def _request(override_id: uuid.UUID, **overrides: object) -> UpdateAsignacionOverrideRequest:
    base = {
        "override_id": override_id,
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _OTRO_REEMPLAZANTE,
        "vigente_desde": date(2026, 8, 1),
        "vigente_hasta": date(2026, 8, 20),
        "clientes": None,
        "motivo": "licencia",
    }
    base.update(overrides)
    return UpdateAsignacionOverrideRequest(**base)  # type: ignore[arg-type]


def _deps(
    existing: AsignacionOverride | None, activos: list[AsignacionOverride] | None = None
) -> UpdateAsignacionOverrideDependencies:
    overrides = AsyncMock()
    overrides.get_by_id.return_value = existing
    overrides.list_activos_por_ausente.return_value = activos or (
        [existing] if existing is not None else []
    )
    calendar = AsyncMock()
    calendar.list_operadores.return_value = [
        Operador(id=_AUSENTE, nombre="Maria Jose Vela"),
        Operador(id=_REEMPLAZANTE, nombre="Victor Paez"),
        Operador(id=_OTRO_REEMPLAZANTE, nombre="Juan Lopez"),
    ]
    return UpdateAsignacionOverrideDependencies(overrides=overrides, calendar=calendar)


@pytest.mark.asyncio
async def test_edita_campos_conservando_id_y_creador() -> None:
    existing = _existente()
    deps = _deps(existing)

    dto = await UpdateAsignacionOverride(deps).execute(_request(existing.id))

    assert dto.id == existing.id
    assert dto.operador_reemplazante_nombre == "Juan Lopez"
    assert dto.vigente_hasta == date(2026, 8, 20)
    assert dto.motivo == "licencia"
    deps.overrides.update.assert_awaited_once()
    guardado = deps.overrides.update.await_args.args[0]
    assert guardado.created_by_user_id == _CREADOR
    assert guardado.estado == "ACTIVA"


@pytest.mark.asyncio
async def test_edita_alcance_de_total_a_parcial() -> None:
    existing = _existente()
    deps = _deps(existing)

    dto = await UpdateAsignacionOverride(deps).execute(
        _request(existing.id, clientes=["NEUMATICOS ROSMI SRL"])
    )

    assert dto.alcance_total is False
    assert dto.clientes == ["NEUMATICOS ROSMI SRL"]


@pytest.mark.asyncio
async def test_editar_inexistente_lanza_not_found() -> None:
    deps = _deps(None)

    with pytest.raises(AsignacionOverrideNotFoundError):
        await UpdateAsignacionOverride(deps).execute(_request(uuid.uuid4()))
    deps.overrides.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_rechaza_editar_un_override_cancelado() -> None:
    existing = _existente(estado="CANCELADA")
    deps = _deps(existing)

    with pytest.raises(OverrideNoEditableError):
        await UpdateAsignacionOverride(deps).execute(_request(existing.id))
    deps.overrides.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_rechaza_reemplazante_fuera_del_catalogo() -> None:
    existing = _existente()
    deps = _deps(existing)

    with pytest.raises(OperadorNoEncontradoError):
        await UpdateAsignacionOverride(deps).execute(
            _request(existing.id, operador_reemplazante_id="vpaez")
        )
    deps.overrides.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_no_conflictua_consigo_mismo_al_conservar_las_fechas() -> None:
    existing = _existente()
    deps = _deps(existing)

    dto = await UpdateAsignacionOverride(deps).execute(_request(existing.id))

    assert dto.estado == "ACTIVA"


@pytest.mark.asyncio
async def test_rechaza_solapamiento_con_otro_override_del_mismo_ausente() -> None:
    existing = _existente()
    otro = _existente(id=uuid.uuid4(), desde=date(2026, 9, 1), hasta=date(2026, 9, 10))
    deps = _deps(existing, activos=[existing, otro])

    with pytest.raises(OverlappingOverrideError):
        await UpdateAsignacionOverride(deps).execute(
            _request(existing.id, vigente_hasta=date(2026, 9, 5))
        )
    deps.overrides.update.assert_not_awaited()
