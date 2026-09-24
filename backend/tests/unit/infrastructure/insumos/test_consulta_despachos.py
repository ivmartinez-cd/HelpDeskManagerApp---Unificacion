"""SQL de despachos OCA en SiGes: un marcador `?` por distribución más el de la ventana,
filtros y joins verificados con dato real, y nada interpolado."""

import pytest

from src.modules.insumos.infrastructure.siges.consulta_despachos import (
    construir_consulta_despachos,
)


@pytest.mark.parametrize(("cantidad", "marcadores_in"), [(1, "?"), (3, "?, ?, ?")])
def test_un_marcador_por_distribucion_mas_el_de_la_ventana(
    cantidad: int, marcadores_in: str
) -> None:
    sql = construir_consulta_despachos(cantidad)

    assert sql.count("?") == cantidad + 1
    assert f"rc.ID_Distribucion IN ({marcadores_in})" in sql


def test_las_distribuciones_van_antes_que_la_ventana_en_el_orden_de_parametros() -> None:
    sql = construir_consulta_despachos(2)

    assert sql.index("IN (?, ?)") < sql.index("DATEADD(day, -?, CAST(GETDATE() AS date))")


def test_filtra_insumos_con_guia_oca_de_19_digitos() -> None:
    sql = construir_consulta_despachos(1)

    assert "rc.TipoRemito = 'I'" in sql
    assert "LEN(rc.Guia) = 19" in sql
    assert "rc.Guia NOT LIKE '%[^0-9]%'" in sql
    assert "rc.Fecha_Remito >= DATEADD(day, -?, CAST(GETDATE() AS date))" in sql


def test_une_los_incidentes_por_id_remito_sin_perder_remitos() -> None:
    sql = construir_consulta_despachos(1)

    assert "LEFT JOIN dbo.Incidente_Insumo_D d ON d.ID_Remito = rc.Id_Remito" in sql
    assert (
        "LEFT JOIN dbo.Incidente_Insumo_C c ON c.ID_Incidente_Insumo = d.ID_Incidente_Insumo" in sql
    )
    assert "LEFT JOIN dbo.Empresa e ON e.ID_Empresa = rc.Id_Empresa" in sql
    assert "LEFT JOIN dbo.Sucursal s ON s.Id_Sucursal = rc.Id_Sucursal" in sql


def test_devuelve_filas_distintas_ordenadas_por_fecha_descendente() -> None:
    sql = construir_consulta_despachos(1)

    assert "SELECT DISTINCT" in sql
    assert "ORDER BY fecha_remito DESC, id_remito, numero_incidente" in sql


def test_no_interpola_valores_ni_deja_llaves_sin_reemplazar() -> None:
    sql = construir_consulta_despachos(3)

    assert "{" not in sql and "}" not in sql
    for valor in ("IN (3", "IN (9", "IN (10", "-30"):
        assert valor not in sql


def test_sin_distribuciones_no_arma_un_in_vacio() -> None:
    with pytest.raises(ValueError):
        construir_consulta_despachos(0)
