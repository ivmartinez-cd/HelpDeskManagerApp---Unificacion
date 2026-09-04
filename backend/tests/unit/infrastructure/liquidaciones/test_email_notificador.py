"""EmailNotificador de liquidaciones: el link del aviso de aprobación apunta
a Web Agentes (legacy), no al frontend nuevo — ver comentario del propio
módulo."""

import uuid
from datetime import datetime

import pytest

from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_APROBADA,
    TIPO_REGULAR,
    Liquidacion,
)
from src.modules.liquidaciones.infrastructure.email_notificador import EmailNotificador

CD_BASE_URL = "https://webagentes.canaldirecto.com.ar"


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


def make_liquidacion(**overrides: object) -> Liquidacion:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "prestador_id": uuid.uuid4(),
        "numero_liquidacion": "3849-2",
        "periodo": "2026-08",
        "tipo_liquidacion": TIPO_REGULAR,
        "nombre_archivo": "liq.xlsx",
        "fecha_importacion": datetime(2026, 8, 1),
        "estado": ESTADO_APROBADA,
        "total_incidentes": 10,
        "total_alertas": 0,
        "total_importe": 1000.0,
    }
    defaults.update(overrides)
    return Liquidacion(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_notificar_aprobacion_linkea_a_web_agentes_por_numero() -> None:
    mailer = FakeMailer()
    liquidacion = make_liquidacion()
    await EmailNotificador(mailer, CD_BASE_URL).notificar_aprobacion(liquidacion)

    assert len(mailer.enviados) == 1
    envio = mailer.enviados[0]
    assert envio["to"] == "jpcorigliano@canaldirecto.com.ar"
    url_esperada = f"{CD_BASE_URL}/liquidations/view/3849-2"
    assert url_esperada in str(envio["body"])
    assert f'href="{url_esperada}"' in str(envio["html_body"])
    assert str(liquidacion.id) not in str(envio["html_body"])


@pytest.mark.asyncio
async def test_fallo_de_envio_no_propaga() -> None:
    notificador = EmailNotificador(FakeMailer(fail=True), CD_BASE_URL)
    await notificador.notificar_aprobacion(make_liquidacion())
