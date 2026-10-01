"""Exports a prueba de formula injection, y re-importables sin perder el texto."""

import io

import pytest

from src.shared.presentation.celdas import CsvWriterSeguro, celda_segura, desescapar_celda


@pytest.mark.parametrize("texto", ["=HYPERLINK(\"x\")", "+1+1", "-2+3", "@SUM(A1)", "\tx"])
def test_texto_peligroso_queda_como_literal_y_vuelve_igual(texto: str) -> None:
    seguro = celda_segura(texto)
    assert seguro == "'" + texto
    assert desescapar_celda(seguro) == texto


@pytest.mark.parametrize("valor", ["Juan Pérez", -5, 3.5, None, ""])
def test_texto_normal_y_numeros_no_se_tocan(valor: object) -> None:
    assert celda_segura(valor) == valor


def test_desescapar_no_toca_apostrofos_legitimos() -> None:
    assert desescapar_celda("'Tito' Gómez") == "'Tito' Gómez"


def test_writer_csv_aplica_a_cada_celda() -> None:
    buf = io.StringIO()
    CsvWriterSeguro(buf).writerow(["=1+1", "ok", -1])
    assert buf.getvalue().strip() == "'=1+1,ok,-1"
