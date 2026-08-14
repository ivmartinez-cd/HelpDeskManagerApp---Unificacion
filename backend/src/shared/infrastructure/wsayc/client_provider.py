"""Fuente única del cliente zeep de wsAyC para toda la app (ADR-018).

El documento WSDL se descarga y parsea UNA vez por proceso — es la parte cara
(~0,2 s medidos) y su parseo tampoco tiene contrato de thread-safety, así que
la construcción va protegida por lock (mismo patrón de construcción protegida
que tenían los gateways). Cada llamada recibe después un `Client` liviano con
`Transport`/`requests.Session` PROPIOS sobre ese Document compartido:
`requests.Session` no está documentado como thread-safe y su `send()` muta el
cookie jar compartido en cada respuesta (`sessions.py:799`, requests 2.34.2);
con Session por llamada, el poller de insumos y los requests de usuarios no
comparten estado mutable. Costo medido: igual que el singleton (mediana
0,998 s vs 1,024 s — domina la latencia del servidor). Delta consciente,
documentado en ADR-018: se pierde la continuidad de cookies entre llamadas
que el singleton de insumos tenía de rebote; wsAyC no la necesita
(liquidaciones ya operaba con cliente fresco por request en producción).

El transporte NO reintenta nunca: toda operación SOAP viaja como POST, y
reintentar `persistNewSupply` duplicaría pedidos reales (regla de negocio
dura del legacy, no un detalle de configuración). Timeout explícito
obligatorio en toda llamada (caracterización §8: una llamada sin timeout
cuelga un thread para siempre).
"""

import threading
from functools import lru_cache
from typing import Any

from zeep import Client
from zeep.transports import Transport
from zeep.wsdl import Document

from src.shared.infrastructure.config.settings import get_settings


class WsAycClientProvider:
    def __init__(self, wsdl_url: str, endpoint: str, timeout_seconds: float) -> None:
        self._wsdl_url = wsdl_url
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._document: Document | None = None
        self._lock = threading.Lock()

    def service(self) -> Any:
        """ServiceProxy con Transport/Session propios sobre el Document
        compartido — pensado para una llamada (o una tanda secuencial dentro
        del mismo thread), nunca para guardarse como estado compartido."""
        client = Client(self._get_document(), transport=self._new_transport())
        client.service._binding_options["address"] = self._endpoint
        return client.service

    def _new_transport(self) -> Transport:
        # Sin retries a propósito (ver docstring del módulo); ambos timeouts:
        # `timeout` cubre cargas de WSDL/XSD, `operation_timeout` los POST.
        return Transport(
            timeout=self._timeout_seconds, operation_timeout=self._timeout_seconds
        )

    def _get_document(self) -> Document:
        with self._lock:
            if self._document is None:
                document = Document(self._wsdl_url, self._new_transport())
                # Resolver bindings una vez acá adentro (Client + service es lo
                # que los materializa lazy) para que ningún par de llamadas
                # concurrentes los resuelva a la vez fuera del lock.
                warm = Client(document, transport=self._new_transport())
                warm.service._binding_options["address"] = self._endpoint
                self._document = document
            return self._document


@lru_cache
def get_wsayc_client_provider() -> WsAycClientProvider:
    settings = get_settings()
    return WsAycClientProvider(
        settings.wsayc_wsdl_url,
        settings.wsayc_endpoint,
        settings.wsayc_timeout_seconds,
    )
