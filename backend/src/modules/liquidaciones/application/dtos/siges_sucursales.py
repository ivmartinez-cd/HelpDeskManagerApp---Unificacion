"""DTOs del alta asistida de Tabla KM (ADR-014, dataset 3)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SucursalSigesDTO:
    """Sucursal de cliente del PST en Siges, con la marca de si el par
    empresa+sucursal ya existe en la Tabla KM local (comparación normalizada).
    Solo lectura: el alta la decide el usuario, el km es siempre manual."""

    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    localidad: str | None
    provincia: str | None
    ya_cargada: bool
    actividad_reciente: bool
