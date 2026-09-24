"""Archivo de exportación a SiGes — `CsvExportService` del Estimador de
Contadores v1.7 (incluye los casos de `CsvExportServiceTests.cs`: la guarda
dura de tipos de toma)."""

from datetime import date

import pytest

from src.modules.contadores.domain.services.estimacion.codificacion_cp1252 import (
    codificar_cp1252,
)
from src.modules.contadores.domain.services.estimacion.export_csv import (
    ENCABEZADO_CSV,
    AuditoriaMaquina,
    FilaExport,
    agrupar_por_maquina,
    contador_export,
    escape_csv,
    linea_csv,
    motivo_de_fuente,
    sanitizar_simbolos,
    tipo_toma_export,
)
from src.modules.contadores.domain.services.estimacion.resumen_observacion import ClaseObservada
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)
from tests.unit.domain.contadores.estimacion._resultado_builder import make_resultado

_FECHA = date(2026, 4, 30)


def _estimado(**cambios: object) -> EstimacionResultado:
    base: dict[str, object] = dict(
        estim_propuesto=12_345,
        impresiones=1_000,
        tipo_toma=14,
        fuente="Historia_Propia",
        metodo="EntreReales",
    )
    return make_resultado(**{**base, **cambios})


def _fila(
    resultado: EstimacionResultado,
    clase: str = "10",
    id_maquina: int = 1,
    serie: str = "SER1",
    empresa: str = "Empresa",
    meses: int | None = None,
) -> FilaExport:
    return FilaExport(
        id_maquina, clase, serie, empresa, "Sucursal", ClaseObservada(resultado, meses)
    )


def _campos(*filas: FilaExport, auditoria: AuditoriaMaquina | None = None) -> list[str]:
    linea = linea_csv(list(filas), _FECHA, auditoria)
    assert linea is not None
    return linea.split(";")


# ── Guarda dura: jamás un tipo real en el CSV (CsvExportServiceTests) ─────────


@pytest.mark.parametrize("tipo_malo", [4, 1, 7, 16])
def test_tipo_inesperado_se_fuerza_a_t14(tipo_malo: int) -> None:
    assert _campos(_fila(_estimado(tipo_toma=tipo_malo)))[2] == "14"


def test_t14_y_t19_salen_tal_cual() -> None:
    assert _campos(_fila(_estimado(tipo_toma=14)))[2] == "14"
    assert _campos(_fila(_estimado(tipo_toma=19)))[2] == "19"


def test_pendiente_sin_tipo_sale_vacio() -> None:
    pendiente = make_resultado(estim_propuesto=None, tipo_toma=None, fuente="Pendiente")

    assert _campos(_fila(pendiente))[2] == ""


def test_tipo_toma_export_none_es_vacio() -> None:
    assert tipo_toma_export(None) == ""


# ── Columnas ───────────────────────────────────────────────────────────────────


def test_maquina_de_una_sola_clase_va_en_las_columnas_4_y_5() -> None:
    campos = _campos(_fila(_estimado()))

    assert campos[:8] == ["SER1", "30/04/2026", "14", "10", "12345", "", "", "14"]


def test_color_que_no_discrimina_va_como_principal_con_su_clase() -> None:
    campos = _campos(_fila(_estimado(tipo_toma=19, fuente="Parque_Cliente_Tec"), clase="20"))

    assert campos[2:8] == ["19", "20", "12345", "", "", "19"]


def test_maquina_que_discrimina_mono_en_4_5_y_color_en_6_7() -> None:
    color = _fila(_estimado(estim_propuesto=800, fuente="Parque_Cliente_Modelo"), clase="20")
    mono = _fila(_estimado(estim_propuesto=5_000))

    campos = _campos(color, mono)

    assert campos[3:8] == ["10", "5000", "20", "800", "14"]


def test_tipo_y_motivo_salen_del_principal() -> None:
    mono = _fila(_estimado(tipo_toma=14, fuente="Historia_Propia"))
    color = _fila(_estimado(tipo_toma=19, fuente="Parque_Grupo_Modelo"), clase="20")

    campos = _campos(mono, color)

    assert (campos[2], campos[7]) == ("14", "14")


def test_fila_real_o_pendiente_va_con_contador_y_motivo_vacios() -> None:
    real = make_resultado(estim_propuesto=None, tipo_toma=None, fuente="Sin_Estimar")
    color = _fila(_estimado(estim_propuesto=800), clase="20")

    campos = _campos(_fila(real), color)

    assert campos[2:8] == ["", "10", "", "20", "800", ""]


def test_contador_redondea_el_medio_lejos_del_cero() -> None:
    """`{x:0}` sobre decimal (un Backup repite el anterior con decimales)."""
    assert contador_export(1_234.5) == "1235"
    assert contador_export(-1_234.5) == "-1235"
    assert contador_export(1_234.49) == "1234"
    assert contador_export(None) == ""


def test_maquina_sin_clase_10_ni_20_no_genera_linea() -> None:
    assert linea_csv([_fila(_estimado(), clase="30")], _FECHA, None) is None


def test_observacion_con_manual_saneada_e_id_log() -> None:
    auditoria = AuditoriaMaquina(sanitizar_simbolos("⚠ revisar; con el técnico"), "4817")

    campos = _campos(_fila(_estimado(impresiones=300)), auditoria=auditoria)

    assert campos[8] == "(!) revisar, con el técnico | Entre reales | +300 imp | #4817"


# ── Orden de las máquinas ──────────────────────────────────────────────────────


def test_agrupa_por_maquina_y_ordena_por_empresa_sucursal_serie_con_cultura() -> None:
    filas = [
        _fila(_estimado(), id_maquina=1, empresa="Zeta", serie="A"),
        _fila(_estimado(), id_maquina=2, empresa="Óptica", serie="B"),
        _fila(_estimado(), clase="20", id_maquina=1, empresa="Zeta", serie="A"),
        _fila(_estimado(), id_maquina=3, empresa="optica", serie="A"),
        _fila(_estimado(), id_maquina=4, empresa="Ñandú", serie="A"),
        _fila(_estimado(), id_maquina=5, empresa="nube", serie="A"),
    ]

    grupos = agrupar_por_maquina(filas)

    assert [g[0].id_maquina for g in grupos] == [5, 4, 3, 2, 1]
    assert [f.clase for f in grupos[-1]] == ["10", "20"]


# ── Helpers ────────────────────────────────────────────────────────────────────


_DATOS_PROPIOS: tuple[FuenteEstimacion, ...] = (
    "Historia_Propia",
    "T4_ST",
    "Backup_SinST",
    "EnTransito",
)
_PARQUE: tuple[FuenteEstimacion, ...] = (
    "Parque_Cliente_Tec",
    "Parque_Cliente_Modelo",
    "Parque_Grupo_Modelo",
    "Parque_Global_Modelo",
)


def test_motivo_14_datos_propios_19_parque_vacio_real_o_pendiente() -> None:
    assert [motivo_de_fuente(f) for f in _DATOS_PROPIOS] == ["14"] * 4
    assert [motivo_de_fuente(f) for f in _PARQUE] == ["19"] * 4
    assert motivo_de_fuente("Sin_Estimar") == ""
    assert motivo_de_fuente("Pendiente") == ""


def test_escape_reemplaza_separador_y_saltos_de_linea() -> None:
    assert escape_csv(None) == ""
    assert escape_csv("a;b") == "a,b"
    assert escape_csv("a\r\nb") == "a b"
    assert escape_csv("a\nb\rc") == "a b c"


def test_sanitizar_simbolos_no_es_longitud_neutral() -> None:
    assert sanitizar_simbolos("Δ5−3–2—1⚠") == "5-3-2-1(!)"


def test_encabezado() -> None:
    assert ENCABEZADO_CSV == (
        "SERIE;FECHA;TIPO;CLASE_1;CONTADOR_1;CLASE_2;CONTADOR_2;MOTIVO;OBSERVACION"
    )


def test_cp1252_con_el_best_fit_de_dotnet() -> None:
    """Lo que no existe en cp1252 no cae todo a "?": .NET aproxima."""
    assert codificar_cp1252("Nación · €") == "Nación · €".encode("cp1252")
    assert codificar_cp1252("ā ł ő − ─") == b"a l o - -"
    assert codificar_cp1252("⚠ 中") == b"? ?"
    assert codificar_cp1252("a😀b") == b"a??b"
