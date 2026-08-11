"""Tests de ListMailLog — GET /api/insumos/mail-log."""

from src.modules.insumos.application.use_cases.list_mail_log import (
    ListMailLog,
    ListMailLogPorts,
)
from tests.unit.domain.insumos.fakes import FakeMailLogRepository


class World:
    def __init__(self) -> None:
        self.mail_log = FakeMailLogRepository()
        self.use_case = ListMailLog(ListMailLogPorts(mail_log=self.mail_log))  # type: ignore[arg-type]


async def test_lista_el_mail_mas_reciente_primero() -> None:
    world = World()
    world.mail_log.add("backup", "Backup diario")
    world.mail_log.add("pending_order_alert", "Pedidos por vencer")

    entries, total = await world.use_case.execute(page=1, size=100)

    assert total == 2
    assert [e.subject for e in entries] == ["Pedidos por vencer", "Backup diario"]


async def test_paginado_en_sql_no_en_memoria() -> None:
    """mail_log crece con cada envío y nunca se poda: la página tiene que salir de un
    LIMIT/OFFSET, no de recortar la tabla entera ya traída."""
    world = World()
    for i in range(5):
        world.mail_log.add("backup", f"Backup {i}")

    entries, total = await world.use_case.execute(page=2, size=2)

    assert total == 5
    assert [e.entry_id for e in entries] == [3, 2]


async def test_los_intentos_fallidos_tambien_se_listan_con_su_error() -> None:
    """El registro es de mails enviados O intentados — un fallo de SMTP no puede
    desaparecer del historial, es justamente lo que se va a mirar."""
    world = World()
    world.mail_log.add("poller_alert", "Poller caído", success=False)

    entries, _ = await world.use_case.execute(page=1, size=100)

    assert entries[0].success is False
    assert entries[0].error == "SMTP timeout"


async def test_sin_mails_la_pagina_viene_vacia_y_el_total_en_cero() -> None:
    world = World()

    entries, total = await world.use_case.execute(page=1, size=100)

    assert (entries, total) == ([], 0)
