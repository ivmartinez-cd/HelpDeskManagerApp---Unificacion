from datetime import UTC, datetime

from src.modules.wati.application.use_cases.list_pendientes import ListPendientes
from src.modules.wati.domain.entities.conversacion import ConversacionWati
from tests.unit.domain.wati.fakes import FakeConversacionRepository, en

_AHORA = en(60)


def _conversacion(wa_id: str, *, operador: str | None) -> ConversacionWati:
    return ConversacionWati(
        wa_id=wa_id,
        nombre=f"Cliente {wa_id}",
        conversation_id="c1",
        ticket_id="t1",
        operador_nombre=operador,
        operador_email=None,
        ultimo_mensaje_cliente_at=en(45),
        esperando_desde=en(45),
        ultima_respuesta_at=None,
        ultimo_bot_at=None,
        cerrada_at=None,
        bot_activo=False,
        ultimo_texto_cliente="hola",
        sincronizado_at=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )


async def test_sin_filtro_devuelve_todos_los_operadores() -> None:
    repo = FakeConversacionRepository()
    repo.rows["111"] = _conversacion("111", operador="MDA Canal Directo")
    repo.rows["222"] = _conversacion("222", operador="Sofi")
    repo.rows["333"] = _conversacion("333", operador=None)
    listar = ListPendientes(repo, reloj=lambda: _AHORA)

    pendientes = await listar.execute()

    assert {p.wa_id for p in pendientes} == {"111", "222", "333"}


async def test_filtro_por_operador_excluye_otros_y_sin_asignar() -> None:
    repo = FakeConversacionRepository()
    repo.rows["111"] = _conversacion("111", operador="MDA Canal Directo")
    repo.rows["222"] = _conversacion("222", operador="Sofi")
    repo.rows["333"] = _conversacion("333", operador=None)
    listar = ListPendientes(repo, reloj=lambda: _AHORA, operador_filtro="MDA Canal Directo")

    pendientes = await listar.execute()

    assert [p.wa_id for p in pendientes] == ["111"]
