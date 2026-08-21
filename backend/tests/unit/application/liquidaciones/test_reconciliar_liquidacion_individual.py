"""Tests de ReconciliarLiquidacionIndividual — orquestación best-effort para
una sola liquidación (disparada al abrir su detalle). Cada motivo de "no hacer
nada" tiene que devolver `reconciliada=False` sin levantar excepción — abrir el
detalle nunca puede fallar por esto. Excepción: estado terminal ya no es un
"no hacer nada" — delega en `ReconciliarLiquidacion`, que igual intenta traer
extra/factura (ver ese módulo)."""

import uuid
from datetime import date

from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacion,
    ReconciliarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reconciliar_liquidacion_individual import (
    ReconciliarLiquidacionIndividual,
    ReconciliarLiquidacionIndividualPorts,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_APROBADA
from src.modules.liquidaciones.domain.services.numeracion_ayc import numero_liquidacion
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdLiquidacion,
    CdLiquidacionDetalle,
)
from src.shared.domain.errors import ExternalServiceError
from tests.unit.domain.liquidaciones.factories import (
    make_liquidacion,
    make_prestador,
    reglas_activas_default,
)
from tests.unit.domain.liquidaciones.fakes import (
    FakePrestadorRepository,
    FakeReglaAlertaRepository,
    FakeSpstRepository,
    FakeTablaKmRepository,
    FakeTarifarioRepository,
)
from tests.unit.domain.liquidaciones.fakes_liquidacion import (
    FakeAlertaRepository,
    FakeIncidenteRepository,
    FakeLiquidacionRepository,
    FakeObservacionRepository,
)

CD_ID = 1310


class FakeCdGateway:
    def __init__(self) -> None:
        self.liquidaciones_por_empresa: dict[int, list[CdLiquidacion]] = {}
        self.detalle_falla = False
        self.detalles_pedidos: list[int] = []
        self.detalle: CdLiquidacionDetalle | None = None

    async def get_liquidaciones(self, empresa_cd_id: int, top: int = 200) -> list[CdLiquidacion]:
        return self.liquidaciones_por_empresa.get(empresa_cd_id, [])

    async def get_incidentes(self, liquidacion_id: int):
        self.detalles_pedidos.append(liquidacion_id)
        if self.detalle_falla:
            raise ExternalServiceError("getLiquidationDetails falló")
        return []

    async def get_detalle(self, liquidacion_ayc_id: int):
        return self.detalle


def make_cd_liq(ayc_id: int, *, cant_incidentes: int = 0) -> CdLiquidacion:
    return CdLiquidacion(
        id=ayc_id,
        prestador_cd_id=CD_ID,
        numero_liquidacion=numero_liquidacion(ayc_id),
        fecha_liquidacion=date(2026, 1, 1),
        estado="Recibida",
        cant_incidentes=cant_incidentes,
    )


class World:
    def __init__(self) -> None:
        self.prestador = make_prestador(cd_prestador_id=CD_ID)
        self.prestadores = FakePrestadorRepository({self.prestador.id: self.prestador})
        self.liquidaciones = FakeLiquidacionRepository()
        self.incidentes = FakeIncidenteRepository()
        self.gateway = FakeCdGateway()
        reanalizar = ReanalizarLiquidacion(
            ReanalizarLiquidacionPorts(
                liquidaciones=self.liquidaciones,
                incidentes=self.incidentes,
                alertas=FakeAlertaRepository(),
                observaciones=FakeObservacionRepository(),
                reglas=FakeReglaAlertaRepository(reglas_activas_default()),
                tablas_km=FakeTablaKmRepository(),
                spsts=FakeSpstRepository(),
                tarifarios=FakeTarifarioRepository(),
            )
        )
        reconciliar = ReconciliarLiquidacion(
            ReconciliarLiquidacionPorts(
                incidentes=self.incidentes,
                liquidaciones=self.liquidaciones,
                reanalizar=reanalizar,
                cd_gateway=self.gateway,
            )
        )
        self.use_case = ReconciliarLiquidacionIndividual(
            ReconciliarLiquidacionIndividualPorts(
                liquidaciones=self.liquidaciones,
                prestadores=self.prestadores,
                cd_gateway=self.gateway,
                reconciliar=reconciliar,
            )
        )

    def con_liquidacion(self, **overrides: object):
        liq = make_liquidacion(prestador_id=self.prestador.id, **overrides)
        self.liquidaciones.rows[liq.id] = liq
        return liq


async def test_liquidacion_no_encontrada_no_reconcilia() -> None:
    world = World()

    resultado = await world.use_case.execute(uuid.uuid4())

    assert resultado.reconciliada is False


async def test_sin_numero_liquidacion_no_reconcilia() -> None:
    world = World()
    liq = world.con_liquidacion(numero_liquidacion=None)

    resultado = await world.use_case.execute(liq.id)

    assert resultado.reconciliada is False
    assert world.gateway.detalles_pedidos == []


async def test_estado_terminal_no_pide_incidentes_pero_reconcilia_extra_y_factura() -> None:
    world = World()
    liq = world.con_liquidacion(
        numero_liquidacion=numero_liquidacion(1), estado=ESTADO_APROBADA
    )
    world.gateway.liquidaciones_por_empresa[CD_ID] = [make_cd_liq(1)]

    resultado = await world.use_case.execute(liq.id)

    assert resultado.reconciliada is True
    assert resultado.estado_actualizado is False
    assert world.gateway.detalles_pedidos == []
    assert world.liquidaciones.rows[liq.id].estado == ESTADO_APROBADA


async def test_estado_terminal_actualiza_factura_si_ayc_la_reporta() -> None:
    world = World()
    liq = world.con_liquidacion(
        numero_liquidacion=numero_liquidacion(1), estado=ESTADO_APROBADA, numero_factura=None
    )
    world.gateway.liquidaciones_por_empresa[CD_ID] = [make_cd_liq(1)]
    world.gateway.detalle = CdLiquidacionDetalle(
        concepto_extra=None, monto_extra=None, numero_factura="2-1575"
    )

    resultado = await world.use_case.execute(liq.id)

    assert resultado.factura_actualizada is True
    assert world.liquidaciones.rows[liq.id].numero_factura == "2-1575"
    assert world.liquidaciones.rows[liq.id].estado == ESTADO_APROBADA
    assert world.gateway.detalles_pedidos == []


async def test_prestador_sin_vinculo_cd_no_reconcilia() -> None:
    world = World()
    world.prestador = make_prestador(cd_prestador_id=None)
    world.prestadores.rows[world.prestador.id] = world.prestador
    liq = world.con_liquidacion(numero_liquidacion=numero_liquidacion(1), estado="recibida")

    resultado = await world.use_case.execute(liq.id)

    assert resultado.reconciliada is False


async def test_ayc_no_reporta_esta_liquidacion_no_reconcilia() -> None:
    world = World()
    liq = world.con_liquidacion(numero_liquidacion=numero_liquidacion(1), estado="recibida")
    world.gateway.liquidaciones_por_empresa[CD_ID] = [make_cd_liq(999)]  # otro numero

    resultado = await world.use_case.execute(liq.id)

    assert resultado.reconciliada is False
    assert world.gateway.detalles_pedidos == []


async def test_soap_de_detalle_falla_no_reconcilia() -> None:
    world = World()
    liq = world.con_liquidacion(numero_liquidacion=numero_liquidacion(1), estado="recibida")
    world.gateway.liquidaciones_por_empresa[CD_ID] = [make_cd_liq(1)]
    world.gateway.detalle_falla = True

    resultado = await world.use_case.execute(liq.id)

    assert resultado.reconciliada is False
    assert world.gateway.detalles_pedidos == [1]


async def test_happy_path_delega_en_reconciliar_liquidacion() -> None:
    world = World()
    liq = world.con_liquidacion(numero_liquidacion=numero_liquidacion(1), estado="recibida")
    world.gateway.liquidaciones_por_empresa[CD_ID] = [make_cd_liq(1, cant_incidentes=0)]

    resultado = await world.use_case.execute(liq.id)

    assert resultado.reconciliada is True
    assert world.gateway.detalles_pedidos == [1]
