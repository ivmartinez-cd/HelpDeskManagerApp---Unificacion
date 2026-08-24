import uuid

import pytest

from src.modules.vacaciones.application.use_cases.siges_vinculo import (
    ProponerVinculosSigesEmpleados,
    SigesVinculoPorts,
    VincularEmpleadoSiges,
)
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    SigesVinculoDuplicadoError,
)
from src.modules.vacaciones.domain.services.vinculacion_siges import SigesTecnicoInfo
from tests.unit.application.vacaciones.fakes import FakeEmpleadoRepo
from tests.unit.domain.vacaciones.factories import make_empleado


class FakeSigesTecnicoGateway:
    def __init__(self, tecnicos: list[SigesTecnicoInfo] | None = None) -> None:
        self._tecnicos = tecnicos or []

    async def list_tecnicos_activos(self) -> list[SigesTecnicoInfo]:
        return self._tecnicos


async def test_propone_vinculo_para_empleado_sin_vincular() -> None:
    empleado = make_empleado(first_name="Agustin", last_name="Haczek")
    ports = SigesVinculoPorts(
        empleados=FakeEmpleadoRepo([empleado]),
        siges=FakeSigesTecnicoGateway(
            [SigesTecnicoInfo(siges_empresa_id=1314, den_comercial="CD - Agustin HACZEK")]
        ),
    )

    resultado = await ProponerVinculosSigesEmpleados(ports).execute()

    assert len(resultado.propuestas) == 1
    propuesta = resultado.propuestas[0]
    assert propuesta.empleado_id == empleado.id
    assert propuesta.siges_empresa_id == 1314
    assert resultado.disponibles == []


async def test_no_propone_para_empleado_ya_vinculado() -> None:
    empleado = make_empleado(
        first_name="Agustin", last_name="Haczek", siges_empresa_id=1314
    )
    ports = SigesVinculoPorts(
        empleados=FakeEmpleadoRepo([empleado]),
        siges=FakeSigesTecnicoGateway(
            [SigesTecnicoInfo(siges_empresa_id=1314, den_comercial="CD - Agustin HACZEK")]
        ),
    )

    resultado = await ProponerVinculosSigesEmpleados(ports).execute()

    assert resultado.propuestas == []
    assert resultado.disponibles == []


async def test_tecnico_sin_match_queda_como_disponible() -> None:
    ports = SigesVinculoPorts(
        empleados=FakeEmpleadoRepo([]),
        siges=FakeSigesTecnicoGateway(
            [SigesTecnicoInfo(siges_empresa_id=99, den_comercial="CD - Sin Match")]
        ),
    )

    resultado = await ProponerVinculosSigesEmpleados(ports).execute()

    assert resultado.propuestas == []
    assert len(resultado.disponibles) == 1
    assert resultado.disponibles[0].siges_empresa_id == 99


async def test_vincular_empleado_siges_guarda_el_vinculo() -> None:
    empleado = make_empleado()
    ports = SigesVinculoPorts(
        empleados=FakeEmpleadoRepo([empleado]), siges=FakeSigesTecnicoGateway()
    )

    actualizado = await VincularEmpleadoSiges(ports).execute(empleado.id, siges_empresa_id=1314)

    assert actualizado.siges_empresa_id == 1314


async def test_vincular_empleado_inexistente_lanza_error() -> None:
    ports = SigesVinculoPorts(empleados=FakeEmpleadoRepo([]), siges=FakeSigesTecnicoGateway())

    with pytest.raises(EmpleadoNoEncontradoError):
        await VincularEmpleadoSiges(ports).execute(uuid.uuid4(), siges_empresa_id=1314)


async def test_vincular_a_tecnico_ya_usado_por_otro_empleado_lanza_error() -> None:
    ya_vinculado = make_empleado(siges_empresa_id=1314)
    sin_vincular = make_empleado()
    ports = SigesVinculoPorts(
        empleados=FakeEmpleadoRepo([ya_vinculado, sin_vincular]),
        siges=FakeSigesTecnicoGateway(),
    )

    with pytest.raises(SigesVinculoDuplicadoError):
        await VincularEmpleadoSiges(ports).execute(sin_vincular.id, siges_empresa_id=1314)
