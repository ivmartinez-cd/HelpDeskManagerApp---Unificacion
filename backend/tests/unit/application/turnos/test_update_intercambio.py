"""Intercambio de turnos (ADR-026): edición in-place del par."""

import uuid
from datetime import date

import pytest

from src.modules.turnos.application.dtos.turno_dtos import (
    IntercambioCommand,
    UpdateAsignacionOverrideCommand,
)
from src.modules.turnos.application.use_cases.create_intercambio import CreateIntercambio
from src.modules.turnos.application.use_cases.intercambio_support import (
    IntercambioDependencies,
)
from src.modules.turnos.application.use_cases.update_asignacion_override import (
    UpdateAsignacionOverride,
    UpdateAsignacionOverrideDependencies,
)
from src.modules.turnos.application.use_cases.update_intercambio import UpdateIntercambio
from src.modules.turnos.domain.errors import (
    IntercambioNotFoundError,
    OverrideEsIntercambioError,
    OverrideNoEditableError,
)
from tests.unit.domain.turnos.fakes import FakeAsignacionOverrideRepository, FakeUserProvider

_MAJO = uuid.uuid4()
_LUNA = uuid.uuid4()
_CREADOR = uuid.uuid4()


def _command(intercambio_id: uuid.UUID | None = None, **overrides: object) -> IntercambioCommand:
    base = {
        "operador_a_id": _MAJO,
        "operador_b_id": _LUNA,
        "desde": date(2026, 8, 20),
        "hasta": date(2026, 8, 20),
        "slot_ids_a": None,
        "slot_ids_b": None,
        "motivo": None,
        "created_by_user_id": _CREADOR,
        "intercambio_id": intercambio_id,
    }
    base.update(overrides)
    return IntercambioCommand(**base)  # type: ignore[arg-type]


def _deps(repo: FakeAsignacionOverrideRepository) -> IntercambioDependencies:
    return IntercambioDependencies(overrides=repo, users=FakeUserProvider())


async def _intercambio_creado(repo: FakeAsignacionOverrideRepository) -> uuid.UUID:
    dto = await CreateIntercambio(_deps(repo)).execute(_command())
    return dto.intercambio_id


async def test_edita_fechas_y_alcance_conservando_ids_y_creador() -> None:
    repo = FakeAsignacionOverrideRepository()
    intercambio_id = await _intercambio_creado(repo)
    ids_antes = set(repo.rows)
    franja = uuid.uuid4()

    dto = await UpdateIntercambio(_deps(repo)).execute(
        _command(
            intercambio_id,
            desde=date(2026, 8, 21),
            hasta=date(2026, 8, 22),
            slot_ids_a=[franja],
            motivo="Cambio de turno",
        )
    )

    assert set(repo.rows) == ids_antes
    assert all(o.created_by_user_id == _CREADOR for o in repo.rows.values())
    assert all(o.intercambio_id == intercambio_id for o in repo.rows.values())
    ida, vuelta = dto.coberturas
    assert (ida.desde, ida.hasta) == (date(2026, 8, 21), date(2026, 8, 22))
    assert ida.slot_ids == [franja] and vuelta.alcance_total
    assert ida.motivo == "Cambio de turno"


async def test_rechaza_intercambio_inexistente() -> None:
    with pytest.raises(IntercambioNotFoundError):
        await UpdateIntercambio(_deps(FakeAsignacionOverrideRepository())).execute(
            _command(uuid.uuid4())
        )


async def test_rechaza_editar_un_intercambio_cancelado() -> None:
    repo = FakeAsignacionOverrideRepository()
    intercambio_id = await _intercambio_creado(repo)
    for o in repo.rows.values():
        o.estado = "CANCELADA"

    with pytest.raises(OverrideNoEditableError):
        await UpdateIntercambio(_deps(repo)).execute(_command(intercambio_id))


async def test_la_edicion_no_conflictua_con_el_propio_par() -> None:
    repo = FakeAsignacionOverrideRepository()
    intercambio_id = await _intercambio_creado(repo)

    # Mismas fechas, mismo alcance total: se excluye a sí mismo del solapamiento.
    dto = await UpdateIntercambio(_deps(repo)).execute(_command(intercambio_id, motivo="x"))

    assert dto.intercambio_id == intercambio_id


async def test_una_mitad_de_intercambio_no_se_edita_como_cobertura_comun() -> None:
    repo = FakeAsignacionOverrideRepository()
    await _intercambio_creado(repo)
    mitad = next(iter(repo.rows.values()))
    deps = UpdateAsignacionOverrideDependencies(overrides=repo, users=FakeUserProvider())

    with pytest.raises(OverrideEsIntercambioError):
        await UpdateAsignacionOverride(deps).execute(
            UpdateAsignacionOverrideCommand(
                override_id=mitad.id,
                operador_ausente_id=mitad.operador_ausente_id,
                operador_reemplazante_id=mitad.operador_reemplazante_id,
                desde=mitad.desde,
                hasta=mitad.hasta,
                slot_ids=None,
                motivo=None,
            )
        )
