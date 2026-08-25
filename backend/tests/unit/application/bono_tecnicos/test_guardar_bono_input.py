import pytest

from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GuardarBonoInputRequest,
)
from src.modules.bono_tecnicos.application.use_cases.guardar_bono_input import GuardarBonoInput
from src.modules.bono_tecnicos.domain.errors import PeriodoInvalidoError, ValorInvalidoError
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from tests.unit.application.bono_tecnicos.fakes import FakeBonoTecnicoInputRepository


async def test_guarda_el_input_en_el_repositorio() -> None:
    repo = FakeBonoTecnicoInputRepository()
    use_case = GuardarBonoInput(repo)

    await use_case.execute(
        GuardarBonoInputRequest(
            id_tecnico=1314, periodo=202605, tecnico="CD - Agustin HACZEK", dias=17
        )
    )

    guardados = await repo.find_by_periodo(Periodo(202605))
    assert len(guardados) == 1
    assert guardados[0].dias == 17


async def test_periodo_invalido_no_guarda_nada() -> None:
    repo = FakeBonoTecnicoInputRepository()
    use_case = GuardarBonoInput(repo)

    with pytest.raises(PeriodoInvalidoError):
        await use_case.execute(
            GuardarBonoInputRequest(id_tecnico=1, periodo=202613, tecnico="CD - Ana", dias=1)
        )


async def test_valor_negativo_no_guarda_nada() -> None:
    repo = FakeBonoTecnicoInputRepository()
    use_case = GuardarBonoInput(repo)

    with pytest.raises(ValorInvalidoError):
        await use_case.execute(
            GuardarBonoInputRequest(id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=-1)
        )


async def test_guarda_medio_dia() -> None:
    repo = FakeBonoTecnicoInputRepository()
    use_case = GuardarBonoInput(repo)

    await use_case.execute(
        GuardarBonoInputRequest(
            id_tecnico=498, periodo=202607, tecnico="CD - Matias MILAN", dias=20.5
        )
    )

    guardados = await repo.find_by_periodo(Periodo(202607))
    assert guardados[0].dias == 20.5
