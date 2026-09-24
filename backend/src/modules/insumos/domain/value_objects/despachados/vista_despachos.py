"""Lo que la pantalla de Despachados lee de la base de HDM (nunca espera a OCA)."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo


class ColumnaOrden(StrEnum):
    """Por qué columna de la tabla se ordena el listado."""

    URGENCIA = "urgencia"
    """El orden por defecto: rango del semáforo con sus desempates internos (rojo por fecha
    límite, naranja y amarillo por fecha de estado más vieja, el resto por la más nueva).
    Ignora la dirección: siempre va de lo más urgente a lo menos."""
    COLOR = "color"
    """Solo el rango del semáforo (rojo, naranja, amarillo, verde, gris, cerrado)."""
    GUIA = "guia"
    REMITO = "remito"
    """Número del primer remito de la guía."""
    CLIENTE = "cliente"
    INCIDENTE = "incidente"
    """Primer incidente del primer remito."""
    ESTADO = "estado"
    """Texto del último estado de OCA."""
    SUCURSAL = "sucursal"
    """Sucursal OCA del último estado."""
    FECHA_REMITO = "fecha_remito"
    FECHA_ESTADO = "fecha_estado"
    LIMITE = "limite"
    """Fecha límite del envío."""


@dataclass(frozen=True, slots=True)
class OrdenDespachos:
    """Orden de la tabla. Los vacíos (sin remito, sin estado OCA, sin límite) van siempre al
    final, en las dos direcciones; a igual valor desempata la guía, ascendente."""

    columna: ColumnaOrden = ColumnaOrden.URGENCIA
    descendente: bool = False


@dataclass(frozen=True, slots=True)
class FiltrosDespachos:
    alcance_desde: date
    """Entran los envíos abiertos, más los cerrados con remito desde esta fecha (la
    ventana de búsqueda en Siges): así "Entregados/Devueltos (30 días)" no crece para
    siempre y un envío abierto viejo nunca desaparece de la vista."""
    texto: str = ""
    """Busca (sin distinguir mayúsculas ni tildes) en guía, cliente, número de remito e
    incidente."""
    colores: tuple[ColorSemaforo, ...] = ()
    """Vacío = todos los colores."""
    operativa: str | None = None
    remito_desde: date | None = None
    remito_hasta: date | None = None
    solo_alertas_abiertas: bool = False
    """La bandeja "Requieren acción": rojo o naranja sin cierre de alerta."""
    orden: OrdenDespachos = field(default_factory=OrdenDespachos)
    """No filtra: viaja con los filtros para que el listado lo aplique en SQL."""


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
