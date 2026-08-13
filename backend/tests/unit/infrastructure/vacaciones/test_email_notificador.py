"""EmailNotificador: destinatarios, paridad de subjects/links con el legacy y
la garantía de que un fallo de envío jamás propaga al use case."""

import uuid
from datetime import date

import pytest

from src.modules.vacaciones.domain.repositories.notificador import (
    DecisionNotif,
    NuevaSolicitudNotif,
)
from src.modules.vacaciones.infrastructure.email_notificador import EmailNotificador

FRONTEND_URL = "http://localhost:3000"


class FakeMailer:
    def __init__(self, fail: bool = False) -> None:
        self.enviados: list[dict[str, str | None]] = []
        self._fail = fail

    async def send(
        self, *, to: str, subject: str, body: str, html_body: str | None = None
    ) -> None:
        if self._fail:
            raise ConnectionError("SMTP caído")
        self.enviados.append(
            {"to": to, "subject": subject, "body": body, "html_body": html_body}
        )


class FakeDestinatarios:
    def __init__(self, emails: list[str]) -> None:
        self._emails = emails
        self.consultados: list[uuid.UUID] = []

    async def emails(self, department_id: uuid.UUID) -> list[str]:
        self.consultados.append(department_id)
        return self._emails


def make_nueva(**overrides: object) -> NuevaSolicitudNotif:
    defaults: dict[str, object] = {
        "empleado_nombre": "Laura Pérez",
        "sector_nombre": "Soporte Técnico",
        "department_id": uuid.uuid4(),
        "start_date": date(2026, 8, 4),
        "end_date": date(2026, 8, 15),
        "dias": 12,
        "target_year": 2026,
        "reason": "Viaje <familiar>",
    }
    defaults.update(overrides)
    return NuevaSolicitudNotif(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_nueva_solicitud_envia_a_cada_destinatario() -> None:
    mailer = FakeMailer()
    destinatarios = FakeDestinatarios(["jefe@canal.com", "admin@canal.com"])
    notif = make_nueva()
    await EmailNotificador(mailer, destinatarios, FRONTEND_URL).notificar_nueva_solicitud(
        notif
    )
    assert destinatarios.consultados == [notif.department_id]
    assert [e["to"] for e in mailer.enviados] == ["jefe@canal.com", "admin@canal.com"]
    primero = mailer.enviados[0]
    assert primero["subject"] == (
        "Nueva solicitud de vacaciones — Laura Pérez — Canal Directo"
    )
    assert "04/08/26" in str(primero["body"])
    assert f"{FRONTEND_URL}/vacaciones/aprobaciones" in str(primero["html_body"])
    # El motivo va escapado en el HTML (viene de input del usuario).
    assert "Viaje &lt;familiar&gt;" in str(primero["html_body"])


@pytest.mark.asyncio
async def test_nueva_solicitud_sin_destinatarios_no_envia() -> None:
    mailer = FakeMailer()
    notificador = EmailNotificador(mailer, FakeDestinatarios([]), FRONTEND_URL)
    await notificador.notificar_nueva_solicitud(make_nueva())
    assert mailer.enviados == []


@pytest.mark.asyncio
async def test_decision_envia_al_empleado() -> None:
    mailer = FakeMailer()
    notificador = EmailNotificador(mailer, FakeDestinatarios([]), FRONTEND_URL)
    await notificador.notificar_decision(
        DecisionNotif(
            empleado_nombre="Laura Pérez",
            empleado_email="lperez@canal.com",
            aprobada=True,
            start_date=date(2026, 8, 4),
            end_date=date(2026, 8, 15),
            comment="Sin observaciones",
        )
    )
    assert len(mailer.enviados) == 1
    envio = mailer.enviados[0]
    assert envio["to"] == "lperez@canal.com"
    assert envio["subject"] == "Solicitud de vacaciones APROBADA — Canal Directo"
    assert "aprobada" in str(envio["body"])
    assert "Sin observaciones" in str(envio["html_body"])


@pytest.mark.asyncio
async def test_fallo_de_envio_no_propaga() -> None:
    notificador = EmailNotificador(
        FakeMailer(fail=True), FakeDestinatarios(["jefe@canal.com"]), FRONTEND_URL
    )
    await notificador.notificar_nueva_solicitud(make_nueva())
    await notificador.notificar_decision(
        DecisionNotif(
            empleado_nombre="Laura Pérez",
            empleado_email="lperez@canal.com",
            aprobada=False,
            start_date=date(2026, 8, 4),
            end_date=date(2026, 8, 15),
            comment=None,
        )
    )
