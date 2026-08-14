from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class OperadorClientesDTO:
    operador_id: str
    operador_nombre: str
    operador_color: str | None
    clientes: int
    impresoras: int | None
    """None cuando Siges no respondió y no hay conteo (los clientes locales
    se muestran igual)."""
    sin_cruce: list[str]
    """Clientes del operador que no cruzaron contra Empresa de Siges — sus
    impresoras no están en la suma."""


@dataclass(frozen=True, slots=True)
class ResumenClientesOperadorDTO:
    desde: date
    hasta: date
    total_clientes: int
    total_impresoras: int | None
    operadores: list[OperadorClientesDTO]
