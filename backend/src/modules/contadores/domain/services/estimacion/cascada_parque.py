from dataclasses import dataclass
from decimal import Decimal

from src.modules.contadores.domain.services.estimacion.redondeo import a_decimal, redondear
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque

MUESTRA_MINIMA_MEDIANA_TRUNCADA = 5  # MetodoUsado del legacy: N>=5 usa P80


@dataclass(frozen=True, slots=True)
class NivelParque:
    """El `EstimacionDecision` que arma `BuildParqueDecision` del legacy."""

    fuente: FuenteEstimacion
    promedio: PromedioParque
    etiqueta: str

    @property
    def impresiones(self) -> Decimal:
        """`Math.Round(prom, 0)`, antes de escalar por recesos."""
        return redondear(a_decimal(self.promedio.valor))

    @property
    def es_mediana_truncada(self) -> bool:
        return self.promedio.n_equipos >= MUESTRA_MINIMA_MEDIANA_TRUNCADA

    @property
    def etiqueta_metodo(self) -> str:
        """`EtiquetaMetodo` del legacy."""
        n = self.promedio.n_equipos
        if self.es_mediana_truncada:
            return f"Mediana truncada P80 · {n} equipos ({self.promedio.n_descartados} descartados)"
        return f"Mediana cruda · {n} equipos (muestra chica, sin truncar)"


def resolver_cascada_parque(entrada: EstimacionInput) -> NivelParque | None:
    """`ResolverCascada` del legacy: primer nivel con promedio mayor a 0, en
    el orden cliente+modelo, grupo+modelo, cliente+tecnología, global+modelo.
    La muestra mínima (N>=2) ya la aplica la consulta, que deja el promedio
    en NULL con N<=1."""
    for fuente, promedio, etiqueta in _niveles(entrada):
        if promedio is not None and promedio.valor > 0:
            return NivelParque(fuente, promedio, etiqueta)
    return None


def _niveles(
    entrada: EstimacionInput,
) -> list[tuple[FuenteEstimacion, PromedioParque | None, str]]:
    tecnologia = "Mono" if entrada.tecnologia == "MONO" else "Color"
    return [
        ("Parque_Cliente_Modelo", entrada.parque_cliente_modelo,
         "Parque del cliente · mismo modelo"),
        ("Parque_Grupo_Modelo", entrada.parque_grupo_modelo,
         "Parque del grupo económico · mismo modelo"),
        ("Parque_Cliente_Tec", entrada.parque_cliente_tecnologia,
         f"Parque del cliente · misma tecnología ({tecnologia})"),
        ("Parque_Global_Modelo", entrada.parque_global_modelo,
         "Parque global · mismo modelo"),
    ]
