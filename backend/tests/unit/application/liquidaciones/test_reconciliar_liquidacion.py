"""Tests de ReconciliarLiquidacion — identidad de `incidente_id` preservada tras
un cambio (nunca borrar y recrear), el triage de la TL sobrevive a un cambio pero
no a una baja, y los guards que protegen contra reconciliar liquidaciones
terminales o con datos incompletos/sospechosos."""

from datetime import date

from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacion,
    ReconciliarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_APROBADA, ESTADO_CERRADA
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdLiquidacion,
    CdLiquidacionDetalle,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import IncidenteImportado
from tests.unit.domain.liquidaciones.factories import (
    make_incidente,
    make_liquidacion,
    make_tarifario,
    reglas_activas_default,
)
from tests.unit.domain.liquidaciones.fakes import (
    FakeCdLiquidacionesGateway,
    FakeReglaAlertaRepository,
    FakeTablaKmRepository,
    FakeTarifarioRepository,
)
from tests.unit.domain.liquidaciones.fakes_liquidacion import (
    FakeAlertaRepository,
    FakeIncidenteRepository,
    FakeLiquidacionRepository,
)

_FECHA = date(2026, 1, 15)


def make_cd_liq(
    cant_incidentes: int, *, estado: str = "Recibida", estado_id: int | None = None
) -> CdLiquidacion:
    return CdLiquidacion(
        id=1,
        prestador_cd_id=1310,
        numero_liquidacion="1-1",
        fecha_liquidacion=_FECHA,
        estado=estado,
        cant_incidentes=cant_incidentes,
        estado_id=estado_id,
    )


def make_remoto(numero_incidente: str, **overrides: object) -> IncidenteImportado:
    base: dict[str, object] = dict(
        numero_incidente=numero_incidente,
        rubro="Impresoras",
        tipo="correctivo",
        empresa_nombre="Empresa Test",
        sucursal_nombre="Sucursal Test",
        nro_serie="SN-1",
        fecha_cierre=_FECHA,
        costo_servicio_cobrado=1500.0,
        cant_km_cobrado=0.0,
        costo_km_cobrado=0.0,
        total_viaje_cobrado=0.0,
        costo_total_cobrado=1500.0,
        pasa_it=True,
    )
    base.update(overrides)
    return IncidenteImportado(**base)  # type: ignore[arg-type]


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.incidentes = FakeIncidenteRepository()
        self.alertas = FakeAlertaRepository()
        self.tarifarios = FakeTarifarioRepository()
        self.cd_gateway = FakeCdLiquidacionesGateway()
        self.reanalizar = ReanalizarLiquidacion(
            ReanalizarLiquidacionPorts(
                liquidaciones=self.liquidaciones,
                incidentes=self.incidentes,
                alertas=self.alertas,
                reglas=FakeReglaAlertaRepository(reglas_activas_default()),
                tablas_km=FakeTablaKmRepository(),
                tarifarios=self.tarifarios,
            )
        )
        self.use_case = ReconciliarLiquidacion(
            ReconciliarLiquidacionPorts(
                incidentes=self.incidentes,
                liquidaciones=self.liquidaciones,
                reanalizar=self.reanalizar,
                cd_gateway=self.cd_gateway,
            )
        )

    def con_liquidacion(self, **overrides: object):
        liq = make_liquidacion(**overrides)
        self.liquidaciones.rows[liq.id] = liq
        return liq

    def con_incidente(self, liquidacion_id, **overrides: object):
        kwargs: dict[str, object] = {"fecha_cierre": _FECHA, **overrides}
        inc = make_incidente(liquidacion_id=liquidacion_id, **kwargs)
        self.incidentes.rows[inc.id] = inc
        return inc


async def test_cambio_actualiza_in_place_preservando_el_id() -> None:
    world = World()
    liq = world.con_liquidacion()
    local = world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=1000.0)
    remoto = make_remoto("1", costo_servicio_cobrado=1500.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.reconciliada is True
    assert resultado.cambios == 1
    assert list(world.incidentes.rows.keys()) == [local.id]
    actualizado = world.incidentes.rows[local.id]
    assert actualizado.costo_servicio_cobrado == 1500.0

    liq_actualizada = world.liquidaciones.rows[liq.id]
    assert liq_actualizada.total_incidentes == 1
    assert liq_actualizada.total_importe == 1500.0


async def test_periodo_se_recalcula_cuando_cierran_incidentes_de_otro_mes() -> None:
    """Caso real: la liquidación se creó con período '2026-03' (fallback, porque
    ninguno de sus incidentes tenía `fecha_cierre` todavía) y luego se cerraron en
    abril/junio — sin este recálculo el período quedaba congelado en '2026-03' aunque
    incidentes/importe sí se reconciliaran bien."""
    world = World()
    liq = world.con_liquidacion(periodo="2026-03")
    world.con_incidente(
        liq.id, numero_incidente="1", fecha_cierre=date(2026, 4, 15), costo_servicio_cobrado=1500.0
    )
    remoto_1 = make_remoto("1", fecha_cierre=date(2026, 4, 15), costo_servicio_cobrado=1500.0)
    remoto_2 = make_remoto("2", fecha_cierre=date(2026, 6, 18), costo_servicio_cobrado=1500.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(2), [remoto_1, remoto_2])

    assert resultado.periodo_actualizado is True
    assert world.liquidaciones.rows[liq.id].periodo == "2026-06"


async def test_periodo_no_se_toca_cuando_ya_coincide() -> None:
    """`_FECHA` (los incidentes de este `World`) es enero 2026 — el período ya
    está bien, así que reconciliar sin diff no debe tocar nada."""
    world = World()
    liq = world.con_liquidacion(periodo="2026-01")
    world.con_incidente(
        liq.id,
        numero_incidente="1",
        costo_servicio_cobrado=1500.0,
        nro_serie="SN-1",
        cant_km_cobrado=0.0,
        costo_km_cobrado=0.0,
        total_viaje_cobrado=0.0,
        costo_total_cobrado=1500.0,
    )
    remoto = make_remoto("1", costo_servicio_cobrado=1500.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert (resultado.altas, resultado.cambios, resultado.bajas) == (0, 0, 0)
    assert resultado.periodo_actualizado is False
    assert world.liquidaciones.rows[liq.id].periodo == "2026-01"


async def test_periodo_se_corrige_aunque_no_haya_diff_de_incidentes() -> None:
    """El caso real que motivó este recálculo (liquidación 3935-8, Tres Arroyos,
    agosto 2026): los incidentes locales ya tenían la `fecha_cierre` correcta y
    coincidían exactamente con lo que reporta AyC (sin diff, por eso `_aplicar`
    nunca corría) — pero el período había quedado fijado por el fallback de
    `extraer_periodo` al crear la liquidación, con sus incidentes todavía
    abiertos, y nada volvía a tocarlo. El recálculo tiene que correr también en
    el camino sin novedades."""
    world = World()
    liq = world.con_liquidacion(periodo="2026-03")
    world.con_incidente(
        liq.id,
        numero_incidente="1",
        fecha_cierre=date(2026, 4, 15),
        costo_servicio_cobrado=1500.0,
        nro_serie="SN-1",
        cant_km_cobrado=0.0,
        costo_km_cobrado=0.0,
        total_viaje_cobrado=0.0,
        costo_total_cobrado=1500.0,
    )
    remoto = make_remoto("1", fecha_cierre=date(2026, 4, 15), costo_servicio_cobrado=1500.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert (resultado.altas, resultado.cambios, resultado.bajas) == (0, 0, 0)
    assert resultado.periodo_actualizado is True
    assert world.liquidaciones.rows[liq.id].periodo == "2026-04"


async def test_alta_crea_incidente_nuevo() -> None:
    world = World()
    liq = world.con_liquidacion()
    remoto = make_remoto("1", costo_servicio_cobrado=1500.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.altas == 1
    [creado] = await world.incidentes.list_by_liquidacion(liq.id)
    assert creado.numero_incidente == "1"


async def test_sin_diferencias_no_toca_nada_pero_reconcilia() -> None:
    world = World()
    liq = world.con_liquidacion(estado="recibida", total_incidentes=1, total_importe=1500.0)
    world.con_incidente(
        liq.id,
        numero_incidente="1",
        costo_servicio_cobrado=1500.0,
        nro_serie="SN-1",
        cant_km_cobrado=0.0,
        costo_km_cobrado=0.0,
        total_viaje_cobrado=0.0,
        costo_total_cobrado=1500.0,
    )
    remoto = make_remoto("1", costo_servicio_cobrado=1500.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1, estado="Recibida"), [remoto])

    assert resultado.reconciliada is True
    assert (resultado.altas, resultado.cambios, resultado.bajas) == (0, 0, 0)
    assert resultado.estado_actualizado is False
    assert world.liquidaciones.rows[liq.id].estado == "recibida"


async def test_triage_sobrevive_a_un_cambio() -> None:
    """El caso central del diseño: la TL descartó una alerta ALT001 sobre un
    incidente; AyC corrige un dato no económico del mismo incidente (nro_serie);
    tras reconciliar, la alerta se regenera (mismo incidente, sigue habiendo
    diferencia de precio) y conserva el descarte — mismo mecanismo que ya prueba
    `test_reanalizar_preserva_el_triage_de_la_tl`, acá disparado por
    `ReconciliarLiquidacion` en vez de un `ReanalizarLiquidacion` manual."""
    world = World()
    liq = world.con_liquidacion()
    world.tarifarios.rows = [make_tarifario(prestador_id=liq.prestador_id, costo_servicio=1500.0)]
    local = world.con_incidente(
        liq.id, numero_incidente="1", costo_servicio_cobrado=1800.0, nro_serie="SN-OLD"
    )
    await world.reanalizar.execute(liq.id)
    [alerta] = world.alertas.por_liquidacion[liq.id]
    assert alerta.tipo_alerta == "ALT001"
    await world.alertas.update_estado(
        liq.id, alerta.id, estado="descartada", justificacion="acordado con el PST"
    )

    remoto = make_remoto("1", costo_servicio_cobrado=1800.0, nro_serie="SN-NEW")
    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.cambios == 1
    assert world.incidentes.rows[local.id].nro_serie == "SN-NEW"
    [regenerada] = world.alertas.por_liquidacion[liq.id]
    assert regenerada.tipo_alerta == "ALT001"
    assert regenerada.estado == "descartada"
    assert regenerada.justificacion == "acordado con el PST"


async def test_triage_no_sobrevive_a_una_baja() -> None:
    """El incidente con la alerta descartada deja de existir del lado de AyC —
    se borra, y con él (vía `ReanalizarLiquidacion`, que ya no lo evalúa) su
    alerta descartada. Los otros dos incidentes no se tocan (33% de bajas, bajo
    el umbral de 50% que aborta por sospecha de mismatch masivo)."""
    world = World()
    liq = world.con_liquidacion()
    world.tarifarios.rows = [make_tarifario(prestador_id=liq.prestador_id, costo_servicio=1500.0)]
    a_borrar = world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=1800.0)
    world.con_incidente(liq.id, numero_incidente="2", costo_servicio_cobrado=1500.0)
    world.con_incidente(liq.id, numero_incidente="3", costo_servicio_cobrado=1500.0)
    await world.reanalizar.execute(liq.id)
    [alerta] = world.alertas.por_liquidacion[liq.id]
    await world.alertas.update_estado(
        liq.id, alerta.id, estado="descartada", justificacion="acordado con el PST"
    )

    remotos = [
        make_remoto("2", costo_servicio_cobrado=1500.0),
        make_remoto("3", costo_servicio_cobrado=1500.0),
    ]
    resultado = await world.use_case.execute(liq, make_cd_liq(2), remotos)

    assert resultado.bajas == 1
    assert a_borrar.id not in world.incidentes.rows
    assert world.alertas.por_liquidacion[liq.id] == []


async def test_guard_estado_terminal_no_toca_incidentes_ni_estado() -> None:
    world = World()
    liq = world.con_liquidacion(estado=ESTADO_APROBADA)
    local = world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=1000.0)
    remoto = make_remoto("1", costo_servicio_cobrado=9999.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.altas == 0
    assert resultado.cambios == 0
    assert resultado.bajas == 0
    assert resultado.estado_actualizado is False
    assert world.incidentes.rows[local.id].costo_servicio_cobrado == 1000.0
    assert world.liquidaciones.rows[liq.id].estado == ESTADO_APROBADA


async def test_estado_terminal_igual_trae_factura_y_extra_de_ayc() -> None:
    """El caso real que motivó separar el guard: en AyC la factura se carga en
    el mismo momento en que se aprueba la liquidación — si esto también
    quedara bloqueado, ese dato nunca llegaría a sincronizarse."""
    world = World()
    liq = world.con_liquidacion(
        estado=ESTADO_APROBADA, numero_factura=None, concepto_extra=None, monto_extra=None
    )
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra="Adicional", monto_extra=500.0, numero_factura="2-1575"
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [])

    assert resultado.reconciliada is True
    assert resultado.extra_actualizado is True
    assert resultado.factura_actualizada is True
    actualizada = world.liquidaciones.rows[liq.id]
    assert actualizada.numero_factura == "2-1575"
    assert actualizada.concepto_extra == "Adicional"
    assert actualizada.monto_extra == 500.0
    assert actualizada.estado == ESTADO_APROBADA


async def test_aprobada_avanza_a_cerrada_cuando_ayc_ya_la_cierra() -> None:
    """El bug reportado 2026-08-25: liquidaciones que AyC cerraba después de
    aprobarlas quedaban mostrando "Aprobada" para siempre porque el guard de
    estado terminal las trataba como igualmente congeladas."""
    world = World()
    liq = world.con_liquidacion(estado=ESTADO_APROBADA)

    resultado = await world.use_case.execute(liq, make_cd_liq(1, estado="Cerrada"), [])

    assert resultado.estado_actualizado is True
    assert world.liquidaciones.rows[liq.id].estado == ESTADO_CERRADA


async def test_cerrada_nunca_se_reabre() -> None:
    world = World()
    liq = world.con_liquidacion(estado=ESTADO_CERRADA)

    resultado = await world.use_case.execute(liq, make_cd_liq(1, estado="Aprobada"), [])

    assert resultado.estado_actualizado is False
    assert world.liquidaciones.rows[liq.id].estado == ESTADO_CERRADA


async def test_extra_se_suma_al_total_importe() -> None:
    """El bug reportado 2026-08-25 (liquidación 3907-5, San Juan): el extra
    cargado por AyC no se reflejaba en total_importe, así que listado y
    dashboard seguían mostrando el total viejo."""
    world = World()
    liq = world.con_liquidacion(total_importe=1500.0, total_incidentes=1)
    world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=1500.0)
    remoto = make_remoto("1", costo_servicio_cobrado=1500.0)
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra="Adicional", monto_extra=500.0, numero_factura=None
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.extra_actualizado is True
    actualizada = world.liquidaciones.rows[liq.id]
    assert actualizada.monto_extra == 500.0
    assert actualizada.total_importe == 2000.0


async def test_incidentes_y_extra_cambian_en_la_misma_pasada_no_se_pisan() -> None:
    """El ajuste por extra tiene que partir del total ya recalculado por el
    diff de incidentes de esta misma pasada — si partiera del total previo a
    ese recálculo, pisaría el cambio de incidentes."""
    world = World()
    liq = world.con_liquidacion(
        total_importe=1600.0, total_incidentes=1, concepto_extra="Adicional", monto_extra=100.0
    )
    world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=1500.0)
    remoto = make_remoto("1", costo_servicio_cobrado=2000.0, costo_total_cobrado=2000.0)
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra="Adicional", monto_extra=300.0, numero_factura=None
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.cambios == 1
    assert resultado.extra_actualizado is True
    actualizada = world.liquidaciones.rows[liq.id]
    assert actualizada.total_importe == 2300.0


async def test_guard_cantidad_declarada_no_coincide_no_reconcilia() -> None:
    world = World()
    liq = world.con_liquidacion()
    local = world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=1000.0)
    remoto = make_remoto("1", costo_servicio_cobrado=9999.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(5), [remoto])

    assert resultado.reconciliada is False
    assert world.incidentes.rows[local.id].costo_servicio_cobrado == 1000.0


async def test_guard_bajas_masivas_aborta() -> None:
    """Con locales que ya no matchean nada (ej. cambio de formato de
    numero_incidente), el diff sería 100% bajas — abortar es más seguro que
    borrar en masa por un bug de matching."""
    world = World()
    liq = world.con_liquidacion()
    world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=1000.0)
    world.con_incidente(liq.id, numero_incidente="2", costo_servicio_cobrado=1000.0)
    remoto = make_remoto("999", costo_servicio_cobrado=1000.0)  # no matchea a nada local

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.reconciliada is False
    assert len(world.incidentes.rows) == 2


async def test_estado_se_pisa_con_el_que_reporta_ayc() -> None:
    world = World()
    liq = world.con_liquidacion(estado="abierta")
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1, estado="Recibida"), [remoto])

    assert resultado.estado_actualizado is True
    assert world.liquidaciones.rows[liq.id].estado == "recibida"


async def test_estado_se_pisa_por_estado_id_con_prioridad_sobre_el_nombre() -> None:
    world = World()
    liq = world.con_liquidacion(estado="recibida")
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)

    resultado = await world.use_case.execute(
        liq, make_cd_liq(1, estado="Recibida", estado_id=3), [remoto]
    )

    assert resultado.estado_actualizado is True
    assert world.liquidaciones.rows[liq.id].estado == "observada"


async def test_estado_puede_avanzar_a_terminal_via_reconciliacion() -> None:
    """La reconciliación puede mover una pendiente directo a `aprobada` — el
    guard de estado terminal mira el estado local *previo* a esta corrida, no
    el nuevo que trae AyC (ver docstring de ReconciliarLiquidacion)."""
    world = World()
    liq = world.con_liquidacion(estado="observada")
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)

    resultado = await world.use_case.execute(
        liq, make_cd_liq(1, estado="Aprobada", estado_id=4), [remoto]
    )

    assert resultado.reconciliada is True
    assert resultado.estado_actualizado is True
    assert world.liquidaciones.rows[liq.id].estado == "aprobada"


async def test_estado_ayc_desconocido_no_se_pisa() -> None:
    world = World()
    liq = world.con_liquidacion(estado="recibida")
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1, estado="Anulada"), [remoto])

    assert resultado.estado_actualizado is False
    assert world.liquidaciones.rows[liq.id].estado == "recibida"


async def test_extra_se_trae_desde_ayc() -> None:
    world = World()
    liq = world.con_liquidacion(concepto_extra=None, monto_extra=None)
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra="Adicional Factura NRO 0002-00001573",
        monto_extra=1499999.0,
        numero_factura=None,
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.extra_actualizado is True
    actualizada = world.liquidaciones.rows[liq.id]
    assert actualizada.concepto_extra == "Adicional Factura NRO 0002-00001573"
    assert actualizada.monto_extra == 1499999.0


async def test_extra_no_pisa_carga_manual_cuando_ayc_no_tiene_nada() -> None:
    """`get_detalle` trae `monto_extra=None` cuando AyC reporta `Extra="0"` —
    la carga manual de la TL (fallback acordado en P4) tiene que sobrevivir
    intacta."""
    world = World()
    liq = world.con_liquidacion(concepto_extra="Seguro de viaje", monto_extra=500.0)
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.extra_actualizado is False
    actualizada = world.liquidaciones.rows[liq.id]
    assert actualizada.concepto_extra == "Seguro de viaje"
    assert actualizada.monto_extra == 500.0


async def test_extra_sin_cambios_no_reporta_actualizacion() -> None:
    world = World()
    liq = world.con_liquidacion(concepto_extra="Ajuste", monto_extra=1000.0)
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra="Ajuste", monto_extra=1000.0, numero_factura=None
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.extra_actualizado is False


async def test_numero_factura_se_trae_desde_ayc() -> None:
    world = World()
    liq = world.con_liquidacion(numero_factura=None)
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra=None, monto_extra=None, numero_factura="2-1575"
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.factura_actualizada is True
    assert world.liquidaciones.rows[liq.id].numero_factura == "2-1575"


async def test_numero_factura_no_se_toca_cuando_ayc_no_la_reporta() -> None:
    """`FacturaLocal`/`FacturaNro` vacíos (liquidación aún no facturada) →
    `numero_factura=None` en `get_detalle` — no hay contraparte manual que
    preservar, pero tampoco hay nada que escribir."""
    world = World()
    liq = world.con_liquidacion(numero_factura=None)
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.factura_actualizada is False
    assert world.liquidaciones.rows[liq.id].numero_factura is None


async def test_numero_factura_sin_cambios_no_reporta_actualizacion() -> None:
    world = World()
    liq = world.con_liquidacion(numero_factura="2-1575")
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra=None, monto_extra=None, numero_factura="2-1575"
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.factura_actualizada is False


async def test_factura_pdf_url_no_se_recalcula_si_ya_estaba_seteada() -> None:
    """Bug real (liquidación 3951-6, 2026-09-04): `Fecha` de AyC en
    `getLiquidationById` no es estable — cambia entre reconciliaciones (p. ej.
    al aprobar la liquidación) sin ser la fecha real en que se cargó la
    factura. Recalcular `factura_pdf_url` con esa fecha en cada reconciliación
    pisaba una URL ya calculada con una fecha distinta y equivocada."""
    world = World()
    url_original = "https://webagentes.canaldirecto.com.ar/files/webagentes/liquidations/x.pdf"
    liq = world.con_liquidacion(numero_factura="2-1575", factura_pdf_url=url_original)
    remoto = make_remoto("1", costo_servicio_cobrado=1000.0)
    world.cd_gateway.detalles_por_liquidacion[1] = CdLiquidacionDetalle(
        concepto_extra=None,
        monto_extra=None,
        numero_factura="2-1575",
        fecha=date(2026, 9, 4),
        rs_prestador="Otro Prestador SRL",
    )

    resultado = await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert resultado.factura_actualizada is False
    assert world.liquidaciones.rows[liq.id].factura_pdf_url == url_original


async def test_reconciliar_pasa_a_abono_cuando_todo_queda_a_un_peso() -> None:
    """SAN JUAN: AyC deja todos los incidentes a $1 y carga el importe real como
    extra — la liquidación pasa a abono y el reanálisis deja de generar ALT001."""
    world = World()
    liq = world.con_liquidacion(tipo_liquidacion="regular")
    world.con_incidente(liq.id, numero_incidente="1", costo_servicio_cobrado=54400.0)
    world.tarifarios.rows = [make_tarifario(prestador_id=liq.prestador_id, costo_servicio=54400.0)]
    remoto = make_remoto("1", costo_servicio_cobrado=1.0, costo_total_cobrado=1.0)

    await world.use_case.execute(liq, make_cd_liq(1), [remoto])

    assert world.liquidaciones.rows[liq.id].tipo_liquidacion == "abono"
    alertas = world.alertas.por_liquidacion.get(liq.id, [])
    assert all(a.tipo_alerta != "ALT001" for a in alertas)
