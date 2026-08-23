import uuid
from datetime import UTC, datetime

import pytest

from src.modules.preventivos.application.dtos.corregir_coordenada_request import (
    CorregirCoordenadaRequest,
)
from src.modules.preventivos.application.use_cases.corregir_coordenada_sucursal import (
    CorregirCoordenadaSucursalUseCase,
)
from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.preventivos.domain.errors import CoordenadaFueraDeRangoError
from tests.unit.application.preventivos.fakes import FakeSucursalCoordenadasRepository

_USER_ID = uuid.uuid4()


def _request(**overrides: object) -> CorregirCoordenadaRequest:
    base: dict[str, object] = dict(
        siges_sucursal_id=1,
        latitud=-34.6,
        longitud=-58.4,
        corregido_por_user_id=_USER_ID,
        corregido_por_nombre="Ana Prueba",
        nota=None,
    )
    base.update(overrides)
    return CorregirCoordenadaRequest(**base)  # type: ignore[arg-type]


async def test_corrige_y_guarda_auditoria() -> None:
    coords = FakeSucursalCoordenadasRepository()
    use_case = CorregirCoordenadaSucursalUseCase(coords)

    await use_case.execute(_request(nota="Estaba en San Justo, corregido a CABA"))

    guardada = coords.resueltas[1]
    assert guardada.latitud == -34.6
    assert guardada.longitud == -58.4
    assert guardada.corregido_por_user_id == _USER_ID
    assert guardada.corregido_por_nombre == "Ana Prueba"
    assert guardada.nota == "Estaba en San Justo, corregido a CABA"


async def test_nota_vacia_se_guarda_como_none() -> None:
    coords = FakeSucursalCoordenadasRepository()
    use_case = CorregirCoordenadaSucursalUseCase(coords)

    await use_case.execute(_request(nota="   "))

    assert coords.resueltas[1].nota is None


async def test_coordenada_fuera_de_rango_no_se_guarda() -> None:
    coords = FakeSucursalCoordenadasRepository()
    use_case = CorregirCoordenadaSucursalUseCase(coords)

    with pytest.raises(CoordenadaFueraDeRangoError):
        await use_case.execute(_request(latitud=10.0, longitud=10.0))

    assert coords.resueltas == {}


async def test_coordenada_cero_cero_no_se_guarda() -> None:
    coords = FakeSucursalCoordenadasRepository()
    use_case = CorregirCoordenadaSucursalUseCase(coords)

    with pytest.raises(CoordenadaFueraDeRangoError):
        await use_case.execute(_request(latitud=0.0, longitud=0.0))


async def test_corregir_pisa_un_override_geocodificado_existente() -> None:
    geocodificada = SucursalCoordenadas(1, -34.5, -58.5, "Direccion vieja", datetime.now(UTC))
    coords = FakeSucursalCoordenadasRepository([geocodificada])
    use_case = CorregirCoordenadaSucursalUseCase(coords)

    await use_case.execute(_request())

    guardada = coords.resueltas[1]
    assert guardada.latitud == -34.6
    assert guardada.corregido_por_user_id == _USER_ID
