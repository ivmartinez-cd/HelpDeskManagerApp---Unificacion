from dataclasses import dataclass, field
from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import (
    EstadoMaquina,
    Tecnologia,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente


@dataclass(frozen=True, slots=True)
class EstimacionInput:
    """Contrato de entrada del motor de estimación para un (equipo, clase de
    contador) pendiente de estimar — una fila de la "grilla de estimación"
    de MODELO_DE_DATOS §3.4. Los candidatos de Partida/T4 ya vienen resueltos
    por la capa de datos (guarda empresa+sucursal, ventana 45/15 días,
    elegibilidad de 24 meses — REGLAS_DE_NEGOCIO §5.2/§5.3): el motor no
    vuelve a elegirlos, solo decide qué hacer con lo que recibió."""

    pendiente_estimar: bool
    fecha_objetivo: date
    periodo_desde: date
    periodo_hasta: date

    estado_maquina: EstadoMaquina
    tecnologia: Tecnologia
    velocidad_ppm: float | None

    ultimo_contador_facturado: LecturaRef
    ultimo_real: LecturaRef | None
    fecha_ultimo_real_no_t4: date | None
    real_anterior: LecturaRef | None
    t4_mas_reciente: LecturaRef | None
    t4_revisado: bool

    parque_cliente_modelo: PromedioParque | None
    parque_grupo_modelo: PromedioParque | None
    parque_cliente_tecnologia: PromedioParque | None
    parque_global_modelo: PromedioParque | None

    prom_6_facturados: float | None

    id_grupo_economico: int
    id_anexo: int
    recesos: list[RecesoCliente] = field(default_factory=list)
