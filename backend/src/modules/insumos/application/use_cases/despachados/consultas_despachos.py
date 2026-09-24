"""Casos de uso de lectura de Insumos > Despachados: tabla, tarjetas, detalle de una guía y
estado de la actualización. Leen solo la base de HDM (nunca esperan a OCA).

"Hoy" es el día en la zona horaria configurada (Argentina) según el reloj inyectado; el
alcance deja a la vista los envíos abiertos y los cerrados con remito en los últimos
`dias_ventana` días.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

from src.modules.insumos.application.dtos.despachados import (
    ConfigConsulta,
    CriterioListado,
    DetalleDespacho,
    EstadoActualizacion,
    ListadoDespachos,
    TarjetasDespachos,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import EnvioSeguido
from src.modules.insumos.domain.errores_despachados import EnvioDespachoNoEncontradoError
from src.modules.insumos.domain.repositories.acciones_despacho_repository import (
    AccionesDespachoRepository,
    CorridasDespachoRepository,
)
from src.modules.insumos.domain.repositories.consulta_despachos_repository import (
    CalendarioFeriados,
    ConsultaDespachosRepository,
)
from src.modules.insumos.domain.repositories.envios_despacho_repository import (
    EnviosDespachoRepository,
    HistorialEstadosRepository,
    RemitosDespachoRepository,
)
from src.modules.insumos.domain.services.despachados.dias_habiles import dias_habiles_hasta
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    FiltrosDespachos,
    Pagina,
)


@dataclass(frozen=True)
class ConsultaDespachosPorts:
    consulta: ConsultaDespachosRepository
    envios: EnviosDespachoRepository
    remitos: RemitosDespachoRepository
    historial: HistorialEstadosRepository
    acciones: AccionesDespachoRepository
    corridas: CorridasDespachoRepository
    feriados: CalendarioFeriados
    reloj: Callable[[], datetime]
    """Hora actual, aware (en UTC)."""


class ListarDespachos:
    def __init__(self, ports: ConsultaDespachosPorts, config: ConfigConsulta) -> None:
        self._ports = ports
        self._config = config

    async def execute(self, criterio: CriterioListado, pagina: Pagina) -> ListadoDespachos:
        hoy = _hoy(self._ports, self._config)
        filtros = _filtros(criterio, _alcance_desde(hoy, self._config))
        filas = await self._ports.consulta.listar(filtros, pagina)
        total = await self._ports.consulta.contar(filtros)
        filas = await _con_dias_para_limite(filas, hoy, self._ports.feriados)
        return ListadoDespachos(filas=filas, total=total)


class ResumirDespachos:
    def __init__(self, ports: ConsultaDespachosPorts, config: ConfigConsulta) -> None:
        self._ports = ports
        self._config = config

    async def execute(self) -> TarjetasDespachos:
        """Contadores de las tarjetas, con los días hábiles que faltan para la fecha límite
        más próxima (la tarjeta roja), contados con el calendario de feriados."""
        hoy = _hoy(self._ports, self._config)
        resumen = await self._ports.consulta.resumir(_alcance_desde(hoy, self._config))
        limite = resumen.limite_mas_proximo
        if limite is None:
            return TarjetasDespachos(resumen=resumen, dias_habiles_limite_mas_proximo=None)
        feriados = await _feriados_entre(self._ports.feriados, hoy, [limite])
        dias = dias_habiles_hasta(hoy, limite, feriados)
        return TarjetasDespachos(resumen=resumen, dias_habiles_limite_mas_proximo=dias)


class ObtenerDetalleDespacho:
    def __init__(self, ports: ConsultaDespachosPorts, config: ConfigConsulta) -> None:
        self._ports = ports
        self._config = config

    async def execute(self, guia: str) -> DetalleDespacho:
        envio = await self._ports.envios.obtener(guia)
        if envio is None:
            raise EnvioDespachoNoEncontradoError(guia)
        return DetalleDespacho(
            envio=envio,
            remitos=await self._ports.remitos.listar_por_guia(guia),
            cambios=await self._ports.historial.listar_por_guia(guia),
            acciones=await self._ports.acciones.listar_por_guia(guia),
            dias_habiles_para_limite=await self._dias_para_limite(envio),
        )

    async def _dias_para_limite(self, envio: EnvioSeguido) -> int | None:
        limite = envio.clasificacion.fecha_limite
        if envio.clasificacion.color is not ColorSemaforo.ROJO or limite is None:
            return None
        hoy = _hoy(self._ports, self._config)
        feriados = await _feriados_entre(self._ports.feriados, hoy, [limite])
        return dias_habiles_hasta(hoy, limite, feriados)


class ConsultarActualizacion:
    def __init__(self, ports: ConsultaDespachosPorts) -> None:
        self._ports = ports

    async def execute(self) -> EstadoActualizacion:
        ultima = await self._ports.corridas.ultima()
        if ultima is None:
            return EstadoActualizacion(ultima=None, ultima_terminada=None, en_curso=False)
        if ultima.terminada_en is not None:
            return EstadoActualizacion(ultima=ultima, ultima_terminada=ultima, en_curso=False)
        terminada = await self._ports.corridas.ultima_terminada()
        return EstadoActualizacion(ultima=ultima, ultima_terminada=terminada, en_curso=True)


def _hoy(ports: ConsultaDespachosPorts, config: ConfigConsulta) -> date:
    return ports.reloj().astimezone(config.zona_horaria).date()


def _alcance_desde(hoy: date, config: ConfigConsulta) -> date:
    return hoy - timedelta(days=config.dias_ventana)


def _filtros(criterio: CriterioListado, alcance_desde: date) -> FiltrosDespachos:
    return FiltrosDespachos(
        alcance_desde=alcance_desde,
        texto=criterio.texto,
        colores=criterio.colores,
        operativa=criterio.operativa,
        remito_desde=criterio.remito_desde,
        remito_hasta=criterio.remito_hasta,
        solo_alertas_abiertas=criterio.solo_alertas_abiertas,
    )


def _limite_rojo(fila: FilaDespacho) -> date | None:
    return fila.fecha_limite if fila.color is ColorSemaforo.ROJO else None


async def _con_dias_para_limite(
    filas: list[FilaDespacho], hoy: date, calendario: CalendarioFeriados
) -> list[FilaDespacho]:
    """Completa los días hábiles a la fecha límite de las filas rojas. Pide los feriados una
    sola vez, y solo si hay alguna fila roja con límite."""
    limites = [limite for fila in filas if (limite := _limite_rojo(fila)) is not None]
    if not limites:
        return filas
    feriados = await _feriados_entre(calendario, hoy, limites)
    return [
        fila
        if (limite := _limite_rojo(fila)) is None
        else replace(fila, dias_habiles_para_limite=dias_habiles_hasta(hoy, limite, feriados))
        for fila in filas
    ]


async def _feriados_entre(
    calendario: CalendarioFeriados, hoy: date, limites: Sequence[date]
) -> frozenset[date]:
    """Feriados del tramo que cubre hoy y todas las fechas límite (vencidas o no)."""
    return await calendario.feriados_entre(min(hoy, *limites), max(hoy, *limites))
