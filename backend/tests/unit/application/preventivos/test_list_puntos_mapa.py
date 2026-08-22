from datetime import date, timedelta

from src.modules.preventivos.application.dtos.list_equipos_request import (
    ListEquiposPorZonaRequest,
)
from src.modules.preventivos.application.use_cases.list_equipos_por_zona import (
    ListEquiposPorZonaDependencies,
    ListEquiposPorZonaUseCase,
)
from src.modules.preventivos.application.use_cases.list_puntos_mapa import (
    ListPuntosMapaDependencies,
    ListPuntosMapaUseCase,
)
from tests.unit.application.preventivos.fakes import (
    FakeHabilitacionRepository,
    FakePreventivosQueryGateway,
    build_equipo,
    build_habilitacion,
)

_EXCLUIDAS: tuple[str, ...] = ()


def _use_case(
    gateway: FakePreventivosQueryGateway, repo: FakeHabilitacionRepository | None = None
) -> ListPuntosMapaUseCase:
    equipos_use_case = ListEquiposPorZonaUseCase(
        ListEquiposPorZonaDependencies(
            gateway=gateway,
            habilitaciones=repo or FakeHabilitacionRepository(),
            zonas_excluidas=_EXCLUIDAS,
        )
    )
    return ListPuntosMapaUseCase(ListPuntosMapaDependencies(equipos_use_case=equipos_use_case))


async def test_colapsa_varias_maquinas_de_una_sucursal_en_un_punto() -> None:
    vencida = date.today() - timedelta(days=400)
    hoy = date.today()
    equipos = [
        build_equipo(1, id_sucursal=10, sucursal="Sucursal A", fecha_ultimo_preventivo=vencida),
        build_equipo(2, id_sucursal=10, sucursal="Sucursal A", fecha_ultimo_preventivo=hoy),
        build_equipo(3, id_sucursal=20, sucursal="Sucursal B", fecha_ultimo_preventivo=hoy),
    ]
    use_case = _use_case(FakePreventivosQueryGateway(equipos))

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert len(result.puntos) == 2
    por_sucursal = {p.id_sucursal: p for p in result.puntos}
    assert por_sucursal[10].cant_maquinas == 2
    assert por_sucursal[10].peor_estado == "vencido"
    assert por_sucursal[20].cant_maquinas == 1
    assert por_sucursal[20].peor_estado == "al_dia"


async def test_dias_vencido_max_es_el_peor_de_la_sucursal() -> None:
    hace_400 = date.today() - timedelta(days=400)
    hace_40 = date.today() - timedelta(days=40)
    equipos = [
        build_equipo(1, id_sucursal=10, frecuencia_dias=180, fecha_ultimo_preventivo=hace_400),
        build_equipo(2, id_sucursal=10, frecuencia_dias=180, fecha_ultimo_preventivo=hace_40),
    ]
    use_case = _use_case(FakePreventivosQueryGateway(equipos))

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert result.puntos[0].dias_vencido_max == 220


async def test_cant_habilitadas_cuenta_solo_las_habilitaciones_activas() -> None:
    # fecha_ultimo_preventivo anterior a la habilitación: si fuera posterior,
    # la limpieza automática del use case de equipos la desactivaría sola.
    hace_un_anio = date.today() - timedelta(days=365)
    equipos = [
        build_equipo(1, id_sucursal=10, fecha_ultimo_preventivo=hace_un_anio),
        build_equipo(2, id_sucursal=10, fecha_ultimo_preventivo=hace_un_anio),
    ]
    repo = FakeHabilitacionRepository([build_habilitacion(1, habilitado_hace_dias=5)])
    use_case = _use_case(FakePreventivosQueryGateway(equipos), repo)

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert result.puntos[0].cant_habilitadas == 1


async def test_coordenada_invalida_queda_marcada_no_descartada() -> None:
    equipos = [
        build_equipo(
            1,
            id_sucursal=10,
            fecha_ultimo_preventivo=date.today(),
            latitud=0.0,
            longitud=0.0,
        )
    ]
    use_case = _use_case(FakePreventivosQueryGateway(equipos))

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert len(result.puntos) == 1
    assert result.puntos[0].ubicado is False
    assert result.puntos[0].latitud == 0.0
