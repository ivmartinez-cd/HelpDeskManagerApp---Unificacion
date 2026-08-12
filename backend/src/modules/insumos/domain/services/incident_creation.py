"""Creación de incidentes de kit de mantenimiento vía el SOAP wsAyC — persistNewIncident.

Investigación de la migración (2026-08-12, ver INTEGRACION_APPS_PLAN.md/memoria del
proyecto): el scraping legacy del portal CakePHP (Ingreso='precorrectivo') NUNCA creó
un incidente Pre-Correctivo real — los dos incidentes de kit reales en producción
(842671, 840018) quedaron registrados como tipo 101 Correctivo al releerlos por SOAP,
porque persistNewIncident (y aparentemente el propio handler del portal) hardcodean
ese tipo para cualquier Ingreso != 'guardia'. persistNewIncident da el mismo resultado
real con mucha menos fragilidad — decisión explícita del usuario de usarlo en vez de
portar el scraping.

Mucho más simple que CanalDirectoOrderCreation (order_creation.py): no hay máquina,
familia ni insumo que resolver, ni supply_cache que sembrar (eso es específico de
pedidos de insumo, no de incidentes)."""

import logging
from collections.abc import Sequence

from src.modules.insumos.domain.errors import IncidenteNoConfirmadoError, IncidenteNoVerificadoError
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.services.verify_with_retries import (
    DEFAULT_RETRY_DELAYS_SECONDS,
    verify_with_retries,
)
from src.modules.insumos.domain.value_objects.incident_request import IncidentRequest
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings

logger = logging.getLogger(__name__)

# Cualquier valor != "guardia" (y no vacío) hace que persistNewIncident cree tipo 101
# Correctivo — "guardia" activa la rama de incidente derivado de guardia, que no aplica
# acá. No es "precorrectivo": ese valor no tiene significado especial en el WS (ver
# docstring del módulo).
_INGRESO_APP = "app"


class CanalDirectoIncidentCreation:
    def __init__(
        self,
        gateway: WsAycGateway,
        settings: CanalDirectoOrderSettings,
        verify_delays: Sequence[float] = DEFAULT_RETRY_DELAYS_SECONDS,
    ) -> None:
        self._gateway = gateway
        self._settings = settings
        self._verify_delays = verify_delays

    async def create_incident(self, request: IncidentRequest) -> str:
        """Crea el incidente y devuelve su ID (string plano, sin check digit —
        persistNewIncident no usa EAN-13 como persistNewSupply)."""
        solicitante = request.solicitante or self._settings.solicitante
        destinatario = request.destinatario or self._settings.destinatario
        payload = _build_payload(request, solicitante, destinatario, self._settings)

        # Nunca se reintenta automáticamente: es la operación que crea el incidente real.
        new_id = await self._gateway.persist_new_incident(payload)
        if not new_id:
            raise IncidenteNoConfirmadoError(request.device_serial)

        await self._verify_created(new_id, request)
        return str(new_id)

    async def _verify_created(self, new_id: int, request: IncidentRequest) -> None:
        """Verificación post-creación obligatoria, con reintentos cortos ante lag de
        lectura — mismo patrón que _verify_created de CanalDirectoOrderCreation. Si no
        verifica, NO se marca procesado (el caller no llama mark_processed)."""
        verified = False

        async def check() -> bool:
            nonlocal verified
            incident = await self._gateway.fetch_incident_by_id(new_id)
            if incident is not None and incident.reference.strip() == request.reference:
                verified = True
                return True
            return False

        if not await verify_with_retries(check, self._verify_delays) or not verified:
            raise IncidenteNoVerificadoError(new_id, request.device_serial)


def _build_payload(
    request: IncidentRequest,
    solicitante: ContactInfo,
    destinatario: ContactInfo,
    settings: CanalDirectoOrderSettings,
) -> dict[str, object]:
    """Campos leídos por wsAyC_server.php::persistNewIncident (líneas 1451-1528) desde
    $item['Incident']. origen_id acá SÍ alcanza con que vaya anidado (a diferencia de
    persistNewSupply, este handler solo lee $incident['origen_id'], no la raíz)."""
    return {
        "Incident": {
            "NroSerie": request.device_serial,
            "Ingreso": _INGRESO_APP,
            "Falla": request.falla,
            "NroIncidenteCliente": request.reference,
            "origen_id": request.origen_id or settings.origen_id,
            "NombreSolicitante": solicitante.nombre,
            "ApellidoSolicitante": solicitante.apellido,
            "TelefonoSolicitante": solicitante.telefono,
            "EmailSolicitante": solicitante.email,
            "SectorSolicitante": solicitante.sector,
            "NombreDestinatario": destinatario.nombre,
            "ApellidoDestinatario": destinatario.apellido,
            "TelefonoDestinatario": destinatario.telefono,
            "EmailDestinatario": destinatario.email,
            "SectorDestinatario": destinatario.sector,
        }
    }
