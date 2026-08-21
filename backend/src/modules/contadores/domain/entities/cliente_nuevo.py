"""Ficha de seguimiento de un cliente nuevo (onboarding de contadores).

Reemplaza el Excel que la TL de Contadores llena a mano cuando Comercial manda
el mail "Nuevo Negocio | <cliente>": la ficha guarda lo que trae ese mail
(cliente, contrato, firma, vendedor, fechas estimadas, equipos previstos) más
lo que la TL decide (operador, día de corte, estado del STC). Lo que sí sabe
Siges (equipos efectivamente instalados, contrato vigente, rubro) no se copia:
se consulta en vivo y se anota sobre la ficha (ver `ResumenSigesClienteNuevo`).
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from src.modules.contadores.domain.errors import (
    InvalidClienteNuevoError,
    InvalidEstadoClienteNuevoError,
)

# Ciclo de vida que sigue la TL: la ficha nace esperando que el PST instale;
# con equipos instalados hay que armar y mandar el STC (sistema de toma de
# contadores) al cliente; una vez enviado queda a la espera de la primera
# facturación, y ahí se cierra. El pase entre estados es manual — Siges solo
# sirve para avisar que "ya hay equipos instalados" (ver `listo_para_stc`).
ESTADO_ESPERANDO_INSTALACION = "ESPERANDO_INSTALACION"
ESTADO_STC_PENDIENTE = "STC_PENDIENTE"
ESTADO_STC_ENVIADO = "STC_ENVIADO"
ESTADO_CERRADO = "CERRADO"
ESTADOS_CLIENTE_NUEVO: tuple[str, ...] = (
    ESTADO_ESPERANDO_INSTALACION,
    ESTADO_STC_PENDIENTE,
    ESTADO_STC_ENVIADO,
    ESTADO_CERRADO,
)
ESTADOS_ABIERTOS: frozenset[str] = frozenset(
    {ESTADO_ESPERANDO_INSTALACION, ESTADO_STC_PENDIENTE, ESTADO_STC_ENVIADO}
)

MAX_CLIENTE = 200
MAX_NOTAS = 1000


@dataclass(slots=True, eq=False)
class ClienteNuevo:
    id: uuid.UUID
    cliente: str
    created_by_user_id: uuid.UUID
    siges_empresa_id: int | None = None
    contrato_nro: str | None = None
    fecha_firma: date | None = None
    vendedor: str | None = None
    # Username de Gestión (`contadores_operadores.id`); sin FK porque ese
    # catálogo se poda en cada sync — misma decisión que ADR-013.
    operador_id: str | None = None
    implementacion_servicio: str | None = None
    fecha_estimada_implementacion: date | None = None
    fecha_estimada_primera_facturacion: date | None = None
    # Día del mes de corte de contadores (1..31); None = "a definir".
    dia_corte: int | None = None
    equipos_previstos: int | None = None
    estado: str = ESTADO_ESPERANDO_INSTALACION
    stc_enviado_el: date | None = None
    notas: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        if not self.cliente.strip() or len(self.cliente) > MAX_CLIENTE:
            raise InvalidClienteNuevoError("El nombre del cliente es obligatorio (máx. 200).")
        if self.estado not in ESTADOS_CLIENTE_NUEVO:
            raise InvalidEstadoClienteNuevoError(self.estado)
        if self.dia_corte is not None and not 1 <= self.dia_corte <= 31:
            raise InvalidClienteNuevoError("El día de corte debe estar entre 1 y 31.")
        if self.equipos_previstos is not None and self.equipos_previstos < 0:
            raise InvalidClienteNuevoError("Los equipos previstos no pueden ser negativos.")
        if self.notas is not None and len(self.notas) > MAX_NOTAS:
            raise InvalidClienteNuevoError("Las notas superan el máximo (1000 caracteres).")

    @property
    def abierta(self) -> bool:
        return self.estado in ESTADOS_ABIERTOS

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClienteNuevo) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(frozen=True, slots=True)
class ResumenSigesClienteNuevo:
    """Lo que Siges sabe de una empresa, anotado sobre la ficha en lectura.
    `equipos_instalados` = máquinas con "Alta en Cliente" (`MaquinaUFisica`,
    motivo 1) en esa empresa — el registro de instalas real, no el incidente
    tipo 103 (ver SIGES_READONLY_CATALOGO_DATOS.md §3 "cliente nuevo")."""

    empresa_id: int
    equipos_instalados: int
    instalas: int
    primera_instalacion: date | None
    ultima_instalacion: date | None
    equipos_con_toma: int
    contrato_nro: str | None
    fecha_firma: date | None
    vendedor: str | None
    rubro: str


@dataclass(frozen=True, slots=True)
class CandidatoClienteNuevo:
    """Empresa de Siges con su primer contrato firmado hace poco y sin ficha
    todavía — sugerencia para que la TL la dé de alta con los datos ya
    cargados (sin tipear lo que viene en el mail de Comercial)."""

    empresa_id: int
    cliente: str
    contrato_nro: str | None
    fecha_firma: date | None
    vendedor: str | None
    rubro: str
    equipos_instalados: int


def listo_para_stc(ficha: ClienteNuevo, resumen: ResumenSigesClienteNuevo | None) -> bool:
    """Aviso, no transición: la ficha sigue esperando instalación pero Siges ya
    muestra equipos instalados (todos los previstos si se cargó la cantidad,
    o al menos uno si no). La TL decide cuándo pasarla a STC pendiente."""
    if resumen is None or ficha.estado != ESTADO_ESPERANDO_INSTALACION:
        return False
    if resumen.equipos_instalados <= 0:
        return False
    if ficha.equipos_previstos:
        return resumen.equipos_instalados >= ficha.equipos_previstos
    return True
