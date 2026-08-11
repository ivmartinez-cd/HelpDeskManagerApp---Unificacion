"""Config de negocio para crear pedidos en Canal Directo (origen, motivo, contactos
globales de fallback) — los valores vienen de las env vars CD_* vía presentation."""

from dataclasses import dataclass

from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

# 3 = Interno: el objetivo entero de usar el SOAP en vez del portal es poder forzar este
# origen (el form HTML siempre dejaba Web). Los pedidos con este origen son invisibles
# para getTopSupplies/portal — de ahí el scan incremental y el cache local.
ORIGEN_INTERNO = "3"


@dataclass(frozen=True)
class CanalDirectoOrderSettings:
    solicitante: ContactInfo
    destinatario: ContactInfo
    origen_id: str = ORIGEN_INTERNO
    motivo_id: str = "1"
    # Base del portal web (CD_BASE_URL) — solo para armar URLs de vista de pedidos.
    portal_base_url: str = "https://webagentes.canaldirecto.com.ar"

    def supply_web_url(self, supply_id: int) -> str:
        return f"{self.portal_base_url}/supplies/view/{supply_id_full(supply_id)}"
