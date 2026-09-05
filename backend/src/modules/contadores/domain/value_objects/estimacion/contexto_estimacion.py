from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente


@dataclass(frozen=True, slots=True)
class ContextoEstimacion:
    """`EstimacionInput` + los recesos ya filtrados por alcance (anexo/grupo
    económico, REGLAS_DE_NEGOCIO §6) — viajan juntos por toda la cascada de
    decisión, así que se agrupan en un solo objeto en vez de pasarse sueltos
    (ARCHITECTURE_GUIDE.md §4: máximo 3 parámetros por función)."""

    entrada: EstimacionInput
    recesos: list[RecesoCliente]
