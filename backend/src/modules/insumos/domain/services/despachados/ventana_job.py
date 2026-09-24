"""Ventana horaria del job programado de Despachados (por defecto, de lunes a sábado de 8 a
20 en hora Argentina). "Actualizar ahora" no la mira: corre cuando lo pide un operador."""

from dataclasses import dataclass
from datetime import datetime

_DIAS_DE_LA_SEMANA = range(7)
_HORAS_DEL_DIA = 24


@dataclass(frozen=True, slots=True)
class VentanaJob:
    dias_semana: frozenset[int]
    """Días en que corre: 0 = lunes … 6 = domingo (como `date.weekday()`)."""
    hora_inicio: int
    """Primera hora incluida (0 a 23)."""
    hora_fin: int
    """Primera hora excluida (1 a 24): de 8 a 20 corre hasta las 19:59."""

    def __post_init__(self) -> None:
        if not 0 <= self.hora_inicio < self.hora_fin <= _HORAS_DEL_DIA:
            raise ValueError(
                "La ventana del job tiene que cumplir 0 <= inicio < fin <= 24 "
                f"(llegó de {self.hora_inicio} a {self.hora_fin})"
            )
        if not self.dias_semana:
            raise ValueError("La ventana del job necesita al menos un día de la semana")
        fuera = sorted(dia for dia in self.dias_semana if dia not in _DIAS_DE_LA_SEMANA)
        if fuera:
            raise ValueError(f"Días de la semana fuera de 0 (lunes) a 6 (domingo): {fuera}")


def dentro_de_ventana(momento: datetime, ventana: VentanaJob) -> bool:
    """True si `momento` (ya en hora Argentina) cae en un día y una hora de la ventana."""
    en_horario = ventana.hora_inicio <= momento.hour < ventana.hora_fin
    return en_horario and momento.weekday() in ventana.dias_semana
