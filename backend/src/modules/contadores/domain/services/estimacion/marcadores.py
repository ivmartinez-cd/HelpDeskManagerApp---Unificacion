from dataclasses import dataclass

from src.modules.contadores.domain.services.estimacion.coloreo import resolver_coloreo
from src.modules.contadores.domain.services.estimacion.salto_imposible import (
    PerfilEquipo,
    hay_salto_imposible,
)
from src.modules.contadores.domain.services.estimacion.semaforo import (
    SenalesSemaforo,
    resolver_semaforo,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    Coloreo,
    Semaforo,
)


@dataclass(frozen=True, slots=True)
class Marcadores:
    borde_salto_imposible: bool
    coloreo: Coloreo | None
    semaforo: Semaforo


@dataclass(frozen=True, slots=True)
class SenalesRama:
    """Lo que cada rama de la cascada sabe de sí misma al pedir sus
    marcadores — todo lo que no sale directo de `EstimacionInput`
    (ARCHITECTURE_GUIDE.md §4: agrupado en vez de parámetros sueltos)."""

    excluir_coloreo: bool = False
    es_cascada_parque: bool = False
    pendiente: bool = False
    t4_sin_revisar: bool = False
    requiere_confirmacion_otro_motivo: bool = False


def evaluar_marcadores(
    entrada: EstimacionInput, impresiones: float | None, senales: SenalesRama
) -> Marcadores:
    """Reúne salto imposible + coloreo + semáforo (REGLAS_DE_NEGOCIO §7) —
    compartido por todas las ramas de la cascada de decisión para no
    reevaluar el orden del semáforo en cada una."""
    dias_periodo = (entrada.periodo_hasta - entrada.periodo_desde).days
    perfil = PerfilEquipo(entrada.tecnologia, entrada.velocidad_ppm)
    salto = (
        hay_salto_imposible(impresiones, dias_periodo, perfil) if impresiones is not None else False
    )
    coloreo = None
    if not senales.excluir_coloreo:
        coloreo = resolver_coloreo(impresiones, entrada.prom_6_facturados)
    semaforo = resolver_semaforo(_senales_semaforo(salto, coloreo, senales))
    return Marcadores(salto, coloreo, semaforo)


def _senales_semaforo(
    salto: bool, coloreo: Coloreo | None, senales: SenalesRama
) -> SenalesSemaforo:
    return SenalesSemaforo(
        ya_real=False,
        salto_imposible=salto,
        es_cascada_parque=senales.es_cascada_parque,
        pendiente=senales.pendiente,
        t4_sin_revisar=senales.t4_sin_revisar,
        requiere_confirmacion_otro_motivo=senales.requiere_confirmacion_otro_motivo,
        coloreo_activo=coloreo in ("AZUL", "NARANJA"),
    )
