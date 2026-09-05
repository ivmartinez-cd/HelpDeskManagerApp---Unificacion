"""Tests de Create/Update/DeleteTarifario — el foco es el recadenado temporal de
vigencias del grupo (prestador, tipo_servicio, spst_id) en cada escritura."""

import uuid
from datetime import date

import pytest

from src.modules.liquidaciones.application.use_cases.config_tarifarios import (
    ConfigTarifariosPorts,
    CreateTarifario,
    DeleteTarifario,
    UpdateTarifario,
)
from src.modules.liquidaciones.domain.errors import TarifarioNoEncontradoError
from tests.unit.domain.liquidaciones.factories import make_tarifario
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigTarifarioRepository


def _ports(repo: FakeConfigTarifarioRepository) -> ConfigTarifariosPorts:
    return ConfigTarifariosPorts(tarifarios=repo)


async def test_create_recadena_el_grupo() -> None:
    prestador_id = uuid.uuid4()
    previo = make_tarifario(
        prestador_id=prestador_id, vigencia_desde=date(2025, 1, 1), vigencia_hasta=None
    )
    repo = FakeConfigTarifarioRepository([previo])

    creado = await CreateTarifario(_ports(repo)).execute(
        prestador_id=prestador_id,
        tipo_servicio="correctivo",
        spst_id=None,
        costo_servicio=2000.0,
        costo_km=120.0,
        vigencia_desde=date(2025, 6, 1),
        vigencia_hasta=None,
    )

    cerrado = await repo.get_by_id(previo.id)
    assert cerrado is not None
    assert cerrado.vigencia_hasta == date(2025, 5, 31)
    assert creado.vigencia_hasta is None


async def test_create_en_otro_grupo_no_toca_el_previo() -> None:
    prestador_id = uuid.uuid4()
    previo = make_tarifario(
        prestador_id=prestador_id, vigencia_desde=date(2025, 1, 1), vigencia_hasta=None
    )
    repo = FakeConfigTarifarioRepository([previo])

    await CreateTarifario(_ports(repo)).execute(
        prestador_id=prestador_id,
        tipo_servicio="preventivo",
        spst_id=None,
        costo_servicio=2000.0,
        costo_km=120.0,
        vigencia_desde=date(2025, 6, 1),
        vigencia_hasta=None,
    )

    intacto = await repo.get_by_id(previo.id)
    assert intacto is not None
    assert intacto.vigencia_hasta is None


async def test_update_que_cambia_de_grupo_recadena_origen_y_destino() -> None:
    prestador_id = uuid.uuid4()
    origen_a = make_tarifario(
        prestador_id=prestador_id, vigencia_desde=date(2025, 1, 1), vigencia_hasta=date(2025, 5, 31)
    )
    origen_b = make_tarifario(
        prestador_id=prestador_id, vigencia_desde=date(2025, 6, 1), vigencia_hasta=None
    )
    destino = make_tarifario(
        prestador_id=prestador_id,
        tipo_servicio="preventivo",
        vigencia_desde=date(2025, 1, 1),
        vigencia_hasta=None,
    )
    repo = FakeConfigTarifarioRepository([origen_a, origen_b, destino])

    updated = await UpdateTarifario(_ports(repo)).execute(
        origen_b.id,
        prestador_id=prestador_id,
        tipo_servicio="preventivo",
        spst_id=None,
        costo_servicio=origen_b.costo_servicio,
        costo_km=origen_b.costo_km,
        vigencia_desde=date(2025, 6, 1),
        vigencia_hasta=None,
    )

    # origen: al irse origen_b, origen_a vuelve a quedar abierto? No — la cadena
    # solo cierra filas contra la siguiente; sin siguiente, origen_a conserva su
    # vigencia_hasta actual (2025-05-31), igual que el legacy.
    quedo_origen = await repo.get_by_id(origen_a.id)
    assert quedo_origen is not None
    assert quedo_origen.vigencia_hasta == date(2025, 5, 31)
    # destino: la fila previa del grupo se cierra contra la recién llegada.
    cerrado_destino = await repo.get_by_id(destino.id)
    assert cerrado_destino is not None
    assert cerrado_destino.vigencia_hasta == date(2025, 5, 31)
    assert updated.tipo_servicio == "preventivo"


async def test_update_inexistente_lanza_not_found() -> None:
    repo = FakeConfigTarifarioRepository()

    with pytest.raises(TarifarioNoEncontradoError):
        await UpdateTarifario(_ports(repo)).execute(
            uuid.uuid4(),
            prestador_id=uuid.uuid4(),
            tipo_servicio="correctivo",
            spst_id=None,
            costo_servicio=1.0,
            costo_km=1.0,
            vigencia_desde=date(2025, 1, 1),
            vigencia_hasta=None,
        )


async def test_delete_recadena_el_grupo_restante() -> None:
    prestador_id = uuid.uuid4()
    primero = make_tarifario(
        prestador_id=prestador_id, vigencia_desde=date(2025, 1, 1), vigencia_hasta=date(2025, 5, 31)
    )
    medio = make_tarifario(
        prestador_id=prestador_id, vigencia_desde=date(2025, 6, 1), vigencia_hasta=date(2025, 8, 31)
    )
    ultimo = make_tarifario(
        prestador_id=prestador_id, vigencia_desde=date(2025, 9, 1), vigencia_hasta=None
    )
    repo = FakeConfigTarifarioRepository([primero, medio, ultimo])

    await DeleteTarifario(_ports(repo)).execute(medio.id)

    # El primero ahora se cierra contra el último (2025-08-31), no contra el borrado.
    recadenado = await repo.get_by_id(primero.id)
    assert recadenado is not None
    assert recadenado.vigencia_hasta == date(2025, 8, 31)
    assert await repo.get_by_id(medio.id) is None


async def test_delete_inexistente_lanza_not_found() -> None:
    repo = FakeConfigTarifarioRepository()

    with pytest.raises(TarifarioNoEncontradoError):
        await DeleteTarifario(_ports(repo)).execute(uuid.uuid4())
