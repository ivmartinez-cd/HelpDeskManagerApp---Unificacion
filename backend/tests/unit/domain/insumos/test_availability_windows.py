"""Tests de build_availability_windows — franjas "sin contacto" desde alertas AVAILABILITY."""

from src.modules.insumos.domain.services.availability_windows import build_availability_windows


def _unavailable(date: str, actual_hours: int | None = None) -> dict:
    description = "Device busy/unavailable for over 24 hours"
    if actual_hours is not None:
        description += f" (actual = {actual_hours} hrs)"
    return {"date": date, "description": description}


def _resumed(date: str) -> dict:
    return {"date": date, "description": "Monitoring resumed"}


def test_racha_completa_es_una_sola_ventana() -> None:
    """Alertas repetidas escalando ("over 72 hours", "over a week"...) son UNA
    desconexión: abre la primera, cierra el próximo resumed."""
    alerts = [
        _unavailable("2026-01-18T10:00:00Z"),
        _unavailable("2026-01-20T10:00:00Z"),
        _unavailable("2026-01-25T10:00:00Z"),
        _resumed("2026-01-29T08:00:00Z"),
    ]

    windows = build_availability_windows(alerts)

    assert len(windows) == 1
    assert windows[0].start == "2026-01-18T10:00:00+00:00"
    assert windows[0].end == "2026-01-29T08:00:00+00:00"


def test_inicio_se_corrige_hacia_atras_con_actual_hrs() -> None:
    """"actual = N hrs" acerca el inicio al momento real de la caída, no a cuándo
    Insight la detectó (recién tras confirmar N horas sin respuesta)."""
    alerts = [
        _unavailable("2026-01-18T10:00:00Z", actual_hours=26),
        _resumed("2026-01-19T10:00:00Z"),
    ]

    windows = build_availability_windows(alerts)

    assert windows[0].start == "2026-01-17T08:00:00+00:00"  # 26 horas antes


def test_orden_de_entrada_no_importa() -> None:
    alerts = [
        _resumed("2026-01-29T08:00:00Z"),
        _unavailable("2026-01-20T10:00:00Z"),
        _unavailable("2026-01-18T10:00:00Z"),
    ]

    windows = build_availability_windows(alerts)

    assert len(windows) == 1
    assert windows[0].start == "2026-01-18T10:00:00+00:00"


def test_racha_sin_cierre_no_genera_ventana() -> None:
    """Todavía offline a la fecha de corte: no se sabe el fin, no se inventa."""
    assert build_availability_windows([_unavailable("2026-01-18T10:00:00Z")]) == []


def test_resumed_sin_racha_abierta_se_ignora() -> None:
    assert build_availability_windows([_resumed("2026-01-29T08:00:00Z")]) == []


def test_alertas_sin_fecha_se_ignoran() -> None:
    alerts = [
        {"date": None, "description": "Device busy/unavailable for over 24 hours"},
        _unavailable("2026-01-18T10:00:00Z"),
        _resumed("2026-01-19T10:00:00Z"),
    ]

    windows = build_availability_windows(alerts)

    assert len(windows) == 1


def test_dos_desconexiones_separadas_son_dos_ventanas() -> None:
    alerts = [
        _unavailable("2026-01-10T10:00:00Z"),
        _resumed("2026-01-11T10:00:00Z"),
        _unavailable("2026-02-01T10:00:00Z"),
        _resumed("2026-02-02T10:00:00Z"),
    ]

    windows = build_availability_windows(alerts)

    assert len(windows) == 2
    assert windows[0].end == "2026-01-11T10:00:00+00:00"
    assert windows[1].start == "2026-02-01T10:00:00+00:00"
