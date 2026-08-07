from src.modules.contadores.domain.services.consumption_calculator import (
    calculate_daily_consumption,
)
from src.modules.contadores.domain.services.trend_window_selector import (
    TrendWindow,
    select_trend_window,
)
from src.modules.contadores.domain.value_objects.audit_entry import AuditEntry
from src.modules.contadores.domain.value_objects.counter_projection_result import (
    CounterProjectionResult,
)
from src.modules.contadores.domain.value_objects.counter_reading import CounterReading
from src.modules.contadores.domain.value_objects.device_projection_input import (
    DeviceProjectionInput,
)
from src.modules.contadores.domain.value_objects.projection_settings import ProjectionSettings

ProjectionOutcome = tuple[CounterProjectionResult, list[AuditEntry]]


def project_device_counter(
    device: DeviceProjectionInput, settings: ProjectionSettings
) -> ProjectionOutcome:
    """Proyecta el contador de un equipo (serie+clase) a `fecha_toma`.
    4 ramas, en este orden: lectura exacta en la fecha (REAL), sin historial
    (SIN_DATOS), última lectura ya suficientemente reciente (REAL sin
    proyectar), o proyección real a partir de la tendencia histórica."""
    ordered = sorted(device.readings, key=lambda r: r.fecha)
    real = [r for r in ordered if r.fecha == device.fecha_toma]
    hist = [r for r in ordered if r.fecha < device.fecha_toma]
    futuro = [r for r in ordered if r.fecha > device.fecha_toma]

    audit = [_entry(device, r, False, "Lectura futura — reservada para validación") for r in futuro]

    if real:
        result, entries = _project_exact_match(device, real, hist)
        return result, audit + entries
    if not hist:
        return _project_no_history(device), audit + [_no_history_entry(device)]

    dias_proy = (device.fecha_toma - hist[-1].fecha).days
    if dias_proy <= settings.tolerancia_dias:
        result, entries = _project_recent_enough(device, hist, dias_proy)
        return result, audit + entries

    result, entries = _project_from_trend(device, hist, dias_proy, settings)
    return result, audit + entries


def _project_exact_match(
    device: DeviceProjectionInput, real: list[CounterReading], hist: list[CounterReading]
) -> ProjectionOutcome:
    ultima = real[-1]
    audit = [_entry(device, r, r is ultima, "Lectura real en fecha de toma") for r in real]
    audit += [
        _entry(device, r, False, "No requerida — hay lectura real en fecha de toma") for r in hist
    ]
    result = CounterProjectionResult(
        serie=device.serie,
        clase=device.clase,
        articulo=device.articulo,
        sector=device.sector,
        fecha_lectura=ultima.fecha,
        contador_base=ultima.contador,
        dias_proyectados=0,
        consumo_diario_promedio=0.0,
        paginas_sumadas=0,
        fecha_toma=device.fecha_toma,
        contador_proyectado=ultima.contador,
        metodo="REAL",
        observaciones=f"Lectura real del {ultima.fecha} (tipo: {ultima.tipo_contador})",
    )
    return result, audit


def _project_no_history(device: DeviceProjectionInput) -> CounterProjectionResult:
    return CounterProjectionResult(
        serie=device.serie,
        clase=device.clase,
        articulo=device.articulo,
        sector=device.sector,
        fecha_lectura=None,
        contador_base=None,
        dias_proyectados=None,
        consumo_diario_promedio=None,
        paginas_sumadas=None,
        fecha_toma=device.fecha_toma,
        contador_proyectado=None,
        metodo="SIN_DATOS",
        observaciones="No existen lecturas previas a la fecha de toma",
    )


def _project_recent_enough(
    device: DeviceProjectionInput, hist: list[CounterReading], dias_proy: int
) -> ProjectionOutcome:
    ultima = hist[-1]
    motivo = f"A {dias_proy} dia(s) de la toma — usada como REAL sin proyectar"
    audit = [
        _entry(device, r, r is ultima, motivo if r is ultima else "No requerida") for r in hist
    ]
    result = CounterProjectionResult(
        serie=device.serie,
        clase=device.clase,
        articulo=device.articulo,
        sector=device.sector,
        fecha_lectura=ultima.fecha,
        contador_base=ultima.contador,
        dias_proyectados=0,
        consumo_diario_promedio=0.0,
        paginas_sumadas=0,
        fecha_toma=device.fecha_toma,
        contador_proyectado=ultima.contador,
        metodo="REAL",
        observaciones=(
            f"Lectura del {ultima.fecha} a {dias_proy} dia(s) de la toma — sin proyección"
        ),
    )
    return result, audit


def _project_from_trend(
    device: DeviceProjectionInput,
    hist: list[CounterReading],
    dias_proy: int,
    settings: ProjectionSettings,
) -> ProjectionOutcome:
    window = select_trend_window(hist, settings)
    audit = _trend_audit_entries(device, hist, window)

    outcome = calculate_daily_consumption(window.readings, settings)
    consumo, desc_consumo = outcome.consumo_diario, outcome.descripcion
    audit += (
        [_entry(device, hist[0], False, f"[Tendencia] {n}") for n in outcome.notas]
        if outcome.notas
        else []
    )

    if dias_proy > settings.max_antiguedad_lectura_dias:
        consumo, desc_consumo = (
            0.0,
            f"Lectura base muy antigua (> {settings.max_antiguedad_lectura_dias} dias)",
        )

    ultima_hist = hist[-1]
    contador_proy = round(ultima_hist.contador + consumo * dias_proy)
    obs = f"{desc_consumo} | {dias_proy} dia(s) proyectado(s) hasta {device.fecha_toma}"
    result = CounterProjectionResult(
        serie=device.serie,
        clase=device.clase,
        articulo=device.articulo,
        sector=device.sector,
        fecha_lectura=ultima_hist.fecha,
        contador_base=ultima_hist.contador,
        dias_proyectados=dias_proy,
        consumo_diario_promedio=round(consumo, 4),
        paginas_sumadas=contador_proy - ultima_hist.contador,
        fecha_toma=device.fecha_toma,
        contador_proyectado=contador_proy,
        metodo="PROYECTADO",
        observaciones=obs,
    )
    return result, audit


def _trend_audit_entries(
    device: DeviceProjectionInput, hist: list[CounterReading], window: TrendWindow
) -> list[AuditEntry]:
    used = {id(r) for r in window.readings}
    entries: list[AuditEntry] = []
    for r in hist:
        if id(r) in used:
            entries.append(_entry(device, r, True, "Usada para calcular la tendencia"))
        else:
            entries.append(_entry(device, r, False, "Descartada (fuera de ventana o pre-reset)"))
    return entries


def _no_history_entry(device: DeviceProjectionInput) -> AuditEntry:
    return AuditEntry(
        device.serie, device.clase, None, None, None, False, "Sin lecturas históricas"
    )


def _entry(
    device: DeviceProjectionInput, reading: CounterReading, usado: bool, motivo: str
) -> AuditEntry:
    return AuditEntry(
        device.serie,
        device.clase,
        reading.fecha,
        reading.contador,
        reading.tipo_contador,
        usado,
        motivo,
    )
