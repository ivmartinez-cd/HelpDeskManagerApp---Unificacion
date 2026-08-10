"""Creación de pedidos de insumos vía el SOAP wsAyC — port de SoapOrderClient.create_order.

La pieza más delicada del módulo (caracterización §3): la clave de idempotencia viaja en
NroIncidenteCliente, persistNewSupply devuelve un ID "exitoso" aunque no haya insertado
fila (MAX+1 sin validar la serie), y la verificación post-creación con reintentos es
obligatoria, no defensiva. La serialización check-then-act contra duplicados NO vive acá:
el caso de uso envuelve esto en ClaimedOrderCreation.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from src.modules.insumos.domain.errors import (
    DatosDeContactoIncompletosError,
    PedidoNoConfirmadoError,
    PedidoNoVerificadoError,
    SerieNoActivaEnCanalDirectoError,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.services.insumo_matching import InsumoQuery, select_insumo_id
from src.modules.insumos.domain.services.verify_with_retries import (
    DEFAULT_RETRY_DELAYS_SECONDS,
    verify_with_retries,
)
from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdMachine, CdSupply
from src.modules.insumos.domain.value_objects.order_request import ContactInfo, OrderRequest
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _ResolvedContact:
    nombre: str
    apellido: str
    telefono: str
    email: str
    sector: str


class CanalDirectoOrderCreation:
    def __init__(
        self,
        gateway: WsAycGateway,
        cache: SupplyCacheRepository,
        settings: CanalDirectoOrderSettings,
        verify_delays: Sequence[float] = DEFAULT_RETRY_DELAYS_SECONDS,
    ) -> None:
        self._gateway = gateway
        self._cache = cache
        self._settings = settings
        self._verify_delays = verify_delays

    async def create_order(self, order: OrderRequest) -> str:
        """Crea el pedido y devuelve su ID visible ("{id}-{check digit}")."""
        machine = await self._resolve_machine(order)
        insumo_id = await self._select_insumo(order, machine)
        solicitante, destinatario = await self._resolve_order_contacts(order, machine)
        _validate_contacts(solicitante, destinatario)
        payload = _build_payload(
            order, machine, insumo_id, solicitante, destinatario, self._settings
        )

        # Nunca se reintenta automáticamente: es la operación que crea el pedido real.
        new_id = await self._gateway.persist_new_supply(payload)
        if not new_id:
            raise PedidoNoConfirmadoError(order.device_serial)

        verified = await self._verify_created(new_id, order)
        await self._seed_cache(new_id, order, machine, verified)
        return supply_id_full(new_id)

    async def _resolve_machine(self, order: OrderRequest) -> CdMachine:
        machine = await self._gateway.get_machine_by_serial(order.device_serial)
        if machine is None or not machine.familia_id:
            raise SerieNoActivaEnCanalDirectoError(order.device_serial)
        return machine

    async def _select_insumo(self, order: OrderRequest, machine: CdMachine) -> str:
        options = await self._gateway.get_article_parts(machine.familia_id)
        line = order.lines[0]
        query = InsumoQuery(
            familia_name=machine.familia_name,
            device_serial=order.device_serial,
            requested_sku=line.sku,
            description=line.description,
            override_insumo_id=order.override_insumo_id,
        )
        return select_insumo_id(options, query)

    async def _resolve_order_contacts(
        self, order: OrderRequest, machine: CdMachine
    ) -> tuple[_ResolvedContact, _ResolvedContact]:
        prefill_sol, prefill_dest = await self._last_order_contacts(machine)
        solicitante = _resolve_contact(order.solicitante, prefill_sol, self._settings.solicitante)
        destinatario = _resolve_contact(
            order.destinatario, prefill_dest, self._settings.destinatario
        )
        return solicitante, destinatario

    async def _last_order_contacts(self, machine: CdMachine) -> tuple[ContactInfo, ContactInfo]:
        """Mejor esfuerzo: contacto del pedido más reciente de la sucursal, como
        aproximación al pre-fill del portal (el SOAP no tiene ese concepto). Nunca
        lanza — ante cualquier problema devuelve vacío y la resolución cae al config."""
        empty = ContactInfo()
        if not machine.empresa_id:
            return empty, empty
        try:
            recent = await self._gateway.get_supplies_for_empresa(
                machine.empresa_id, machine.sucursal_id, top="5"
            )
            if not recent:
                return empty, empty
            full = await self._gateway.fetch_supply_by_id(recent[0].supply_id)
            return _prefill_contacts(full) if full else (empty, empty)
        except Exception as exc:
            logger.warning(
                "No se pudo obtener contacto de referencia para empresa=%s sucursal=%s",
                machine.empresa_id,
                machine.sucursal_id,
                exc_info=exc,
            )
            return empty, empty

    async def _verify_created(self, new_id: int, order: OrderRequest) -> CdSupply:
        """Verificación post-creación obligatoria, con reintentos cortos ante lag de
        lectura (caso real 443017/SDS-974325: la primera lectura no vio el pedido
        recién creado). Si no verifica, NO se marca procesado — el próximo ciclo puede
        reintentar sin riesgo (ver reconcile para el caso "en realidad sí se creó")."""
        found: CdSupply | None = None

        async def check() -> bool:
            nonlocal found
            supply = await self._gateway.fetch_supply_by_id(new_id)
            if supply is not None and supply.reference.strip() == order.reference:
                found = supply
                return True
            return False

        if not await verify_with_retries(check, self._verify_delays) or found is None:
            raise PedidoNoVerificadoError(new_id, order.device_serial)
        return found

    async def _seed_cache(
        self, new_id: int, order: OrderRequest, machine: CdMachine, verified: CdSupply
    ) -> None:
        """Sembrar supply_serial_cache ahora, no esperar al próximo ciclo del scan: los
        pedidos con origen Interno no aparecen en getTopSupplies/portal, así que esta
        tabla es la única fuente que ve este pedido para el anti-duplicados."""
        line = order.lines[0]
        description = await self._gateway.get_supply_description(new_id)
        entry = CachedSupply(
            supply_id=new_id,
            serial=order.device_serial,
            estado=cd_state.PENDIENTE,
            empresa_id=machine.empresa_id,
            fecha=parse_cd_datetime(verified.fecha),
            sku=line.sku,
            description=description or line.description,
        )
        await self._cache.upsert([entry])


def _resolve_contact(
    zona: ContactInfo | None, prefill: ContactInfo, cfg: ContactInfo
) -> _ResolvedContact:
    """Prioridad zona (customer_zone_contacts) → último pedido de la sucursal → config.

    persistNewSupply concatena Nombre + ' ' + Apellido de todos modos, así que cuando se
    cae a la capa del prefill SOAP —que solo tiene el nombre completo, sin separar
    apellido— se manda todo en `nombre` y `apellido` vacío: da el mismo resultado final.
    """
    if zona and (zona.apellido or zona.nombre):
        nombre, apellido = zona.nombre, zona.apellido
    elif prefill.nombre:
        nombre, apellido = prefill.nombre, ""
    else:
        nombre, apellido = cfg.nombre, cfg.apellido
    telefono = (zona.telefono if zona else "") or prefill.telefono or cfg.telefono
    email = (zona.email if zona else "") or prefill.email or cfg.email
    # El SOAP no expone sector (getSupplyById no lo trae pese a que sí se guarda al
    # crear) — no hay capa intermedia posible para este campo.
    sector = (zona.sector if zona else "") or cfg.sector
    return _ResolvedContact(nombre, apellido, telefono, email, sector)


def _prefill_contacts(full: CdSupply) -> tuple[ContactInfo, ContactInfo]:
    solicitante = ContactInfo(
        nombre=full.solicitante_nombre,
        telefono=full.solicitante_telefono,
        email=full.solicitante_email,
    )
    destinatario = ContactInfo(
        nombre=full.destinatario_nombre,
        telefono=full.destinatario_telefono,
        email=full.destinatario_email,
    )
    return solicitante, destinatario


def _validate_contacts(solicitante: _ResolvedContact, destinatario: _ResolvedContact) -> None:
    missing = []
    if not solicitante.nombre and not solicitante.apellido:
        missing.append("solicitante_nombre/apellido")
    if not solicitante.telefono:
        missing.append("solicitante_telefono")
    if not solicitante.email:
        missing.append("solicitante_email")
    if not destinatario.nombre and not destinatario.apellido:
        missing.append("destinatario_nombre/apellido")
    if not destinatario.telefono:
        missing.append("destinatario_telefono")
    if not destinatario.email:
        missing.append("destinatario_email")
    if missing:
        raise DatosDeContactoIncompletosError(missing)


def _supply_section(
    order: OrderRequest,
    solicitante: _ResolvedContact,
    destinatario: _ResolvedContact,
    settings: CanalDirectoOrderSettings,
) -> dict[str, object]:
    revision = "1" if order.revision else "0"
    return {
        "NombreSolicitante": solicitante.nombre,
        "ApellidoSolicitante": solicitante.apellido,
        "TelefonoSolicitante": solicitante.telefono,
        "EmailSolicitante": solicitante.email,
        "SectorSolicitante": solicitante.sector,
        "NombreDestinatario": destinatario.nombre,
        "ApellidoDestinatario": destinatario.apellido,
        "TelefonoDestinatario": destinatario.telefono,
        "EmailDestinatario": destinatario.email,
        "EmailDestinatario2": "",
        "EmailDestinatario3": "",
        "SectorDestinatario": destinatario.sector,
        "NroIncidenteCliente": order.reference,
        "CartuchosADevolver": "0",
        "NroSerie": order.device_serial,
        "Detalle": order.detalle or "",
        "Revision": revision,
        "revision": revision,
        "origen_id": settings.origen_id,
    }


def _build_payload(
    order: OrderRequest,
    machine: CdMachine,
    insumo_id: str,
    solicitante: _ResolvedContact,
    destinatario: _ResolvedContact,
    settings: CanalDirectoOrderSettings,
) -> dict[str, object]:
    """`origen_id` va TAMBIÉN en la RAÍZ del payload, no solo anidado en Supply — bug
    real corregido en el legacy: wsAyC_server.php lee $supply['origen_id']; anidado
    solo, todo pedido terminaba con origen Web en vez de Interno. Regla dura del
    CLAUDE.md legacy, no volver a romperla."""
    line = order.lines[0]
    revision = "1" if order.revision else "0"
    return {
        "Supply": _supply_section(order, solicitante, destinatario, settings),
        "Detail": [
            {
                "familia_id": machine.familia_id,
                "insumo_id": insumo_id,
                "cantidad": str(line.quantity),
                "motivo_id": settings.motivo_id,
            }
        ],
        "origen_id": settings.origen_id,
        "Revision": revision,
        "revision": revision,
    }
