from src.modules.contadores.domain.services.estimacion.export_csv import (
    escape_csv,
    motivo_de_fuente,
    sanitizar_simbolos,
    tipo_toma_export,
)


def test_motivo_datos_propios_da_14() -> None:
    assert motivo_de_fuente("Historia_Propia") == "14"
    assert motivo_de_fuente("T4_ST") == "14"
    assert motivo_de_fuente("Backup_SinST") == "14"
    assert motivo_de_fuente("EnTransito") == "14"


def test_motivo_parque_da_19() -> None:
    assert motivo_de_fuente("Parque_Cliente_Tec") == "19"
    assert motivo_de_fuente("Parque_Cliente_Modelo") == "19"
    assert motivo_de_fuente("Parque_Grupo_Modelo") == "19"
    assert motivo_de_fuente("Parque_Global_Modelo") == "19"


def test_motivo_real_o_pendiente_da_vacio() -> None:
    assert motivo_de_fuente("Sin_Estimar") == ""
    assert motivo_de_fuente("Pendiente") == ""


def test_tipo_toma_sin_estimar_da_vacio() -> None:
    assert tipo_toma_export(None) == ""


def test_tipo_toma_14_y_19_pasan_tal_cual() -> None:
    assert tipo_toma_export(14) == "14"
    assert tipo_toma_export(19) == "19"


def test_tipo_toma_guarda_dura_fuerza_14_para_cualquier_otro_valor() -> None:
    """Nunca un tipo "real" — última línea de defensa (REGLAS_DE_NEGOCIO §4)."""
    assert tipo_toma_export(1) == "14"
    assert tipo_toma_export(4) == "14"
    assert tipo_toma_export(20) == "14"


def test_escape_vacio_o_none_da_vacio() -> None:
    assert escape_csv(None) == ""
    assert escape_csv("") == ""


def test_escape_reemplaza_separador_y_saltos_de_linea() -> None:
    assert escape_csv("a;b") == "a,b"
    assert escape_csv("a\r\nb") == "a b"
    assert escape_csv("a\nb") == "a b"
    assert escape_csv("a\rb") == "a b"


def test_sanitizar_simbolos_reemplaza_los_conocidos() -> None:
    assert sanitizar_simbolos("Δ") == ""
    assert sanitizar_simbolos("5−3") == "5-3"
    assert sanitizar_simbolos("a–b") == "a-b"
    assert sanitizar_simbolos("a—b") == "a-b"
    assert sanitizar_simbolos("⚠aviso") == "(!)aviso"


def test_sanitizar_simbolos_no_es_longitud_neutral() -> None:
    """"⚠" (1 char) -> "(!)" (3 chars) — por eso se aplica ANTES de
    presupuestar el largo, nunca después."""
    assert len(sanitizar_simbolos("⚠")) == 3
