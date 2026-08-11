"""Tests de los dos tiempos medidos sobre los pedidos creados de un cliente."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from src.modules.insumos.domain.services.fulfillment_stats import (
    compute_fulfillment,
    compute_pending_to_dispatch,
    supply_id_of,
)
from src.modules.insumos.domain.value_objects.audit_statistics import (
    DispatchRow,
    FulfillmentRow,
)
from src.modules.insumos.domain.value_objects.cd_supply import SupplyStatusEvent

TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def _fulfillment(asked_hour: int, loaded_hour: int, sku: str = "CF230A") -> FulfillmentRow:
    """Miércoles 2026-06-03, horario expresado en hora argentina (UTC-3)."""
    return FulfillmentRow(
        sku=sku,
        device_serial="SERIE1",
        hp_request_time=datetime(2026, 6, 3, asked_hour + 3, tzinfo=UTC),
        created_at=datetime(2026, 6, 3, loaded_hour + 3, tzinfo=UTC),
    )


def test_promedio_y_peor_caso_sobre_los_medibles() -> None:
    summary = compute_fulfillment(
        [_fulfillment(9, 10), _fulfillment(9, 12, sku="LENTO")],
        timezone=TZ,
        work_hour_start=8,
        work_hour_end=18,
    )

    assert summary.measured == 2
    assert summary.average == 120.0  # (60 + 180) / 2
    assert summary.maximum == 180.0
    assert summary.worst is not None and summary.worst.row.sku == "LENTO"


def test_delta_negativo_por_reloj_desfasado_no_sesga_el_promedio() -> None:
    """HP puede registrar una hora posterior a la carga; ese pedido no se mide, no
    se cuenta como 0."""
    summary = compute_fulfillment(
        [_fulfillment(12, 9), _fulfillment(9, 10)],
        timezone=TZ,
        work_hour_start=8,
        work_hour_end=18,
    )

    assert summary.measured == 1
    assert summary.average == 60.0


def test_sin_filas_medibles_no_se_inventa_promedio() -> None:
    summary = compute_fulfillment([], timezone=TZ, work_hour_start=8, work_hour_end=18)

    assert (summary.measured, summary.average, summary.maximum) == (0, None, None)
    assert summary.worst is None


def _dispatch(order_id: str, created_day: int) -> DispatchRow:
    return DispatchRow(
        sku="CF230A",
        device_serial="SERIE1",
        internal_order_id=order_id,
        created_at=datetime(2026, 6, created_day, 12, tzinfo=UTC),
    )


def _despachado(day: int) -> list[SupplyStatusEvent]:
    return [
        SupplyStatusEvent(estado="Pendiente", first_seen_at=datetime(2026, 6, 1, tzinfo=UTC)),
        SupplyStatusEvent(
            estado="Despachado", first_seen_at=datetime(2026, 6, day, 12, tzinfo=UTC)
        ),
    ]


def test_transito_en_dias_corridos_incluye_el_fin_de_semana() -> None:
    """No son horas hábiles: es tránsito logístico de Canal Directo, no gestión propia."""
    summary = compute_pending_to_dispatch(
        [_dispatch("441770-3", created_day=5)], {441770: _despachado(day=8)}
    )  # viernes 5 → lunes 8 de junio de 2026

    assert (summary.measured, summary.average) == (1, 3.0)


def test_un_pedido_que_nunca_llego_a_despachado_no_se_mide() -> None:
    summary = compute_pending_to_dispatch(
        [_dispatch("441770-3", created_day=1)],
        {
            441770: [
                SupplyStatusEvent(
                    estado="Pendiente", first_seen_at=datetime(2026, 6, 1, tzinfo=UTC)
                )
            ]
        },
    )

    assert (summary.measured, summary.average, summary.worst) == (0, None, None)


def test_id_de_pedido_no_parseable_queda_afuera() -> None:
    summary = compute_pending_to_dispatch([_dispatch("SIN-ID", created_day=1)], {})

    assert summary.measured == 0


def test_supply_id_of_toma_el_numero_antes_del_guion() -> None:
    assert supply_id_of("441770-3") == 441770
    assert supply_id_of("DRYRUN-SDS-1") is None
