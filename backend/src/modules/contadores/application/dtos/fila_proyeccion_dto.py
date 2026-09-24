from dataclasses import dataclass
from datetime import date

from src.modules.contadores.application.dtos.parque_historico_dto import ParqueHistorico
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import (
    EstadoMaquina,
    Tecnologia,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    DetalleParque,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    Coloreo,
    MetodoEstimacion,
    Semaforo,
)


@dataclass(frozen=True, slots=True)
class FilaProyeccionDto:
    """Una fila de la grilla de Proyección — un (equipo, clase de contador).
    Combina datos de identidad/ubicación (que no maneja el motor) con el
    resultado final (automático o decisión restaurada del operador).

    `ultimo_facturado_*` es el `ContadorAnterior` del legacy (`None` si el
    equipo no tiene contador facturado). En una fila real, `estim_propuesto`,
    `tipo_toma` y `fecha_toma_actual` son el contador actual ya cargado
    (celda "real-cargado" del legacy: `FC_ImpreContadorActual`,
    `FC_TipoToma_ContActual`, `FC_Fecha_ContActual`) e `impresiones` son
    `FC_ImpresionesReales`. `editado_por_operador` es la marca "editado" del
    legacy (la fila muestra una decisión del operador, no el automático).

    La observación que escribe el operador no viaja en la fila: el legacy
    solo la graba en la auditoría. `guia_operador` es la
    `NotaOperador` del motor: el tooltip del estimado la agrega debajo de
    `detalle_calculo` (`GrillaEstimacion.TooltipEstim`) y no viaja al CSV.
    `metodo`/`etiqueta_nivel` alimentan el tooltip "Detalle de estimación"
    (`EstimacionTooltip`: no se muestra con método "NoAplica").
    `t4_sin_revisar` es el borde amarillo `warn-st` de la celda del estimado
    y `meses_sin_real_en_alerta` el "meses sin real" en rojo.

    `estado_maquina_desc`/`empresa_actual_desc` son la columna Modelo del
    legacy (estado y "Ubic Actual"); `id_art_gen`/`id_modo_oper` y
    `parque_historico` alimentan "Detalle por Modelo" (y su versión
    histórica); `ultimo_real_*`/`real_anterior_*` son las lecturas con las que
    el panel preselecciona L y P (`PanelCandidatos.PreseleccionarPL`)."""

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
    ultimo_facturado_valor: float | None
    ultimo_facturado_fecha: date | None
    ultimo_facturado_tipo: int | None
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
    es_clase_sintetica: bool = False
    detalle_parque: DetalleParque | None = None
    dias_par_pl: int | None = None
    tasa_diaria: float | None = None
    dias_proyectados: int | None = None
    detalle_calculo: str = ""
    fecha_toma_actual: date | None = None
    editado_por_operador: bool = False
    guia_operador: str | None = None
    metodo: MetodoEstimacion = "NoAplica"
    etiqueta_nivel: str = ""
    t4_sin_revisar: bool = False
    meses_sin_real_en_alerta: bool = False
    estado_maquina_desc: str = ""
    empresa_actual_desc: str | None = None
    id_art_gen: int | None = None
    id_modo_oper: int = 0
    ultimo_real_fecha: date | None = None
    ultimo_real_tipo: int | None = None
    real_anterior_fecha: date | None = None
    real_anterior_tipo: int | None = None
    parque_historico: ParqueHistorico | None = None
