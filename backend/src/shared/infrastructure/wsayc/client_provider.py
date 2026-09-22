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

Autenticación (sep-2026, ver `auth.py`): cada operación viaja con
`Authorization: Bearer <token>`. Ante un fault `AuthenticationError` (token
vencido) se re-loguea y se repite la operación UNA vez — no contradice la regla
de arriba: el servidor rechaza el request antes de ejecutar nada, así que ni
`persistNewSupply` se duplica (mismo criterio que el legacy). Un fault
`AuthorizationError` (la ACL de CDS no habilita el método) se traduce a
`ExternalPermissionDeniedError`, con el método puntual en el log.
"""

import logging
import threading
from functools import lru_cache
from typing import Any

from zeep import Client
from zeep.exceptions import Fault
from zeep.transports import Transport
from zeep.wsdl import Document

from src.shared.domain.errors import ExternalPermissionDeniedError
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.wsayc.auth import WsAycTokenManager

logger = logging.getLogger(__name__)


class _AuthenticatedService:
    """Imita al ServiceProxy de zeep (`service().getX(...)`), pero cada operación
    pasa por `WsAycClientProvider.call` con token y re-login."""

    def __init__(self, provider: "WsAycClientProvider") -> None:
        self._provider = provider

    def __getattr__(self, operation: str) -> Any:
        def invoke(**kwargs: Any) -> Any:
            return self._provider.call(operation, **kwargs)

        return invoke


def _fault_code_has(exc: Fault, marker: str) -> bool:
    return marker in str(exc.code or "")


class WsAycClientProvider:
    def __init__(
        self,
        wsdl_url: str,
        endpoint: str,
        timeout_seconds: float,
        credentials: tuple[str, str] = ("", ""),
    ) -> None:
        self._wsdl_url = wsdl_url
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._document: Document | None = None
        self._lock = threading.Lock()
        username, password = credentials
        self._tokens = WsAycTokenManager(username, password, self._login)

    def service(self) -> Any:
        """Proxy de operaciones autenticadas. Cada operación usa un Transport/
        Session propio sobre el Document compartido — nunca guardar el resultado
        de una operación de zeep como estado compartido."""
        return _AuthenticatedService(self)

    def call(self, operation: str, **kwargs: Any) -> Any:
        token = self._tokens.current()
        try:
            return getattr(self._raw_service(token), operation)(**kwargs)
        except Fault as exc:
            if _fault_code_has(exc, "AuthorizationError"):
                logger.warning(
                    "wsAyC: la ACL de CDS no habilita %s para el usuario de servicios web",
                    operation,
                    extra={"wsayc_operation": operation},
                )
                raise ExternalPermissionDeniedError(
                    ExternalPermissionDeniedError.user_message
                ) from exc
            if not _fault_code_has(exc, "AuthenticationError"):
                raise
            logger.info("wsAyC: token rechazado en %s (%s), re-logueando", operation, exc.message)
        return getattr(self._raw_service(self._tokens.renew(token)), operation)(**kwargs)

    def _login(self, username: str, password: str) -> object:
        return self._raw_service(None).login(username=username, password=password)

    def _raw_service(self, token: str | None) -> Any:
        transport = self._new_transport()
        if token is not None:
            transport.session.headers["Authorization"] = f"Bearer {token}"
        client = Client(self._get_document(), transport=transport)
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
        (settings.wsayc_username, settings.wsayc_password.get_secret_value()),
    )
