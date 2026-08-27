from datetime import date

from src.modules.sla.application.use_cases.list_incidentes_derivados import (
    ListIncidentesDerivados,
)
from tests.unit.application.sla.fakes_derivados import (
    FakeDerivadosQueryGateway,
    build_derivado,
)
from tests.unit.application.sla.fakes_pendientes import FakePrestadorLookup

PERIODO = 202608


async def test_filtra_a_pst_del_interior() -> None:
    gateway = FakeDerivadosQueryGateway([
        build_derivado(1, id_tecnico=11, tecnico="PST Interior"),
        build_derivado(2, id_tecnico=99, tecnico="CD Local"),
    ])
    lookup = FakePrestadorLookup(pst_ids=[11])
    use_case = ListIncidentesDerivados(gateway, lookup)

    resultado = await use_case.execute(PERIODO)

    assert [dto.id_incidente for dto in resultado] == [1]


async def test_respeta_siges_ids_filtro_dentro_de_los_del_interior() -> None:
    gateway = FakeDerivadosQueryGateway([
        build_derivado(1, id_tecnico=11, tecnico="PST A"),
        build_derivado(2, id_tecnico=22, tecnico="PST B"),
    ])
    lookup = FakePrestadorLookup(pst_ids=[11, 22])
    use_case = ListIncidentesDerivados(gateway, lookup)

    resultado = await use_case.execute(PERIODO, siges_ids_filtro=[22])

    assert [dto.id_incidente for dto in resultado] == [2]


async def test_enriquece_con_el_operador_del_pst() -> None:
    gateway = FakeDerivadosQueryGateway([build_derivado(1, id_tecnico=11, tecnico="PST A")])
    lookup = FakePrestadorLookup(pst_ids=[11], pst_to_operador={11: "Victor Paez"})
    use_case = ListIncidentesDerivados(gateway, lookup)

    resultado = await use_case.execute(PERIODO)

    assert resultado[0].operador == "Victor Paez"


async def test_pst_sin_operador_asignado_devuelve_none() -> None:
    gateway = FakeDerivadosQueryGateway([build_derivado(1, id_tecnico=11, tecnico="PST A")])
    lookup = FakePrestadorLookup(pst_ids=[11])
    use_case = ListIncidentesDerivados(gateway, lookup)

    resultado = await use_case.execute(PERIODO)

    assert resultado[0].operador is None


async def test_ordena_por_dias_desde_ingreso_descendente() -> None:
    gateway = FakeDerivadosQueryGateway([
        build_derivado(1, id_tecnico=11, tecnico="PST A", dias_desde_ingreso=3),
        build_derivado(2, id_tecnico=11, tecnico="PST A", dias_desde_ingreso=9),
        build_derivado(3, id_tecnico=11, tecnico="PST A", dias_desde_ingreso=1),
    ])
    lookup = FakePrestadorLookup(pst_ids=[11])
    use_case = ListIncidentesDerivados(gateway, lookup)

    resultado = await use_case.execute(PERIODO)

    assert [dto.id_incidente for dto in resultado] == [2, 1, 3]


async def test_periodo_sin_datos_devuelve_vacio() -> None:
    gateway = FakeDerivadosQueryGateway([])
    lookup = FakePrestadorLookup(pst_ids=[11])
    use_case = ListIncidentesDerivados(gateway, lookup)

    resultado = await use_case.execute(PERIODO)

    assert resultado == []


async def test_deriva_el_rango_de_fechas_del_periodo() -> None:
    gateway = FakeDerivadosQueryGateway([])
    lookup = FakePrestadorLookup(pst_ids=[11])
    use_case = ListIncidentesDerivados(gateway, lookup)

    await use_case.execute(PERIODO)

    assert gateway.rangos_consultados == [(date(2026, 8, 1), date(2026, 8, 31))]
