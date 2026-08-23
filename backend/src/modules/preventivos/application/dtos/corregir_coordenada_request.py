import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CorregirCoordenadaRequest:
    """`corregido_por_*` sale SIEMPRE de la identidad de la sesión (lo arma
    el router desde `Identity`), nunca del body del request — mismo criterio
    que `HabilitarEquipoRequest`."""

    siges_sucursal_id: int
    latitud: float
    longitud: float
    corregido_por_user_id: uuid.UUID
    corregido_por_nombre: str
    nota: str | None = None
