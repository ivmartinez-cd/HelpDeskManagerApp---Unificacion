"""LoggingNotificador (solo loguea, nunca manda) y SystemClock."""

import logging
import uuid
from datetime import date

import pytest

from src.modules.vacaciones.domain.repositories.notificador import (
    DecisionNotif,
    NuevaSolicitudNotif,
)
from src.modules.vacaciones.infrastructure.logging_notificador import LoggingNotificador
from src.modules.vacaciones.infrastructure.system_clock import SystemClock

_LOGGER = "src.modules.vacaciones.infrastructure.logging_notificador"


async def test_nueva_solicitud_se_loguea_con_empleado_y_rango(
    caplog: pytest.LogCaptureFixture,
) -> None:
    notif = NuevaSolicitudNotif(
        empleado_nombre="Laura Pérez",
        sector_nombre="Soporte",
        department_id=uuid.uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 11),
        dias=5,
        target_year=2026,
        reason=None,
    )
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        await LoggingNotificador().notificar_nueva_solicitud(notif)

    assert len(caplog.records) == 1
    mensaje = caplog.records[0].getMessage()
    assert "Laura Pérez" in mensaje
    assert "2026-09-07" in mensaje and "2026-09-11" in mensaje
    assert "5 días" in mensaje


@pytest.mark.parametrize(("aprobada", "texto"), [(True, "APROBADA"), (False, "RECHAZADA")])
async def test_decision_se_loguea_con_el_veredicto(
    caplog: pytest.LogCaptureFixture, aprobada: bool, texto: str
) -> None:
    notif = DecisionNotif(
        empleado_nombre="Laura Pérez",
        empleado_email="lperez@canal.com",
        aprobada=aprobada,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 11),
        comment=None,
    )
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        await LoggingNotificador().notificar_decision(notif)

    assert len(caplog.records) == 1
    mensaje = caplog.records[0].getMessage()
    assert texto in mensaje
    assert "lperez@canal.com" in mensaje


def test_system_clock_devuelve_la_fecha_de_hoy() -> None:
    assert SystemClock().hoy() == date.today()
