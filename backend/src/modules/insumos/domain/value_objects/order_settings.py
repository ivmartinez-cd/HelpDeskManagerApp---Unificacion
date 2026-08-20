"""Config de negocio para crear pedidos en Canal Directo (origen, motivo, contactos
globales de fallback) — los valores vienen de las env vars CD_* vía presentation."""

from dataclasses import dataclass

from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

# 6 = Proactivo: origen dado de alta en Canal Directo (2026-08) exclusivo para esta app.
# El objetivo entero de usar el SOAP en vez del portal es poder forzar un origen propio
# (el form HTML siempre dejaba Web). Antes se usaba 3 = Interno, pero getTopSupplies lo
# excluye explícitamente (WHERE ... AND i.ID_Origen <> 3) — los pedidos quedaban
# invisibles en AyC y en el listado del portal. Proactivo sí atraviesa ese filtro.
# El cache local (supply_serial_cache) sigue siendo necesario igual: el gate
# anti-duplicados en creación (find_active_supply_by_serial / supply_lookup.py) solo
# consulta el cache, no llama a getTopSupplies en vivo — sin el seed inmediato al crear
# quedaría la misma ventana de duplicado que existía con origen 3.
ORIGEN_PROACTIVO = "6"


@dataclass(frozen=True)
class CanalDirectoOrderSettings:
    solicitante: ContactInfo
    destinatario: ContactInfo
    origen_id: str = ORIGEN_PROACTIVO
    motivo_id: str = "1"
    # Base del portal web (CD_BASE_URL) — solo para armar URLs de vista de pedidos.
    portal_base_url: str = "https://webagentes.canaldirecto.com.ar"

    def supply_web_url(self, supply_id: int) -> str:
        return f"{self.portal_base_url}/supplies/view/{supply_id_full(supply_id)}"
