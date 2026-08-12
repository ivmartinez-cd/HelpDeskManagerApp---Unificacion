"""Tests de caracterización de las funciones puras de parsing de la importación.

Cubre `_valores.py`, `metadata.py`, `normalizacion.py` y `constructor.py` sin ningún
I/O ni pandas: son funciones deterministas sobre strings/dicts, testeables en
aislamiento total. Los casos replican los formatos reales que exporta el sistema fuente
del prestador (nombres de archivo reales, montos con separador de miles, fechas en los
formatos observados en los archivos .xls descargados)."""

from datetime import date

import pytest

from src.modules.liquidaciones.domain.entities.liquidacion import (
    TIPO_CC,
    TIPO_DEPOSITO,
    TIPO_PRECO,
    TIPO_REGULAR,
)
from src.modules.liquidaciones.domain.entities.tarifario import (
    TIPO_CORRECTIVO,
    TIPO_GUARDIA,
    TIPO_INSTALACION_DESINSTALACION,
    TIPO_PRE_CORRECTIVO,
    TIPO_PREVENTIVO,
    TIPO_SISTEMAS,
)
from src.modules.liquidaciones.domain.services.importacion._valores import (
    parse_fecha,
    parse_monto,
)
from src.modules.liquidaciones.domain.services.importacion.constructor import (
    armar_resultado_importacion,
    construir_incidente_importado,
)
from src.modules.liquidaciones.domain.services.importacion.metadata import (
    extraer_numero_liquidacion,
    extraer_periodo,
    extraer_tipo_liquidacion,
    mapear_columnas,
)
from src.modules.liquidaciones.domain.services.importacion.normalizacion import (
    normalizar_tipo_servicio,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)

# ---------------------------------------------------------------------------
# parse_monto
# ---------------------------------------------------------------------------


class TestParseMonto:
    def test_entero_simple(self) -> None:
        assert parse_monto("1500") == pytest.approx(1500.0)

    def test_decimal_con_coma(self) -> None:
        # formato argentino: "1.500,00" → 1500.00
        assert parse_monto("1.500,00") == pytest.approx(1500.0)

    def test_miles_sin_decimales(self) -> None:
        assert parse_monto("10.000") == pytest.approx(10000.0)

    def test_prefijo_pesos(self) -> None:
        assert parse_monto("$ 2.300,50") == pytest.approx(2300.5)

    def test_valor_none(self) -> None:
        assert parse_monto(None) == pytest.approx(0.0)

    def test_cadena_vacia(self) -> None:
        assert parse_monto("") == pytest.approx(0.0)

    def test_guion_vacio(self) -> None:
        assert parse_monto("-") == pytest.approx(0.0)

    def test_nan_texto(self) -> None:
        assert parse_monto("nan") == pytest.approx(0.0)

    def test_none_texto(self) -> None:
        assert parse_monto("none") == pytest.approx(0.0)

    def test_valor_ilegible(self) -> None:
        assert parse_monto("N/A") == pytest.approx(0.0)

    def test_float_con_punto_decimal_trata_el_punto_como_miles(self) -> None:
        # parse_monto recibe texto de CSV argentino — si pandas ya lo convirtió a float,
        # "1234.56" → elimina el punto (separador de miles) → 123456.0. No es un bug:
        # los valores numéricos reales llegan como texto desde pandas en estos archivos.
        assert parse_monto(1234.56) == pytest.approx(123456.0)

    def test_int_ya_parseado(self) -> None:
        assert parse_monto(0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# parse_fecha
# ---------------------------------------------------------------------------


class TestParseFecha:
    def test_formato_yyyymmdd(self) -> None:
        assert parse_fecha("20260115") == date(2026, 1, 15)

    def test_formato_dd_mm_yyyy(self) -> None:
        assert parse_fecha("15/01/2026") == date(2026, 1, 15)

    def test_formato_yyyy_mm_dd(self) -> None:
        assert parse_fecha("2026-01-15") == date(2026, 1, 15)

    def test_formato_dd_mm_yy(self) -> None:
        assert parse_fecha("15/01/26") == date(2026, 1, 15)

    def test_formato_dd_mm_yyyy_con_guion(self) -> None:
        assert parse_fecha("15-01-2026") == date(2026, 1, 15)

    def test_none(self) -> None:
        assert parse_fecha(None) is None

    def test_cadena_vacia(self) -> None:
        assert parse_fecha("") is None

    def test_nan(self) -> None:
        assert parse_fecha("nan") is None

    def test_formato_ilegible(self) -> None:
        assert parse_fecha("no-es-fecha") is None


# ---------------------------------------------------------------------------
# mapear_columnas
# ---------------------------------------------------------------------------


class TestMapearColumnas:
    def test_nombres_exactos(self) -> None:
        cols = ["Incidente", "Rubro", "Tipo", "Empresa", "Sucursal"]
        mapeo = mapear_columnas(cols)
        assert mapeo["Incidente"] == "numero_incidente"
        assert mapeo["Rubro"] == "rubro"
        assert mapeo["Tipo"] == "tipo"
        assert mapeo["Empresa"] == "empresa"
        assert mapeo["Sucursal"] == "sucursal"

    def test_nombres_con_variantes(self) -> None:
        cols = ["Nro Incidente", "Fecha Cierre", "Costo Serv.", "Cant. KM", "P.IT"]
        mapeo = mapear_columnas(cols)
        assert mapeo["Nro Incidente"] == "numero_incidente"
        assert mapeo["Fecha Cierre"] == "fecha_cierre"
        assert mapeo["Costo Serv."] == "costo_serv"
        assert mapeo["Cant. KM"] == "cant_km"
        assert mapeo["P.IT"] == "pasa_it"

    def test_columna_desconocida_se_ignora(self) -> None:
        mapeo = mapear_columnas(["Columna Rara", "Incidente"])
        assert "Columna Rara" not in mapeo
        assert mapeo["Incidente"] == "numero_incidente"

    def test_lista_vacia(self) -> None:
        assert mapear_columnas([]) == {}

    def test_cliente_mapea_a_empresa(self) -> None:
        mapeo = mapear_columnas(["Cliente"])
        assert mapeo["Cliente"] == "empresa"

    def test_costo_km_variante(self) -> None:
        mapeo = mapear_columnas(["Precio KM"])
        assert mapeo["Precio KM"] == "costo_km"


# ---------------------------------------------------------------------------
# extraer_numero_liquidacion
# ---------------------------------------------------------------------------


class TestExtraerNumeroLiquidacion:
    def test_patron_tipico_con_guion(self) -> None:
        assert extraer_numero_liquidacion("liquidacion_1-2_20260101.xls") == "1-2"

    def test_patron_con_guion_bajo(self) -> None:
        # el legacy usaba guion bajo en algunos exports — se normaliza a guion
        assert extraer_numero_liquidacion("liquidacion_1_2_20260101.xls") == "1-2"

    def test_sin_patron(self) -> None:
        assert extraer_numero_liquidacion("export_general.xls") == ""

    def test_case_insensitive(self) -> None:
        assert extraer_numero_liquidacion("Liquidacion_3-5_20260201.XLS") == "3-5"


# ---------------------------------------------------------------------------
# extraer_tipo_liquidacion
# ---------------------------------------------------------------------------


class TestExtraerTipoLiquidacion:
    def test_regular_por_defecto(self) -> None:
        assert extraer_tipo_liquidacion("liquidacion_1-1_20260101.xls") == TIPO_REGULAR

    def test_preco(self) -> None:
        assert extraer_tipo_liquidacion("liquidacion_preco_1-1_20260101.xls") == TIPO_PRECO

    def test_cc(self) -> None:
        assert extraer_tipo_liquidacion("liquidacion_cc_1-1_20260101.xls") == TIPO_CC

    def test_centro_civico(self) -> None:
        assert extraer_tipo_liquidacion("liquidacion_centro_civico_2026.xls") == TIPO_CC

    def test_deposito(self) -> None:
        assert extraer_tipo_liquidacion("liquidacion_deposito_enero.xls") == TIPO_DEPOSITO

    def test_bodega(self) -> None:
        assert extraer_tipo_liquidacion("liquidacion_bodega_enero.xls") == TIPO_DEPOSITO


# ---------------------------------------------------------------------------
# extraer_periodo
# ---------------------------------------------------------------------------


class TestExtraerPeriodo:
    def _inc(self, fecha: date) -> IncidenteImportado:
        return IncidenteImportado(
            numero_incidente="12345-1",
            rubro="Impresoras",
            tipo="correctivo",
            empresa_nombre="Empresa Test",
            sucursal_nombre="Sucursal Test",
            nro_serie="",
            fecha_cierre=fecha,
            costo_servicio_cobrado=0.0,
            cant_km_cobrado=0.0,
            costo_km_cobrado=0.0,
            total_viaje_cobrado=0.0,
            costo_total_cobrado=0.0,
            pasa_it=True,
        )

    def test_periodo_desde_fechas_de_incidentes(self) -> None:
        incidentes = [self._inc(date(2026, 1, 10)), self._inc(date(2026, 1, 20))]
        assert extraer_periodo("archivo.xls", incidentes) == "2026-01"

    def test_periodo_mas_frecuente_gana(self) -> None:
        incidentes = [
            self._inc(date(2026, 1, 5)),
            self._inc(date(2026, 1, 10)),
            self._inc(date(2025, 12, 28)),
        ]
        assert extraer_periodo("archivo.xls", incidentes) == "2026-01"

    def test_fallback_a_nombre_de_archivo(self) -> None:
        # sin incidentes: la fecha en el nombre asume que se exportó el mes siguiente
        # al liquidado (e.g. exportado el 20260201 → período 2026-01)
        assert extraer_periodo("liquidacion_20260201.xls", []) == "2026-01"

    def test_fallback_enero_sube_anio(self) -> None:
        # exportado el 20260101 → período 2025-12
        assert extraer_periodo("liquidacion_20260101.xls", []) == "2025-12"

    def test_sin_incidentes_ni_fecha_en_nombre(self) -> None:
        assert extraer_periodo("export.xls", []) == ""


# ---------------------------------------------------------------------------
# normalizar_tipo_servicio
# ---------------------------------------------------------------------------


class TestNormalizarTipoServicio:
    def test_correctivo(self) -> None:
        assert normalizar_tipo_servicio("Correctivo") == TIPO_CORRECTIVO

    def test_preventivo(self) -> None:
        assert normalizar_tipo_servicio("Preventivo") == TIPO_PREVENTIVO

    def test_instalacion(self) -> None:
        assert normalizar_tipo_servicio("Instalación") == TIPO_INSTALACION_DESINSTALACION

    def test_desinstalacion(self) -> None:
        assert normalizar_tipo_servicio("Desinstalacion equipo") == TIPO_INSTALACION_DESINSTALACION

    def test_pre_correctivo_con_guion(self) -> None:
        assert normalizar_tipo_servicio("Pre-correctivo") == TIPO_PRE_CORRECTIVO

    def test_pre_correctivo_sin_guion(self) -> None:
        assert normalizar_tipo_servicio("Pre correctivo") == TIPO_PRE_CORRECTIVO

    def test_preco_abreviado(self) -> None:
        assert normalizar_tipo_servicio("Preco") == TIPO_PRE_CORRECTIVO

    def test_guardia(self) -> None:
        assert normalizar_tipo_servicio("Guardia técnica") == TIPO_GUARDIA

    def test_sistemas(self) -> None:
        assert normalizar_tipo_servicio("Sistemas") == TIPO_SISTEMAS

    def test_vacio_cae_a_correctivo(self) -> None:
        assert normalizar_tipo_servicio("") == TIPO_CORRECTIVO

    def test_desconocido_devuelve_el_texto(self) -> None:
        # texto libre no reconocido → se pasa tal cual (mismo comportamiento legacy)
        assert normalizar_tipo_servicio("Mantenimiento especial") == "mantenimiento especial"

    def test_instalacion_gana_a_correctivo_como_substring(self) -> None:
        # "instalacion correctiva" contiene "correctivo" como substring,
        # pero la instalación tiene precedencia (orden del if en el código)
        assert normalizar_tipo_servicio("Instalacion correctiva") == TIPO_INSTALACION_DESINSTALACION


# ---------------------------------------------------------------------------
# construir_incidente_importado
# ---------------------------------------------------------------------------


class TestConstruirIncidenteImportado:
    def _fila_base(self) -> dict[str, object]:
        return {
            "numero_incidente": "12345-1",
            "rubro": "Impresoras",
            "tipo": "Correctivo",
            "empresa": "Empresa Test",
            "sucursal": "Sucursal Test",
            "nro_serie": "SN001",
            "fecha_cierre": "15/01/2026",
            "costo_serv": "1.500,00",
            "cant_km": "0",
            "costo_km": "0",
            "total_viaje": "0",
            "costo_total": "1.500,00",
            "pasa_it": "SI",
        }

    def test_happy_path(self) -> None:
        inc = construir_incidente_importado(self._fila_base())
        assert inc is not None
        assert inc.numero_incidente == "12345-1"
        assert inc.tipo == TIPO_CORRECTIVO
        assert inc.costo_servicio_cobrado == pytest.approx(1500.0)
        assert inc.costo_total_cobrado == pytest.approx(1500.0)
        assert inc.fecha_cierre == date(2026, 1, 15)
        assert inc.pasa_it is True

    def test_numero_incidente_con_prefijo_extrae_patron(self) -> None:
        fila = {**self._fila_base(), "numero_incidente": "INC 12345-1 (extra)"}
        inc = construir_incidente_importado(fila)
        assert inc is not None
        assert inc.numero_incidente == "12345-1"

    def test_fila_nan_devuelve_none(self) -> None:
        fila = {**self._fila_base(), "numero_incidente": "nan"}
        assert construir_incidente_importado(fila) is None

    def test_fila_encabezado_repetido_devuelve_none(self) -> None:
        fila = {**self._fila_base(), "numero_incidente": "Incidente"}
        assert construir_incidente_importado(fila) is None

    def test_numero_vacio_devuelve_none(self) -> None:
        fila = {**self._fila_base(), "numero_incidente": ""}
        assert construir_incidente_importado(fila) is None

    def test_pasa_it_no(self) -> None:
        fila = {**self._fila_base(), "pasa_it": "NO"}
        inc = construir_incidente_importado(fila)
        assert inc is not None
        assert inc.pasa_it is False

    def test_rubro_vacio_cae_a_impresoras(self) -> None:
        fila = {**self._fila_base(), "rubro": ""}
        inc = construir_incidente_importado(fila)
        assert inc is not None
        assert inc.rubro == "Impresoras"

    def test_monto_con_separador_de_miles(self) -> None:
        fila = {**self._fila_base(), "costo_serv": "12.500,75", "costo_total": "12.500,75"}
        inc = construir_incidente_importado(fila)
        assert inc is not None
        assert inc.costo_servicio_cobrado == pytest.approx(12500.75)


# ---------------------------------------------------------------------------
# armar_resultado_importacion
# ---------------------------------------------------------------------------


class TestArmarResultadoImportacion:
    def _fila(self, numero: str = "12345-1", costo: str = "1500") -> dict[str, object]:
        return {
            "numero_incidente": numero,
            "rubro": "Impresoras",
            "tipo": "Correctivo",
            "empresa": "Empresa Test",
            "sucursal": "Sucursal Test",
            "nro_serie": "",
            "fecha_cierre": "15/01/2026",
            "costo_serv": costo,
            "cant_km": "0",
            "costo_km": "0",
            "total_viaje": "0",
            "costo_total": costo,
            "pasa_it": "SI",
        }

    def test_resultado_con_dos_incidentes(self) -> None:
        filas = [self._fila("12345-1"), self._fila("12345-2")]
        res = armar_resultado_importacion("liquidacion_1-1_20260101.xls", filas)
        assert len(res.incidentes) == 2
        assert res.numero_liquidacion == "1-1"
        assert res.tipo_liquidacion == TIPO_REGULAR

    def test_filtra_filas_invalidas(self) -> None:
        filas = [
            self._fila("12345-1"),
            {**self._fila(), "numero_incidente": "nan"},
            {**self._fila(), "numero_incidente": "Incidente"},
        ]
        res = armar_resultado_importacion("archivo.xls", filas)
        assert len(res.incidentes) == 1

    def test_lista_vacia_devuelve_resultado_vacio(self) -> None:
        res = armar_resultado_importacion("liquidacion_20260201.xls", [])
        assert res.incidentes == []
        assert res.numero_liquidacion == ""
        assert res.periodo == "2026-01"

    def test_periodo_derivado_de_fechas_de_incidentes(self) -> None:
        res = armar_resultado_importacion("archivo.xls", [self._fila()])
        assert res.periodo == "2026-01"
