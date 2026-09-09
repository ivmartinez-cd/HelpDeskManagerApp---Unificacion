from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoxplotParqueDto:
    """Distribución del parque de referencia usado en la estimación —
    solo para el gráfico del panel de candidatos (detectar outliers). `q1`/
    `q3` llegan `None` cuando el nivel de parque resuelto no trae criterio
    IQR (solo Cliente+Tecnología lo calcula hoy, ver `PromedioParque`); el
    frontend arma los bigotes de Tukey y decide qué mostrar. `valor_equipo`
    es la propuesta automática del motor para este equipo (paridad con
    `Equipo.Impresiones` de `PanelCandidatos.razor`), no el valor del parque."""

    n_equipos: int
    q1: float | None
    mediana: float
    q3: float | None
    valor_equipo: float | None
