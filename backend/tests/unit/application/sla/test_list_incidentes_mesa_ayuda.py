from src.modules.sla.application.use_cases.list_incidentes_mesa_ayuda import (
    ListIncidentesMesaAyuda,
)
from tests.unit.application.sla.fakes_mesa_ayuda import (
    FakeMesaAyudaQueryGateway,
    build_mesa_ayuda,
)

ID_TECNICO = 428


async def test_ordena_por_dias_transcurridos_descendente() -> None:
    gateway = FakeMesaAyudaQueryGateway(
        [
            build_mesa_ayuda(1, dias_transcurridos=3),
            build_mesa_ayuda(2, dias_transcurridos=9),
            build_mesa_ayuda(3, dias_transcurridos=1),
        ]
    )
    use_case = ListIncidentesMesaAyuda(gateway, ID_TECNICO)

    resultado = await use_case.execute()

    assert [dto.id_incidente for dto in resultado] == [2, 1, 3]
    assert gateway.ids_tecnico_consultados == [ID_TECNICO]


async def test_filtra_por_operador() -> None:
    gateway = FakeMesaAyudaQueryGateway(
        [
            build_mesa_ayuda(1, operador_login="vipaez", dias_transcurridos=3),
            build_mesa_ayuda(2, operador_login="ltorres", dias_transcurridos=9),
        ]
    )
    use_case = ListIncidentesMesaAyuda(gateway, ID_TECNICO)

    resultado = await use_case.execute(operador_login="ltorres")

    assert [dto.id_incidente for dto in resultado] == [2]


async def test_lista_vacia() -> None:
    use_case = ListIncidentesMesaAyuda(FakeMesaAyudaQueryGateway(), ID_TECNICO)

    assert await use_case.execute() == []


async def test_demorado_marca_mas_de_siete_dias() -> None:
    gateway = FakeMesaAyudaQueryGateway(
        [
            build_mesa_ayuda(1, dias_transcurridos=7),
            build_mesa_ayuda(2, dias_transcurridos=8),
        ]
    )
    use_case = ListIncidentesMesaAyuda(gateway, ID_TECNICO)

    resultado = {dto.id_incidente: dto.demorado for dto in await use_case.execute()}

    assert resultado == {1: False, 2: True}
