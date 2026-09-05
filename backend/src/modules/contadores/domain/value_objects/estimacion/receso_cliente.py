from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RecesoCliente:
    """Período sin uso declarado para un cliente (REGLAS_DE_NEGOCIO §6).
    Alcance por anexo específico (`id_anexo` no nulo) o por grupo económico
    completo (`id_anexo` nulo, `id_grupo_economico` define el alcance)."""

    fecha_desde: date
    fecha_hasta: date
    id_grupo_economico: int
    id_anexo: int | None
