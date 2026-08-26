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
    terminal no anulado; None = nunca se registró un preventivo hecho.
    `fecha_instalacion` es el último incidente tipo 103 (Instalación-
    Desinstalación) en estado terminal no anulado — ancla para estimar
    `fecha_tentativa` del primer preventivo cuando nunca hubo uno real (ver
    domain/services/vencimiento.py); None si nunca se registró.
    `domicilio` es `Sucursal.Domicilio` normalizado (agregado 2026-08-23
    para que el mapa muestre la dirección junto al pin y se pueda validar la
    ubicación a ojo — mismo `normalizar_domicilio` que usa el geocoding).
    `latitud`/`longitud` son `Sucursal.Latitud`/`Longitud` parseadas (texto
    libre en Siges, no siempre numérico ni cargado) — None cuando no hay valor
    o no parsea; validarlas es responsabilidad de
    `domain/services/coordenadas.py`, no de esta entidad."""

    id_maquina: int
    id_sucursal: int
    serie: str
    modelo: str
    cliente: str
    sucursal: str
    zona: str
    frecuencia_dias: int | None
    fecha_ultimo_preventivo: date | None
    fecha_instalacion: date | None
    domicilio: str
    latitud: float | None
    longitud: float | None


@dataclass(frozen=True, slots=True)
class ParqueZonaSnapshot:
    """Resultado de una pasada por Siges para una zona, con su sello de
    frescura (la UI muestra "actualizado hace X" porque el gateway cachea)."""

    equipos: tuple[EquipoPreventivo, ...]
    consultado_en: datetime
