"""Parser de logs HP (§5 caracterización): normalización de espacios, meses en
español, hora sin zero-pad, header en las primeras 3 líneas, fallback por
espacios y reporte de líneas inválidas."""

from datetime import datetime

import pytest

from src.modules.analisis_log_hp.domain.services import log_parser
from src.modules.analisis_log_hp.domain.services.log_parser import (
    normalize_log_text,
    parse_log_text,
)

_LINEA_OK = "Error\t13.20.01\t05-ago-2026 9:05:00\t12345\tFW2025\thttp://help/13.20"


class TestNormalizeLogText:
    def test_dos_o_mas_espacios_se_vuelven_tab(self) -> None:
        assert normalize_log_text("a  b   c") == "a\tb\tc"

    def test_un_solo_espacio_se_conserva(self) -> None:
        assert normalize_log_text("a b") == "a b"

    def test_normaliza_linea_por_linea(self) -> None:
        assert normalize_log_text("a  b\nc   d") == "a\tb\nc\td"


class TestParseLogTextLineaValida:
    def test_parsea_tipo_codigo_contador_firmware_y_ayuda(self) -> None:
        report = parse_log_text(_LINEA_OK)
        assert report.errors == []
        evt = report.events[0]
        assert (evt.type, evt.code, evt.counter) == ("ERROR", "13.20.01", 12345)
        assert (evt.firmware, evt.help_reference) == ("FW2025", "http://help/13.20")

    def test_mes_en_espanol_y_hora_sin_zero_pad(self) -> None:
        evt = parse_log_text(_LINEA_OK).events[0]
        assert evt.timestamp == datetime(2026, 8, 5, 9, 5, 0)

    def test_mes_en_ingles_con_mayusculas_raras(self) -> None:
        linea = "Warning\t41.03\t05-SEP-2026 10:00:00\t1\tFW\thelp"
        evt = parse_log_text(linea).events[0]
        assert evt.timestamp == datetime(2026, 9, 5, 10, 0, 0)
        assert evt.type == "WARNING"

    def test_cinco_columnas_rellena_ayuda_vacia(self) -> None:
        linea = "Info\tINFO1\t05-ago-2026 09:05:00\t10\tFW"
        evt = parse_log_text(linea).events[0]
        assert evt.help_reference is None
        assert evt.firmware == "FW"

    def test_fallback_por_espacios_con_ayuda_multi_token(self) -> None:
        linea = "Error 13.20 05-ago-2026 09:05:00 10 FW ayuda con espacios"
        evt = parse_log_text(linea).events[0]
        assert evt.code == "13.20"
        assert evt.help_reference == "ayuda con espacios"

    def test_fallback_por_espacios_sin_ayuda(self) -> None:
        linea = "Error 13.20 05-ago-2026 09:05:00 10 FW"
        evt = parse_log_text(linea).events[0]
        assert evt.help_reference is None

    def test_columna_intermedia_vacia_se_colapsa_como_en_el_legacy(self) -> None:
        # Las celdas vacías se descartan antes de asignar columnas: un firmware
        # vacío corre la ayuda a la posición de firmware (port textual, §5.1).
        linea = "Info\tINFO1\t05-ago-2026 09:05:00\t10\t\thelp"
        evt = parse_log_text(linea).events[0]
        assert evt.firmware == "help"
        assert evt.help_reference is None


class TestParseLogTextHeaderYLineasVacias:
    def test_header_en_primeras_lineas_se_saltea_sin_error(self) -> None:
        texto = "Tipo\tCódigo\tFecha\tContador\tFirmware\tAyuda\n" + _LINEA_OK
        report = parse_log_text(texto)
        assert len(report.events) == 1
        assert report.errors == []

    def test_header_despues_de_tres_lineas_se_reporta_como_error(self) -> None:
        texto = "\n".join([_LINEA_OK, _LINEA_OK, _LINEA_OK, "Tipo\tCódigo\tFecha\tC\tF\tA"])
        report = parse_log_text(texto)
        assert len(report.events) == 3
        assert len(report.errors) == 1
        assert report.errors[0].line_number == 4

    def test_lineas_vacias_se_ignoran(self) -> None:
        report = parse_log_text("\n\n" + _LINEA_OK + "\n   \n")
        assert len(report.events) == 1
        assert report.errors == []


class TestParseLogTextErrores:
    @pytest.mark.parametrize(
        ("linea", "motivo"),
        [
            ("Error\t13.20", "6 columnas"),
            ("Error\t13.20\t05-ago-2026\t10\tFW\thelp", "fecha y hora"),
            ("Error\t13.20\t05/08/2026 09:05:00\t10\tFW\thelp", "DD-MMM-YYYY"),
            ("Error\t13.20\t05-xxx-2026 09:05:00\t10\tFW\thelp", "Timestamp inválido"),
            ("Error\t13.20\t05-ago-2026 09:05:00\tabc\tFW\thelp", "entero positivo"),
            ("Fatal\t13.20\t05-ago-2026 09:05:00\t10\tFW\thelp", "Tipo de evento"),
        ],
    )
    def test_linea_invalida_se_reporta_con_motivo(self, linea: str, motivo: str) -> None:
        report = parse_log_text(linea)
        assert report.events == []
        assert len(report.errors) == 1
        assert motivo in report.errors[0].reason
        assert report.errors[0].raw_line == linea

    def test_payload_se_trunca_al_maximo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(log_parser, "MAX_LOGS_LENGTH", len(_LINEA_OK))
        texto = _LINEA_OK + "\n" + _LINEA_OK
        report = parse_log_text(texto)
        assert len(report.events) == 1
