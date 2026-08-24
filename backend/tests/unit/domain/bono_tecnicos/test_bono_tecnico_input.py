import pytest

from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.errors import ValorInvalidoError


def test_acepta_valores_validos() -> None:
    input_ = BonoTecnicoInput(
        id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=17, tareas_varias=25
    )

    assert input_.dias == 17
    assert input_.tareas_varias == 25


def test_rechaza_dias_negativos() -> None:
    with pytest.raises(ValorInvalidoError):
        BonoTecnicoInput(id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=-1, tareas_varias=0)


def test_rechaza_tareas_varias_negativas() -> None:
    with pytest.raises(ValorInvalidoError):
        BonoTecnicoInput(id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=0, tareas_varias=-1)


def test_dias_cero_es_valido() -> None:
    # Dias=0 significa "todavía no cargado" — GetPuntajesPeriodo lo interpreta
    # como puntaje null, no es un valor prohibido a nivel de la entidad.
    input_ = BonoTecnicoInput(
        id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=0, tareas_varias=0
    )

    assert input_.dias == 0
