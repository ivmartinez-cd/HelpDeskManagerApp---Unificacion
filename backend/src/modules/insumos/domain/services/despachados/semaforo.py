"""Reglas del semáforo de Despachados: del último estado de OCA a color, alerta y cierre.

El catálogo de `IdEstado` sale del relevamiento de OCA; lo que no está en él no se adivina:
queda en amarillo (naranja si trae motivo) con "Estado nuevo, revisar" y
`estado_desconocido`, para que quien llama lo loguee y alguien lo sume al catálogo. Los
textos de OCA llegan con tildes, mayúsculas y espacios variables, así que toda comparación
de texto se hace normalizada.
"""

import unicodedata
from dataclasses import replace
from datetime import date

from src.modules.insumos.domain.services.despachados.dias_habiles import (
    dias_habiles_transcurridos,
    fecha_limite_retiro,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
    ContextoClasificacion,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca

ESTADOS_VERDES = frozenset({1, 44, 34, 10, 2, 4})
"""Verdes con "Sin Motivo"; con cualquier otro motivo pasan a naranja (regla general)."""
ESTADOS_VERDES_SOLO_SIN_MOTIVO = frozenset({35})
"""El relevamiento anota el 35 aparte ("verde solo sin motivo"), pero la regla del motivo es
la misma que para `ESTADOS_VERDES`: se separa solo para que se lea igual que el relevamiento."""
ESTADOS_NARANJA = frozenset({48})
"""Naranja aunque venga con "Sin Motivo" (visita reprogramada)."""
ESTADOS_ROJOS = frozenset({45})
"""En espera de retiro por sucursal: corre el plazo antes de la devolución."""
ESTADOS_GRIS_CERRADO = frozenset({13})
ESTADOS_GRIS_ABIERTO = frozenset({49})
ESTADOS_CERRADOS = frozenset({8, 56})
ESTADOS_ACUSE_SIN_ID = frozenset(
    {"Acuse en Rendicion", "Envio a Rendir a Otra Suc", "Rendicion de Acuse Finalizado"}
)
"""Estados de acuse: OCA los informa sin `IdEstado`, se reconocen por el texto."""
ESTADOS_CONOCIDOS = (
    ESTADOS_VERDES
    | ESTADOS_VERDES_SOLO_SIN_MOTIVO
    | ESTADOS_NARANJA
    | ESTADOS_ROJOS
    | ESTADOS_GRIS_CERRADO
    | ESTADOS_GRIS_ABIERTO
    | ESTADOS_CERRADOS
)
"""Solo `IdEstado` numéricos: los acuses se reconocen por texto. Para saber si un estado es
desconocido usar `ClasificacionEnvio.estado_desconocido`, no esta constante."""
DIAS_LIMITE_RETIRO = 5
SIN_MOTIVO = "Sin Motivo"

OBSERVACION_ESTADO_NUEVO = "Estado nuevo, revisar"
OBSERVACION_SIN_DATOS = "Sin datos en OCA"
OBSERVACION_ESPERANDO_INGRESO = "Esperando ingreso en OCA"

_VERDE = ClasificacionEnvio(
    color=ColorSemaforo.VERDE,
    alerta=False,
    abierto=True,
    fecha_limite=None,
    observacion="",
    estado_desconocido=False,
)
_AMARILLO = replace(_VERDE, color=ColorSemaforo.AMARILLO)
_NARANJA = replace(_VERDE, color=ColorSemaforo.NARANJA, alerta=True)
_GRIS_ABIERTO = replace(_VERDE, color=ColorSemaforo.GRIS)
_GRIS_CERRADO = replace(_VERDE, color=ColorSemaforo.GRIS, abierto=False)
_CERRADO = replace(_VERDE, color=ColorSemaforo.CERRADO, abierto=False)


def normalizar_texto(texto: str) -> str:
    """Sin tildes, en minúsculas (`casefold`) y con los espacios recortados y colapsados."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_tildes.casefold().split())


_ACUSES_NORMALIZADOS = frozenset(normalizar_texto(t) for t in ESTADOS_ACUSE_SIN_ID)
_SIN_MOTIVO_NORMALIZADO = normalizar_texto(SIN_MOTIVO)


def clasificar_estado(estado: EstadoOca, contexto: ContextoClasificacion) -> ClasificacionEnvio:
    """Color del semáforo según esta precedencia: cerrado (8, 56, acuses) > gris cerrado
    (13) > rojo (45) > naranja (48 o con motivo) > gris abierto (49) > estado nuevo
    (amarillo) > verde, o amarillo si lleva `dias_sin_movimiento` hábiles sin cambios.
    """
    if _es_cerrado(estado):
        return _CERRADO
    if estado.id_estado in ESTADOS_GRIS_CERRADO:
        return _GRIS_CERRADO
    if estado.id_estado in ESTADOS_ROJOS:
        limite = fecha_limite_retiro(estado.fecha_estado, contexto.feriados, DIAS_LIMITE_RETIRO)
        return replace(_VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=limite)
    if estado.id_estado not in ESTADOS_CONOCIDOS:
        return _estado_nuevo(estado)
    if estado.id_estado in ESTADOS_NARANJA or _tiene_motivo(estado):
        return _NARANJA
    if estado.id_estado in ESTADOS_GRIS_ABIERTO:
        return _GRIS_ABIERTO
    return _verde_o_sin_movimiento(estado.fecha_estado, contexto)


def clasificar_sin_datos(fecha_remito: date, contexto: ContextoClasificacion) -> ClasificacionEnvio:
    """Guía que OCA todavía no registra: verde durante los primeros `dias_sin_movimiento`
    días hábiles desde el remito (tarda en ingresar), después amarillo."""
    dias = dias_habiles_transcurridos(fecha_remito, contexto.hoy, contexto.feriados)
    if dias >= contexto.dias_sin_movimiento:
        return replace(_AMARILLO, observacion=OBSERVACION_SIN_DATOS)
    return replace(_VERDE, observacion=OBSERVACION_ESPERANDO_INGRESO)


def _es_cerrado(estado: EstadoOca) -> bool:
    """Entregado/cerrado por `IdEstado`, o acuse (llega sin `IdEstado`) por texto."""
    if estado.id_estado is None:
        return normalizar_texto(estado.estado) in _ACUSES_NORMALIZADOS
    return estado.id_estado in ESTADOS_CERRADOS


def _tiene_motivo(estado: EstadoOca) -> bool:
    """True si el motivo dice algo distinto de "Sin Motivo" (vacío cuenta como sin motivo)."""
    motivo = normalizar_texto(estado.motivo)
    return motivo not in ("", _SIN_MOTIVO_NORMALIZADO)


def _estado_nuevo(estado: EstadoOca) -> ClasificacionEnvio:
    """Estado fuera del catálogo: naranja si trae motivo (la visita falló igual), si no
    amarillo; en los dos casos marcado para revisar y loguear."""
    base = _NARANJA if _tiene_motivo(estado) else _AMARILLO
    return replace(base, observacion=OBSERVACION_ESTADO_NUEVO, estado_desconocido=True)


def _verde_o_sin_movimiento(
    fecha_estado: date, contexto: ContextoClasificacion
) -> ClasificacionEnvio:
    """Verde, salvo que `FechaEstado` lleve `dias_sin_movimiento` días hábiles sin cambiar."""
    dias = dias_habiles_transcurridos(fecha_estado, contexto.hoy, contexto.feriados)
    if dias < contexto.dias_sin_movimiento:
        return _VERDE
    unidad = "día hábil" if dias == 1 else "días hábiles"
    return replace(_AMARILLO, observacion=f"Sin movimiento hace {dias} {unidad}")
