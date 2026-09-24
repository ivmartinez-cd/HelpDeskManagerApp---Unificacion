"""Textos `DetalleCalculo` / `EtiquetaNivel` de las ramas que usan regla de
tres (`EstimarEntreReales` y `RecalcularConPL` del legacy), carácter por
carácter — incluidos "Δ", "−" (U+2212) y "⚠"."""

from src.modules.contadores.domain.services.estimacion.formato_es_ar import (
    con_signo,
    entero,
    fecha_corta,
    hasta_dos_decimales,
)
from src.modules.contadores.domain.services.estimacion.redondeo import a_decimal
from src.modules.contadores.domain.services.estimacion.regla_de_tres import ReglaDeTres
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

_AVISO_INTERPOLACION = " · ⚠ lectura posterior a la fecha objetivo — interpolado hacia atrás"
_AVISO_T4 = " · ⚠ usa T4 (Informe S. Técnico) — confirmar"
_AJUSTADO_POR_RECESO = " · ajustado por receso"


def _tramo(r3: ReglaDeTres) -> str:
    calendario = f" (de {r3.dias_par_calendario}d cal.)" if r3.ajustado_por_receso else ""
    tasa = hasta_dos_decimales(r3.tasa_diaria)
    return f"Δ{r3.dias_par}d activos{calendario} · {tasa}/día · {con_signo(r3.dias_proyectados)}d"


def _receso(r3: ReglaDeTres) -> str:
    return f" · receso −{r3.dias_receso}d" if r3.ajustado_por_receso else ""


def _interpolacion(r3: ReglaDeTres) -> str:
    return _AVISO_INTERPOLACION if r3.dias_proyectados < 0 else ""


def detalle_entre_reales(r3: ReglaDeTres, incluye_t4: bool) -> str:
    t4 = _AVISO_T4 if incluye_t4 else ""
    llegada = entero(r3.llegada_proyectada)
    return (
        f"Entre dos reales · {_tramo(r3)} a fecha objetivo · "
        f"Llegada {llegada}{_receso(r3)}{t4}{_interpolacion(r3)}"
    )


def etiqueta_entre_reales(r3: ReglaDeTres, incluye_t4: bool) -> str:
    receso = _AJUSTADO_POR_RECESO if r3.ajustado_por_receso else ""
    t4 = " (incluye un T4)" if incluye_t4 else ""
    return f"Entre dos lecturas reales del propio equipo{receso}{t4}"


def _pareja(partida: LecturaRef, llegada: LecturaRef) -> str:
    p = f"P:{fecha_corta(partida.fecha)}={entero(a_decimal(partida.valor))}"
    return f"{p} · L:{fecha_corta(llegada.fecha)}={entero(a_decimal(llegada.valor))}"


def detalle_pl(partida: LecturaRef, llegada: LecturaRef, r3: ReglaDeTres) -> str:
    return (
        f"P/L manual · {_pareja(partida, llegada)} · {_tramo(r3)} hasta fecha objetivo"
        f"{_receso(r3)}{_interpolacion(r3)}"
    )


def etiqueta_pl(partida: LecturaRef, llegada: LecturaRef, r3: ReglaDeTres) -> str:
    receso = _AJUSTADO_POR_RECESO if r3.ajustado_por_receso else ""
    return f"Pareja P/L manual · {_pareja(partida, llegada)}{receso}"
