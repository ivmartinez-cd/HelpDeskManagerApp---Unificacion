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
    # Nombre del operador (catálogo de contadores, cruzado por nombre con el
    # usuario logueado, ADR-009): cuando viene, solo se listan los equipos de
    # clientes asignados a ese operador — es lo que ve un operador sin
    # `contadores.manage` (decisión del usuario 2026-08-21). `None` = todos.
    solo_operador_nombre: str | None = None
    # El universo incluye Backup/Backup Fijo/Baja Solicitada/No Localizado
    # junto con lo realmente activo (ver docstring de `equipos_sin_real_query`).
    # `True` acota a `estado_maquina == "Activa en Cliente"` — lo que de
    # verdad necesita una visita, sin backups ni equipos perdidos mezclados.
    solo_activos: bool = False
