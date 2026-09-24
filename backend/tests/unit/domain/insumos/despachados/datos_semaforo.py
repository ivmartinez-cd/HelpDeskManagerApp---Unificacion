"""Datos de prueba de las reglas del semáforo de Despachados."""

from dataclasses import replace
from datetime import date

from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

LUNES_21_SEP = date(2026, 9, 21)
VIERNES_9_OCT = date(2026, 10, 9)
VIERNES_30_OCT = date(2026, 10, 30)
"""29 días hábiles después del 21/09: muy por encima de cualquier umbral de sin movimiento."""
FERIADO_12_OCT = frozenset({date(2026, 10, 12)})
EN_VIAJE = "En viaje a Centro de Distribución de Destino"
EN_ESPERA = "En Espera de Retiro por Sucursal"
OTRO_TEXTO = "texto de OCA"
"""Para los casos en que la regla mira solo `IdEstado`."""

VERDE = ClasificacionEnvio(
    color=ColorSemaforo.VERDE,
    alerta=False,
    abierto=True,
    fecha_limite=None,
    observacion="",
    estado_desconocido=False,
)
NARANJA = replace(VERDE, color=ColorSemaforo.NARANJA, alerta=True)
GRIS_ABIERTO = replace(VERDE, color=ColorSemaforo.GRIS)
GRIS_CERRADO = replace(VERDE, color=ColorSemaforo.GRIS, abierto=False)
CERRADO = replace(VERDE, color=ColorSemaforo.CERRADO, abierto=False)
AMARILLO = replace(VERDE, color=ColorSemaforo.AMARILLO)
ESTADO_NUEVO = replace(AMARILLO, observacion="Estado nuevo, revisar", estado_desconocido=True)
ROJO_LIMITE_25_SEP = replace(
    VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 25)
)
"""Rojo de un 45 con `FechaEstado` el lunes 21/09/2026."""
VERDES_DEL_CATALOGO = (1, 44, 34, 10, 2, 4, 35)
"""Escritos a mano, no importados de `semaforo`: así el test fija el catálogo."""


def estado_oca(id_estado: int | None, texto: str, motivo: str) -> EstadoOca:
    """Envío a domicilio con `FechaEstado` el lunes 21/09/2026."""
    return EstadoOca(
        numero_envio="3867500000000123456",
        operativa="434324",
        orden_retiro="",
        sucursal_actual="",
        fecha_estado=LUNES_21_SEP,
        estado=texto,
        id_estado=id_estado,
        motivo=motivo,
        cantidad_paquetes=1,
    )


def con_fecha(estado: EstadoOca, fecha_estado: date) -> EstadoOca:
    return replace(estado, fecha_estado=fecha_estado)


def contexto_en(hoy: date, feriados: frozenset[date] = frozenset()) -> ContextoClasificacion:
    return ContextoClasificacion(hoy=hoy, feriados=feriados)
