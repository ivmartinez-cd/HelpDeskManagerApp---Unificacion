from datetime import timedelta

from src.modules.wati.application.use_cases.get_pendientes_resumen import GetPendientesResumen
from src.modules.wati.application.use_cases.list_pendientes import ListPendientes
from src.modules.wati.application.use_cases.sync_conversaciones import SyncConversaciones
from src.modules.wati.domain.value_objects.evento import ContactoWati
from tests.unit.domain.wati.fakes import (
    FakeConversacionRepository,
    FakeWatiGateway,
    en,
    msg_cliente,
    msg_operador,
)

AHORA = en(60)


def _contacto(wa_id: str, minutos_last_updated: int) -> ContactoWati:
    return ContactoWati(
        wa_id=wa_id, nombre=f"Cliente {wa_id}", last_updated=en(minutos_last_updated)
    )


async def test_revisa_los_contactos_recientes_y_marca_los_que_esperan() -> None:
    gateway = FakeWatiGateway(
        contactos=[_contacto("111", 50), _contacto("222", 40)],
        eventos={"111": [msg_cliente(45)], "222": [msg_cliente(30), msg_operador(35)]},
    )
    repo = FakeConversacionRepository()

    resultado = await SyncConversaciones(gateway, repo, reloj=lambda: AHORA).execute()

    assert resultado.contactos_revisados == 2
    assert resultado.esperando == 1
    assert resultado.descartados == 0
    assert sorted(gateway.consultados) == ["111", "222"]
    assert repo.rows["111"].espera_respuesta(AHORA)
    assert not repo.rows["222"].espera_respuesta(AHORA)


async def test_ignora_contactos_fuera_de_la_ventana_pero_sigue_vigilando_los_que_esperan() -> None:
    repo = FakeConversacionRepository()
    # Ciclo 1: el contacto 333 entra por la lista de contactos y queda esperando.
    gateway = FakeWatiGateway(contactos=[_contacto("333", 10)], eventos={"333": [msg_cliente(5)]})
    await SyncConversaciones(gateway, repo, reloj=lambda: AHORA).execute()

    # Ciclo 2, tres días después: ya no aparece entre los contactos recientes
    # (ventana 48 h) pero el repo lo sigue teniendo como esperando → se revisa igual.
    despues = AHORA + timedelta(days=3)
    gateway2 = FakeWatiGateway(
        contactos=[_contacto("999", 60 * 24 * 3)],
        eventos={"333": [msg_cliente(5), msg_operador(8)], "999": [msg_cliente(60 * 24 * 3)]},
    )
    resultado = await SyncConversaciones(gateway2, repo, reloj=lambda: despues).execute()

    assert sorted(gateway2.consultados) == ["333", "999"]
    assert resultado.contactos_revisados == 2
    assert not repo.rows["333"].espera_respuesta(despues)


async def test_respeta_el_tope_por_ciclo_y_cuenta_los_descartados() -> None:
    contactos = [_contacto(str(i), 50) for i in range(5)]
    gateway = FakeWatiGateway(contactos=contactos, eventos={})
    repo = FakeConversacionRepository()

    resultado = await SyncConversaciones(
        gateway, repo, max_por_ciclo=3, reloj=lambda: AHORA
    ).execute()

    assert resultado.contactos_revisados == 3
    assert resultado.descartados == 2
    assert len(gateway.consultados) == 3


async def test_listado_y_resumen_leen_el_estado_sincronizado() -> None:
    gateway = FakeWatiGateway(
        contactos=[_contacto("111", 50), _contacto("222", 40), _contacto("333", 30)],
        eventos={
            "111": [msg_cliente(45, operador="MDA")],
            "222": [msg_cliente(20, operador="MDA")],
            "333": [msg_cliente(50, operador="Bot")],
        },
    )
    repo = FakeConversacionRepository()
    await SyncConversaciones(gateway, repo, reloj=lambda: AHORA).execute()
    listar = ListPendientes(repo, reloj=lambda: AHORA)

    pendientes = await listar.execute()
    resumen = await GetPendientesResumen(repo, listar).execute()

    assert [p.wa_id for p in pendientes] == ["222", "111", "333"]
    assert [p.minutos_esperando for p in pendientes] == [40, 15, 10]
    assert resumen.total == 3
    assert resumen.sin_asignar == 1
    assert resumen.max_minutos_esperando == 40
    por_operador = [(o.operador, o.cantidad) for o in resumen.por_operador]
    assert por_operador == [("MDA", 2), ("Sin asignar", 1)]
    assert resumen.sincronizado_at == AHORA
