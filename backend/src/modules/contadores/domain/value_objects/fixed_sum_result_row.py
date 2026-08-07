from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FixedSumResultRow:
    """Formato de salida ANGOSTO (no CLASE_10/CLASE_20 como el resto de las
    herramientas) — así lo hace la app vieja para Suma Fija."""

    serie: str
    estado: str
    contador_actual: int
    fecha: str
    tipo: str
    clase: str
    contador: int | str
