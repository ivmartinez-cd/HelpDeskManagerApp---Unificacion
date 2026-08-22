from datetime import UTC, datetime

from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from tests.unit.application.sla.fakes_pendientes import (
    FakePendientesQueryGateway,
    FakePendientesSnapshotRepository,
    FakePrestadorLookup,
    build_sin_cerrar,
)


def _build_use_case(
    gateway: FakePendientesQueryGateway,
    lookup: FakePrestadorLookup,
    repo: FakePendientesSnapshotRepository | None = None,
    meses_corte: int = 6,
) -> RefreshPendientesSnapshot:
    return RefreshPendientesSnapshot(
        gateway, repo or FakePendientesSnapshotRepository(), lookup, meses_corte
    )


async def test_consulta_siges_con_los_meses_de_corte_configurados() -> None:
    gateway = FakePendientesQueryGateway()

    await _build_use_case(gateway, FakePrestadorLookup(), meses_corte=9).execute()

    assert gateway.meses_consultados == [9]


async def test_descarta_incidentes_de_tecnicos_que_no_son_pst() -> None:
    incidentes = [
        build_sin_cerrar(1, 100, "PST Trelew"),
        build_sin_cerrar(2, 999, "CD - Ana"),
    ]
    lookup = FakePrestadorLookup(pst_ids=[100])

    snapshot = await _build_use_case(FakePendientesQueryGateway(incidentes), lookup).execute()

    assert [i.id_incidente for i in snapshot.incidentes] == [1]
    assert snapshot.total == 1


async def test_agrupa_por_prestador_ordenado_por_nombre() -> None:
    incidentes = [
        build_sin_cerrar(1, 200, "PST Zapala"),
        build_sin_cerrar(2, 100, "PST Bariloche"),
        build_sin_cerrar(3, 200, "PST Zapala"),
    ]
    lookup = FakePrestadorLookup(pst_ids=[100, 200])

    snapshot = await _build_use_case(FakePendientesQueryGateway(incidentes), lookup).execute()

    assert [(p.tecnico, p.cantidad, p.ids_incidente) for p in snapshot.por_prestador] == [
        ("PST Bariloche", 1, [2]),
        ("PST Zapala", 2, [1, 3]),
    ]


async def test_suma_por_operador_e_ignora_pst_sin_operador() -> None:
    incidentes = [
        build_sin_cerrar(1, 100, "PST A"),
        build_sin_cerrar(2, 200, "PST B"),
        build_sin_cerrar(3, 200, "PST B"),
        build_sin_cerrar(4, 300, "PST C"),
    ]
    lookup = FakePrestadorLookup(pst_ids=[100, 200, 300], pst_to_operador={100: "Zoe", 200: "Ana"})

    snapshot = await _build_use_case(FakePendientesQueryGateway(incidentes), lookup).execute()

    assert [(o.operador_nombre, o.cantidad) for o in snapshot.por_operador] == [
        ("Ana", 2),
        ("Zoe", 1),
    ]
    sin_operador = next(p for p in snapshot.por_prestador if p.id_tecnico == 300)
    assert sin_operador.operador_nombre is None


async def test_persiste_el_snapshot_con_updated_at_utc() -> None:
    repo = FakePendientesSnapshotRepository()
    antes = datetime.now(UTC)

    snapshot = await _build_use_case(
        FakePendientesQueryGateway(), FakePrestadorLookup(), repo=repo
    ).execute()

    assert repo.upserts == 1
    assert repo.snapshot is snapshot
    assert snapshot.updated_at.tzinfo is not None
    assert snapshot.updated_at >= antes


async def test_sin_incidentes_devuelve_snapshot_vacio() -> None:
    snapshot = await _build_use_case(
        FakePendientesQueryGateway(), FakePrestadorLookup(pst_ids=[1])
    ).execute()

    assert snapshot.total == 0
    assert snapshot.incidentes == []
    assert snapshot.por_prestador == []
    assert snapshot.por_operador == []
