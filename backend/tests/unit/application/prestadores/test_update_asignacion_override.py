import uuid
from datetime import date

import pytest

from src.modules.prestadores.application.dtos.prestador_dtos import (
    UpdateAsignacionOverrideCommand,
)
from src.modules.prestadores.application.use_cases.update_asignacion_override import (
    UpdateAsignacionOverride,
    UpdateAsignacionOverrideDependencies,
)
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import (
    AsignacionOverrideNotFoundError,
    InvalidOverrideRangeError,
    OperadorNoEncontradoError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
    OverrideNoEditableError,
    PrestadorNotFoundError,
)
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
    FakeAsignacionOverrideRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)

_AUSENTE = uuid.uuid4()
_REEMPLAZANTE = uuid.uuid4()
_OTRO_REEMPLAZANTE = uuid.uuid4()
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


def _command(override_id: uuid.UUID, **overrides: object) -> UpdateAsignacionOverrideCommand:
    base = {
        "override_id": override_id,
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _OTRO_REEMPLAZANTE,
        "desde": date(2026, 8, 1),
        "hasta": date(2026, 8, 20),
        "prestador_ids": None,
        "motivo": "licencia",
    }
    base.update(overrides)
    return UpdateAsignacionOverrideCommand(**base)  # type: ignore[arg-type]


def _deps(
    overrides: FakeAsignacionOverrideRepository,
    prestadores: FakePrestadorRepository | None = None,
) -> UpdateAsignacionOverrideDependencies:
    users = FakeUserProvider()
    users.users[_AUSENTE] = UserInfo(id=_AUSENTE, full_name="Ausente Real")
    users.users[_OTRO_REEMPLAZANTE] = UserInfo(
        id=_OTRO_REEMPLAZANTE, full_name="Reemplazante Nuevo"
    )
    return UpdateAsignacionOverrideDependencies(
        overrides=overrides, users=users, prestadores=prestadores or FakePrestadorRepository()
    )


def _prestador_existente(prestadores: FakePrestadorRepository) -> uuid.UUID:
    pst = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="PST Rosario",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=_AUSENTE,
        is_active=True,
    )
    prestadores.rows[pst.id] = pst
    return pst.id


async def test_edita_campos_conservando_id_y_creador() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    dto = await UpdateAsignacionOverride(_deps(repo)).execute(_command(override.id))

    assert dto.id == override.id
    assert dto.operador_reemplazante_nombre == "Reemplazante Nuevo"
    assert dto.hasta == date(2026, 8, 20)
    assert dto.motivo == "licencia"
    assert repo.rows[override.id].created_by_user_id == _CREADOR
    assert repo.rows[override.id].estado == "ACTIVA"


async def test_edita_alcance_de_total_a_parcial() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override
    prestadores = FakePrestadorRepository()
    pst = _prestador_existente(prestadores)

    dto = await UpdateAsignacionOverride(_deps(repo, prestadores)).execute(
        _command(override.id, prestador_ids=[pst])
    )

    assert dto.alcance_total is False
    assert dto.prestador_ids == [pst]


async def test_rechaza_reemplazante_o_prestador_inexistentes() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    with pytest.raises(OperadorNoEncontradoError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, operador_reemplazante_id=uuid.uuid4())
        )
    with pytest.raises(PrestadorNotFoundError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, prestador_ids=[uuid.uuid4()])
        )
    assert repo.rows[override.id].motivo == "vacaciones"


async def test_editar_inexistente_lanza_not_found() -> None:
    repo = FakeAsignacionOverrideRepository()

    with pytest.raises(AsignacionOverrideNotFoundError):
        await UpdateAsignacionOverride(_deps(repo)).execute(_command(uuid.uuid4()))


async def test_rechaza_editar_un_override_cancelado() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente(estado="CANCELADA")
    repo.rows[override.id] = override

    with pytest.raises(OverrideNoEditableError):
        await UpdateAsignacionOverride(_deps(repo)).execute(_command(override.id))


async def test_rechaza_rango_invalido() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    with pytest.raises(InvalidOverrideRangeError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, desde=date(2026, 8, 20), hasta=date(2026, 8, 1))
        )


async def test_rechaza_mismo_operador_como_ausente_y_reemplazante() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    with pytest.raises(OverrideMismoOperadorError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, operador_reemplazante_id=_AUSENTE)
        )


async def test_no_conflictua_consigo_mismo_al_conservar_las_fechas() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    dto = await UpdateAsignacionOverride(_deps(repo)).execute(_command(override.id))

    assert dto.estado == "ACTIVA"


async def test_rechaza_solapamiento_con_otro_override_del_mismo_ausente() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    otro = _existente(id=uuid.uuid4(), desde=date(2026, 9, 1), hasta=date(2026, 9, 10))
    repo.rows[override.id] = override
    repo.rows[otro.id] = otro

    with pytest.raises(OverlappingOverrideError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, hasta=date(2026, 9, 5))
        )
