from dataclasses import dataclass


@dataclass(slots=True)
class Operador:
    """Operador de facturación de Gestión (catálogo scrapeado de
    /planificacion/ver). `color` es una aproximación: el background_color
    más frecuente entre sus eventos sincronizados, no un dato de identidad
    real de Gestión."""

    id: str
    nombre: str
    color: str | None = None
