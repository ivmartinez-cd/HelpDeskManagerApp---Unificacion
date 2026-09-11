from dataclasses import dataclass


@dataclass(slots=True)
class Operador:
    """Operador de facturación de Gestión. Identidad (`nombre`, `color`)
    resuelta contra `dbo.UsuariosWeb` en Siges/ORION por login (ver
    ADR-012) — ya no es una aproximación derivada de los eventos."""

    id: str
    nombre: str
    color: str | None = None
