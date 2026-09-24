"""Forma de entrada al motor de estimación para un equipo de un proceso de
facturación — sea de ejemplo (`infrastructure/ejemplo/`) o real contra SiGes
(`infrastructure/siges/`). Reemplazar la fuente de datos es el único cambio
necesario: el resto del pipeline (`_construir_estimacion_input.py`,
`get_tablero_proyeccion.py`) no distingue entre ambas."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.contadores.application.dtos.parque_historico_dto import ParqueHistorico
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
    # `ContadorAnterior` del legacy: `None` si el equipo no tiene contador
    # facturado (no se inventa una lectura 0).
    ultimo_contador_facturado: LecturaRef | None
    ya_real: bool = False
    valor_real_cargado: float | None = None
    # Fila ya real: `FC_ImpresionesReales` y tipo/fecha del contador actual
    # (`FC_TipoToma_ContActual` / `FC_Fecha_ContActual`).
    impresiones_reales: float | None = None
    tipo_toma_actual: int | None = None
    fecha_toma_actual: date | None = None
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
    # `PromGlobalModelo_Imp` (fallback de salto imposible sin velocidad).
    prom_global_modelo_imp: float | None = None
    # N / P80 / cruda por nivel aunque el P80 sea NULL ("Detalle por Modelo
    # histórico"); `None` en los datos de ejemplo (se deriva de los parques).
    parque_historico: ParqueHistorico | None = None


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
    # Datos de la fila de Siges que la grilla del legacy muestra y el motor no
    # usa: `EstadoMaquinaDesc` (texto del estado), `EmpresaActualDesc` ("Ubic
    # Actual", solo si la máquina cambió de empresa desde el cierre; `None`
    # si no), y `ID_ArtGen`/`ID_ModoOper` con los que el legacy agrupa el
    # detalle por modelo (ModoOper 2/4 = Cl.20 total, 3/5 = solo color).
    estado_maquina_desc: str = ""
    empresa_actual_desc: str | None = None
    id_art_gen: int | None = None
    id_modo_oper: int = 0
