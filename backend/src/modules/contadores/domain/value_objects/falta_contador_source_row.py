from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FaltaContadorSourceRow:
    """Una fila del CSV de origen (export de SIGES) antes de filtrar por
    `Tipo` y armar el formato ancho de Estimación en 0."""

    tipo: str
    serie: str
    contador: int
    nombre_clase: str | None
