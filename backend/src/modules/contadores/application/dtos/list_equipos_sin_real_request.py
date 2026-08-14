from dataclasses import dataclass
from typing import Literal

SortBy = Literal["meses", "cliente", "sucursal", "modelo", "operador"]
SortDir = Literal["asc", "desc"]


@dataclass(frozen=True)
class ListEquiposSinRealRequest:
    min_meses: int = 3
    search: str | None = None
    sort_by: SortBy = "meses"
    sort_dir: SortDir = "desc"
    force_refresh: bool = False
