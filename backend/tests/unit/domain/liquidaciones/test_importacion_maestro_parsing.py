"""Tests de caracterización de las funciones puras del importador de Excel maestro
de PST (`domain/services/importacion_maestro/`). Grids como listas literales
(`list[list[Any]]`), sin pandas — mismo criterio que `test_importacion_parsing.py`.
Los casos replican los formatos reales observados en los archivos del legacy
(celdas combinadas, headers duplicados, hojas sin "AGENTE:")."""

from datetime import date
from typing import Any

import pytest

from src.modules.liquidaciones.domain.errors import ArchivoMaestroInvalidoError
from src.modules.liquidaciones.domain.services.importacion_maestro._grid import (
    buscar_columna,
    buscar_valor_agente,
    detectar_fila_header,
    grid_a_filas,
)
from src.modules.liquidaciones.domain.services.importacion_maestro._valores import (
    parse_numero_excel,
    url_o_none,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.constructor import (
    armar_resultado_importacion_maestro,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.hojas import (
    detectar_hoja_principal,
    detectar_hoja_tabla_km,
    parse_vigencia_desde_nombre,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.matching import matchear_spst
from src.modules.liquidaciones.domain.services.importacion_maestro.tabla_km import (
    extraer_spst_nombres,
    extraer_tabla_km,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.tarifarios import (
    extraer_tarifarios,
)

GRID_PRINCIPAL: list[list[Any]] = [
    ["", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "AGENTE:", "PENTACOM", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", ""],
    ["CORRECTIVOS", "", "", "", "", "", "", "", "", "", "", ""],
    [
        "Incidente", "Tipo", "Empresa", "Sucursal", "Nro. Serie", "Cantidad",
        "Costo Serv", "Cant. Km", "Costo Km", "Total viaje", "Costo total", "Fecha Cierre",
    ],
    [
        "12345-1", "Correctivo", "EMPRESA A", "SUC A", "SN1", 1,
        1500.0, 10.0, 100.0, 2500.0, 4000.0, "2026-01-05",
    ],
    [
        "12345-2", "Preventivo", "EMPRESA B", "SUC B", "SN2", 1,
        2000.0, 5.0, 100.0, 2500.0, 4500.0, "2026-01-06",
    ],
    ["", "TOTAL GENERAL", "", "", "", "", 99999.0, "", "", "", "", ""],
]

GRID_TABLA_KM: list[list[Any]] = [
    [
        "Sucursal", "Empresa", "Domicilio", "Localidad", "Provincia", "Prestador",
        "Domicilio", "Localidad", "Provincia", "Kms recorrido", "Aplica viático",
        "Kms a facturar", "RECORRIDO",
    ],
    [
        "SUC A", "EMPRESA A", "Calle 1", "Ciudad A", "Cordoba", "BASE NORTE",
        "", "", "", 45.0, "", "", "https://maps.example.com/a",
    ],
    [
        "SUC B", "EMPRESA B", "Calle 2", "Ciudad B", "Cordoba", "BASE SUR",
        "", "", "", 10.0, "", "", "no es un link",
    ],
    ["SUC C", "EMPRESA C", "", "", "", "BASE NORTE", "", "", "", None, "", "", ""],
]


# ---------------------------------------------------------------------------
# _grid
# ---------------------------------------------------------------------------


class TestBuscarValorAgente:
    def test_celda_siguiente(self) -> None:
        assert buscar_valor_agente(GRID_PRINCIPAL) == "PENTACOM"

    def test_forma_inline(self) -> None:
        grid = [["AGENTE: PENTACOM"]]
        assert buscar_valor_agente(grid) == "PENTACOM"

    def test_celda_combinada_vacia_sigue_buscando(self) -> None:
        # celda inmediatamente a la derecha vacía (celda combinada) — el legacy
        # tomaba idx+1 fijo y ahí caía en NaN, terminaba creando un prestador "nan".
        grid = [["", "AGENTE:", "", "", "PENTACOM"]]
        assert buscar_valor_agente(grid) == "PENTACOM"

    def test_sin_marcador(self) -> None:
        assert buscar_valor_agente([["Incidente", "Tipo"], ["1", "correctivo"]]) is None

    def test_valor_nan_no_cuenta(self) -> None:
        assert buscar_valor_agente([["AGENTE:", "nan"]]) is None


class TestDetectarFilaHeader:
    def test_encuentra_fila(self) -> None:
        assert detectar_fila_header(GRID_PRINCIPAL, "Incidente") == 4

    def test_sin_marcador(self) -> None:
        assert detectar_fila_header(GRID_PRINCIPAL, "Columna Inexistente") is None


class TestGridAFilas:
    def test_headers_repetidos_conserva_primera_ocurrencia(self) -> None:
        filas = grid_a_filas(GRID_TABLA_KM, 0)
        # 3 "Domicilio"/"Localidad"/"Provincia" en el header, solo la primera
        # ocurrencia de cada uno sobrevive como clave del dict.
        assert list(filas[0].keys()).count("Domicilio") == 1
        assert filas[0]["Domicilio"] == "Calle 1"

    def test_cantidad_de_filas(self) -> None:
        assert len(grid_a_filas(GRID_TABLA_KM, 0)) == 3


class TestBuscarColumna:
    def test_match_exacto_case_insensitive(self) -> None:
        assert buscar_columna(["sucursal", "Empresa"], "Sucursal") == "sucursal"

    def test_no_es_substring(self) -> None:
        # a diferencia de importacion/metadata.mapear_columnas, acá "Tipo" NO
        # debe matchear "Tipo de Equipo".
        assert buscar_columna(["Tipo de Equipo"], "Tipo") is None

    def test_sin_match(self) -> None:
        assert buscar_columna(["Empresa"], "Sucursal") is None


# ---------------------------------------------------------------------------
# _valores
# ---------------------------------------------------------------------------


class TestParseNumeroExcel:
    def test_float_real_no_se_interpreta_como_miles(self) -> None:
        # a diferencia de importacion/_valores.py::parse_monto, un float real de
        # Excel se toma tal cual (1234.56, no 123456.0).
        assert parse_numero_excel(1234.56) == pytest.approx(1234.56)

    def test_texto_limpio(self) -> None:
        assert parse_numero_excel("45.5") == pytest.approx(45.5)

    def test_valor_ilegible_devuelve_none(self) -> None:
        assert parse_numero_excel("N/A") is None

    def test_valor_none_devuelve_none(self) -> None:
        assert parse_numero_excel(None) is None

    def test_cadena_vacia_devuelve_none(self) -> None:
        assert parse_numero_excel("") is None


class TestUrlONone:
    def test_link_valido(self) -> None:
        assert url_o_none("https://maps.example.com/a") == "https://maps.example.com/a"

    def test_texto_que_no_es_link(self) -> None:
        assert url_o_none("no es un link") is None

    def test_valor_none(self) -> None:
        assert url_o_none(None) is None


# ---------------------------------------------------------------------------
# hojas
# ---------------------------------------------------------------------------


class TestDetectarHojaPrincipal:
    def test_encuentra_por_agente_sin_importar_nombre_de_hoja(self) -> None:
        # el archivo se llama "ABRIL", no "ENERO" — el bug del legacy no se replica.
        hojas = {"ABRIL": GRID_PRINCIPAL, "TABLA KMS": GRID_TABLA_KM}
        assert detectar_hoja_principal(hojas) == "ABRIL"

    def test_ninguna_hoja_tiene_agente(self) -> None:
        hojas = {"INCIDENTES": [["Incidente", "Tipo"], ["1", "correctivo"]]}
        assert detectar_hoja_principal(hojas) is None


class TestDetectarHojaTablaKm:
    def test_variantes_de_nombre(self) -> None:
        for nombre in ("TABLA KMS", "TABLA DE KMS", "TABLA KMS 2023"):
            assert detectar_hoja_tabla_km({nombre: GRID_TABLA_KM}) == nombre

    def test_sin_hoja_compatible(self) -> None:
        assert detectar_hoja_tabla_km({"INCIDENTES": GRID_PRINCIPAL}) is None


class TestParseVigenciaDesdeNombre:
    def test_patron_estandar(self) -> None:
        assert parse_vigencia_desde_nombre("PENTACOM 202601.xlsx", date(2026, 6, 1)) == date(
            2026, 1, 1
        )

    def test_mes_invalido_cae_a_hoy(self) -> None:
        assert parse_vigencia_desde_nombre("PENTACOM 202613.xlsx", date(2026, 6, 1)) == date(
            2026, 6, 1
        )

    def test_sin_patron_cae_a_hoy(self) -> None:
        assert parse_vigencia_desde_nombre("archivo_sin_fecha.xlsx", date(2026, 6, 1)) == date(
            2026, 6, 1
        )

    def test_rename_de_descarga_duplicada_no_matchea(self) -> None:
        # limitación conocida y aceptada: "PENTACOM 202601 (1).xlsx" (rename típico
        # de Chrome ante una descarga duplicada) no matchea el patrón anclado a la
        # extensión — cae al fallback de "hoy", igual que el legacy.
        assert parse_vigencia_desde_nombre(
            "PENTACOM 202601 (1).xlsx", date(2026, 6, 1)
        ) == date(2026, 6, 1)


# ---------------------------------------------------------------------------
# tarifarios
# ---------------------------------------------------------------------------


class TestExtraerTarifarios:
    def test_extrae_y_normaliza_tipo(self) -> None:
        filas = grid_a_filas(GRID_PRINCIPAL, 4)
        tarifarios = extraer_tarifarios(filas, date(2026, 1, 1))
        tipos = {t.tipo_servicio for t in tarifarios}
        assert tipos == {"correctivo", "preventivo"}

    def test_descarta_tipo_fuera_de_whitelist(self) -> None:
        # "TOTAL GENERAL" no normaliza a ningún tipo conocido — se descarta, no se
        # persiste como tarifario basura.
        filas = grid_a_filas(GRID_PRINCIPAL, 4)
        tarifarios = extraer_tarifarios(filas, date(2026, 1, 1))
        assert all(t.costo_servicio != 99999.0 for t in tarifarios)

    def test_descarta_costo_no_positivo(self) -> None:
        filas = [{"Tipo": "Correctivo", "Costo Serv": 0, "Costo Km": 100}]
        assert extraer_tarifarios(filas, date(2026, 1, 1)) == []

    def test_dedup_dentro_del_archivo(self) -> None:
        filas = [
            {"Tipo": "Correctivo", "Costo Serv": 1500.0, "Costo Km": 100.0},
            {"Tipo": "Correctivo", "Costo Serv": 1500.0, "Costo Km": 100.0},
        ]
        assert len(extraer_tarifarios(filas, date(2026, 1, 1))) == 1


# ---------------------------------------------------------------------------
# tabla_km
# ---------------------------------------------------------------------------


class TestExtraerTablaKm:
    def test_extrae_filas_validas(self) -> None:
        filas = grid_a_filas(GRID_TABLA_KM, 0)
        resultado = extraer_tabla_km(filas)
        assert {r.sucursal_nombre for r in resultado} == {"SUC A", "SUC B"}

    def test_descarta_fila_sin_kms(self) -> None:
        filas = grid_a_filas(GRID_TABLA_KM, 0)
        resultado = extraer_tabla_km(filas)
        assert all(r.sucursal_nombre != "SUC C" for r in resultado)

    def test_url_invalida_queda_none(self) -> None:
        filas = grid_a_filas(GRID_TABLA_KM, 0)
        resultado = {r.sucursal_nombre: r for r in extraer_tabla_km(filas)}
        assert resultado["SUC B"].url_maps is None
        assert resultado["SUC A"].url_maps == "https://maps.example.com/a"

    def test_aplica_viatico_por_umbral(self) -> None:
        filas = grid_a_filas(GRID_TABLA_KM, 0)
        resultado = {r.sucursal_nombre: r for r in extraer_tabla_km(filas)}
        assert resultado["SUC A"].aplica_viatico is True  # 45.0 > 30.0
        assert resultado["SUC B"].aplica_viatico is False  # 10.0 <= 30.0


class TestExtraerSpstNombres:
    def test_dedup_case_insensitive(self) -> None:
        filas = grid_a_filas(GRID_TABLA_KM, 0)
        assert extraer_spst_nombres(filas) == ["BASE NORTE", "BASE SUR"]


# ---------------------------------------------------------------------------
# matching
# ---------------------------------------------------------------------------


class TestMatchearSpst:
    def test_exacto_case_insensitive(self) -> None:
        assert matchear_spst("base norte", ["BASE NORTE", "BASE SUR"]) == "BASE NORTE"

    def test_substring_buscado_en_disponible(self) -> None:
        assert matchear_spst("NORTE", ["BASE NORTE", "BASE SUR"]) == "BASE NORTE"

    def test_substring_disponible_en_buscado(self) -> None:
        assert matchear_spst("BASE NORTE VILLA MERCEDES", ["NORTE"]) == "NORTE"

    def test_sin_match(self) -> None:
        assert matchear_spst("OESTE", ["BASE NORTE"]) is None

    def test_nombre_buscado_none(self) -> None:
        assert matchear_spst(None, ["BASE NORTE"]) is None


# ---------------------------------------------------------------------------
# constructor (composición completa)
# ---------------------------------------------------------------------------


class TestArmarResultadoImportacionMaestro:
    def test_composicion_completa(self) -> None:
        hojas = {"ENERO": GRID_PRINCIPAL, "TABLA KMS": GRID_TABLA_KM}
        resultado = armar_resultado_importacion_maestro(
            hojas, "PENTACOM 202601.xlsx", date(2026, 6, 1)
        )
        assert resultado.nombre_corto == "PENTACOM"
        assert resultado.vigencia == date(2026, 1, 1)
        assert resultado.hoja_tabla_km == "TABLA KMS"
        assert {s.nombre for s in resultado.spsts} == {"BASE NORTE", "BASE SUR"}
        assert len(resultado.tarifarios) == 2
        assert len(resultado.tabla_km) == 2

    def test_sin_hoja_agente_lanza(self) -> None:
        hojas = {"INCIDENTES": [["Incidente", "Tipo"], ["1", "correctivo"]]}
        with pytest.raises(ArchivoMaestroInvalidoError):
            armar_resultado_importacion_maestro(hojas, "CATAMARCA 202604.xlsx", date(2026, 6, 1))

    def test_sin_hoja_tabla_km_no_es_fatal(self) -> None:
        # ej. CATAMARCA 202604.xlsx en los docs del legacy: tiene hoja principal
        # pero no tiene ninguna hoja de Tabla KM.
        hojas = {"ABRIL": GRID_PRINCIPAL}
        resultado = armar_resultado_importacion_maestro(
            hojas, "CATAMARCA 202604.xlsx", date(2026, 6, 1)
        )
        assert resultado.hoja_tabla_km is None
        assert resultado.spsts == []
        assert resultado.tabla_km == []
        assert len(resultado.tarifarios) == 2
