from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionManualDto:
    """El resultado que el operador vio y confirmó explícitamente al aceptar
    (P/L manual o "forzar método") — distinto del cálculo automático del
    motor. Cuando está presente, el tablero y el export usan estos valores
    tal cual en vez de volver a correr `estimar()` para ese equipo/clase."""

    contador_propuesto: float | None
    tipo_toma: int | None
    fuente: str
    metodo_detalle: str


@dataclass(frozen=True, slots=True)
class DecisionOperadorDto:
    pendiente: bool = False
    nota: str | None = None
    manual: DecisionManualDto | None = None
