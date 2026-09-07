"""ALT011 — Doble Facturación: el costo de servicio cobrado es exactamente el
doble del esperado (tarifario o acuerdo por cliente), en cualquier tipo de
servicio. Caso propio, separado de ALT001, porque es la forma en que los
prestadores cobran dos tareas en un incidente (instalación + desinstalación,
dos equipos, segunda visita) y la TL necesita verlo como tal para decidir si
corresponde o si es doble facturación (pedido de Iván, 2026-09-07: 385 ALT001
pendientes con cobrado = 2 × tarifario, San Juan resolvía el caso cargando la
tarifa de instalación al doble). Cuando esta regla está activa, ALT001 no
dispara para el mismo incidente (ver `motor.py`)."""

from src.modules.liquidaciones.domain.entities.acuerdo_precio_cliente import (
    AcuerdoPrecioCliente,
)
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.services.motor_reglas.alt001_precio import (
    TOLERANCIA_PRECIO,
    precio_esperado,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo

MULTIPLO_DOBLE = 2


def es_doble_facturacion(
    incidente: Incidente,
    tarifario: Tarifario | None,
    acuerdo: AcuerdoPrecioCliente | None = None,
) -> bool:
    if incidente.fecha_cierre is None:
        return False
    esperado = precio_esperado(tarifario, acuerdo)
    if not esperado:
        return False
    cobrado = incidente.costo_servicio_cobrado or 0
    return abs(cobrado - MULTIPLO_DOBLE * esperado) <= TOLERANCIA_PRECIO


def evaluar_alt011(
    incidente: Incidente,
    tarifario: Tarifario | None,
    acuerdo: AcuerdoPrecioCliente | None = None,
) -> list[Hallazgo]:
    if not es_doble_facturacion(incidente, tarifario, acuerdo):
        return []
    esperado = precio_esperado(tarifario, acuerdo) or 0.0
    cobrado = incidente.costo_servicio_cobrado or 0
    contexto = {
        "cobrado": cobrado,
        "esperado": esperado,
        "diferencia": round(cobrado - esperado, 2),
        "multiplo": MULTIPLO_DOBLE,
        "tipo_servicio": incidente.tipo,
    }
    return [Hallazgo(_descripcion(cobrado, esperado, incidente.tipo), contexto)]


def _descripcion(cobrado: float, esperado: float, tipo: str) -> str:
    return (
        f"Cobró el doble del tarifario: ${cobrado:,.2f} = 2 × ${esperado:,.2f} "
        f"({tipo}). Verificar si son dos tareas reales "
        f"(instalación + desinstalación, dos equipos) o doble facturación"
    )
