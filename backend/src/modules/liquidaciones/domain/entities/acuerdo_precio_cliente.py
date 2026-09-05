"""Acuerdo de precio por cliente — acuerdos_precio_cliente.

Un prestador puede tener, para un cliente puntual, un precio distinto al de su
tarifario: SALTA cobra el doble a las mineras (Minera del Altiplano, Sal de
Vida, Sales de Jujuy — "Costo doble aprobado por AO"), un monto fijo a Refinor y
el precio viejo a YAGUAR. Hasta 2026-09 eso era una ALT001 por incidente que la
TL resolvía a mano cada mes con el mismo motivo (32 alertas con la misma
justificación). El acuerdo guarda esa decisión una sola vez: el motor toma el
precio acordado como el esperado (`precio_esperado`) y solo alerta si el
prestador cobra algo distinto a lo acordado.

`tipo_servicio=None` aplica a todos los tipos; uno específico gana sobre el
general. Exactamente uno de `factor` (multiplicador del tarifario, ej. 2.0) o
`precio_fijo` (monto acordado) tiene que estar cargado — lo valida el caso de
uso. El match por cliente es por `empresa_nombre` normalizado (sin acentos,
minúsculas), igual que el par empresa+sucursal de Tabla KM."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class AcuerdoPrecioCliente:
    id: uuid.UUID
    prestador_id: uuid.UUID
    empresa_nombre: str
    tipo_servicio: str | None
    factor: float | None
    precio_fijo: float | None
    motivo: str
    vigencia_desde: date
    vigencia_hasta: date | None
    created_at: datetime

    def precio_esperado(self, precio_tarifario: float | None) -> float | None:
        """Monto fijo si lo hay; si no, el tarifario por el factor. `None` cuando
        el acuerdo es por factor y no hay tarifario contra el cual aplicarlo."""
        if self.precio_fijo is not None:
            return self.precio_fijo
        if precio_tarifario is None or self.factor is None:
            return None
        return round(precio_tarifario * self.factor, 2)
