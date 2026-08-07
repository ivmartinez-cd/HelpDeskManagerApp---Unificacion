from dataclasses import dataclass

from src.modules.contadores.domain.errors import NoFaltaContadorRowsError
from src.modules.contadores.domain.value_objects.estimation_zero_row import EstimationZeroRow
from src.modules.contadores.domain.value_objects.falta_contador_source_row import (
    FaltaContadorSourceRow,
)

_TIPO_SALIDA = "14"
_FILTRO_TIPO = "falta contador"


@dataclass(slots=True)
class _Accumulator:
    clase_10: str = ""
    contador_10: int = 0
    clase_20: str = ""
    contador_20: int = 0


def build_estimation_zero_rows(
    source: list[FaltaContadorSourceRow], fecha_nueva: str
) -> list[EstimationZeroRow]:
    """Filtra filas con `Tipo` conteniendo "FALTA CONTADOR" (case-insensitive,
    igual que `counters_tools.py` — no `csv_en0.py`, que es código muerto) y
    arma una fila por serie en formato ancho CLASE_10/CLASE_20."""
    relevant = [r for r in source if _FILTRO_TIPO in r.tipo.lower()]
    if not relevant:
        raise NoFaltaContadorRowsError

    grouped = _group_by_serie(relevant)
    return [
        EstimationZeroRow(
            serie=serie,
            fecha=fecha_nueva,
            tipo=_TIPO_SALIDA,
            clase_10=acc.clase_10,
            contador_10=acc.contador_10,
            clase_20=acc.clase_20,
            contador_20=acc.contador_20,
        )
        for serie, acc in sorted(grouped.items())
    ]


def _group_by_serie(rows: list[FaltaContadorSourceRow]) -> dict[str, _Accumulator]:
    grouped: dict[str, _Accumulator] = {}
    for r in rows:
        acc = grouped.setdefault(r.serie, _Accumulator())
        es_color = (r.nombre_clase or "").strip().lower() == "color"
        if es_color:
            acc.clase_20 = "20"
            acc.contador_20 = max(acc.contador_20, r.contador)
        elif r.nombre_clase is not None:
            acc.clase_10 = "10"
            acc.contador_10 = max(acc.contador_10, r.contador)
    return grouped
