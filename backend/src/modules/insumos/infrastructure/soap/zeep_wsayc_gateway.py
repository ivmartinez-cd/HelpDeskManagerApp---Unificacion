"""Adapter zeep del puerto WsAycGateway (SOAP wsAyC de Canal Directo).

zeep es sincrónico (requests) — cada llamada corre en un thread (asyncio.to_thread) para
no bloquear el event loop. El transporte NO reintenta nunca: toda operación SOAP viaja
como POST, y reintentar persistNewSupply duplicaría pedidos reales (regla de negocio
dura del legacy, no un detalle de configuración). Timeout explícito obligatorio en toda
llamada (caracterización §8: una llamada sin timeout cuelga un thread para siempre).
"""

import asyncio
import json
import logging
import threading
from typing import Any

from zeep import Client
from zeep.transports import Transport

from src.modules.insumos.domain.value_objects.cd_supply import CdMachine, CdSupply
from src.modules.insumos.domain.value_objects.serial_number import clean_serial
from src.modules.insumos.infrastructure.soap import wsayc_parsing as parsing

logger = logging.getLogger(__name__)

WSDL_URL = "https://wsg.cdsisa.com.ar/wsAyC_server.php?wsdl"
REAL_ENDPOINT = "https://wsg.cdsisa.com.ar/wsAyC_server.php"
_TIMEOUT_SECONDS = 30


class ZeepWsAycGateway:
    """El cliente zeep se construye lazy y se cachea (cargar el WSDL es caro) — el lock
    evita construirlo dos veces si dos requests llegan a la vez al primer uso."""

    def __init__(self, wsdl_url: str = WSDL_URL, endpoint: str = REAL_ENDPOINT) -> None:
        self._wsdl_url = wsdl_url
        self._endpoint = endpoint
        self._client: Client | None = None
        self._client_lock = threading.Lock()

    def _service(self) -> Any:
        with self._client_lock:
            if self._client is None:
                transport = Transport(
                    timeout=_TIMEOUT_SECONDS, operation_timeout=_TIMEOUT_SECONDS
                )
                client = Client(self._wsdl_url, transport=transport)
                client.service._binding_options["address"] = self._endpoint
                self._client = client
            return self._client.service

    async def get_machine_by_serial(self, serial: str) -> CdMachine | None:
        # Sin try/except a propósito: el caller necesita distinguir "confirmado sin
        # asignar" (None) de "no se pudo consultar" (excepción) — ver el puerto.
        cleaned = clean_serial(serial)
        raw = await asyncio.to_thread(
            lambda: self._service().getMachineBySerial(SerialNumber=cleaned)
        )
        return parsing.parse_machine(raw)

    async def get_article_parts(self, familia_id: str) -> dict[str, str]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getArticleParts(IdFamilia=str(familia_id))
            )
            return parsing.parse_article_parts(raw)
        except Exception as exc:
            logger.warning("SOAP getArticleParts(%s) falló", familia_id, exc_info=exc)
            return {}

    async def persist_new_supply(self, payload: dict[str, object]) -> int:
        # Sin try/except y sin reintento: es la operación que crea el pedido real — la
        # excepción debe llegar cruda al caso de uso, que nunca la reintenta solo.
        datos = json.dumps(payload)
        raw = await asyncio.to_thread(lambda: self._service().persistNewSupply(Datos=datos))
        return parsing.parse_persist_response(raw)

    async def fetch_supply_by_id(self, supply_id: int) -> CdSupply | None:
        try:
            # Ojo: el parámetro del WSDL se llama `id` (no IdSupply) — pasarlo mal lanza
            # TypeError en zeep y el scan entero queda ciego en silencio.
            raw = await asyncio.to_thread(lambda: self._service().getSupplyById(id=str(supply_id)))
            return parsing.parse_supply_by_id(raw)
        except Exception as exc:
            # warning (no debug): una excepción acá es un problema real (WSDL, red), no
            # un "ID inexistente" — eso devuelve '[]' sin excepción.
            logger.warning("SOAP getSupplyById(%d) falló", supply_id, exc_info=exc)
            return None

    async def get_supply_description(self, supply_id: int) -> str:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getSupplyDetails(id=str(supply_id), top="30")
            )
            return parsing.parse_details_description(raw)
        except Exception as exc:
            logger.warning("SOAP getSupplyDetails(%s) falló", supply_id, exc_info=exc)
            return ""

    async def get_supplies_for_empresa(
        self, empresa_id: str, sucursal_id: str = "", top: str = "200"
    ) -> list[CdSupply]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getTopSupplies(
                    IdEmpresa=empresa_id,
                    IdSucursal=sucursal_id,
                    IdSector="",
                    OrderBy="",
                    Top=top,
                    IdEstado="",
                )
            )
            return parsing.parse_top_supplies(raw)
        except Exception as exc:
            logger.error("SOAP getTopSupplies(empresa=%s) falló", empresa_id, exc_info=exc)
            return []
