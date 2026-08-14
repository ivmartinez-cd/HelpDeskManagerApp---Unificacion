import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HabilitarEquipoRequest:
    """`habilitado_por_*` sale SIEMPRE de la identidad de la sesión (lo arma
    el router desde `Identity`), nunca del body del request."""

    siges_maquina_id: int
    habilitado_por_user_id: uuid.UUID
    habilitado_por_nombre: str
    nota: str | None = None


@dataclass(frozen=True, slots=True)
class DeshabilitarEquipoRequest:
    siges_maquina_id: int
    deshabilitado_por_nombre: str
