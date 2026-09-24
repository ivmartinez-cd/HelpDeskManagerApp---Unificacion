"""Tests unitarios de los casos de uso de lectura de Despachados (listado, resumen, detalle
y estado de la actualización), con fakes en memoria.

`AHORA` es el jueves 24/09/2026 a las 12:00 en Argentina; el lunes 12/10/2026 es feriado.
"""

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

import pytest

from src.modules.insumos.application.dtos.despachados import (
    ConfigConsulta,
    CriterioListado,
    DetalleDespacho,
    EstadoActualizacion,
    ListadoDespachos,
)
from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ConsultaDespachosPorts,
    ConsultarActualizacion,
    ListarDespachos,
    ObtenerDetalleDespacho,
    ResumirDespachos,
)
from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionNueva,
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.domain.errores_despachados import EnvioDespachoNoEncontradoError
from src.modules.insumos.domain.value_objects.despachados.cambio_estado import CambioEstado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    FiltrosDespachos,
    Pagina,
    ResumenDespachos,
)
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    ARGENTINA,
    GUIA_A,
    GUIA_B,
    VERDE,
    FakeAccionesDespacho,
    FakeCalendarioFeriados,
    FakeEnviosDespacho,
    FakeRemitosDespacho,
    despacho,
    envio,
)

CONFIG = ConfigConsulta(dias_ventana=30, zona_horaria=ARGENTINA)
PAGINA = Pagina(limite=25, desplazamiento=50)
RESUMEN = ResumenDespachos(
    por_color=dict.fromkeys(ColorSemaforo, 1),
    alertas_rojas=1,
    alertas_naranjas=1,
    naranjas_sin_accion=0,
    limite_mas_proximo=date(2026, 9, 25),
    operativas=("434324",),
)


def fila(guia: str, color: ColorSemaforo = ColorSemaforo.VERDE, **cambios: Any) -> FilaDespacho:
    base = FilaDespacho(
        guia=guia,
        color=color,
        alerta_abierta=False,
        observacion="",
        fecha_limite=None,
        estado="En viaje",
        motivo="",
        sucursal_oca="Rosario",
        fecha_estado=date(2026, 9, 23),
        operativa="434324",
        cliente="Cliente Test",
        fecha_remito=date(2026, 9, 22),
        numero_remito=50001,
        cantidad_remitos=1,
        incidente="440001",
        cantidad_incidentes=1,
        ultima_accion=None,
        con_error=False,
    )
    return replace(base, **cambios)


def corrida(corrida_id: int, terminada_en: datetime | None) -> Corrida:
    return Corrida(
        id=corrida_id,
        origen=OrigenCorrida.PROGRAMADA,
        iniciada_en=datetime(2026, 9, 24, 13, corrida_id, tzinfo=UTC),
        usuario_nombre=None,
        terminada_en=terminada_en,
        resumen=ResumenCorrida(consultas_ok=corrida_id),
    )


class FakeConsultaDespachos:
    def __init__(self) -> None:
        self.filas: list[FilaDespacho] = []
        self.total = 0
        self.listados: list[tuple[FiltrosDespachos, Pagina]] = []
        self.contados: list[FiltrosDespachos] = []
        self.resumidos: list[date] = []

    async def listar(self, filtros: FiltrosDespachos, pagina: Pagina) -> list[FilaDespacho]:
        self.listados.append((filtros, pagina))
        return list(self.filas)

    async def contar(self, filtros: FiltrosDespachos) -> int:
        self.contados.append(filtros)
        return self.total

    async def resumir(self, alcance_desde: date) -> ResumenDespachos:
        self.resumidos.append(alcance_desde)
        return RESUMEN


class FakeHistorialConsulta:
    def __init__(self) -> None:
        self.cambios: dict[str, list[CambioEstado]] = {}

    async def registrar(self, guia: str, estado: EstadoOca, color: ColorSemaforo) -> None:
        raise AssertionError("una consulta no registra cambios")

    async def listar_por_guia(self, guia: str) -> list[CambioEstado]:
        return list(self.cambios.get(guia, []))


class FakeCorridasConsulta:
    def __init__(self, corridas: Sequence[Corrida] = ()) -> None:
        self.corridas = list(corridas)
        self.pedidos_de_terminada = 0

    async def iniciar(self, origen: OrigenCorrida, usuario_nombre: str | None) -> Corrida:
        raise AssertionError("una consulta no inicia corridas")

    async def terminar(self, corrida_id: int, resumen: ResumenCorrida) -> None:
        raise AssertionError("una consulta no termina corridas")

    async def cerrar_interrumpidas(self, motivo: str) -> int:
        raise AssertionError("una consulta no cierra corridas")

    async def ultima(self) -> Corrida | None:
        return self.corridas[-1] if self.corridas else None

    async def ultima_terminada(self) -> Corrida | None:
        self.pedidos_de_terminada += 1
        terminadas = [c for c in self.corridas if c.terminada_en is not None]
        return terminadas[-1] if terminadas else None


class MundoConsulta:
    def __init__(self, ahora: datetime = AHORA) -> None:
        self.consulta = FakeConsultaDespachos()
        self.envios = FakeEnviosDespacho()
        self.remitos = FakeRemitosDespacho()
        self.historial = FakeHistorialConsulta()
        self.acciones = FakeAccionesDespacho()
        self.corridas = FakeCorridasConsulta()
        self.feriados = FakeCalendarioFeriados()
        self.ahora = ahora

    def ports(self) -> ConsultaDespachosPorts:
        return ConsultaDespachosPorts(
            consulta=self.consulta,
            envios=self.envios,
            remitos=self.remitos,
            historial=self.historial,
            acciones=self.acciones,
            corridas=self.corridas,
            feriados=self.feriados,
            reloj=lambda: self.ahora,
        )


async def test_listar_arma_los_filtros_con_el_alcance_y_devuelve_el_total() -> None:
    mundo = MundoConsulta()
    mundo.consulta.filas = [fila(GUIA_A)]
    mundo.consulta.total = 51
    criterio = CriterioListado(
        texto="toner",
        colores=(ColorSemaforo.ROJO, ColorSemaforo.NARANJA),
        operativa="434324",
        remito_desde=date(2026, 9, 1),
        remito_hasta=date(2026, 9, 20),
        solo_alertas_abiertas=True,
    )

    listado = await ListarDespachos(mundo.ports(), CONFIG).execute(criterio, PAGINA)

    filtros = FiltrosDespachos(
        alcance_desde=date(2026, 8, 25),
        texto="toner",
        colores=(ColorSemaforo.ROJO, ColorSemaforo.NARANJA),
        operativa="434324",
        remito_desde=date(2026, 9, 1),
        remito_hasta=date(2026, 9, 20),
        solo_alertas_abiertas=True,
    )
    assert listado == ListadoDespachos(filas=[fila(GUIA_A)], total=51)
    assert mundo.consulta.listados == [(filtros, PAGINA)]
    assert mundo.consulta.contados == [filtros]


async def test_hoy_es_el_dia_en_argentina_y_no_en_utc() -> None:
    mundo = MundoConsulta(ahora=datetime(2026, 9, 25, 2, 30, tzinfo=UTC))

    await ListarDespachos(mundo.ports(), CONFIG).execute(CriterioListado(), PAGINA)

    assert mundo.consulta.contados[0].alcance_desde == date(2026, 8, 25)


async def test_listar_completa_dias_habiles_solo_en_las_filas_rojas_con_limite() -> None:
    mundo = MundoConsulta()
    mundo.consulta.filas = [
        fila("1", ColorSemaforo.ROJO, fecha_limite=date(2026, 10, 13)),
        fila("2", ColorSemaforo.ROJO, fecha_limite=date(2026, 9, 22)),
        fila("3", ColorSemaforo.ROJO, fecha_limite=date(2026, 9, 24)),
        fila("4", ColorSemaforo.ROJO),
        fila("5", ColorSemaforo.NARANJA, fecha_limite=date(2026, 9, 30)),
    ]

    listado = await ListarDespachos(mundo.ports(), CONFIG).execute(CriterioListado(), PAGINA)

    # 13/10: del viernes 25/09 al martes 13/10 son 12 días hábiles (el 12/10 es feriado).
    dias = [f.dias_habiles_para_limite for f in listado.filas]
    assert dias == [12, -2, 0, None, None]
    assert mundo.feriados.consultas == [(date(2026, 9, 22), date(2026, 10, 13))]


async def test_listar_sin_filas_rojas_no_pide_feriados() -> None:
    mundo = MundoConsulta()
    mundo.consulta.filas = [fila("1"), fila("2", ColorSemaforo.ROJO)]

    listado = await ListarDespachos(mundo.ports(), CONFIG).execute(CriterioListado(), PAGINA)

    assert listado.filas == mundo.consulta.filas
    assert mundo.feriados.consultas == []


async def test_resumir_usa_el_mismo_alcance_que_el_listado() -> None:
    mundo = MundoConsulta()

    resumen = await ResumirDespachos(mundo.ports(), CONFIG).execute()

    assert resumen == RESUMEN
    assert mundo.consulta.resumidos == [date(2026, 8, 25)]


async def _mundo_con_detalle(color: ColorSemaforo, limite: date | None) -> MundoConsulta:
    mundo = MundoConsulta()
    clasificacion = replace(VERDE, color=color, fecha_limite=limite, alerta=limite is not None)
    mundo.envios.envios = {GUIA_A: envio(GUIA_A, clasificacion=clasificacion)}
    mundo.remitos.guardados = [despacho(GUIA_A, 1), despacho(GUIA_B, 2), despacho(GUIA_A, 3)]
    mundo.historial.cambios = {GUIA_A: [_cambio(color)]}
    await mundo.acciones.agregar(_accion_nueva(GUIA_A))
    await mundo.acciones.agregar(_accion_nueva(GUIA_B))
    return mundo


def _cambio(color: ColorSemaforo) -> CambioEstado:
    return CambioEstado(
        id_estado=45,
        estado="En sucursal",
        motivo="Sin Motivo",
        sucursal="Rosario",
        fecha_estado=date(2026, 9, 23),
        color=color,
        observado_en=AHORA,
    )


def _accion_nueva(guia: str) -> AccionNueva:
    return AccionNueva(
        guia=guia,
        tipo=TipoAccion.LLAMADO_CLIENTE,
        detalle="Se avisó al cliente",
        resultado=ResultadoAccion.PENDIENTE,
        cerro_alerta=False,
        usuario_id=None,
        usuario_nombre="Ana",
    )


async def test_detalle_trae_remitos_cambios_y_acciones_de_la_guia() -> None:
    mundo = await _mundo_con_detalle(ColorSemaforo.VERDE, None)

    detalle = await ObtenerDetalleDespacho(mundo.ports(), CONFIG).execute(GUIA_A)

    assert detalle == DetalleDespacho(
        envio=mundo.envios.envios[GUIA_A],
        remitos=[despacho(GUIA_A, 1), despacho(GUIA_A, 3)],
        cambios=[_cambio(ColorSemaforo.VERDE)],
        acciones=[mundo.acciones.acciones[0]],
        dias_habiles_para_limite=None,
    )
    assert mundo.feriados.consultas == []


async def test_detalle_en_rojo_calcula_los_dias_habiles_al_limite() -> None:
    mundo = await _mundo_con_detalle(ColorSemaforo.ROJO, date(2026, 10, 13))

    detalle = await ObtenerDetalleDespacho(mundo.ports(), CONFIG).execute(GUIA_A)

    assert detalle.dias_habiles_para_limite == 12
    assert mundo.feriados.consultas == [(date(2026, 9, 24), date(2026, 10, 13))]


async def test_detalle_en_rojo_vencido_da_negativo() -> None:
    mundo = await _mundo_con_detalle(ColorSemaforo.ROJO, date(2026, 9, 23))

    detalle = await ObtenerDetalleDespacho(mundo.ports(), CONFIG).execute(GUIA_A)

    assert detalle.dias_habiles_para_limite == -1
    assert mundo.feriados.consultas == [(date(2026, 9, 23), date(2026, 9, 24))]


async def test_detalle_de_una_guia_inexistente() -> None:
    mundo = MundoConsulta()

    with pytest.raises(EnvioDespachoNoEncontradoError):
        await ObtenerDetalleDespacho(mundo.ports(), CONFIG).execute(GUIA_A)


async def test_actualizacion_sin_corridas() -> None:
    estado = await ConsultarActualizacion(MundoConsulta().ports()).execute()

    assert estado == EstadoActualizacion(ultima=None, ultima_terminada=None, en_curso=False)


async def test_actualizacion_con_la_ultima_terminada_no_vuelve_a_consultar() -> None:
    mundo = MundoConsulta()
    terminada = corrida(2, AHORA)
    mundo.corridas.corridas = [corrida(1, AHORA), terminada]

    estado = await ConsultarActualizacion(mundo.ports()).execute()

    assert estado == EstadoActualizacion(
        ultima=terminada, ultima_terminada=terminada, en_curso=False
    )
    assert mundo.corridas.pedidos_de_terminada == 0


async def test_actualizacion_en_curso_trae_la_ultima_terminada() -> None:
    mundo = MundoConsulta()
    anterior, en_curso = corrida(1, AHORA), corrida(2, None)
    mundo.corridas.corridas = [anterior, en_curso]

    estado = await ConsultarActualizacion(mundo.ports()).execute()

    assert estado == EstadoActualizacion(ultima=en_curso, ultima_terminada=anterior, en_curso=True)
