"""Tests de SincronizarLiquidaciones — dedup por numero_liquidacion, guardia de
detalle vacío (`fallidas`, hallazgo H-2), conteo real de `sin_prestador` (H-3),
filtro por prestador (H-5) y exclusión de inactivos (H-6, vía el fake que espeja
el contrato de `list_con_cd_id`)."""

import dataclasses
from datetime import date

from src.modules.liquidaciones.application.use_cases._cd_mapping import a_importado
from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacion,
    ReconciliarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.sincronizar_liquidaciones import (
    SincronizarLiquidaciones,
    SincronizarLiquidacionesPorts,
)
from src.modules.liquidaciones.domain.services.numeracion_ayc import numero_liquidacion
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdIncidenteRow,
    CdLiquidacion,
)
from src.shared.domain.errors import ExternalServiceError
from tests.unit.domain.liquidaciones.factories import (
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


def make_cd_liquidacion(liq_id: int, *, cant_incidentes: int = 1) -> CdLiquidacion:
    return CdLiquidacion(
        id=liq_id,
        prestador_cd_id=1310,
        numero_liquidacion=numero_liquidacion(liq_id),
        fecha_liquidacion=date(2026, 8, 6),
        estado="Cerrada",
        cant_incidentes=cant_incidentes,
    )


def make_cd_incidente(inc_id: int = 1) -> CdIncidenteRow:
    return CdIncidenteRow(
        id=inc_id,
        tipo="Correctivo",
        empresa_nombre="Empresa Test",
        sucursal_nombre="Sucursal Test",
        nro_serie="SN-1",
        fecha_cierre=date(2026, 7, 30),
        costo_servicio=1000.0,
        cant_km=0.0,
        costo_km=0.0,
        rubro="Impresoras",
        pasa_it=True,
    )


class FakeCdGateway:
    """Devuelve lo cargado por empresa; el detalle puede forzarse vacío o fallido
    para simular el 502 de Cloudflare que motivó la guardia de `fallidas`."""

    def __init__(self) -> None:
        self.liquidaciones_por_empresa: dict[int, list[CdLiquidacion]] = {}
        self.incidentes_por_liq: dict[int, list[CdIncidenteRow]] = {}
        self.detalles_fallidos: set[int] = set()
        self.detalles_pedidos: list[int] = []

    async def get_liquidaciones(
        self, empresa_cd_id: int, top: int = 200
    ) -> list[CdLiquidacion]:
        return self.liquidaciones_por_empresa.get(empresa_cd_id, [])

    async def get_incidentes(self, liquidacion_id: int) -> list[CdIncidenteRow]:
        self.detalles_pedidos.append(liquidacion_id)
        if liquidacion_id in self.detalles_fallidos:
            raise ExternalServiceError(f"getLiquidationDetails(id={liquidacion_id}) falló")
        return self.incidentes_por_liq.get(liquidacion_id, [])

    async def get_detalle(self, liquidacion_ayc_id: int):
        return None


class World:
    def __init__(self) -> None:
        self.gateway = FakeCdGateway()
        self.prestadores = FakePrestadorRepository()
        self.liquidaciones = FakeLiquidacionRepository()
        self.incidentes = FakeIncidenteRepository()
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
        self.use_case = SincronizarLiquidaciones(
            SincronizarLiquidacionesPorts(
                cd_gateway=self.gateway,
                prestadores=self.prestadores,
                liquidaciones=self.liquidaciones,
                incidentes=self.incidentes,
                reanalizar=reanalizar,
                reconciliar=reconciliar,
            )
        )

    def con_prestador_vinculado(self, cd_id: int = 1310, **overrides: object):
        prestador = make_prestador(cd_prestador_id=cd_id, **overrides)
        self.prestadores.rows[prestador.id] = prestador
        return prestador


async def test_crea_las_nuevas_y_saltea_las_existentes() -> None:
    world = World()
    prestador = world.con_prestador_vinculado()
    world.gateway.liquidaciones_por_empresa[1310] = [
        make_cd_liquidacion(3922),
        make_cd_liquidacion(3894),
    ]
    world.gateway.incidentes_por_liq = {3922: [make_cd_incidente()], 3894: [make_cd_incidente(2)]}
    # 3922-4 ya existe (importada por CSV con el dv real 3-1-3-1)
    await world.liquidaciones.create(
        prestador_id=prestador.id, numero_liquidacion="3922-4", periodo="2026-07",
        tipo_liquidacion="regular", nombre_archivo=None, total_incidentes=1, total_importe=1.0,
    )

    resultado = await world.use_case.execute()

    assert resultado.creadas == 1
    assert resultado.ya_existentes == 1
    assert resultado.fallidas == 0
    # a diferencia de ADR-015 §4 (aditivo puro), ahora el detalle SOAP también
    # se pide para la existente pendiente (3922) — se reconcilia, no se saltea.
    assert set(world.gateway.detalles_pedidos) == {3894, 3922}
    assert resultado.reconciliadas == 1
    numeros = await world.liquidaciones.list_numeros_liquidacion()
    assert numeros == {"3922-4", "3894-2"}


async def test_detalle_vacio_con_incidentes_declarados_no_crea_y_cuenta_fallida() -> None:
    """H-2: si el detalle vuelve vacío pero el listado declaraba incidentes (el 502
    de CF durante la validación), NO se crea una liquidación vacía permanente."""
    world = World()
    world.con_prestador_vinculado()
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894, cant_incidentes=6)]
    # sin incidentes_por_liq → get_incidentes devuelve []

    resultado = await world.use_case.execute()

    assert resultado.creadas == 0
    assert resultado.fallidas == 1
    assert await world.liquidaciones.list_numeros_liquidacion() == set()


async def test_detalle_vacio_declarado_vacio_si_se_crea() -> None:
    """Una liquidación que AyC declara con 0 incidentes es legítimamente vacía."""
    world = World()
    world.con_prestador_vinculado()
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894, cant_incidentes=0)]

    resultado = await world.use_case.execute()

    assert resultado.creadas == 1
    assert resultado.fallidas == 0


async def test_sin_prestador_cuenta_los_activos_sin_vinculo() -> None:
    """H-3: `sin_prestador` dejó de estar hardcodeado en 0."""
    world = World()
    world.con_prestador_vinculado()
    sin_vinculo = make_prestador(nombre_corto="SINCD", cd_prestador_id=None)
    world.prestadores.rows[sin_vinculo.id] = sin_vinculo
    inactivo = make_prestador(nombre_corto="BAJA", cd_prestador_id=None, activo=False)
    world.prestadores.rows[inactivo.id] = inactivo

    resultado = await world.use_case.execute()

    assert resultado.sin_prestador == 1  # el inactivo no cuenta


async def test_filtro_por_prestador_acota_el_sync() -> None:
    """H-5: con `prestador_id` solo se sincroniza ese prestador."""
    world = World()
    objetivo = world.con_prestador_vinculado(cd_id=1310, nombre_corto="JUNIN")
    world.con_prestador_vinculado(cd_id=1285, nombre_corto="SMTUC")
    world.gateway.liquidaciones_por_empresa = {
        1310: [make_cd_liquidacion(3894)],
        1285: [make_cd_liquidacion(3911)],
    }
    world.gateway.incidentes_por_liq = {3894: [make_cd_incidente()], 3911: [make_cd_incidente(2)]}

    resultado = await world.use_case.execute(objetivo.id)

    assert resultado.creadas == 1
    assert await world.liquidaciones.list_numeros_liquidacion() == {"3894-2"}


async def test_prestador_inactivo_con_cd_id_queda_fuera() -> None:
    """H-6: `list_con_cd_id` devuelve solo activos — la baja saca del sync."""
    world = World()
    world.con_prestador_vinculado(cd_id=1310, activo=False)
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894)]
    world.gateway.incidentes_por_liq = {3894: [make_cd_incidente()]}

    resultado = await world.use_case.execute()

    assert resultado.creadas == 0
    assert await world.liquidaciones.list_numeros_liquidacion() == set()


async def test_gateway_fallido_no_crea_y_cuenta_fallida() -> None:
    """Un fallo real del detalle SOAP (`ExternalServiceError`) tiene el mismo efecto
    que un detalle vacío: no se crea, se cuenta `fallidas`, se reintenta después."""
    world = World()
    world.con_prestador_vinculado()
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894, cant_incidentes=6)]
    world.gateway.detalles_fallidos.add(3894)

    resultado = await world.use_case.execute()

    assert resultado.creadas == 0
    assert resultado.fallidas == 1
    assert await world.liquidaciones.list_numeros_liquidacion() == set()


async def test_detalle_parcial_no_crea_y_cuenta_fallida() -> None:
    """Un detalle no vacío pero incompleto (filas descartadas en el parseo) tiene
    que atraparse igual que el vacío total — no solo `if not filas_cd`."""
    world = World()
    world.con_prestador_vinculado()
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894, cant_incidentes=3)]
    world.gateway.incidentes_por_liq[3894] = [make_cd_incidente(1), make_cd_incidente(2)]

    resultado = await world.use_case.execute()

    assert resultado.creadas == 0
    assert resultado.fallidas == 1
    assert await world.liquidaciones.list_numeros_liquidacion() == set()


async def test_anuladas_se_reportan_en_el_resultado() -> None:
    """`_detectar_y_eliminar_anuladas` ya calculaba `anuladas` pero `execute()` no lo
    sumaba al resultado final — el endpoint siempre reportaba 0 pese a borrar."""
    world = World()
    prestador = world.con_prestador_vinculado()
    await world.liquidaciones.create(
        prestador_id=prestador.id, numero_liquidacion="3894-2", periodo="2026-07",
        tipo_liquidacion="regular", nombre_archivo=None, total_incidentes=1, total_importe=1.0,
    )
    # AyC ya no reporta 3894 (anulada allá); sigue reportando otra vigente.
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3900, cant_incidentes=0)]

    resultado = await world.use_case.execute()

    assert resultado.anuladas == 1
    assert resultado.creadas == 1
    numeros = await world.liquidaciones.list_numeros_liquidacion()
    assert "3894-2" not in numeros
    assert len(numeros) == 1


async def test_permitir_eliminar_anuladas_false_nunca_borra() -> None:
    """El job de fondo llama con `permitir_eliminar_anuladas=False` — ni siquiera
    corre `_detectar_y_eliminar_anuladas`, aunque AyC ya no reporte la liquidación."""
    world = World()
    prestador = world.con_prestador_vinculado()
    await world.liquidaciones.create(
        prestador_id=prestador.id, numero_liquidacion="3894-2", periodo="2026-07",
        tipo_liquidacion="regular", nombre_archivo=None, total_incidentes=1, total_importe=1.0,
    )
    # AyC ya no reporta 3894 — con permitir_eliminar_anuladas=True esto la borraría.
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3900, cant_incidentes=0)]

    resultado = await world.use_case.execute(permitir_eliminar_anuladas=False)

    assert resultado.anuladas == 0
    numeros = await world.liquidaciones.list_numeros_liquidacion()
    assert "3894-2" in numeros


async def test_liquidacion_nueva_nace_abierta_y_vinculada_al_prestador() -> None:
    world = World()
    prestador = world.con_prestador_vinculado()
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894)]
    world.gateway.incidentes_por_liq = {3894: [make_cd_incidente()]}

    await world.use_case.execute()

    liq = next(iter(world.liquidaciones.rows.values()))
    assert liq.estado == "abierta"
    assert liq.prestador_id == prestador.id
    assert liq.numero_liquidacion == "3894-2"


async def test_liquidacion_cerrada_no_pide_detalle_ni_se_reconcilia() -> None:
    """Una liquidación ya cerrada queda totalmente afuera del cruce con AyC — ni
    se le pide el detalle SOAP ni se intenta reconciliar (no hay ningún estado
    más allá al que pueda avanzar)."""
    world = World()
    prestador = world.con_prestador_vinculado()
    creada = await world.liquidaciones.create(
        prestador_id=prestador.id, numero_liquidacion="3894-2", periodo="2026-07",
        tipo_liquidacion="regular", nombre_archivo=None, total_incidentes=1, total_importe=100.0,
    )
    await world.liquidaciones.update_estado(creada.id, "cerrada")
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894, cant_incidentes=1)]
    world.gateway.incidentes_por_liq = {3894: [make_cd_incidente()]}

    resultado = await world.use_case.execute()

    assert resultado.ya_existentes == 1
    assert resultado.reconciliadas == 0
    assert 3894 not in world.gateway.detalles_pedidos
    assert world.liquidaciones.rows[creada.id].total_importe == 100.0


async def test_liquidacion_aprobada_avanza_a_cerrada_sin_pedir_detalle() -> None:
    """El bug reportado 2026-08-25: liquidaciones 3905-7/3906-6/3907-5 quedaban
    "Aprobada" para siempre porque el loop de sync las excluía del cruce con AyC
    antes de que ReconciliarLiquidacion pudiera evaluarlas. Ahora sí se cruzan
    (sin pedirles el detalle de incidentes, no hace falta) y su estado avanza
    a cerrada cuando AyC ya la reporta así."""
    world = World()
    prestador = world.con_prestador_vinculado()
    creada = await world.liquidaciones.create(
        prestador_id=prestador.id, numero_liquidacion="3894-2", periodo="2026-07",
        tipo_liquidacion="regular", nombre_archivo=None, total_incidentes=1, total_importe=100.0,
    )
    await world.liquidaciones.update_estado(creada.id, "aprobada")
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894, cant_incidentes=1)]
    world.gateway.incidentes_por_liq = {3894: [make_cd_incidente()]}

    resultado = await world.use_case.execute()

    assert resultado.ya_existentes == 1
    assert resultado.reconciliadas == 1
    assert resultado.estados_actualizados == 1
    assert 3894 not in world.gateway.detalles_pedidos
    assert world.liquidaciones.rows[creada.id].estado == "cerrada"


async def test_ya_existente_pendiente_se_reconcilia_de_punta_a_punta() -> None:
    """Wiring completo: una liquidación `abierta` con un incidente cuyo costo
    cambió en AyC termina con el importe actualizado tras un solo `execute()`."""
    world = World()
    prestador = world.con_prestador_vinculado()
    creada = await world.liquidaciones.create(
        prestador_id=prestador.id, numero_liquidacion="3894-2", periodo="2026-07",
        tipo_liquidacion="regular", nombre_archivo=None, total_incidentes=1, total_importe=500.0,
    )
    viejo = dataclasses.replace(
        a_importado(make_cd_incidente(2)),
        costo_servicio_cobrado=500.0, total_viaje_cobrado=0.0, costo_total_cobrado=500.0,
    )
    await world.incidentes.bulk_create(creada.id, [viejo])
    world.gateway.liquidaciones_por_empresa[1310] = [make_cd_liquidacion(3894, cant_incidentes=1)]
    world.gateway.incidentes_por_liq = {3894: [make_cd_incidente(2)]}  # ahora cuesta 1000.0

    resultado = await world.use_case.execute()

    assert resultado.reconciliadas == 1
    assert world.liquidaciones.rows[creada.id].total_importe == 1000.0
