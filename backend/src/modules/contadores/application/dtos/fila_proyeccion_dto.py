from dataclasses import dataclass
from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import (
    EstadoMaquina,
    Tecnologia,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    Coloreo,
    Semaforo,
)


@dataclass(frozen=True, slots=True)
class FilaProyeccionDto:
    """Una fila de la grilla de Proyección — un (equipo, clase de contador).
    Combina datos de identidad/ubicación (que no maneja el motor) con el
    `EstimacionResultado` de `estimar()`."""

    id_maquina: int
    nro_serie: str
    empresa: str
    sucursal: str
    sector: str
    modelo: str
    tecnologia: Tecnologia
    estado_maquina: EstadoMaquina
    clase: str
    meses_sin_real: int | None
    historico_12: tuple[float, ...]
    prom_6_facturados: float | None
    ultimo_facturado_valor: float
    ultimo_facturado_fecha: date
    ultimo_facturado_tipo: int
    es_real: bool
    estim_propuesto: float | None
    tipo_toma: int | None
    impresiones: float | None
    fuente: str
    metodo_detalle: str
    coloreo: Coloreo | None
    borde_salto_imposible: bool
    semaforo: Semaforo
    requiere_confirmacion: bool
    nota_operador: str | None = None
    es_clase_sintetica: bool = False
