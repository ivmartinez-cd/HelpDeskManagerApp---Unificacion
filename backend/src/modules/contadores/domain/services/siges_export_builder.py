from src.modules.contadores.domain.value_objects.counter_projection_result import (
    CounterProjectionResult,
)
from src.modules.contadores.domain.value_objects.siges_row import SigesRow

SIGES_TIPO = 4


def build_siges_rows(results: list[CounterProjectionResult]) -> list[SigesRow]:
    """Series que van a facturación: **toda** serie con al menos una clase
    PROYECTADA entra entera (Mono y Color juntos), aunque la otra clase sea
    REAL — regla verificada contra `construir_siges` de la app vieja."""
    proyectadas = {r.serie for r in results if r.metodo == "PROYECTADO"}
    grouped = _group_by_serie(results, proyectadas)
    return [_build_row(serie, group) for serie, group in grouped.items()]


def _group_by_serie(
    results: list[CounterProjectionResult], series: set[str]
) -> dict[str, list[CounterProjectionResult]]:
    grouped: dict[str, list[CounterProjectionResult]] = {}
    for r in results:
        if r.serie in series:
            grouped.setdefault(r.serie, []).append(r)
    return grouped


def _build_row(serie: str, group: list[CounterProjectionResult]) -> SigesRow:
    mono = next((r for r in group if r.clase == "Mono"), None)
    color = next((r for r in group if r.clase == "Color"), None)
    ref = mono or color
    assert ref is not None  # group nunca está vacío (viene de un groupby)
    return SigesRow(
        serie=serie,
        fecha=ref.fecha_toma,
        tipo=SIGES_TIPO,
        clase_10="10" if mono else "",
        contador_10=mono.contador_proyectado if mono and mono.contador_proyectado else "",
        clase_20="20" if color else "",
        contador_20=color.contador_proyectado if color and color.contador_proyectado else "",
        motivo=_combine_metodos(group),
        observaciones=_combine_observaciones(mono, color),
    )


def _combine_observaciones(
    mono: CounterProjectionResult | None, color: CounterProjectionResult | None
) -> str:
    if mono and color and mono.observaciones == color.observaciones:
        return mono.observaciones
    parts = []
    if mono:
        parts.append(f"Mono: {mono.observaciones}")
    if color:
        parts.append(f"Color: {color.observaciones}")
    return " | ".join(parts)


def _combine_metodos(group: list[CounterProjectionResult]) -> str:
    metodos = sorted({r.metodo for r in group})
    return metodos[0] if len(metodos) == 1 else " / ".join(metodos)
