from src.modules.sla.application.use_cases.list_pendientes import ListPendientes
from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from tests.unit.application.sla.fakes_pendientes import (
    FakePendientesQueryGateway,
    FakePendientesSnapshotRepository,
    FakePrestadorLookup,
    build_sin_cerrar,
)


def _build(
    incidentes: list[IncidenteSinCerrar],
) -> tuple[ListPendientes, FakePendientesQueryGateway]:
    gateway = FakePendientesQueryGateway(incidentes)
    repo = FakePendientesSnapshotRepository()
    lookup = FakePrestadorLookup(pst_ids=[100, 200])
    return ListPendientes(repo, RefreshPendientesSnapshot(gateway, repo, lookup, 6)), gateway


async def test_ordena_por_dias_en_estado_descendente() -> None:
    incidentes = [
        build_sin_cerrar(1, 100, "PST A", dias_en_estado=2),
        build_sin_cerrar(2, 200, "PST B", dias_en_estado=10),
        build_sin_cerrar(3, 100, "PST A", dias_en_estado=5),
    ]
    use_case, _ = _build(incidentes)

    result = await use_case.execute()

    assert [dto.id_incidente for dto in result] == [2, 3, 1]


async def test_filtra_por_siges_ids() -> None:
    incidentes = [build_sin_cerrar(1, 100, "PST A"), build_sin_cerrar(2, 200, "PST B")]
    use_case, _ = _build(incidentes)

    result = await use_case.execute(siges_ids_filtro=[200])

    assert [dto.id_incidente for dto in result] == [2]


async def test_filtro_vacio_devuelve_vacio_sin_consultar() -> None:
    use_case, gateway = _build([build_sin_cerrar(1, 100, "PST A")])

    result = await use_case.execute(siges_ids_filtro=[])

    assert result == []
    assert gateway.meses_consultados == []


async def test_mapea_los_campos_del_incidente() -> None:
    incidente = build_sin_cerrar(42, 100, "PST Trelew", dias_en_estado=7)
    use_case, _ = _build([incidente])

    (dto,) = await use_case.execute()

    assert dto.id_incidente == 42
    assert dto.tecnico == "PST Trelew"
    assert dto.id_tecnico == 100
    assert dto.cliente == incidente.cliente
    assert dto.sucursal == incidente.sucursal
    assert dto.modelo == incidente.modelo
    assert dto.nro_serie == incidente.nro_serie
    assert dto.fecha_ingreso == incidente.fecha_ingreso
    assert dto.fecha_finalizacion == incidente.fecha_finalizacion
    assert dto.dias_en_estado == 7


async def test_lee_del_snapshot_cacheado_en_la_segunda_llamada() -> None:
    use_case, gateway = _build([build_sin_cerrar(1, 100, "PST A")])

    await use_case.execute()
    await use_case.execute()

    assert gateway.meses_consultados == [6]
