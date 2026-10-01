import uuid
from collections.abc import Callable
from dataclasses import dataclass

from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
)
from src.modules.contadores.application.use_cases._releer_pl_manual import ReleerLecturas
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.ports.estim_log_port import EstimLogPort


@dataclass(frozen=True, slots=True)
class DependenciasProyeccion:
    """Proceso real → Postgres y Siges; modo ejemplo (sin `nro_proceso`) →
    stores en memoria, como sus recesos. Lo de Siges va como fábrica/callable
    perezoso: el modo ejemplo nunca toca ORION (ni exige que esté configurado)."""

    decisiones_reales: DecisionesOperadorPort
    decisiones_ejemplo: DecisionesOperadorPort
    constructor_siges: Callable[[], ConstructorEntradaSiges]
    releer_siges: ReleerLecturas
    estim_log: EstimLogPort

    def decisiones(self, nro_proceso: int | None) -> DecisionesOperadorPort:
        return self.decisiones_ejemplo if nro_proceso is None else self.decisiones_reales


@dataclass(frozen=True, slots=True)
class OperadorProyeccion:
    """Quién actúa: lo que la auditoría graba (`Estim_Log`)."""

    user_id: uuid.UUID
    email: str
