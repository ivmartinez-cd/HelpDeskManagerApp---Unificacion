from datetime import UTC, datetime

from src.modules.sla.application.use_cases.get_pendientes_resumen import GetPendientesResumen
from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.domain.entities.pendientes_snapshot import (
    PendientesSnapshot,
    PrestadorPendientes,
)
from tests.unit.application.sla.fakes_pendientes import (
    FakePendientesQueryGateway,
    FakePendientesSnapshotRepository,
    FakePrestadorLookup,
    build_sin_cerrar,
)

_INCIDENTES = [
    build_sin_cerrar(1, 100, "PST A"),
    build_sin_cerrar(2, 200, "PST B"),
    build_sin_cerrar(3, 200, "PST B"),
    build_sin_cerrar(4, 300, "PST C"),
]
_OPERADORES = {100: "Zoe", 200: "Ana"}


def _build(
    incidentes: list[IncidenteSinCerrar], repo: FakePendientesSnapshotRepository | None = None
) -> tuple[GetPendientesResumen, FakePendientesQueryGateway]:
    gateway = FakePendientesQueryGateway(incidentes)
    repo = repo or FakePendientesSnapshotRepository()
    lookup = FakePrestadorLookup(pst_ids=[100, 200, 300], pst_to_operador=_OPERADORES)
    refresher = RefreshPendientesSnapshot(gateway, repo, lookup, meses_corte=6)
    return GetPendientesResumen(repo, refresher), gateway


async def test_sin_filtro_devuelve_total_y_desglose_completo() -> None:
    use_case, _ = _build(_INCIDENTES)

    result = await use_case.execute()

    assert result.total == 4
    assert [(p.tecnico, p.cantidad) for p in result.por_prestador] == [
        ("PST A", 1),
        ("PST B", 2),
        ("PST C", 1),
    ]
    assert [(o.operador_nombre, o.cantidad) for o in result.por_operador] == [
        ("Ana", 2),
        ("Zoe", 1),
    ]


async def test_filtro_por_siges_ids_recorta_prestadores_total_y_operadores() -> None:
    use_case, _ = _build(_INCIDENTES)

    result = await use_case.execute(siges_ids_filtro=[200, 300])

    assert result.total == 3
    assert [p.id_tecnico for p in result.por_prestador] == [200, 300]
    assert [(o.operador_nombre, o.cantidad) for o in result.por_operador] == [("Ana", 2)]


async def test_filtro_vacio_devuelve_resumen_en_cero() -> None:
    use_case, _ = _build(_INCIDENTES)

    result = await use_case.execute(siges_ids_filtro=[])

    assert result.total == 0
    assert result.por_prestador == []
    assert result.por_operador == []


async def test_mapea_ids_incidente_y_operador_del_prestador() -> None:
    use_case, _ = _build(_INCIDENTES)

    result = await use_case.execute(siges_ids_filtro=[200])

    (prestador,) = result.por_prestador
    assert prestador.ids_incidente == [2, 3]
    assert prestador.operador_nombre == "Ana"


async def test_cold_start_dispara_un_refresh_y_luego_lee_del_cache() -> None:
    use_case, gateway = _build(_INCIDENTES)

    await use_case.execute()
    await use_case.execute()

    assert gateway.meses_consultados == [6]


async def test_con_snapshot_cacheado_no_consulta_siges() -> None:
    updated_at = datetime(2026, 8, 20, 10, 0, tzinfo=UTC)
    cacheado = PendientesSnapshot(
        total=1,
        incidentes=[],
        por_prestador=[
            PrestadorPendientes(
                id_tecnico=7, tecnico="PST X", cantidad=1, ids_incidente=[9], operador_nombre=None
            )
        ],
        por_operador=[],
        updated_at=updated_at,
    )
    use_case, gateway = _build(_INCIDENTES, repo=FakePendientesSnapshotRepository(cacheado))

    result = await use_case.execute()

    assert gateway.meses_consultados == []
    assert result.total == 1
    assert result.updated_at == updated_at
