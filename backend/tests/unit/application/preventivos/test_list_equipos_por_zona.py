from datetime import date, timedelta

import pytest

from src.modules.preventivos.application.dtos.list_equipos_request import (
    ListEquiposPorZonaRequest,
)
from src.modules.preventivos.application.use_cases.list_equipos_por_zona import (
    DESHABILITADO_POR_SISTEMA,
    ListEquiposPorZonaDependencies,
    ListEquiposPorZonaUseCase,
)
from src.modules.preventivos.domain.errors import ZonaInvalidaError
from tests.unit.application.preventivos.fakes import (
    FakeHabilitacionRepository,
    FakePreventivosQueryGateway,
    build_equipo,
    build_habilitacion,
)

_EXCLUIDAS = ("INTERIOR", "BSAS.*")


def _use_case(
    gateway: FakePreventivosQueryGateway, repo: FakeHabilitacionRepository | None = None
) -> ListEquiposPorZonaUseCase:
    return ListEquiposPorZonaUseCase(
        ListEquiposPorZonaDependencies(
            gateway=gateway,
            habilitaciones=repo or FakeHabilitacionRepository(),
            zonas_excluidas=_EXCLUIDAS,
        )
    )


async def test_zona_excluida_lanza_error_sin_consultar_siges() -> None:
    gateway = FakePreventivosQueryGateway()

    with pytest.raises(ZonaInvalidaError):
        await _use_case(gateway).execute(ListEquiposPorZonaRequest(zona="INTERIOR"))

    assert gateway.zonas_consultadas == []


async def test_ordena_vencidos_primero_y_mas_atrasado_arriba() -> None:
    hace_un_anio = date.today() - timedelta(days=365)
    hace_siete_meses = date.today() - timedelta(days=210)
    reciente = date.today() - timedelta(days=10)
    equipos = [
        build_equipo(1, fecha_ultimo_preventivo=reciente),  # al_dia
        build_equipo(2, fecha_ultimo_preventivo=hace_siete_meses),  # vencido 30 días
        build_equipo(3, fecha_ultimo_preventivo=None),  # sin_preventivo
        build_equipo(4, fecha_ultimo_preventivo=hace_un_anio),  # vencido 185 días
        build_equipo(5, frecuencia_dias=0, fecha_ultimo_preventivo=reciente),  # sin_frec
    ]
    use_case = _use_case(FakePreventivosQueryGateway(equipos))

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    orden = [a.equipo.id_maquina for a in result.equipos]
    assert orden == [4, 2, 3, 1, 5]
    assert [a.estado for a in result.equipos] == [
        "vencido",
        "vencido",
        "sin_preventivo",
        "al_dia",
        "sin_frecuencia",
    ]


async def test_filtra_por_estado_habilitado_y_busqueda() -> None:
    vencida = date.today() - timedelta(days=400)
    equipos = [
        build_equipo(1, cliente="Hospital Italiano", fecha_ultimo_preventivo=vencida),
        build_equipo(2, cliente="Celulosa Campana", fecha_ultimo_preventivo=vencida),
        build_equipo(3, cliente="Hospital Italiano", fecha_ultimo_preventivo=date.today()),
    ]
    repo = FakeHabilitacionRepository([build_habilitacion(1)])
    use_case = _use_case(FakePreventivosQueryGateway(equipos), repo)

    por_estado = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR", estado="vencido"))
    habilitados = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR", habilitado=True))
    buscados = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR", search="hospital"))

    # Igual de atrasados -> desempata por cliente alfabético.
    assert [a.equipo.id_maquina for a in por_estado.equipos] == [2, 1]
    assert [a.equipo.id_maquina for a in habilitados.equipos] == [1]
    assert habilitados.equipos[0].habilitacion is not None
    assert habilitados.equipos[0].habilitacion.habilitado_por == "Ana Prueba"
    assert sorted(a.equipo.id_maquina for a in buscados.equipos) == [1, 3]


async def test_habilitacion_se_limpia_sola_con_preventivo_posterior() -> None:
    # Habilitada hace 10 días; el último preventivo cerrado es de hoy ->
    # el pedido ya se cumplió y la marca se desactiva sola, con auditoría.
    equipos = [build_equipo(1, fecha_ultimo_preventivo=date.today())]
    repo = FakeHabilitacionRepository([build_habilitacion(1, habilitado_hace_dias=10)])
    use_case = _use_case(FakePreventivosQueryGateway(equipos), repo)

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert result.equipos[0].habilitacion is None
    guardada = repo.habilitaciones[0]
    assert guardada.activa is False
    assert guardada.deshabilitado_por == DESHABILITADO_POR_SISTEMA
    assert guardada.deshabilitado_en is not None


async def test_habilitacion_sin_preventivo_posterior_sigue_activa() -> None:
    hace_un_anio = date.today() - timedelta(days=365)
    equipos = [build_equipo(1, fecha_ultimo_preventivo=hace_un_anio)]
    repo = FakeHabilitacionRepository([build_habilitacion(1, habilitado_hace_dias=5)])
    use_case = _use_case(FakePreventivosQueryGateway(equipos), repo)

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert result.equipos[0].habilitacion is not None
    assert repo.habilitaciones[0].activa is True
