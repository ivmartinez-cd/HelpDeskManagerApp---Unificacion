"""Puerto de dominio para el servicio SOAP wsAyC de Canal Directo.

La implementación concreta vive en infrastructure/soap/zeep_wsayc_gateway.py. Los
contratos de manejo de error POR MÉTODO replican al legacy (soap_query.py) — no son
uniformes a propósito: cada caller necesita una semántica distinta.
"""

from typing import Protocol

from src.modules.insumos.domain.value_objects.cd_supply import CdIncident, CdMachine, CdSupply


class WsAycGateway(Protocol):
    async def get_machine_by_serial(self, serial: str) -> CdMachine | None:
        """None = el servicio devolvió "[]" (equipo sin asignar, candidato a bodega).

        A diferencia del resto, acá la excepción de red/WSDL SÍ se propaga: el caller
        necesita distinguir "confirmado sin asignar" de "no se pudo consultar".
        El adapter limpia el serial (clean_serial) antes de consultar: el match de CD
        es exacto y un punto/espacio de más da un falso "sin asignar".
        """
        ...

    async def get_machine_incidents(self, machine_id: str, top: int = 3) -> list[CdIncident]:
        """Últimos ST técnicos del equipo, abiertos y cerrados, más reciente primero
        (getMachineIncidents sin filtro de estado/tipo).

        [] si no hay incidentes o hay un error (se loguea allá) — lo consume el
        diagnóstico de la ventana de validación 0%, que es best-effort por diseño.
        """
        ...

    async def get_article_parts(self, familia_id: str) -> dict[str, str]:
        """Insumos disponibles para una familia, normalizado a {id: nombre}.

        Dict vacío si la familia no tiene insumos o hay un error (se loguea allá).
        """
        ...

    async def persist_new_supply(self, payload: dict[str, object]) -> int:
        """Crea el pedido real. Devuelve el ID informado, o 0 si el servicio no confirmó.

        NUNCA se reintenta (ni acá ni en el transporte): reintentar la creación
        arriesga un pedido duplicado real. El ID "exitoso" no garantiza que la fila
        exista (el INSERT...SELECT del servidor no valida la serie) — el caller DEBE
        verificar releyendo con fetch_supply_by_id.
        """
        ...

    async def persist_new_incident(self, payload: dict[str, object]) -> int:
        """Crea el incidente real (Correctivo, tipo 101 — persistNewIncident no admite
        Pre-Correctivo, ver ADR/investigación de la migración). Devuelve el ID
        informado, o 0 si el servicio no confirmó.

        NUNCA se reintenta (mismo motivo que persist_new_supply): reintentar arriesga
        un incidente duplicado real. El caller DEBE verificar releyendo con
        fetch_incident_by_id.
        """
        ...

    async def fetch_supply_by_id(self, supply_id: int) -> CdSupply | None:
        """None si el ID no existe ("[]") o si hubo un error (se loguea allá).

        Única forma de ver pedidos de origen Interno (getTopSupplies los excluye).
        """
        ...

    async def fetch_incident_by_id(self, incident_id: int) -> CdSupply | None:
        """Como fetch_supply_by_id pero para incidentes de ST (kits de mantenimiento) —
        None si no existe o hay error (se loguea allá)."""
        ...

    async def get_supply_description(self, supply_id: int) -> str:
        """Descripción real del consumible (campo "Insumo" del primer Detail).

        "" si el pedido no tiene ítems o hay un error — los callers tratan "" como
        "sin dato" (ver resolve_supply_match en el legacy).
        """
        ...

    async def get_supplies_for_empresa(
        self, empresa_id: str, sucursal_id: str = "", top: str = "200"
    ) -> list[CdSupply]:
        """Supplies visibles en getTopSupplies (excluye origen Interno). [] ante error."""
        ...

    async def void_supply(self, supply_id: int) -> bool:
        """Anula (cancela) un supply. El servicio SIEMPRE responde "true" sin importar
        el payload —no distingue "anulado" de "ID inexistente ignorado"—, así que True
        solo confirma que la llamada SOAP no falló. El caller DEBE reconsultar con
        fetch_supply_by_id y verificar que el estado cambió a Anulado/Cancelado."""
        ...

    async def void_incident(self, incident_id: int) -> bool:
        """Como void_supply pero para incidentes de ST (kits de mantenimiento) —
        misma trampa: True no garantiza la anulación, reconsultar siempre."""
        ...
