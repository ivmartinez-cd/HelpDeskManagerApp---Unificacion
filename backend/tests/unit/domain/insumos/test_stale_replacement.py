"""Tests de is_stale_replaced (SDS no cierra la alerta tras el reemplazo físico)."""

from src.modules.insumos.domain.services.stale_replacement import is_stale_replaced


def test_reemplazo_posterior_a_la_solicitud_es_stale() -> None:
    assert is_stale_replaced("2026-08-01T10:00:00.000Z", "2026-08-03T09:00:00.000Z")


def test_reemplazo_anterior_no_es_stale() -> None:
    assert not is_stale_replaced("2026-08-03T09:00:00.000Z", "2026-08-01T10:00:00.000Z")


def test_sin_fechas_no_es_stale() -> None:
    assert not is_stale_replaced(None, "2026-08-03T09:00:00.000Z")
    assert not is_stale_replaced("2026-08-01T10:00:00.000Z", None)
    assert not is_stale_replaced("", "")
