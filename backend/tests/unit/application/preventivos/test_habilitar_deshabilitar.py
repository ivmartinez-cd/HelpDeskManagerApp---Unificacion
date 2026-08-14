import uuid

import pytest

from src.modules.preventivos.application.dtos.habilitar_request import (
    DeshabilitarEquipoRequest,
    HabilitarEquipoRequest,
)
from src.modules.preventivos.application.use_cases.deshabilitar_equipo import (
    DeshabilitarEquipoUseCase,
)
from src.modules.preventivos.application.use_cases.habilitar_equipo import (
    HabilitarEquipoUseCase,
)
from src.modules.preventivos.domain.errors import (
    HabilitacionNoEncontradaError,
    HabilitacionYaActivaError,
)
from tests.unit.application.preventivos.fakes import (
    FakeHabilitacionRepository,
    build_habilitacion,
)

_USER_ID = uuid.uuid4()


def _habilitar_request(nota: str | None = None) -> HabilitarEquipoRequest:
    return HabilitarEquipoRequest(
        siges_maquina_id=31852,
        habilitado_por_user_id=_USER_ID,
        habilitado_por_nombre="Ana Prueba",
        nota=nota,
    )


async def test_habilitar_crea_marca_con_auditoria() -> None:
    repo = FakeHabilitacionRepository()

    info = await HabilitarEquipoUseCase(repo).execute(_habilitar_request(nota="  urgente  "))

    assert info.habilitado_por == "Ana Prueba"
    assert info.nota == "urgente"
    guardada = repo.habilitaciones[0]
    assert guardada.siges_maquina_id == 31852
    assert guardada.habilitado_por_user_id == _USER_ID
    assert guardada.activa is True


async def test_habilitar_nota_vacia_queda_none() -> None:
    repo = FakeHabilitacionRepository()

    info = await HabilitarEquipoUseCase(repo).execute(_habilitar_request(nota="   "))

    assert info.nota is None


async def test_habilitar_dos_veces_lanza_conflicto() -> None:
    repo = FakeHabilitacionRepository([build_habilitacion(31852)])

    with pytest.raises(HabilitacionYaActivaError):
        await HabilitarEquipoUseCase(repo).execute(_habilitar_request())

    assert len(repo.habilitaciones) == 1


async def test_deshabilitar_deja_auditoria_de_quien() -> None:
    repo = FakeHabilitacionRepository([build_habilitacion(31852)])

    await DeshabilitarEquipoUseCase(repo).execute(
        DeshabilitarEquipoRequest(siges_maquina_id=31852, deshabilitado_por_nombre="Beto")
    )

    guardada = repo.habilitaciones[0]
    assert guardada.activa is False
    assert guardada.deshabilitado_por == "Beto"
    assert guardada.deshabilitado_en is not None


async def test_deshabilitar_sin_habilitacion_activa_lanza_not_found() -> None:
    repo = FakeHabilitacionRepository()

    with pytest.raises(HabilitacionNoEncontradaError):
        await DeshabilitarEquipoUseCase(repo).execute(
            DeshabilitarEquipoRequest(siges_maquina_id=1, deshabilitado_por_nombre="Beto")
        )
