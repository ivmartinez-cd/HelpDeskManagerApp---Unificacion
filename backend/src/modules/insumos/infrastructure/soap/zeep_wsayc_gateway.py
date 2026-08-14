"""Adapter zeep del puerto WsAycGateway (SOAP wsAyC de Canal Directo).

zeep es sincrónico (requests) — cada llamada corre en un thread (asyncio.to_thread) para
no bloquear el event loop. El cliente sale del provider compartido (ADR-018): WSDL
parseado una vez por proceso, Session propia por llamada, transporte sin reintentos
(reintentar persistNewSupply duplicaría pedidos reales) y timeout explícito — ver
`shared/infrastructure/wsayc/client_provider.py`. Acá quedan las operaciones, el parsing
y el manejo de errores por método, que son negocio de insumos.
"""

import asyncio
import json
import logging
from typing import Any

from src.modules.insumos.domain.value_objects.cd_supply import CdIncident, CdMachine, CdSupply
from src.modules.insumos.domain.value_objects.serial_number import clean_serial
from src.modules.insumos.infrastructure.soap import wsayc_parsing as parsing
from src.shared.infrastructure.wsayc.client_provider import (
    WsAycClientProvider,
    get_wsayc_client_provider,
)

logger = logging.getLogger(__name__)


class ZeepWsAycGateway:
    def __init__(self, provider: WsAycClientProvider | None = None) -> None:
        self._provider = provider or get_wsayc_client_provider()

    def _service(self) -> Any:
        return self._provider.service()

    async def get_machine_by_serial(self, serial: str) -> CdMachine | None:
        # Sin try/except a propósito: el caller necesita distinguir "confirmado sin
        # asignar" (None) de "no se pudo consultar" (excepción) — ver el puerto.
        cleaned = clean_serial(serial)
        raw = await asyncio.to_thread(
            lambda: self._service().getMachineBySerial(SerialNumber=cleaned)
        )
        return parsing.parse_machine(raw)

    async def get_machine_incidents(self, machine_id: str, top: int = 3) -> list[CdIncident]:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getMachineIncidents(
                    IdMaquina=machine_id,
                    IdEmpresa="",
                    IdSucursal="",
                    IdSector="",
                    top=str(top),
                    estado="",
                    tipo="",
                )
            )
            return parsing.parse_incidents(raw)
        except Exception as exc:
            logger.warning("SOAP getMachineIncidents(maquina=%s) falló", machine_id, exc_info=exc)
            return []

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

    async def persist_new_incident(self, payload: dict[str, object]) -> int:
        # Sin try/except y sin reintento, mismo motivo que persist_new_supply: es la
        # operación que crea el incidente real.
        datos = json.dumps(payload)
        raw = await asyncio.to_thread(lambda: self._service().persistNewIncident(Datos=datos))
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

    async def fetch_incident_by_id(self, incident_id: int) -> CdSupply | None:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().getIncidentById(id=str(incident_id))
            )
            return parsing.parse_incident_by_id(raw)
        except Exception as exc:
            logger.warning("SOAP getIncidentById(%d) falló", incident_id, exc_info=exc)
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

    async def void_supply(self, supply_id: int) -> bool:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().voidSupply(
                    Datos=json.dumps({"Supply": {"id": str(supply_id)}})
                )
            )
            return str(raw).strip().lower() == "true"
        except Exception as exc:
            logger.error("SOAP voidSupply(%d) falló", supply_id, exc_info=exc)
            return False

    async def void_incident(self, incident_id: int) -> bool:
        try:
            raw = await asyncio.to_thread(
                lambda: self._service().voidIncident(
                    Datos=json.dumps({"Incident": {"id": str(incident_id)}})
                )
            )
            return str(raw).strip().lower() == "true"
        except Exception as exc:
            logger.error("SOAP voidIncident(%d) falló", incident_id, exc_info=exc)
            return False

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
