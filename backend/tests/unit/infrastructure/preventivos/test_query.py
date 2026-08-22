"""Contrato de las consultas SQL de preventivos: cantidad y orden de los
placeholders posicionales (pyodbc no soporta parámetros con nombre) y los
filtros de universo que el gateway da por sentados."""

import pytest

from src.modules.preventivos.infrastructure.siges.query import PARQUE_ZONA_SQL, ZONAS_SQL


def test_parque_zona_tiene_tres_placeholders_meses_meses_zona() -> None:
    assert PARQUE_ZONA_SQL.count("?") == 3
    assert PARQUE_ZONA_SQL.rstrip().endswith("S.Cuadricula = ?")


def test_parque_zona_trae_sucursal_y_coordenadas_para_el_mapa() -> None:
    assert "S.Id_Sucursal AS id_sucursal" in PARQUE_ZONA_SQL
    assert "S.Latitud AS latitud" in PARQUE_ZONA_SQL
    assert "S.Longitud AS longitud" in PARQUE_ZONA_SQL


def test_zonas_tiene_dos_placeholders_de_meses() -> None:
    assert ZONAS_SQL.count("?") == 2


@pytest.mark.parametrize("sql", [PARQUE_ZONA_SQL, ZONAS_SQL])
def test_ambas_consultas_filtran_solo_impresoras_y_clientes_vivos(sql: str) -> None:
    assert "AG.Descripcion LIKE 'PRT %'" in sql
    assert "AG.Descripcion LIKE 'MFP %'" in sql
    assert "M.ID_Estado_Maquina = 1" in sql
    assert "E.ID_Tipo_Empresa IN (101, 102)" in sql
    assert "DATEADD(month, -?, GETDATE())" in sql


@pytest.mark.parametrize("sql", [PARQUE_ZONA_SQL, ZONAS_SQL])
def test_ambas_consultas_son_solo_lectura(sql: str) -> None:
    assert sql.lstrip().upper().startswith("SELECT")
    for verbo in ("INSERT", "UPDATE", "DELETE", "EXEC"):
        assert verbo not in sql.upper()
