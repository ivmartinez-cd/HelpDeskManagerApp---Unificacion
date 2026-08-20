"""Vistas de dominio de lo que devuelve el wsAyC — la infraestructura mapea los dicts
crudos del SOAP (claves "NroIncidenteCliente", "Familia", etc.) a estos tipos."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CdMachine:
    """Ubicación/estado del equipo según getMachineBySerial."""

    familia_id: str
    familia_name: str = ""
    empresa_id: str = ""
    empresa_name: str = ""   # razón social — clasificación de offline usa este, no empresa_id
    sucursal_id: str = ""
    sucursal_name: str = ""  # nombre de sucursal para el detalle de offline
    machine_id: str = ""  # id interno de CD — clave para getMachineIncidents
    estado: str = ""  # Estado del equipo en Canal Directo (para detalle de offline)


@dataclass(frozen=True)
class CdIncident:
    """Un ST técnico visto por getMachineIncidents — evidencia informativa del
    diagnóstico de la ventana de validación 0% (nunca decide nada por sí solo).

    Las fechas quedan en el formato crudo de CD ("DD/MM/YYYY HH:MM:SS", ya en hora
    Argentina) — se parsean con parse_cd_datetime donde se consumen."""

    numero: str  # NroIncidente (o id si no viene)
    estado: str = ""
    fecha: str = ""
    fecha_cierre: str = ""
    tecnico: str = ""  # Tecnico, o VisitaA como fallback
    motivo: str = ""


@dataclass(frozen=True)
class CdSupply:
    """Un supply visto por getSupplyById/getTopSupplies.

    `fecha` queda en el formato crudo de CD ("DD/MM/YYYY[ HH:MM:SS]", ya en hora
    Argentina) — se parsea recién al persistir en cache (ver parse_cd_datetime).
    Los campos de contacto solo vienen poblados en getSupplyById (el prefill de
    contactos del último pedido de la sucursal los usa).
    """

    supply_id: int
    reference: str = ""  # NroIncidenteCliente — la clave de idempotencia
    estado: str = ""
    fecha: str = ""
    empresa_id: str = ""
    nro_serie_solicitud: str = ""
    nro_serie: str = ""
    sku: str = ""  # NroArticulo
    descripcion: str = ""
    sucursal: str = ""  # "Sucursal" — se usa como nombre de zona en import-from-supply
    sector: str = ""   # "Sector" — se copia a sol_sector/dest_sector
    solicitante_nombre: str = ""  # "Solicitante" (nombre completo, sin separar apellido)
    solicitante_telefono: str = ""
    solicitante_email: str = ""
    destinatario_nombre: str = ""  # "EntregaA"
    destinatario_telefono: str = ""
    destinatario_email: str = ""


@dataclass(frozen=True)
class CachedSupply:
    """Entrada de supply_serial_cache. Cubre el remanente de pedidos con origen Interno
    (getTopSupplies y el portal los excluyen) y, sembrada al crear (_seed_cache), los
    pedidos nuevos con origen Proactivo — el gate anti-duplicados en creación solo
    consulta esta tabla, no llama a getTopSupplies en vivo."""

    supply_id: int
    serial: str
    estado: str = ""
    empresa_id: str = ""
    fecha: datetime | None = None
    sku: str = ""
    description: str = ""


@dataclass(frozen=True)
class SupplyStatusEvent:
    """Un estado del pedido en CD y cuándo la app lo detectó por primera vez.

    No es el momento exacto de la transición real en CD (no lo expone) — es "cuándo
    lo notamos", con la granularidad del poller y de las visitas a la UI (tabla
    supply_status_history)."""

    estado: str
    first_seen_at: datetime


@dataclass(frozen=True)
class ActiveSupplyView:
    """Pedido activo tal como lo consumen los bloqueos anti-duplicado y el frontend."""

    nro: str  # "{supply_id}-{check digit}"
    estado: str
    fecha: str
    serie: str
    url: str
