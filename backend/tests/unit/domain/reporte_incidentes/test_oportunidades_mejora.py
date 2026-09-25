"""Caracterización: port de `tests/insights.test.ts` del legacy."""

from src.modules.reporte_incidentes.domain.services.oportunidades_mejora import (
    ItemSinReparacion,
    oportunidades_de_mejora,
)
from tests.unit.domain.reporte_incidentes.fakes import incidente

_MAL_USO = "Mal uso / Negligencia"


def test_ignora_las_subcategorias_que_si_son_trabajo_sobre_el_equipo() -> None:
    r = oportunidades_de_mejora([
        incidente(categoria="Hardware y Desgaste", subcategoria="Fusor / Kit de mantenimiento"),
        incidente(categoria="Insumos y Toner", subcategoria="Toner / Cartucho"),
    ])
    assert (r.fuera_del_equipo_total, r.sin_reparacion_total, r.items) == (0, 0, [])


def test_arma_el_titular_con_los_casos_cerrados_sin_reparar_el_equipo() -> None:
    r = oportunidades_de_mejora([
        incidente(subcategoria="Diagnostico / Sin falla"),
        incidente(subcategoria="Diagnostico / Sin falla"),
        incidente(subcategoria="Instructivo / Autoresolucion"),
        incidente(subcategoria="Driver / PC / Spooler"),
        incidente(subcategoria="Fusor / Kit de mantenimiento"),
    ])
    assert (r.total, r.sin_reparacion_total, r.sin_reparacion_pct) == (5, 4, 80)
    # Ordenado por cantidad, no por el orden de la taxonomía.
    assert r.sin_reparacion_items[0] == ItemSinReparacion("Diagnostico / Sin falla", 2, 40)
    assert len(r.sin_reparacion_items) == 3


def test_no_repite_en_el_resto_las_subcategorias_que_ya_estan_en_el_titular() -> None:
    r = oportunidades_de_mejora([
        incidente(subcategoria="Driver / PC / Spooler"),
        incidente(subcategoria="Configuracion de red / IP"),
        incidente(subcategoria="Papel especial / Troquelado"),
    ])
    assert (r.fuera_del_equipo_total, r.sin_reparacion_total) == (3, 1)
    assert sorted(i.subcategoria for i in r.items) == [
        "Configuracion de red / IP",
        "Papel especial / Troquelado",
    ]


def test_marca_concentrado_cuando_una_sucursal_domina_la_subcategoria() -> None:
    sucursales = ["Norte", "Norte", "Norte", "Sur"]
    r = oportunidades_de_mejora([incidente(subcategoria=_MAL_USO, sucursal=s) for s in sucursales])
    item = r.items[0]
    assert item.concentrado
    assert (item.sucursal_principal, item.sucursal_principal_pct) == ("Norte", 75)


def test_marca_no_concentrado_cuando_esta_repartido_entre_sucursales() -> None:
    sucursales = ["Norte", "Sur", "Este", "Oeste"]
    r = oportunidades_de_mejora([incidente(subcategoria=_MAL_USO, sucursal=s) for s in sucursales])
    assert not r.items[0].concentrado


def test_el_resto_se_limita_a_las_4_principales() -> None:
    subcategorias = [
        "Papel especial / Troquelado",
        "Papel inadecuado / humedad / mala calidad",
        "Mal uso / Negligencia",
        "Problema externo / Red del cliente",
        "Mesa de ayuda / Sin respuesta del cliente",
    ]
    r = oportunidades_de_mejora([incidente(subcategoria=s) for s in subcategorias])
    assert len(r.items) == 4


def test_devuelve_agregados_neutros_para_un_reporte_vacio() -> None:
    r = oportunidades_de_mejora([])
    assert (r.total, r.fuera_del_equipo_total, r.fuera_del_equipo_pct) == (0, 0, 0)
    assert (r.sin_reparacion_total, r.sin_reparacion_items, r.items) == (0, [], [])
