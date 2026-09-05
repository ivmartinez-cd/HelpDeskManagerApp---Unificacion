"""ABM de acuerdos de precio por cliente: validaciones y escritura."""

import uuid
from datetime import date

import pytest

from src.modules.liquidaciones.application.use_cases.config_acuerdos import (
    AcuerdoDatos,
    ConfigAcuerdosPorts,
    CreateAcuerdo,
    DeleteAcuerdo,
    UpdateAcuerdo,
)
from src.modules.liquidaciones.domain.errors import (
    AcuerdoPrecioInvalidoError,
    AcuerdoPrecioNoEncontradoError,
)
from tests.unit.domain.liquidaciones.factories import make_acuerdo
from tests.unit.domain.liquidaciones.fakes import FakeAcuerdoPrecioClienteRepository


def _datos(**overrides: object) -> AcuerdoDatos:
    base: dict[str, object] = dict(
        empresa_nombre="Refinor",
        tipo_servicio=None,
        factor=None,
        precio_fijo=78119.0,
        motivo="Arreglo por ir a planta",
        vigencia_desde=date(2026, 1, 1),
        vigencia_hasta=None,
    )
    base.update(overrides)
    return AcuerdoDatos(**base)  # type: ignore[arg-type]


class TestCreateAcuerdo:
    async def test_crea_con_precio_fijo(self) -> None:
        repo = FakeAcuerdoPrecioClienteRepository()
        prestador_id = uuid.uuid4()

        creado = await CreateAcuerdo(ConfigAcuerdosPorts(repo)).execute(prestador_id, _datos())

        assert creado.prestador_id == prestador_id
        assert creado.precio_fijo == 78119.0
        assert repo.rows == [creado]

    @pytest.mark.parametrize(
        "overrides",
        [
            {"factor": 2.0},  # ambos
            {"precio_fijo": None},  # ninguno
            {"factor": 0.0, "precio_fijo": None},
            {"precio_fijo": -1.0},
            {"motivo": "  "},
            {"empresa_nombre": ""},
            {"vigencia_hasta": date(2025, 12, 31)},
        ],
    )
    async def test_datos_invalidos_rechazados(self, overrides: dict[str, object]) -> None:
        repo = FakeAcuerdoPrecioClienteRepository()
        with pytest.raises(AcuerdoPrecioInvalidoError):
            await CreateAcuerdo(ConfigAcuerdosPorts(repo)).execute(
                uuid.uuid4(), _datos(**overrides)
            )
        assert repo.rows == []


class TestUpdateDelete:
    async def test_update_reemplaza_campos(self) -> None:
        existente = make_acuerdo()
        repo = FakeAcuerdoPrecioClienteRepository([existente])

        actualizado = await UpdateAcuerdo(ConfigAcuerdosPorts(repo)).execute(
            existente.id, _datos(empresa_nombre="Sal de Vida", factor=2.0, precio_fijo=None)
        )

        assert actualizado.empresa_nombre == "Sal de Vida"
        assert actualizado.factor == 2.0

    async def test_update_inexistente_lanza_not_found(self) -> None:
        with pytest.raises(AcuerdoPrecioNoEncontradoError):
            await UpdateAcuerdo(ConfigAcuerdosPorts(FakeAcuerdoPrecioClienteRepository())).execute(
                uuid.uuid4(), _datos()
            )

    async def test_delete_devuelve_el_borrado(self) -> None:
        existente = make_acuerdo()
        repo = FakeAcuerdoPrecioClienteRepository([existente])

        borrado = await DeleteAcuerdo(ConfigAcuerdosPorts(repo)).execute(existente.id)

        assert borrado.id == existente.id
        assert repo.rows == []
