"""Tests de BackfillEstadoLiquidaciones — actualiza estado local desde wsAyC.

Solo toca liquidaciones con estado='abierta'. dry_run=True cuenta sin escribir.
"""

from datetime import date
from uuid import UUID

from src.modules.liquidaciones.application.use_cases.backfill_estado_liquidaciones import (
    BackfillEstadoLiquidaciones,
    BackfillEstadoLiquidacionesPorts,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_ABIERTA
from src.modules.liquidaciones.domain.services.numeracion_ayc import numero_liquidacion
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import CdLiquidacion
from tests.unit.domain.liquidaciones.factories import make_liquidacion, make_prestador
from tests.unit.domain.liquidaciones.fakes import (
    FakeCdLiquidacionesGateway,
    FakeLiquidacionRepository,
    FakePrestadorRepository,
)

CD_ID = 504


def make_cd_liq(ayc_id: int, estado: str = "Cerrada") -> CdLiquidacion:
    return CdLiquidacion(
        id=ayc_id,
        prestador_cd_id=CD_ID,
        numero_liquidacion=numero_liquidacion(ayc_id),
        fecha_liquidacion=date(2026, 1, 1),
        estado=estado,
        cant_incidentes=1,
    )


class World:
    def __init__(self) -> None:
        self.prestador = make_prestador(cd_prestador_id=CD_ID)
        self.prestadores = FakePrestadorRepository({self.prestador.id: self.prestador})
        self.liquidaciones = FakeLiquidacionRepository()
        self.gateway = FakeCdLiquidacionesGateway()
        self.use_case = BackfillEstadoLiquidaciones(
            BackfillEstadoLiquidacionesPorts(
                cd_gateway=self.gateway,
                prestadores=self.prestadores,
                liquidaciones=self.liquidaciones,
            )
        )

    def add_liq(self, ayc_id: int, estado: str = ESTADO_ABIERTA) -> UUID:
        liq = make_liquidacion(
            prestador_id=self.prestador.id,
            numero_liquidacion=numero_liquidacion(ayc_id),
            estado=estado,
        )
        self.liquidaciones.rows[liq.id] = liq
        return liq.id

    def add_ayc_liq(self, ayc_id: int, estado: str = "Cerrada") -> None:
        self.gateway.liquidaciones_por_empresa.setdefault(CD_ID, []).append(
            make_cd_liq(ayc_id, estado)
        )


async def test_dry_run_no_escribe_en_db() -> None:
    world = World()
    liq_id = world.add_liq(1)
    world.add_ayc_liq(1, "Cerrada")

    resultado = await world.use_case.execute(dry_run=True)

    assert resultado.dry_run is True
    assert resultado.total_actualizadas == 1
    assert world.liquidaciones.rows[liq_id].estado == ESTADO_ABIERTA  # sin cambio


async def test_actualiza_abierta_con_estado_real_de_ayc() -> None:
    world = World()
    liq_id = world.add_liq(10)
    world.add_ayc_liq(10, "Aprobada")

    resultado = await world.use_case.execute(dry_run=False)

    assert resultado.total_actualizadas == 1
    assert resultado.por_estado_destino == {"aprobada": 1}
    assert world.liquidaciones.rows[liq_id].estado == "aprobada"


async def test_respeta_liquidaciones_no_abierta() -> None:
    world = World()
    world.add_liq(20, estado="aprobada")  # manual de la TL — no debe tocarse
    world.add_ayc_liq(20, "Cerrada")

    resultado = await world.use_case.execute(dry_run=False)

    assert resultado.total_actualizadas == 0  # list_filtered(estado=abierta) no la devuelve


async def test_sin_match_en_ayc_incrementa_sin_match() -> None:
    world = World()
    world.add_liq(30)  # local, abierta
    # gateway devuelve lista vacía → no hay match

    resultado = await world.use_case.execute(dry_run=False)

    assert resultado.total_actualizadas == 0
    assert resultado.prestadores[0].sin_match == 1


async def test_estado_ayc_desconocido_se_salta() -> None:
    world = World()
    world.add_liq(40)
    world.add_ayc_liq(40, "EstadoRaro")

    resultado = await world.use_case.execute(dry_run=False)

    assert resultado.total_actualizadas == 0
    assert resultado.prestadores[0].saltadas == 1


async def test_filtra_por_prestador_id() -> None:
    world = World()
    otro_prestador = make_prestador(cd_prestador_id=999)
    world.prestadores.rows[otro_prestador.id] = otro_prestador

    liq_principal = make_liquidacion(
        prestador_id=world.prestador.id,
        numero_liquidacion=numero_liquidacion(50),
        estado=ESTADO_ABIERTA,
    )
    liq_otro = make_liquidacion(
        prestador_id=otro_prestador.id,
        numero_liquidacion=numero_liquidacion(51),
        estado=ESTADO_ABIERTA,
    )
    world.liquidaciones.rows[liq_principal.id] = liq_principal
    world.liquidaciones.rows[liq_otro.id] = liq_otro
    world.add_ayc_liq(50, "Cerrada")

    resultado = await world.use_case.execute(
        dry_run=False, prestador_id=world.prestador.id
    )

    assert len(resultado.prestadores) == 1
    assert resultado.prestadores[0].prestador_id == str(world.prestador.id)
    assert world.liquidaciones.rows[liq_otro.id].estado == ESTADO_ABIERTA  # intacta
