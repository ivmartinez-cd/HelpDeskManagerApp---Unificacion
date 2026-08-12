import pytest

from src.modules.sla.application.dtos.sla_dtos import GetSlaComplianceRequest
from src.modules.sla.application.use_cases.get_sla_compliance import GetSlaCompliance
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.domain.entities.incidente_sla import (
    RESULTADO_CORRECTO,
    RESULTADO_VENCIDO,
)
from src.modules.sla.domain.errors import PeriodoInvalidoError
from src.modules.sla.domain.value_objects.periodo import Periodo
from tests.unit.domain.sla.fakes import (
    FakeSlaQueryGateway,
    FakeSlaSnapshotRepository,
    build_incidente,
)


def _build_use_case(gateway: FakeSlaQueryGateway) -> GetSlaCompliance:
    repo = FakeSlaSnapshotRepository()
    return GetSlaCompliance(repo, RefreshSlaSnapshot(gateway, repo))


async def test_sin_incidentes_devuelve_ceros_sin_dividir_por_cero() -> None:
    use_case = _build_use_case(FakeSlaQueryGateway())

    result = await use_case.execute(GetSlaComplianceRequest(periodo=202608))

    assert result.total == 0
    assert result.correctos == 0
    assert result.vencidos == 0
    assert result.pct_correctos == 0.0
    assert result.pct_vencidos == 0.0
    assert result.vencidos_por_tecnico == []


async def test_calcula_totales_y_porcentajes() -> None:
    incidentes = [
        build_incidente(1, "CD - Ana", RESULTADO_CORRECTO),
        build_incidente(2, "CD - Ana", RESULTADO_CORRECTO),
        build_incidente(3, "CD - Ana", RESULTADO_CORRECTO),
        build_incidente(4, "CD - Beto", RESULTADO_VENCIDO),
    ]
    use_case = _build_use_case(FakeSlaQueryGateway(incidentes))

    result = await use_case.execute(GetSlaComplianceRequest(periodo=202608))

    assert result.total == 4
    assert result.correctos == 3
    assert result.vencidos == 1
    assert result.pct_correctos == 75.0
    assert result.pct_vencidos == 25.0


async def test_redondea_porcentajes_a_dos_decimales() -> None:
    incidentes = [build_incidente(1, "CD - Ana", RESULTADO_VENCIDO)] + [
        build_incidente(i, "CD - Ana", RESULTADO_CORRECTO) for i in range(2, 8)
    ]
    use_case = _build_use_case(FakeSlaQueryGateway(incidentes))

    result = await use_case.execute(GetSlaComplianceRequest(periodo=202608))

    # 1/7 = 14,2857...% -> 14,29 / 85,71
    assert result.pct_vencidos == 14.29
    assert result.pct_correctos == 85.71


async def test_agrupa_vencidos_por_tecnico_por_cantidad_y_nombre() -> None:
    incidentes = [
        build_incidente(10, "PST Comodoro Rivadavia", RESULTADO_VENCIDO),
        build_incidente(11, "CD - Nicolás MON", RESULTADO_VENCIDO),
        build_incidente(12, "PST Comodoro Rivadavia", RESULTADO_VENCIDO),
        build_incidente(13, "CD - Ana", RESULTADO_VENCIDO),
        build_incidente(14, "CD - Zoe", RESULTADO_CORRECTO),
    ]
    use_case = _build_use_case(FakeSlaQueryGateway(incidentes))

    result = await use_case.execute(GetSlaComplianceRequest(periodo=202608))

    assert [(g.tecnico, g.cantidad) for g in result.vencidos_por_tecnico] == [
        ("PST Comodoro Rivadavia", 2),
        ("CD - Ana", 1),
        ("CD - Nicolás MON", 1),
    ]
    assert result.vencidos_por_tecnico[0].ids_incidente == [10, 12]


async def test_consulta_el_periodo_pedido() -> None:
    gateway = FakeSlaQueryGateway()

    await _build_use_case(gateway).execute(GetSlaComplianceRequest(periodo=202608))

    assert gateway.periodos_consultados == [Periodo(202608)]


async def test_periodo_invalido_lanza_error_sin_consultar() -> None:
    gateway = FakeSlaQueryGateway()

    with pytest.raises(PeriodoInvalidoError):
        await _build_use_case(gateway).execute(GetSlaComplianceRequest(periodo=202613))

    assert gateway.periodos_consultados == []


async def test_lee_del_snapshot_cacheado_sin_volver_a_consultar_mercurio() -> None:
    gateway = FakeSlaQueryGateway([build_incidente(1, "CD - Ana", RESULTADO_VENCIDO)])
    repo = FakeSlaSnapshotRepository()
    use_case = GetSlaCompliance(repo, RefreshSlaSnapshot(gateway, repo))

    await use_case.execute(GetSlaComplianceRequest(periodo=202608))
    await use_case.execute(GetSlaComplianceRequest(periodo=202608))

    assert gateway.periodos_consultados == [Periodo(202608)]
