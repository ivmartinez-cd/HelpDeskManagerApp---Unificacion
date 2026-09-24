"""Parseo de `GetEnvioEstadoActual` de OCA: fila en `//NewDataSet/Table`, textos
recortados, `IdEstado` opcional (acuses) y errores de formato como
`RespuestaOcaInvalidaError`. Las muestras replican respuestas reales observadas."""

from datetime import date

import pytest

from src.modules.insumos.domain.errores_despachados import RespuestaOcaInvalidaError
from src.modules.insumos.infrastructure.oca.parseo_estado_oca import parsear_estado_actual

_GUIA = "2610800000000214438"

_FILA_REAL = """
    <Operativa>434324</Operativa><OrdenRetiro>148732544</OrdenRetiro>
    <FechaRetiro>24/09/2026</FechaRetiro><Remito>Envio</Remito>
    <Destinatarios>SINDICATO DE PETROLEO Y GAS</Destinatarios><eMail />
    <NumeroEnvio>2610800000000214438</NumeroEnvio><CantidadPaquetes>4</CantidadPaquetes>
    <Seguro>10.0000</Seguro><SucursalActual>CENTRO DE OPERACIONES BS AS </SucursalActual>
    <CIDestino /><FechaEstado>24/09/2026</FechaEstado><Estado>En proceso de Retiro</Estado>
    <IdEstado>1</IdEstado><Motivo>Sin Motivo</Motivo>
"""


def _new_dataset(fila: str) -> bytes:
    return f'<NewDataSet xmlns=""><Table>{fila}</Table></NewDataSet>'.encode()


def _dataset_completo(fila: str) -> bytes:
    """DataSet tal como lo serializa OCA: esquema (que nombra "Table" en un atributo)
    más el diffgram con la fila."""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<DataSet xmlns="#Oca_e_Pak">
  <xs:schema id="NewDataSet" xmlns="" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="NewDataSet"><xs:complexType><xs:choice>
      <xs:element name="Table"/>
    </xs:choice></xs:complexType></xs:element>
  </xs:schema>
  <diffgr:diffgram xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1">
    <NewDataSet xmlns=""><Table diffgr:id="Table1">{fila}</Table></NewDataSet>
  </diffgr:diffgram>
</DataSet>""".encode()


def _fila_con(**reemplazos: str) -> str:
    """La fila real con algunos elementos reemplazados (el valor es el XML completo)."""
    fila = _FILA_REAL
    for etiqueta, xml in reemplazos.items():
        inicio = fila.index(f"<{etiqueta}>")
        fin = fila.index(f"</{etiqueta}>") + len(f"</{etiqueta}>")
        fila = fila[:inicio] + xml + fila[fin:]
    return fila


def test_parsea_la_fila_real_del_ejemplo() -> None:
    estado = parsear_estado_actual(_new_dataset(_FILA_REAL), _GUIA)

    assert estado is not None
    assert estado.numero_envio == _GUIA
    assert estado.operativa == "434324"
    assert estado.orden_retiro == "148732544"
    assert estado.sucursal_actual == "CENTRO DE OPERACIONES BS AS"
    assert estado.fecha_estado == date(2026, 9, 24)
    assert estado.estado == "En proceso de Retiro"
    assert estado.id_estado == 1
    assert estado.motivo == "Sin Motivo"
    assert estado.cantidad_paquetes == 4


def test_dataset_completo_con_esquema_y_diffgram() -> None:
    estado = parsear_estado_actual(_dataset_completo(_FILA_REAL), _GUIA)

    assert estado is not None
    assert estado.id_estado == 1
    assert estado.estado == "En proceso de Retiro"


def test_dataset_sin_table_es_none() -> None:
    vacio = (
        b'<DataSet xmlns="#Oca_e_Pak"><diffgr:diffgram '
        b'xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1"/></DataSet>'
    )

    assert parsear_estado_actual(vacio, _GUIA) is None


def test_esquema_sin_filas_es_none() -> None:
    """El esquema nombra "Table" pero no hay fila: no se confunde con un estado."""
    xml = _dataset_completo("").replace(b'<Table diffgr:id="Table1"></Table>', b"")

    assert parsear_estado_actual(xml, _GUIA) is None


def test_acuse_sin_id_estado() -> None:
    fila = _fila_con(IdEstado="", Estado="<Estado> Rendicion de Acuse Finalizado </Estado>")

    estado = parsear_estado_actual(_new_dataset(fila), _GUIA)

    assert estado is not None
    assert estado.id_estado is None
    assert estado.estado == "Rendicion de Acuse Finalizado"


def test_id_estado_vacio_es_none() -> None:
    estado = parsear_estado_actual(_new_dataset(_fila_con(IdEstado="<IdEstado />")), _GUIA)

    assert estado is not None
    assert estado.id_estado is None


def test_id_estado_no_numerico_es_error() -> None:
    fila = _fila_con(IdEstado="<IdEstado>uno</IdEstado>")

    with pytest.raises(RespuestaOcaInvalidaError, match="IdEstado"):
        parsear_estado_actual(_new_dataset(fila), _GUIA)


@pytest.mark.parametrize("fecha", ["<FechaEstado>2026-09-24</FechaEstado>", "<FechaEstado />", ""])
def test_fecha_estado_invalida_o_ausente_es_error(fecha: str) -> None:
    fila = _fila_con(FechaEstado=fecha)

    with pytest.raises(RespuestaOcaInvalidaError, match=_GUIA):
        parsear_estado_actual(_new_dataset(fila), _GUIA)


def test_xml_roto_es_error() -> None:
    with pytest.raises(RespuestaOcaInvalidaError, match="XML mal formado"):
        parsear_estado_actual(b"<DataSet><Table>", _GUIA)


@pytest.mark.parametrize(
    "cuerpo",
    [
        b'<string xmlns="http://tempuri.org/">Servicio no disponible</string>',
        b"<html><body><h1>Acceso bloqueado</h1></body></html>",
    ],
    ids=["error-asmx", "pagina-del-proxy"],
)
def test_xml_que_no_es_un_dataset_es_error_y_no_una_guia_sin_datos(cuerpo: bytes) -> None:
    # Si se tomara como None, la guía pasaría a "Sin datos en OCA" sin que OCA lo dijera.
    with pytest.raises(RespuestaOcaInvalidaError, match="no es un DataSet de OCA"):
        parsear_estado_actual(cuerpo, _GUIA)


def test_motivo_vacio_queda_vacio() -> None:
    estado = parsear_estado_actual(_new_dataset(_fila_con(Motivo="<Motivo />")), _GUIA)

    assert estado is not None
    assert estado.motivo == ""


def test_numero_envio_vacio_usa_la_guia_consultada() -> None:
    fila = _fila_con(NumeroEnvio="<NumeroEnvio> </NumeroEnvio>")

    estado = parsear_estado_actual(_new_dataset(fila), _GUIA)

    assert estado is not None
    assert estado.numero_envio == _GUIA


@pytest.mark.parametrize(
    "cantidad", ["<CantidadPaquetes />", "<CantidadPaquetes>x</CantidadPaquetes>"]
)
def test_cantidad_paquetes_vacia_o_ilegible_es_none(cantidad: str) -> None:
    estado = parsear_estado_actual(_new_dataset(_fila_con(CantidadPaquetes=cantidad)), _GUIA)

    assert estado is not None
    assert estado.cantidad_paquetes is None
