from dataclasses import dataclass, field

from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    Coloreo,
    FuenteEstimacion,
    MarcaEstimacion,
    MetodoEstimacion,
    Semaforo,
)


@dataclass(frozen=True, slots=True)
class DetalleParque:
    """Composición del promedio de parque usado — alimenta el tooltip
    "Detalle de estimación" del frontend (`EstimacionTooltip` legacy).
    `es_mediana_truncada` decide el régimen (N>=5 → P80) igual que
    `MetodoUsado` del legacy."""

    n_equipos: int
    n_descartados: int
    es_mediana_truncada: bool
    mediana_cruda: float | None
    media_cruda: float | None


@dataclass(frozen=True, slots=True)
class EstimacionResultado:
    """Salida del motor para un (equipo, clase de contador) — el `EquipoGrilla`
    del legacy (`CalculadorContadores`). `estim_propuesto`/`impresiones` salen
    ya redondeados a entero como en el legacy (`Math.Round`, bancario).
    `tipo_toma` es el `TipoTomaSugerido`: 14 (también cuando la fuente es un
    T4 ST — el estimador nunca graba T4), 19 (parque) o `None` (real /
    pendiente). `detalle_calculo` es el texto `DetalleCalculo` idéntico al
    legacy, `etiqueta_nivel` el pie del tooltip
    (`EstimacionDecision.EtiquetaNivel`), `metodo` y `marcas` el
    `EstimacionDecision.Metodo`/`Marcas` ("NoAplica" y vacío cuando el legacy
    no arma decisión: lectura real o pendiente). `nota_operador` es la
    `NotaOperador` (guía del tooltip, no viaja al CSV). `t4_sin_revisar` es el
    `BordeAmarilloT4PFcero`. Fuente "Pendiente" equivale a
    `RequierePendiente` del legacy."""

    estim_propuesto: float | None
    impresiones: float | None
    tipo_toma: int | None
    fuente: FuenteEstimacion
    metodo_detalle: str
    requiere_confirmacion: bool = False
    semaforo: Semaforo = "VERDE"
    borde_salto_imposible: bool = False
    coloreo: Coloreo | None = None
    nota_operador: str | None = None
    meses_sin_real_en_alerta: bool = False
    dias_par_pl: int | None = None
    ajustado_por_receso: bool = False
    dias_receso_descontados: int = 0
    dias_proyectados: int | None = None
    par_incluye_t4: bool = False
    t4_sin_revisar: bool = False
    tasa_diaria: float | None = None
    detalle_parque: DetalleParque | None = None
    detalle_calculo: str = ""
    etiqueta_nivel: str = ""
    metodo: MetodoEstimacion = "NoAplica"
    marcas: frozenset[MarcaEstimacion] = field(default_factory=frozenset)
