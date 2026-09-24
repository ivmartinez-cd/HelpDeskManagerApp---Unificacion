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
    """Contrato de entrada del motor para un (equipo, clase de contador) — una
    fila de la grilla de estimación (`EquipoGrillaRaw` del legacy). Las
    lecturas (último real, real anterior, T4) ya vienen elegidas por la
    consulta a SiGes: el motor no vuelve a elegirlas.

    `ultimo_contador_facturado` es el `ContadorAnterior` del legacy: `None`
    cuando el equipo no tiene contador facturado (el motor usa 0 donde el
    legacy usa `GetValueOrDefault()`). `id_grupo_economico` es el grupo de la
    fila y `id_anexo` el anexo del proceso — con ellos se filtran los recesos
    (`Receso.AplicaA`). `impresiones_reales` es `FC_ImpresionesReales`, lo
    que el motor devuelve como impresiones de una fila ya real."""

    pendiente_estimar: bool
    fecha_objetivo: date
    periodo_desde: date
    periodo_hasta: date

    estado_maquina: EstadoMaquina
    tecnologia: Tecnologia
    velocidad_ppm: float | None

    ultimo_contador_facturado: LecturaRef | None
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
    impresiones_reales: float | None = None
