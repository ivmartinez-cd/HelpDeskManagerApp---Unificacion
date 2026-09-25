"""Caracterización: port de `tests/aggregate.test.ts` del legacy."""

from src.modules.reporte_incidentes.domain.services.resumen import (
    Conteo,
    ConteoSubcategoria,
    resumir,
)
from tests.unit.domain.reporte_incidentes.fakes import incidente

_TAXONOMIA = ["Insumos y Toner", "Conectividad y Red"]


def test_cuenta_el_total_y_rankea_la_categoria_principal_con_su_porcentaje() -> None:
    r = resumir(
        [incidente(categoria="Insumos y Toner")] * 3 + [incidente(categoria="Conectividad y Red")],
        _TAXONOMIA,
    )
    assert (r.total, r.categoria_principal) == (4, "Insumos y Toner")
    assert (r.categoria_principal_cantidad, r.categoria_principal_pct) == (3, 75)


def test_excluye_categorias_sin_incidentes_y_ordena_de_mayor_a_menor() -> None:
    r = resumir(
        [
            incidente(categoria="Conectividad y Red"),
            incidente(categoria="Insumos y Toner"),
            incidente(categoria="Insumos y Toner"),
        ],
        _TAXONOMIA,
    )
    assert r.categorias == [Conteo("Insumos y Toner", 2), Conteo("Conectividad y Red", 1)]


def test_clasifica_como_sin_clasificar_los_incidentes_sin_categoria() -> None:
    r = resumir([incidente(), incidente()], _TAXONOMIA)
    assert (r.categoria_principal, r.categoria_principal_cantidad) == ("Sin Clasificar", 2)


def test_categorias_fuera_de_la_taxonomia_van_despues_en_los_empates() -> None:
    r = resumir(
        [incidente(categoria="Pendiente de revision"), incidente(categoria="Conectividad y Red")],
        _TAXONOMIA,
    )
    assert [c.nombre for c in r.categorias] == ["Conectividad y Red", "Pendiente de revision"]


def test_arma_la_serie_temporal_por_dia_ordenada_ascendente() -> None:
    r = resumir(
        [
            incidente(fecha="2026-06-10"),
            incidente(fecha="2026-06-02"),
            incidente(fecha="2026-06-10"),
        ],
        _TAXONOMIA,
    )
    assert r.evolucion == [Conteo("2026-06-02", 1), Conteo("2026-06-10", 2)]


def test_rankea_sucursales_y_limita_a_las_6_principales() -> None:
    otras = ["Sur", "Este", "Oeste", "Deposito", "Anexo"]
    incidentes = (
        [incidente(sucursal="Central") for _ in range(5)]
        + [incidente(sucursal="Norte") for _ in range(2)]
        + [incidente(sucursal=s) for s in otras]
    )
    r = resumir(incidentes, _TAXONOMIA)
    assert (r.sucursal_principal, r.sucursal_principal_cantidad) == ("Central", 5)
    assert len(r.sucursales) == 6
    assert "Anexo" not in [s.nombre for s in r.sucursales]


def test_agrega_subcategorias_conservando_su_categoria_padre() -> None:
    r = resumir(
        [
            incidente(categoria="Insumos y Toner", subcategoria="Toner Defectuoso"),
            incidente(categoria="Insumos y Toner", subcategoria="Toner Defectuoso"),
            incidente(categoria="Conectividad y Red", subcategoria="Configuracion IP / Red"),
        ],
        _TAXONOMIA,
    )
    assert r.subcategorias[0] == ConteoSubcategoria("Toner Defectuoso", 2, "Insumos y Toner")


def test_usa_sin_subcategorizar_cuando_falta_la_subcategoria() -> None:
    r = resumir([incidente(categoria="Insumos y Toner")], _TAXONOMIA)
    assert r.subcategorias[0].nombre == "Sin subcategorizar"


def test_devuelve_agregados_neutros_para_un_reporte_vacio() -> None:
    r = resumir([], _TAXONOMIA)
    assert (r.total, r.categoria_principal, r.categoria_principal_pct) == (0, "—", 0)
    assert r.categorias == r.evolucion == r.sucursales == []


def test_porcentaje_redondea_las_mitades_hacia_arriba_como_math_round() -> None:
    r = resumir([incidente(categoria="Insumos y Toner")] + [incidente()] * 7, _TAXONOMIA)
    assert r.categoria_principal_pct == 88  # 7/8 = 87,5 %
