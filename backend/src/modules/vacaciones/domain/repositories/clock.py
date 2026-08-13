from datetime import date
from typing import Protocol


class Clock(Protocol):
    """Fecha actual inyectable (D11 del plan): el módulo trabaja con DATE y
    todas las comparaciones "hoy vs fecha" pasan por acá — testeable y sin
    off-by-one de timezone."""

    def hoy(self) -> date: ...
