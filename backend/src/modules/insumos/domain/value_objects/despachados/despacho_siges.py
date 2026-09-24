"""Remito de insumos despachado por OCA, tal como lo registra SiGes.

Fuente: `dbo.Remito_Cab` (tipo 'I', guía de 19 dígitos), unido a
`Incidente_Insumo_D`/`Incidente_Insumo_C` por `ID_Remito` para saber qué pedidos
de insumos viajan en el remito. Un remito puede llevar varios incidentes y, en
casos aislados, una misma guía aparece en más de un remito.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class IncidenteInsumo:
    """Pedido de insumos que viaja en el remito (`Incidente_Insumo_C`)."""

    numero: str
    """`NroIncidente` — el número con el que se conoce el pedido (ej. "446207")."""
    numero_cliente: str
    """`Nro_Incidente_Cliente` — referencia propia del cliente; "" si no tiene."""


@dataclass(frozen=True, slots=True)
class DespachoSiges:
    id_remito: int
    numero_remito: int
    guia: str
    """Número de envío OCA: exactamente 19 dígitos."""
    id_distribucion: int
    """`Distribucion.Id`: 3 OCA, 9 OCA SP, 10 OCA Prioritario."""
    fecha_remito: date
    bultos: int
    cliente: str
    """`Empresa.Den_Comercial` del cliente del remito."""
    sucursal_cliente: str
    """`Sucursal.Descripcion` de destino; "" si el remito no la tiene."""
    entrega_a: str
    """`Remito_Cab.Entrega_a` — a quién se entrega."""
    incidentes: tuple[IncidenteInsumo, ...]
