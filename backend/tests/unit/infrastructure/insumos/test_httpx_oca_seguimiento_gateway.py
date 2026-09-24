"""HttpxOcaSeguimientoGateway contra httpx.MockTransport (sin red): parámetros y
User-Agent del GET, reintentos solo ante 5xx/429 o fallas de transporte, y toda falla
de OCA como `ExternalServiceError`. Las esperas entre reintentos se neutralizan."""

from collections.abc import Callable

import httpx
import pytest

from src.modules.insumos.domain.errores_despachados import RespuestaOcaInvalidaError
from src.modules.insumos.infrastructure.oca import httpx_oca_seguimiento_gateway
from src.modules.insumos.infrastructure.oca.httpx_oca_seguimiento_gateway import (
    HttpxOcaSeguimientoGateway,
)
from src.shared.domain.errors import ExternalServiceError

_URL = "https://oca.example/ePak_tracking/Oep_TrackEPak.asmx/GetEnvioEstadoActual"
_GUIA = "2610800000000214438"
_RESPUESTA_OK = b"""<DataSet xmlns="#Oca_e_Pak">
  <xs:schema xmlns="" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="Table"/>
  </xs:schema>
  <diffgr:diffgram xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1"><NewDataSet xmlns="">
    <Table><NumeroEnvio>2610800000000214438</NumeroEnvio><FechaEstado>24/09/2026</FechaEstado>
    <IdEstado>1</IdEstado><Estado>En proceso de Retiro</Estado><Motivo>Sin Motivo</Motivo></Table>
  </NewDataSet></diffgr:diffgram></DataSet>"""
_RESPUESTA_VACIA = (
    b'<DataSet xmlns="#Oca_e_Pak"><diffgr:diffgram '
    b'xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1"/></DataSet>'
)

Respuesta = httpx.Response | Exception


class _OcaFalsa:
    """Devuelve las respuestas en orden (la última se repite) y guarda los pedidos."""

    def __init__(self, *respuestas: Respuesta) -> None:
        self.respuestas = list(respuestas)
        self.pedidos: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.pedidos.append(request)
        respuesta = self.respuestas.pop(0) if len(self.respuestas) > 1 else self.respuestas[0]
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


@pytest.fixture
def esperas(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    registradas: list[float] = []

    async def sin_pausa(segundos: float) -> None:
        registradas.append(segundos)

    monkeypatch.setattr(httpx_oca_seguimiento_gateway.asyncio, "sleep", sin_pausa)
    return registradas


def _gateway(handler: Callable[[httpx.Request], httpx.Response]) -> HttpxOcaSeguimientoGateway:
    return HttpxOcaSeguimientoGateway(_URL, 30.0, transport=httpx.MockTransport(handler))


async def test_envia_guia_orden_retiro_vacia_y_user_agent_propio() -> None:
    oca = _OcaFalsa(httpx.Response(200, content=_RESPUESTA_OK))

    await _gateway(oca).consultar_estado_actual(_GUIA)

    pedido = oca.pedidos[0]
    assert pedido.method == "GET"
    assert str(pedido.url).startswith(_URL)
    assert pedido.url.params["numeroEnvio"] == _GUIA
    assert pedido.url.params["ordenRetiro"] == ""
    assert pedido.headers["User-Agent"] == "helpdesk-manager/1.0 (+insumos-despachados)"


async def test_200_devuelve_el_estado_parseado() -> None:
    oca = _OcaFalsa(httpx.Response(200, content=_RESPUESTA_OK))

    estado = await _gateway(oca).consultar_estado_actual(_GUIA)

    assert estado is not None
    assert estado.numero_envio == _GUIA
    assert estado.id_estado == 1
    assert estado.estado == "En proceso de Retiro"


async def test_500_y_luego_200_reintenta(esperas: list[float]) -> None:
    oca = _OcaFalsa(httpx.Response(500), httpx.Response(200, content=_RESPUESTA_OK))

    estado = await _gateway(oca).consultar_estado_actual(_GUIA)

    assert estado is not None
    assert len(oca.pedidos) == 2
    assert esperas == [0.5]


async def test_500_persistente_agota_reintentos_y_loguea_la_guia(
    esperas: list[float], caplog: pytest.LogCaptureFixture
) -> None:
    oca = _OcaFalsa(httpx.Response(500))

    with pytest.raises(ExternalServiceError, match="HTTP 500"):
        await _gateway(oca).consultar_estado_actual(_GUIA)

    assert len(oca.pedidos) == 3
    assert esperas == [0.5, 1.0]
    assert f"No se pudo consultar OCA para la guía {_GUIA}" in caplog.text


async def test_404_no_reintenta(esperas: list[float]) -> None:
    oca = _OcaFalsa(httpx.Response(404))

    with pytest.raises(ExternalServiceError, match="HTTP 404"):
        await _gateway(oca).consultar_estado_actual(_GUIA)

    assert len(oca.pedidos) == 1
    assert esperas == []


async def test_error_de_conexion_reintenta_y_termina_en_external_service_error(
    esperas: list[float],
) -> None:
    oca = _OcaFalsa(httpx.ConnectError("sin ruta"))

    with pytest.raises(ExternalServiceError, match=_GUIA):
        await _gateway(oca).consultar_estado_actual(_GUIA)

    assert len(oca.pedidos) == 3


async def test_xml_roto_es_respuesta_invalida() -> None:
    oca = _OcaFalsa(httpx.Response(200, content=b"<html>Proxy error</html"))

    with pytest.raises(RespuestaOcaInvalidaError):
        await _gateway(oca).consultar_estado_actual(_GUIA)


async def test_error_http_deja_en_el_log_el_comienzo_del_cuerpo(
    esperas: list[float], caplog: pytest.LogCaptureFixture
) -> None:
    causa = "System.InvalidOperationException: Request format is invalid"
    oca = _OcaFalsa(httpx.Response(400, text=causa))

    with pytest.raises(ExternalServiceError, match="HTTP 400"):
        await _gateway(oca).consultar_estado_actual(_GUIA)

    assert causa in caplog.text


async def test_campo_ilegible_no_loguea_los_datos_del_destinatario(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cuerpo = _RESPUESTA_OK.replace(b"24/09/2026", b"2026-09-24").replace(
        b"<Motivo>", b"<eMail>destinatario@example.com</eMail><Motivo>"
    )
    oca = _OcaFalsa(httpx.Response(200, content=cuerpo))

    with pytest.raises(RespuestaOcaInvalidaError, match="FechaEstado"):
        await _gateway(oca).consultar_estado_actual(_GUIA)

    assert f"respuesta ilegible para la guía {_GUIA}" in caplog.text
    assert "destinatario@example.com" not in caplog.text


async def test_guia_desconocida_es_none() -> None:
    oca = _OcaFalsa(httpx.Response(200, content=_RESPUESTA_VACIA))

    assert await _gateway(oca).consultar_estado_actual(_GUIA) is None
