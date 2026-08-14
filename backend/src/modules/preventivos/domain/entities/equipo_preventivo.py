from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class EquipoPreventivo:
    """Una máquina activa del parque local con lo necesario para calcular su
    vencimiento de preventivo. Todo sale de Siges en una sola consulta (ver
    infrastructure/siges/query.py); acá no hay estado calculado — eso es del
    servicio de vencimientos.

    `frecuencia_dias` viene de `Sucursal.TipoPreventivo` → `TipoPreventivo.Dias`
    (por sucursal, no por máquina); 0 o None significa "sin frecuencia cargada"
    y el dominio NO inventa un vencimiento en ese caso.
    `fecha_ultimo_preventivo` es el último incidente tipo 102 en estado
    terminal no anulado; None = nunca se registró un preventivo hecho."""

    id_maquina: int
    serie: str
    modelo: str
    cliente: str
    sucursal: str
    zona: str
    frecuencia_dias: int | None
    fecha_ultimo_preventivo: date | None


@dataclass(frozen=True, slots=True)
class ParqueZonaSnapshot:
    """Resultado de una pasada por Siges para una zona, con su sello de
    frescura (la UI muestra "actualizado hace X" porque el gateway cachea)."""

    equipos: tuple[EquipoPreventivo, ...]
    consultado_en: datetime
