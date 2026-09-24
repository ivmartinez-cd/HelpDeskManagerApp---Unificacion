"""Entradas y salidas de los casos de uso de lectura de Insumos > Despachados."""

from dataclasses import dataclass, field
from datetime import date, tzinfo

from src.modules.insumos.domain.entities.despachados.accion_registrada import AccionRegistrada
from src.modules.insumos.domain.entities.despachados.corrida import Corrida
from src.modules.insumos.domain.entities.despachados.envio_seguido import EnvioSeguido
from src.modules.insumos.domain.value_objects.despachados.cambio_estado import CambioEstado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    OrdenDespachos,
    ResumenDespachos,
)


@dataclass(frozen=True)
class CriterioListado:
    """Filtros que elige el operador en la pantalla (el alcance lo pone el caso de uso)."""

    texto: str = ""
    colores: tuple[ColorSemaforo, ...] = ()
    operativa: str | None = None
    remito_desde: date | None = None
    remito_hasta: date | None = None
    solo_alertas_abiertas: bool = False
    orden: OrdenDespachos = field(default_factory=OrdenDespachos)
    """Columna y dirección elegidas en la tabla; por defecto, urgencia."""


@dataclass(frozen=True)
class ConfigConsulta:
    dias_ventana: int
    """Días hacia atrás desde hoy en los que un envío cerrado sigue a la vista (la misma
    ventana con la que se buscan los remitos en Siges)."""
    zona_horaria: tzinfo
    """Zona en la que se decide qué día es "hoy" (Argentina)."""


@dataclass(frozen=True)
class ListadoDespachos:
    filas: list[FilaDespacho]
    total: int
    """Total de envíos que cumplen el criterio, sin paginar."""


@dataclass(frozen=True)
class TarjetasDespachos:
    resumen: ResumenDespachos
    dias_habiles_limite_mas_proximo: int | None
    """Días hábiles de hoy a `resumen.limite_mas_proximo` (0 vence hoy, negativo vencido);
    None si no hay ningún envío en rojo con fecha límite."""


@dataclass(frozen=True)
class DetalleDespacho:
    envio: EnvioSeguido
    remitos: list[DespachoSiges]
    """Del más viejo al más nuevo."""
    cambios: list[CambioEstado]
    """Del más reciente al más viejo."""
    acciones: list[AccionRegistrada]
    """De la más reciente a la más vieja."""
    dias_habiles_para_limite: int | None
    """Solo en rojo con fecha límite: 0 vence hoy, negativo vencido."""


@dataclass(frozen=True)
class EstadoActualizacion:
    ultima: Corrida | None
    ultima_terminada: Corrida | None
    en_curso: bool
    """La última corrida todavía no terminó."""
