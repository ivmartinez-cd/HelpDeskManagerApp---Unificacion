"""Caracterización: port de `tests/filters.test.ts` del legacy."""

from src.modules.reporte_incidentes.domain.services.filtros import (
    Filtros,
    OpcionFiltro,
    aplicar_filtros,
    opciones_filtro,
    sanear_filtros,
    valor_dimension,
)
from tests.unit.domain.reporte_incidentes.fakes import incidente

_MUESTRA = [
    incidente(sucursal="Central", categoria="Insumos y Toner", subcategoria="Toner"),
    incidente(sucursal="Central", categoria="Insumos y Toner", subcategoria="Toner"),
    incidente(sucursal="Norte", categoria="Conectividad y Red", subcategoria="IP"),
    incidente(sucursal="Norte"),
]


def test_normaliza_categoria_ausente_como_sin_clasificar() -> None:
    assert valor_dimension(incidente(), "categoria") == "Sin Clasificar"


def test_normaliza_subcategoria_ausente_como_sin_subcategorizar() -> None:
    assert valor_dimension(incidente(), "subcategoria") == "Sin subcategorizar"


def test_cuenta_valores_por_dimension_y_ordena_por_frecuencia() -> None:
    o = opciones_filtro(_MUESTRA)
    assert o.sucursales == [OpcionFiltro("Central", 2), OpcionFiltro("Norte", 2)]
    assert o.categorias[0] == OpcionFiltro("Insumos y Toner", 2)


def test_agrupa_lo_ausente_bajo_sin_clasificar_y_sin_subcategorizar() -> None:
    o = opciones_filtro(_MUESTRA)
    assert OpcionFiltro("Sin Clasificar", 1) in o.categorias
    assert OpcionFiltro("Sin subcategorizar", 1) in o.subcategorias


def test_conserva_solo_valores_que_existen_entre_las_opciones_del_periodo() -> None:
    crudos = Filtros(sucursal="Central", categoria="Inexistente", subcategoria="Toner")
    assert sanear_filtros(crudos, opciones_filtro(_MUESTRA)) == Filtros("Central", "", "Toner")


def test_sin_filtros_devuelve_todo() -> None:
    assert len(aplicar_filtros(_MUESTRA, Filtros())) == 4


def test_combina_filtros_con_and() -> None:
    filtros = Filtros("Central", "Insumos y Toner", "Toner")
    assert len(aplicar_filtros(_MUESTRA, filtros)) == 2


def test_filtra_sin_clasificar_alcanzando_incidentes_sin_categoria() -> None:
    r = aplicar_filtros(_MUESTRA, Filtros(categoria="Sin Clasificar"))
    assert len(r) == 1 and r[0].categoria is None


def test_activos_es_false_sin_filtros_y_true_con_alguno() -> None:
    assert not Filtros().activos
    assert Filtros(subcategoria="Toner").activos
