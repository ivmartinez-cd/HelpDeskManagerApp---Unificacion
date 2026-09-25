"""DatosPersona: normaliza lo que comparten ficha y cuenta, y rechaza basura."""

import pytest

from src.modules.personas.domain.entities.persona import DatosPersona
from src.modules.personas.domain.errors import DatosPersonaInvalidosError


def test_normaliza_mail_y_espacios_de_nombres() -> None:
    datos = DatosPersona(
        first_name="  Agustin ", last_name="Haczek  Paz", email=" AHaczek@Canal.com ", color="#abc"
    )

    assert datos.first_name == "Agustin"
    assert datos.last_name == "Haczek Paz"
    assert datos.email == "ahaczek@canal.com"
    assert datos.nombre_completo == "Agustin Haczek Paz"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("email", "sin-arroba"), ("color", "rojo"), ("color", "#12345"), ("first_name", "   ")],
)
def test_rechaza_datos_invalidos(campo: str, valor: str) -> None:
    base = {"first_name": "Ana", "last_name": "Paz", "email": "ana@canal.com", "color": "#112233"}
    base[campo] = valor

    with pytest.raises(DatosPersonaInvalidosError):
        DatosPersona(**base)
