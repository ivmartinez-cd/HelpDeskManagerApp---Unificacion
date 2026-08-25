from types import SimpleNamespace
from typing import Any

from src.modules.bono_tecnicos.infrastructure.mercurio.row_mapping import (
    map_row,
    pivot_conteos,
)


def _row(**overrides: Any) -> SimpleNamespace:
    """Fila como la devuelve pyodbc (acceso por atributo, nombres de columna
    de la consulta agrupada), con los tipos crudos del driver."""
    base: dict[str, Any] = {
        "Tecnico": "CD - Agustin HACZEK",
        "IdTecnico": 501,
        "Categoria": "Correctivo",
        "Cantidad": 47,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila() -> None:
    fila = map_row(_row())

    assert fila.tecnico == "CD - Agustin HACZEK"
    assert fila.id_tecnico == 501
    assert fila.categoria == "Correctivo"
    assert fila.cantidad == 47


def test_tecnico_null_no_rompe_el_mapeo() -> None:
    assert map_row(_row(Tecnico=None)).tecnico == ""


def test_recorta_espacios_de_los_char_fijos() -> None:
    assert map_row(_row(Tecnico="CD - Agustin HACZEK   ")).tecnico == "CD - Agustin HACZEK"


def test_pivot_arma_un_conteo_por_tecnico_con_las_5_categorias() -> None:
    filas = [
        map_row(_row(Categoria="Correctivo", Cantidad=47)),
        map_row(_row(Categoria="Preventivo", Cantidad=44)),
        map_row(_row(Categoria="InstDes", Cantidad=4)),
        map_row(_row(Categoria="PreCorrectivo", Cantidad=1)),
        map_row(_row(Categoria="EntregaInsumos", Cantidad=22)),
    ]

    conteos = pivot_conteos(filas, periodo=202605)

    assert len(conteos) == 1
    conteo = conteos[0]
    assert conteo.tecnico == "CD - Agustin HACZEK"
    assert conteo.id_tecnico == 501
    assert conteo.periodo == 202605
    assert conteo.correctivo == 47
    assert conteo.preventivo == 44
    assert conteo.inst_des == 4
    assert conteo.pre_correctivo == 1
    assert conteo.entrega_insumos == 22


def test_pivot_separa_por_tecnico_y_completa_categorias_ausentes_con_cero() -> None:
    filas = [
        map_row(_row(Tecnico="CD - Ana", IdTecnico=1, Categoria="Correctivo", Cantidad=3)),
        map_row(_row(Tecnico="CD - Beto", IdTecnico=2, Categoria="Preventivo", Cantidad=5)),
    ]

    conteos = {c.tecnico: c for c in pivot_conteos(filas, periodo=202605)}

    assert conteos["CD - Ana"].correctivo == 3
    assert conteos["CD - Ana"].preventivo == 0
    assert conteos["CD - Beto"].preventivo == 5
    assert conteos["CD - Beto"].correctivo == 0


def test_pivot_excluye_filas_que_no_son_tecnicos_reales() -> None:
    filas = [
        map_row(_row(Tecnico="CD - Ana", IdTecnico=1, Categoria="Correctivo", Cantidad=3)),
        map_row(
            _row(
                Tecnico="CD - Prestador Servicio Técnico",
                IdTecnico=901,
                Categoria="Correctivo",
                Cantidad=9,
            )
        ),
        map_row(
            _row(Tecnico="CD - Mesa de ayuda", IdTecnico=902, Categoria="Correctivo", Cantidad=9)
        ),
        map_row(
            _row(Tecnico="CD - Hector Arguello", IdTecnico=903, Categoria="Correctivo", Cantidad=9)
        ),
        map_row(
            _row(Tecnico="CD - Diego Estevez", IdTecnico=904, Categoria="Correctivo", Cantidad=9)
        ),
        map_row(_row(Tecnico="CD - Daas", IdTecnico=905, Categoria="Correctivo", Cantidad=9)),
    ]

    conteos = {c.tecnico: c for c in pivot_conteos(filas, periodo=202605)}

    assert set(conteos) == {"CD - Ana"}
