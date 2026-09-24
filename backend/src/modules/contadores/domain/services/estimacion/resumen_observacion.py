"""Columna OBSERVACION del CSV de SiGes — `ResumenObservacion` del Estimador de
Contadores v1.7, dentro del límite de `Contadores.observaciones` (varchar(200)
= 200 bytes; el archivo va en cp1252, 1 byte por caracter).

Tres capas: factorización (Mono y Color por el mismo método se escriben una
vez con "M+C:"), vocabulario corto y degradación por prioridad. Orden de
conservación (lo último es lo primero que se suelta): observación manual del
operador (con reserva garantizada de `RESERVA_MANUAL`), método + marcas,
impresiones, `#IdLog`, estadísticos, contexto. Funciones puras."""

from dataclasses import dataclass

from src.modules.contadores.domain.services.estimacion.observacion_estadisticos import (
    contexto,
    estadisticos,
    impresiones,
)
from src.modules.contadores.domain.services.estimacion.observacion_etiquetas import (
    mismo_metodo,
    texto_metodo,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

MAX_OBSERVACION = 200
RESERVA_MANUAL = 100
_SEP = " | "
# `char.IsWhiteSpace` de .NET (lo que saca `Trim()`); `str.strip()` de Python
# además saca U+001C..U+001F.
_BLANCOS_NET = (
    "\t\n\v\f\r \u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
)


@dataclass(frozen=True, slots=True)
class ClaseObservada:
    """Una fila (clase) de la máquina tal como la lee el resumen: el
    `EquipoGrilla` efectivo del legacy (con la decisión del operador)."""

    resultado: EstimacionResultado
    meses_sin_real: int | None = None

    @property
    def estimada(self) -> bool:
        """`Estim_Propuesto` y `Decision` presentes: método "NoAplica" es
        una fila sin `EstimacionDecision` (lectura real o pendiente)."""
        r = self.resultado
        return r.estim_propuesto is not None and r.metodo != "NoAplica"


def armar_resumen_observacion(
    cl10: ClaseObservada | None,
    cl20: ClaseObservada | None,
    observacion_manual: str | None = None,
    id_log: str | None = None,
) -> str:
    """`ResumenObservacion.Construir`: manual | detalle | #IdLog."""
    manual = _como_utf16((observacion_manual or "").strip(_BLANCOS_NET))
    log = f"#{id_log}" if id_log else ""
    costo_manual = 0 if not manual else min(len(manual), RESERVA_MANUAL) + len(_SEP)
    costo_log = 0 if not log else len(log) + len(_SEP)
    detalle = _detalle(cl10, cl20, max(MAX_OBSERVACION - costo_manual - costo_log, 0))
    # Lo que el detalle no usó vuelve al operador.
    cupo_manual = MAX_OBSERVACION - (len(detalle) + len(_SEP) if detalle else 0) - costo_log
    partes = [recortar(manual, max(cupo_manual, 0)), detalle, log]
    return _SEP.join(p for p in partes if p)


@dataclass(frozen=True, slots=True)
class _Niveles:
    metodo: str
    impresiones: str
    estadisticos: str
    contexto: str


def _detalle(cl10: ClaseObservada | None, cl20: ClaseObservada | None, cupo: int) -> str:
    """Método e impresiones garantizados (el método se recorta contra lo que
    dejan las impresiones); estadísticos y contexto entran si hay lugar, y uno
    que no entra no bloquea al siguiente."""
    if cupo <= 0:
        return ""
    niveles = _niveles(cl10, cl20)
    if niveles is None:
        return ""
    reserva = len(niveles.impresiones) + len(_SEP) if niveles.impresiones else 0
    texto = recortar(niveles.metodo, cupo - reserva)
    if not texto:
        return recortar(niveles.metodo, cupo)
    for nivel in (niveles.impresiones, niveles.estadisticos, niveles.contexto):
        if nivel and len(texto) + len(nivel) + len(_SEP) <= cupo:
            texto += _SEP + nivel
    return texto


def _niveles(cl10: ClaseObservada | None, cl20: ClaseObservada | None) -> _Niveles | None:
    mono = cl10 if cl10 is not None and cl10.estimada else None
    color = cl20 if cl20 is not None and cl20.estimada else None
    if mono is None and color is None:
        return None
    ambas = mono is not None and color is not None
    principal = mono if mono is not None else color
    assert principal is not None
    return _Niveles(
        metodo=_nivel_metodo(mono, color, discrimina=cl10 is not None and cl20 is not None),
        impresiones=impresiones(_r(mono), _r(color), ambas),
        estadisticos=estadisticos(principal.resultado),
        contexto=_nivel_contexto(principal, color if ambas else None),
    )


def _nivel_metodo(
    mono: ClaseObservada | None, color: ClaseObservada | None, discrimina: bool
) -> str:
    if mono is not None and color is not None:
        if mismo_metodo(mono.resultado, color.resultado):
            return "M+C:" + texto_metodo(mono.resultado)
        return f"M:{texto_metodo(mono.resultado)} / C:{texto_metodo(color.resultado)}"
    # Una sola clase ESTIMADA: si la máquina discrimina (la otra ya es real),
    # el prefijo dice a qué columna del CSV se refiere el texto.
    una = mono if mono is not None else color
    assert una is not None
    prefijo = "" if not discrimina else ("M:" if mono is not None else "C:")
    return prefijo + texto_metodo(una.resultado)


def _nivel_contexto(principal: ClaseObservada, color: ClaseObservada | None) -> str:
    """Si el Mono salió de historia propia y el Color del parque, el "sin real
    Nm" está del lado del Color."""
    texto = contexto(principal.resultado.fuente, principal.meses_sin_real)
    if not texto and color is not None:
        texto = contexto(color.resultado.fuente, color.meses_sin_real)
    return texto


def _r(clase: ClaseObservada | None) -> EstimacionResultado | None:
    return clase.resultado if clase is not None else None


def _como_utf16(texto: str) -> str:
    """El legacy mide y corta en unidades UTF-16: un caracter fuera del plano
    básico (un emoji) ocupa 2 y sale como "??" en cp1252. Se lo reemplaza por
    dos caracteres que también salen como "?" para que el presupuesto de 200
    y el recorte coincidan."""
    return "".join("\ufffd\ufffd" if ord(c) > 0xFFFF else c for c in texto)


def recortar(texto: str, maximo: int) -> str:
    """Corta con "..." (o en seco si el cupo es de 3 o menos)."""
    if maximo <= 0:
        return ""
    if len(texto) <= maximo:
        return texto
    return texto[:maximo] if maximo <= 3 else texto[: maximo - 3] + "..."
