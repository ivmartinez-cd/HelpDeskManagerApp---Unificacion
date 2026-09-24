"""Lo que la pantalla de Despachados lee de la base de HDM (nunca espera a OCA)."""

from dataclasses import dataclass
from datetime import date, datetime

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo


@dataclass(frozen=True, slots=True)
class FiltrosDespachos:
    alcance_desde: date
    """Entran los envíos abiertos, más los cerrados con remito desde esta fecha (la
    ventana de búsqueda en Siges): así "Entregados/Devueltos (30 días)" no crece para
    siempre y un envío abierto viejo nunca desaparece de la vista."""
    texto: str = ""
    """Busca (sin distinguir mayúsculas) en guía, cliente, número de remito e incidente."""
    colores: tuple[ColorSemaforo, ...] = ()
    """Vacío = todos los colores."""
    operativa: str | None = None
    remito_desde: date | None = None
    remito_hasta: date | None = None
    solo_alertas_abiertas: bool = False
    """La bandeja "Requieren acción": rojo o naranja sin cierre de alerta."""


@dataclass(frozen=True, slots=True)
class Pagina:
    limite: int
    desplazamiento: int


@dataclass(frozen=True, slots=True)
class UltimaAccion:
    tipo: TipoAccion
    resultado: ResultadoAccion
    usuario_nombre: str
    creada_en: datetime


@dataclass(frozen=True, slots=True)
class FilaDespacho:
    guia: str
    color: ColorSemaforo
    alerta_abierta: bool
    observacion: str
    fecha_limite: date | None
    estado: str
    """Texto del último estado de OCA; "" si OCA todavía no registra la guía."""
    motivo: str
    sucursal_oca: str
    fecha_estado: date | None
    operativa: str
    cliente: str
    fecha_remito: date
    numero_remito: int | None
    """El del primer remito de la guía (por fecha e id)."""
    cantidad_remitos: int
    incidente: str
    """El primer incidente del primer remito; "" si no tiene."""
    cantidad_incidentes: int
    """Incidentes distintos entre todos los remitos de la guía."""
    ultima_accion: UltimaAccion | None
    con_error: bool
    """La última consulta a OCA falló (se muestra el último estado bueno)."""
    dias_habiles_para_limite: int | None = None
    """Solo en rojo: días hábiles de hoy a la fecha límite (0 = vence hoy, negativo =
    vencido). Lo completa el caso de uso con el calendario de feriados, no el repositorio."""


@dataclass(frozen=True, slots=True)
class ResumenDespachos:
    """Tarjetas y contadores del menú, dentro del mismo alcance que `FiltrosDespachos`."""

    por_color: dict[ColorSemaforo, int]
    """Cantidad de envíos por color (todos los colores presentes, 0 si no hay)."""
    alertas_rojas: int
    """Alertas abiertas en rojo (contador rojo del menú)."""
    alertas_naranjas: int
    naranjas_sin_accion: int
    """Envíos en naranja sin ninguna acción registrada."""
    limite_mas_proximo: date | None
    """La fecha límite más cercana entre los envíos en rojo."""
    operativas: tuple[str, ...]
    """Operativas OCA presentes, ordenadas (opciones del filtro)."""
