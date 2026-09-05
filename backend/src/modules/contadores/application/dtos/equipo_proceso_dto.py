"""Forma de entrada al motor de estimación para un equipo de un proceso de
facturación — sea de ejemplo (`infrastructure/ejemplo/`) o real contra SiGes
(`infrastructure/siges/`). Reemplazar la fuente de datos es el único cambio
necesario: el resto del pipeline (`_construir_estimacion_input.py`,
`get_tablero_proyeccion.py`) no distingue entre ambas."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import (
    EstadoMaquina,
    Tecnologia,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque


@dataclass(frozen=True, slots=True)
class ClaseProceso:
    clase: str
    tecnologia: Tecnologia
    velocidad_ppm: float | None
    ultimo_contador_facturado: LecturaRef
    ya_real: bool = False
    valor_real_cargado: float | None = None
    ultimo_real: LecturaRef | None = None
    fecha_ultimo_real_no_t4: date | None = None
    real_anterior: LecturaRef | None = None
    t4_mas_reciente: LecturaRef | None = None
    t4_revisado: bool = False
    parque_cliente_modelo: PromedioParque | None = None
    parque_grupo_modelo: PromedioParque | None = None
    parque_cliente_tecnologia: PromedioParque | None = None
    parque_global_modelo: PromedioParque | None = None
    prom_6_facturados: float | None = None
    historico_12: tuple[float, ...] = field(default_factory=tuple)
    es_clase_sintetica: bool = False


@dataclass(frozen=True, slots=True)
class EquipoProceso:
    id_maquina: int
    nro_serie: str
    empresa: str
    sucursal: str
    sector: str
    modelo: str
    estado_maquina: EstadoMaquina
    clases: tuple[ClaseProceso, ...]
