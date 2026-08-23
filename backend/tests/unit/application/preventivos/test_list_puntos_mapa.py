from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

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
from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from tests.unit.application.preventivos.fakes import (
    FakeHabilitacionRepository,
    FakePreventivosQueryGateway,
    FakeSucursalCoordenadasRepository,
    build_equipo,
    build_habilitacion,
)

_EXCLUIDAS: tuple[str, ...] = ()
# Misma tz que usa el use case (list_equipos_por_zona.py) para "hoy": ancla
# el test a una sola lectura de reloj en vez de dos (una acá, otra dentro del
# use case), que podían discrepar en 1 día justo al cruzar la medianoche.
_TZ_LOCAL = ZoneInfo("America/Argentina/Buenos_Aires")


def _use_case(
    gateway: FakePreventivosQueryGateway,
    repo: FakeHabilitacionRepository | None = None,
    coordenadas: FakeSucursalCoordenadasRepository | None = None,
) -> ListPuntosMapaUseCase:
    equipos_use_case = ListEquiposPorZonaUseCase(
        ListEquiposPorZonaDependencies(
            gateway=gateway,
            habilitaciones=repo or FakeHabilitacionRepository(),
            zonas_excluidas=_EXCLUIDAS,
        )
    )
    return ListPuntosMapaUseCase(
        ListPuntosMapaDependencies(
            equipos_use_case=equipos_use_case,
            sucursal_coordenadas=coordenadas or FakeSucursalCoordenadasRepository(),
        )
    )


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
    hoy = datetime.now(_TZ_LOCAL).date()
    hace_400 = hoy - timedelta(days=400)
    hace_40 = hoy - timedelta(days=40)
    equipos = [
        build_equipo(1, id_sucursal=10, frecuencia_dias=180, fecha_ultimo_preventivo=hace_400),
        build_equipo(2, id_sucursal=10, frecuencia_dias=180, fecha_ultimo_preventivo=hace_40),
    ]
    use_case = _use_case(FakePreventivosQueryGateway(equipos))

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    # 400 - 180 = 220 días de atraso; anclado a `hoy` en vez de un número
    # fijo para no depender de en qué instante exacto corre el test.
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


async def test_coordenada_geocodificada_completa_la_sin_ubicar() -> None:
    equipos = [
        build_equipo(
            1,
            id_sucursal=10,
            fecha_ultimo_preventivo=date.today(),
            latitud=0.0,
            longitud=0.0,
        )
    ]
    resuelta = SucursalCoordenadas(
        siges_sucursal_id=10,
        latitud=-31.5,
        longitud=-68.5,
        formatted_address="Domicilio geocodificado",
        fecha_resolucion=datetime.now(UTC),
    )
    coordenadas = FakeSucursalCoordenadasRepository([resuelta])
    use_case = _use_case(FakePreventivosQueryGateway(equipos), coordenadas=coordenadas)

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert result.puntos[0].ubicado is True
    assert (result.puntos[0].latitud, result.puntos[0].longitud) == (-31.5, -68.5)


async def test_override_pisa_una_coordenada_de_siges_ya_valida() -> None:
    # El pin de Siges pasa la validación de bbox pero es un pin compartido
    # (ver domain/services/pines_sospechosos.py): una vez geocodificada, la
    # resolución manda igual, no solo cuando faltaba coordenada.
    equipos = [
        build_equipo(
            1,
            id_sucursal=10,
            fecha_ultimo_preventivo=date.today(),
            latitud=-34.6,
            longitud=-58.4,
        )
    ]
    resuelta = SucursalCoordenadas(
        siges_sucursal_id=10,
        latitud=-31.5,
        longitud=-68.5,
        formatted_address="Domicilio corregido",
        fecha_resolucion=datetime.now(UTC),
    )
    coordenadas = FakeSucursalCoordenadasRepository([resuelta])
    use_case = _use_case(FakePreventivosQueryGateway(equipos), coordenadas=coordenadas)

    result = await use_case.execute(ListEquiposPorZonaRequest(zona="SUR"))

    assert result.puntos[0].ubicado is True
    assert (result.puntos[0].latitud, result.puntos[0].longitud) == (-31.5, -68.5)
