from src.modules.contadores.domain.value_objects.fixed_sum_result_row import FixedSumResultRow
from src.modules.contadores.domain.value_objects.fixed_sum_source_row import FixedSumSourceRow

_ESTADOS_SIN_SUMA = frozenset({"Desaparecida", "Backup Fijo"})
_ESTADO_ACTIVO = "Activa en Cliente"
_TIPO_SALIDA = "14"
_CLASE_SALIDA = "10"


def build_fixed_sum_rows(
    source: list[FixedSumSourceRow], fecha: str, hojas_a_sumar: int
) -> list[FixedSumResultRow]:
    return [_build_row(r, fecha, hojas_a_sumar) for r in source]


def _build_row(row: FixedSumSourceRow, fecha: str, hojas_a_sumar: int) -> FixedSumResultRow:
    return FixedSumResultRow(
        serie=row.serie,
        estado=row.estado,
        contador_actual=row.contador_actual,
        fecha=fecha,
        tipo=_TIPO_SALIDA,
        clase=_CLASE_SALIDA,
        contador=_resolve_contador(row, hojas_a_sumar),
    )


def _resolve_contador(row: FixedSumSourceRow, hojas_a_sumar: int) -> int | str:
    """Orden de prioridad verificado en vivo: Estado "sin suma" gana incluso
    si además fuera Activa en Cliente; contador==1 gana sobre Activa en
    Cliente; cualquier otro Estado no listado deja el contador vacío."""
    if row.estado in _ESTADOS_SIN_SUMA:
        return row.contador_actual
    if row.contador_actual == 1:
        return row.contador_actual
    if row.estado == _ESTADO_ACTIVO:
        return row.contador_actual + hojas_a_sumar
    return ""
