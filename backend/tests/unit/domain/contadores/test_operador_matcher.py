from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.services.operador_matcher import resolve_nombre_operador

_CATALOGO = [
    Operador(id="318", nombre="Maria Jose Vela"),
    Operador(id="1246", nombre="Victor Paez"),
    Operador(id="288", nombre="Mariana Rodriguez"),
    Operador(id="1250", nombre="Elizabeth Rodriguez"),
    Operador(id="1273", nombre="Luna Torres"),
    Operador(id="846", nombre="Contadores CanalDirecto"),
    Operador(id="749", nombre="Ivan Martinez"),
    Operador(id="1123", nombre="Nora Martinez"),
]


def test_matchea_iniciales_mas_apellido() -> None:
    assert resolve_nombre_operador("mjvela", _CATALOGO) == "Maria Jose Vela"
    assert resolve_nombre_operador("ltorres", _CATALOGO) == "Luna Torres"


def test_matchea_prefijo_del_nombre_mas_apellido() -> None:
    assert resolve_nombre_operador("vipaez", _CATALOGO) == "Victor Paez"
    assert resolve_nombre_operador("marodriguez", _CATALOGO) == "Mariana Rodriguez"


def test_matchea_nombre_completo_literal() -> None:
    assert resolve_nombre_operador("Ivan Martinez", _CATALOGO) == "Ivan Martinez"
    assert resolve_nombre_operador("ivan martinez", _CATALOGO) == "Ivan Martinez"


def test_matchea_palabra_suelta_del_nombre() -> None:
    assert resolve_nombre_operador("contadores", _CATALOGO) == "Contadores CanalDirecto"


def test_ambiguo_o_desconocido_devuelve_none() -> None:
    # "martinez" a secas matchea como palabra suelta a Ivan y a Nora: ambiguo.
    assert resolve_nombre_operador("martinez", _CATALOGO) is None
    assert resolve_nombre_operador("jperez", _CATALOGO) is None
    assert resolve_nombre_operador("", _CATALOGO) is None
