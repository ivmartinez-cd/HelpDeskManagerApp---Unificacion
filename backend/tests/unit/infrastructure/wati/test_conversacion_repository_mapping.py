"""Mapeo entidad <-> fila del repositorio SQLAlchemy de conversaciones, sin
base de datos: el modelo ORM se instancia en memoria. Las consultas en sí son
tests de integración."""

from datetime import UTC, datetime

from src.modules.wati.domain.entities.conversacion import ConversacionWati
from src.modules.wati.infrastructure.models.conversacion_model import ConversacionWatiModel
from src.modules.wati.infrastructure.repositories.sqlalchemy_conversacion_repository import (
    _to_entity,
    _to_row,
)

_T0 = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


def _conversacion() -> ConversacionWati:
    return ConversacionWati(
        wa_id="5491130648978",
        nombre="Tienda 0649",
        conversation_id="c1",
        ticket_id="t1",
        operador_nombre="MDA",
        operador_email="mda@canaldirecto.com.ar",
        ultimo_mensaje_cliente_at=_T0,
        esperando_desde=_T0,
        ultima_respuesta_at=None,
        ultimo_bot_at=None,
        cerrada_at=None,
        bot_activo=False,
        ultimo_texto_cliente="sigue sin enviar",
        sincronizado_at=_T0,
    )


def test_to_row_incluye_la_clave_y_todos_los_campos_de_la_entidad() -> None:
    row = _to_row(_conversacion())

    assert row["wa_id"] == "5491130648978"
    assert row["nombre"] == "Tienda 0649"
    assert row["esperando_desde"] == _T0
    assert row["ultima_respuesta_at"] is None
    assert row["bot_activo"] is False
    assert set(row) == set(ConversacionWati.__slots__)


def test_to_entity_reconstruye_la_conversacion_desde_el_modelo() -> None:
    original = _conversacion()
    modelo = ConversacionWatiModel(**_to_row(original))

    reconstruida = _to_entity(modelo)

    assert reconstruida == original
