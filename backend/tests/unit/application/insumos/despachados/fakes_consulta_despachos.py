"""Fakes en memoria y datos de prueba de los casos de uso de lectura de Despachados."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

from src.modules.insumos.application.dtos.despachados import ConfigConsulta
from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ConsultaDespachosPorts,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
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
    FakeAccionesDespacho,
    FakeCalendarioFeriados,
    FakeEnviosDespacho,
    FakeRemitosDespacho,
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
        self.resumen = RESUMEN

    async def listar(self, filtros: FiltrosDespachos, pagina: Pagina) -> list[FilaDespacho]:
        self.listados.append((filtros, pagina))
        return list(self.filas)

    async def contar(self, filtros: FiltrosDespachos) -> int:
        self.contados.append(filtros)
        return self.total

    async def resumir(self, alcance_desde: date) -> ResumenDespachos:
        self.resumidos.append(alcance_desde)
        return self.resumen


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
