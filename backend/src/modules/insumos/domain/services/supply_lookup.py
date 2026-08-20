"""Lecturas de pedidos existentes en Canal Directo — port de la mitad de solo lectura
de SoapOrderClient (lookup_supplies_by_serial, find_order_by_reference,
fetch_supply_article_description)."""

import logging

from src.modules.insumos.domain.errors import ConsultaDePedidosNoDisponibleError
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_datetime import format_cd_datetime
from src.modules.insumos.domain.value_objects.cd_supply import ActiveSupplyView, CdSupply
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.domain.value_objects.serial_number import clean_serial
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

logger = logging.getLogger(__name__)

_CACHE_CANDIDATES_LIMIT = 20


class CanalDirectoSupplyLookup:
    def __init__(
        self,
        gateway: WsAycGateway,
        cache: SupplyCacheRepository,
        settings: CanalDirectoOrderSettings,
    ) -> None:
        self._gateway = gateway
        self._cache = cache
        self._settings = settings

    async def lookup_supplies_by_serial(
        self, device_serial: str, raise_on_error: bool = False
    ) -> list[ActiveSupplyView]:
        """Pedidos activos para una serie, combinando dos fuentes (ninguna sola alcanza):
        el cache local (sembrado al crear; sigue siendo necesario porque el gate
        anti-duplicados no llama a getTopSupplies en vivo, y porque cubre el remanente
        con origen Interno, que getTopSupplies sigue excluyendo) y getTopSupplies
        (pedidos con origen Proactivo de esta app y los cargados a mano en el portal).
        raise_on_error=True (autocarga) solo propaga si AMBAS fuentes fallan: con una
        alcanza para no arriesgar duplicado."""
        serial = clean_serial(device_serial)
        if not serial:
            return []
        results: dict[str, ActiveSupplyView] = {}
        local_failed = await self._collect_from_cache(serial, results)
        remote_failed = await self._collect_from_portal(serial, results)
        if local_failed and remote_failed and raise_on_error:
            raise ConsultaDePedidosNoDisponibleError(device_serial)
        return list(results.values())

    async def _collect_from_cache(
        self, serial: str, results: dict[str, ActiveSupplyView]
    ) -> bool:
        try:
            for row in await self._cache.get_by_serial(serial, limit=_CACHE_CANDIDATES_LIMIT):
                if row.estado in cd_state.INACTIVE_STATES:
                    continue
                nro = supply_id_full(row.supply_id)
                results[nro] = ActiveSupplyView(
                    nro=nro,
                    estado=row.estado,
                    fecha=format_cd_datetime(row.fecha),
                    serie=row.serial,
                    url=self._settings.supply_web_url(row.supply_id),
                )
            return False
        except Exception as exc:
            logger.error(
                "lookup_supplies_by_serial: cache local falló para serie %s",
                serial,
                exc_info=exc,
            )
            return True

    async def _collect_from_portal(
        self, serial: str, results: dict[str, ActiveSupplyView]
    ) -> bool:
        try:
            machine = await self._gateway.get_machine_by_serial(serial)
            if machine and machine.empresa_id:
                supplies = await self._gateway.get_supplies_for_empresa(
                    machine.empresa_id, machine.sucursal_id, top="100"
                )
                for supply in supplies:
                    self._add_portal_supply(results, serial, supply)
            return False
        except Exception as exc:
            logger.error(
                "lookup_supplies_by_serial: getTopSupplies falló para serie %s",
                serial,
                exc_info=exc,
            )
            return True

    def _add_portal_supply(
        self, results: dict[str, ActiveSupplyView], serial: str, supply: CdSupply
    ) -> None:
        # Fail-safe: una fila sin serie se incluye igual (mismo criterio que aplicaba el
        # portal) — mejor un falso bloqueo que un duplicado silencioso.
        row_serial = supply.nro_serie_solicitud.strip()
        if row_serial and not row_serial.upper().startswith(serial.upper()):
            return
        if supply.estado in cd_state.INACTIVE_STATES or not supply.supply_id:
            return
        nro = supply_id_full(supply.supply_id)
        results.setdefault(
            nro,
            ActiveSupplyView(
                nro=nro,
                estado=supply.estado,
                fecha=supply.fecha,
                serie=row_serial,
                url=self._settings.supply_web_url(supply.supply_id),
            ),
        )

    async def find_order_by_reference(self, device_serial: str, reference: str) -> CdSupply | None:
        """Reconciliación: busca entre los pedidos cacheados de la serie uno cuyo
        NroIncidenteCliente sea exactamente `reference` — para vincular un pedido que
        create_order reportó fallido pero que en realidad sí se creó. Nunca crea nada.
        Relee cada candidato fresco por SOAP: acá no alcanza una aproximación por
        SKU/descripción, hace falta certeza total antes de vincular."""
        serial = clean_serial(device_serial)
        if not serial:
            return None
        for row in await self._cache.get_by_serial(serial, limit=_CACHE_CANDIDATES_LIMIT):
            if row.estado in cd_state.INACTIVE_STATES:
                continue
            supply = await self._gateway.fetch_supply_by_id(row.supply_id)
            if supply is not None and supply.reference.strip() == reference:
                return supply
        return None

    async def fetch_supply_article_description(self, supply_id_ref: str) -> str:
        """Descripción del artículo pedido, vía el primer detalle del pedido. Nunca
        lanza — "" es "sin dato" (ver resolve_supply_match en el legacy)."""
        text = (supply_id_ref or "").strip()
        if not text:
            return ""
        try:
            supply_id = int(text.split("-")[0])
        except ValueError:
            return ""
        return await self._gateway.get_supply_description(supply_id)
