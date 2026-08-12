"""Tests de send_mail_to_all — describe un envío a N destinatarios como una sola
fila de mail_log, sin tocar la BD."""

from src.modules.insumos.application.jobs.mail_delivery import send_mail_to_all
from src.modules.insumos.domain.value_objects.mail_log_entry import MailMessage
from tests.unit.domain.insumos.fakes import FakeMailer

MESSAGE = MailMessage(kind="poller_alert", subject="Asunto", body="Cuerpo")


async def test_todos_los_destinatarios_ok_da_success_true_y_csv_completo() -> None:
    mailer = FakeMailer()
    recipients = ["a@example.com", "b@example.com"]

    delivery = await send_mail_to_all(mailer, recipients, MESSAGE)

    assert delivery.log.success is True
    assert delivery.log.error is None
    assert delivery.log.recipients == "a@example.com,b@example.com"
    assert delivery.delivered == 2


async def test_un_destinatario_falla_da_success_false_y_menciona_la_direccion() -> None:
    mailer = FakeMailer()
    mailer.fail_for = {"b@example.com"}
    recipients = ["a@example.com", "b@example.com"]

    delivery = await send_mail_to_all(mailer, recipients, MESSAGE)

    assert delivery.log.success is False
    assert delivery.delivered == 1
    assert "b@example.com" in (delivery.log.error or "")


async def test_todos_fallan_da_delivered_cero_y_success_false() -> None:
    mailer = FakeMailer()
    recipients = ["a@example.com", "b@example.com"]
    mailer.fail_for = set(recipients)

    delivery = await send_mail_to_all(mailer, recipients, MESSAGE)

    assert delivery.delivered == 0
    assert delivery.log.success is False
    assert "a@example.com" in (delivery.log.error or "")
    assert "b@example.com" in (delivery.log.error or "")


async def test_lista_vacia_no_explota_y_da_success_false() -> None:
    mailer = FakeMailer()

    delivery = await send_mail_to_all(mailer, [], MESSAGE)

    assert delivery.delivered == 0
    assert delivery.log.success is False
    assert delivery.log.recipients == ""
    assert mailer.sent == []


async def test_kind_y_subject_de_la_fila_vienen_del_mensaje() -> None:
    mailer = FakeMailer()

    delivery = await send_mail_to_all(mailer, ["a@example.com"], MESSAGE)

    assert delivery.log.kind == "poller_alert"
    assert delivery.log.subject == "Asunto"


async def test_ok_no_deja_rastro_de_error_por_destinatario_que_no_fallo() -> None:
    mailer = FakeMailer()

    delivery = await send_mail_to_all(mailer, ["a@example.com"], MESSAGE)

    assert delivery.log.error is None
    assert mailer.sent == [("a@example.com", "Asunto", "Cuerpo")]
