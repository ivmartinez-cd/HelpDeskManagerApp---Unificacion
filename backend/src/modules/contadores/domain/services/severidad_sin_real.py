"""Clasificación de severidad por meses sin contador real.

Única fuente de verdad de los umbrales de alerta del análisis de equipos sin
contador real — la UI solo mapea cada nivel a un color, no re-decide cortes.
Umbrales pensados para el laburo mes a mes de recuperación de reales: hasta
2 meses es el ciclo normal de gestión, 3-5 ya es un atraso a trabajar, 6-11
es un estimado con margen de error serio, y >= 12 es un equipo cuya
facturación hace un año que no pisa la realidad."""

from typing import Literal

SeveridadSinReal = Literal["critico", "alto", "medio", "bajo"]

_UMBRAL_CRITICO = 12
_UMBRAL_ALTO = 6
_UMBRAL_MEDIO = 3


def severidad_por_meses(meses_sin_real: int) -> SeveridadSinReal:
    if meses_sin_real >= _UMBRAL_CRITICO:
        return "critico"
    if meses_sin_real >= _UMBRAL_ALTO:
        return "alto"
    if meses_sin_real >= _UMBRAL_MEDIO:
        return "medio"
    return "bajo"
